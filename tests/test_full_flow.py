import pytest
from httpx import AsyncClient
from datetime import date
from sqlalchemy import select
from backend.models.operation import SubscriptionQrCode

@pytest.mark.asyncio
async def test_full_flow(client: AsyncClient, db_session):
    # Seed Roles
    from backend.models.user import Role, User
    from backend.core.security import hash_password
    
    admin_role = Role(role_name="ADMIN")
    member_role = Role(role_name="MEMBER")
    db_session.add(admin_role)
    db_session.add(member_role)
    await db_session.commit()

    # 1. Create Admin User (Manual)
    admin_user = User(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        phone_number="5551112233",
        password_hash=hash_password("adminpassword"),
        is_active=True
    )
    # Re-fetch role to attach to session if needed, but they are in same session
    admin_user.roles.append(admin_role)
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)
    admin_user_id = admin_user.id
    
    # Create Instructor (using Admin user)
    from backend.models.user import Instructor
    instructor = Instructor(user_id=admin_user_id, bio="Master Trainer")
    db_session.add(instructor)
    
    await db_session.commit()

    # Login as Admin to get token
    login_data = {"username": "admin@example.com", "password": "adminpassword"}
    response = await client.post("/api/v1/auth/login/access-token", data=login_data)
    assert response.status_code == 200
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Register Member User
    member_data = {
        "email": "member@example.com",
        "password": "memberpassword",
        "first_name": "Member",
        "last_name": "User",
        "phone_number": "5559998877"
    }
    response = await client.post("/api/v1/auth/register", json=member_data)
    assert response.status_code == 200
    member_id = response.json()["id"]

    # 3. Create Service Structure (Category -> Offering -> Plan -> Package)
    # Category
    cat_resp = await client.post("/api/v1/services/categories", json={"name": "Fitness", "description": "General Fitness"}, headers=admin_headers)
    assert cat_resp.status_code == 200
    category_id = cat_resp.json()["id"]

    # Offering
    off_resp = await client.post("/api/v1/services/offerings", json={
        "name": "Pilates", 
        "description": "Pilates Class", 
        "category_id": category_id,
        "default_duration_minutes": 60
    }, headers=admin_headers)
    assert off_resp.status_code == 200
    offering_id = off_resp.json()["id"]

    # Plan
    plan_resp = await client.post("/api/v1/services/plans", json={
        "name": "10 Pack", 
        "sessions_granted": 10, 
        "validity_days": 60, 
        "cycle_period": "monthly"
    }, headers=admin_headers)
    assert plan_resp.status_code == 200
    plan_id = plan_resp.json()["id"]

    # Package
    pkg_resp = await client.post("/api/v1/services/packages", json={
        "name": "Pilates 10 Pack",
        "price": 1000.0,
        "category_id": category_id,
        "offering_id": offering_id,
        "plan_id": plan_id,
        "is_active": True
    }, headers=admin_headers)
    assert pkg_resp.status_code == 200
    package_id = pkg_resp.json()["id"]

    # 4. Sell Subscription
    sub_data = {
        "member_user_id": member_id,
        "package_id": package_id,
        "start_date": str(date.today()),
        "status": "active",
        "initial_payment": {
            "amount_paid": 1000.0,
            "payment_method": "KREDI_KARTI"
        }
    }
    sub_resp = await client.post("/api/v1/sales/subscriptions-with-events", json=sub_data, headers=admin_headers)
    assert sub_resp.status_code == 200
    subscription_id = sub_resp.json()["id"]
    
    # 4.5 Create Class Event for Check-in
    # Create Template
    tmpl_resp = await client.post("/api/v1/operations/templates", json={"name": "Morning Pilates"}, headers=admin_headers)
    assert tmpl_resp.status_code == 200
    template_id = tmpl_resp.json()["id"]

    # Create Event
    from datetime import datetime, timedelta
    start_time = datetime.now() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=1)
    
    event_resp = await client.post("/api/v1/operations/events", json={
        "template_id": template_id,
        "instructor_user_id": admin_user_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "capacity": 20
    }, headers=admin_headers)
    assert event_resp.status_code == 200
    event_id = event_resp.json()["id"]

    # Create Booking Permission (Manual)
    from backend.models.operation import BookingPermission
    permission = BookingPermission(package_id=package_id, template_id=template_id)
    db_session.add(permission)
    await db_session.commit()

    # 5. Web Login (Phone)
    login_data = {
        "phone_number": "5559998877",
        "password": "memberpassword"
    }
    # Note: Form data
    login_resp = await client.post("/web/login", data=login_data, follow_redirects=False)
    assert login_resp.status_code == 302
    assert "access_token" in login_resp.cookies

    # 6. Access Web Dashboard (should redirect to card detail since 1 card)
    web_resp = await client.get("/web/", follow_redirects=False)
    assert web_resp.status_code == 302
    assert f"/web/cards/{subscription_id}" in web_resp.headers["location"]

    # 7. Get Card Detail
    card_resp = await client.get(f"/web/cards/{subscription_id}")
    assert card_resp.status_code == 200
    assert "Pilates 10 Pack" in card_resp.text
    
    # Get QR Token from DB for Check-in test
    stmt = select(SubscriptionQrCode).where(SubscriptionQrCode.subscription_id == subscription_id)
    result = await db_session.execute(stmt)
    qr_code_obj = result.scalar_one()
    qr_token = qr_code_obj.qr_token

    # 8. Check-in
    checkin_data = {"qr_token": qr_token, "event_id": event_id}
    checkin_resp = await client.post("/api/v1/checkin/check-in", json=checkin_data, headers=admin_headers)
    assert checkin_resp.status_code == 200
    assert checkin_resp.json()["success"] == True
    assert checkin_resp.json()["remaining_sessions"] == 9
