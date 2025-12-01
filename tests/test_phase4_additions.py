import pytest
from httpx import AsyncClient
from datetime import date, datetime, timedelta
from sqlalchemy import select
from backend.models.operation import SubscriptionQrCode, BookingPermission
from backend.models.user import Role, User, Instructor
from backend.core.security import hash_password

@pytest.mark.asyncio
async def test_finance_and_scan(client: AsyncClient, db_session):
    # --- SETUP ---
    # Seed Roles
    admin_role = Role(role_name="ADMIN")
    member_role = Role(role_name="MEMBER")
    db_session.add(admin_role)
    db_session.add(member_role)
    await db_session.commit()

    # Create Admin
    admin_user = User(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        phone_number="5551112233",
        password_hash=hash_password("adminpassword"),
        is_active=True
    )
    admin_user.roles.append(admin_role)
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)
    admin_user_id = admin_user.id
    
    # Create Instructor
    instructor = Instructor(user_id=admin_user_id, bio="Master Trainer")
    db_session.add(instructor)
    await db_session.commit()

    # Login Admin
    login_data = {"username": "admin@example.com", "password": "adminpassword"}
    response = await client.post("/api/v1/auth/login/access-token", data=login_data)
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create Member
    member_data = {
        "email": "member@example.com",
        "password": "memberpassword",
        "first_name": "Member",
        "last_name": "User",
        "phone_number": "5559998877"
    }
    response = await client.post("/api/v1/auth/register", json=member_data)
    member_id = response.json()["id"]

    # Create Service Structure
    cat_resp = await client.post("/api/v1/services/categories", json={"name": "Fitness", "description": "General Fitness"}, headers=admin_headers)
    category_id = cat_resp.json()["id"]

    off_resp = await client.post("/api/v1/services/offerings", json={"name": "Pilates", "description": "Pilates Class", "category_id": category_id, "default_duration_minutes": 60}, headers=admin_headers)
    offering_id = off_resp.json()["id"]

    plan_resp = await client.post("/api/v1/services/plans", json={"name": "10 Pack", "sessions_granted": 10, "validity_days": 60, "cycle_period": "monthly"}, headers=admin_headers)
    plan_id = plan_resp.json()["id"]

    pkg_resp = await client.post("/api/v1/services/packages", json={"name": "Pilates 10 Pack", "price": 1000.0, "category_id": category_id, "offering_id": offering_id, "plan_id": plan_id, "is_active": True}, headers=admin_headers)
    package_id = pkg_resp.json()["id"]

    # Sell Subscription (Creates Payment)
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
    sub_resp = await client.post("/api/v1/sales/subscriptions", json=sub_data, headers=admin_headers)
    subscription_id = sub_resp.json()["id"]

    # --- TEST 1: Finance History ---
    finance_resp = await client.get("/api/v1/sales/payments", params={"page": 1, "size": 10}, headers=admin_headers)
    assert finance_resp.status_code == 200
    data = finance_resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["amount_paid"] == "1000.00"
    assert data["items"][0]["member_name"] == "Member User"
    assert data["items"][0]["package_name"] == "Pilates 10 Pack"

    # Filter by Member
    finance_resp_filtered = await client.get("/api/v1/sales/payments", params={"page": 1, "size": 10, "member_id": member_id}, headers=admin_headers)
    assert finance_resp_filtered.status_code == 200
    assert finance_resp_filtered.json()["total"] == 1

    # --- TEST 2: QR Scan Logic ---
    # Create Template & Event
    tmpl_resp = await client.post("/api/v1/operations/templates", json={"name": "Morning Pilates"}, headers=admin_headers)
    template_id = tmpl_resp.json()["id"]

    # Event starting in 10 mins
    start_time = datetime.now() + timedelta(minutes=10)
    end_time = start_time + timedelta(hours=1)
    
    event_resp = await client.post("/api/v1/operations/events", json={
        "template_id": template_id,
        "instructor_user_id": admin_user_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "capacity": 20
    }, headers=admin_headers)
    event_id = event_resp.json()["id"]

    # Add Permission
    permission = BookingPermission(package_id=package_id, template_id=template_id)
    db_session.add(permission)
    await db_session.commit()

    # Get QR Token
    stmt = select(SubscriptionQrCode).where(SubscriptionQrCode.subscription_id == subscription_id)
    result = await db_session.execute(stmt)
    qr_token = result.scalar_one().qr_token

    # Scan QR
    scan_resp = await client.get(f"/api/v1/checkin/scan?qr_token={qr_token}", headers=admin_headers)
    assert scan_resp.status_code == 200
    scan_data = scan_resp.json()
    
    assert scan_data["valid"] == True
    assert scan_data["member_name"] == "Member User"
    assert scan_data["remaining_sessions"] == 10
    assert len(scan_data["eligible_events"]) == 1
    assert scan_data["eligible_events"][0]["id"] == event_id
    assert scan_data["eligible_events"][0]["name"] == "Morning Pilates"

    # Test Invalid QR
    scan_resp_invalid = await client.get("/api/v1/checkin/scan?qr_token=invalid_token", headers=admin_headers)
    assert scan_resp_invalid.status_code == 200
    assert scan_resp_invalid.json()["valid"] == False
