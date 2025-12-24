import pytest
from httpx import AsyncClient
from datetime import date, datetime, timedelta
from sqlalchemy import select
from backend.models.operation import SubscriptionQrCode, BookingPermission
from backend.models.user import Role, User, Instructor
from backend.core.security import hash_password

@pytest.mark.asyncio
async def test_time_based_checkin_flow(client: AsyncClient, db_session):
    """
    Test TIME_BASED subscription check-in without requiring events.
    
    Scenario:
    1. Create TIME_BASED plan and package
    2. Sell subscription to member
    3. Check-in via QR without selecting event
    4. Verify attendance_count increments
    5. Check history shows "Zaman Bazlı Katılım"
    """
    
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
    
    # Login as Member to get their token
    login_data_member = {"username": "member@example.com", "password": "memberpassword"}
    response = await client.post("/api/v1/auth/login/access-token", data=login_data_member)
    member_token = response.json()["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}"}

    # Create Service Structure
    cat_resp = await client.post("/api/v1/services/categories", json={"name": "Fitness", "description": "General Fitness"}, headers=admin_headers)
    category_id = cat_resp.json()["id"]

    off_resp = await client.post("/api/v1/services/offerings", json={"name": "Yoga", "description": "Yoga Class", "category_id": category_id, "default_duration_minutes": 60}, headers=admin_headers)
    offering_id = off_resp.json()["id"]

    # --- TEST 1: Create TIME_BASED Plan ---
    plan_resp = await client.post(
        "/api/v1/services/plans", 
        json={
            "name": "Unlimited Monthly", 
            "sessions_granted": 0,  # 0 indicates TIME_BASED
            "validity_days": 30, 
            "cycle_period": "monthly",
            "access_type": "TIME_BASED"  # Explicitly set TIME_BASED
        }, 
        headers=admin_headers
    )
    assert plan_resp.status_code == 200
    plan_id = plan_resp.json()["id"]
    plan_data = plan_resp.json()
    assert plan_data["access_type"] == "TIME_BASED"

    pkg_resp = await client.post(
        "/api/v1/services/packages", 
        json={
            "name": "Yoga Unlimited", 
            "price": 500.0, 
            "category_id": category_id, 
            "offering_id": offering_id, 
            "plan_id": plan_id, 
            "is_active": True
        }, 
        headers=admin_headers
    )
    assert pkg_resp.status_code == 200
    package_id = pkg_resp.json()["id"]

    # --- TEST 2: Sell TIME_BASED Subscription ---
    sub_data = {
        "member_user_id": member_id,
        "package_id": package_id,
        "start_date": str(date.today()),
        "status": "active",
        "initial_payment": {
            "amount_paid": 500.0,
            "payment_method": "KREDI_KARTI"
        }
    }
    sub_resp = await client.post("/api/v1/sales/subscriptions-with-events", json=sub_data, headers=admin_headers)
    assert sub_resp.status_code == 200
    subscription_id = sub_resp.json()["id"]
    sub_info = sub_resp.json()
    assert sub_info["access_type"] == "TIME_BASED"
    assert sub_info["attendance_count"] == 0

    # --- TEST 3: Get QR Token and Check Initial Status ---
    stmt = select(SubscriptionQrCode).where(SubscriptionQrCode.subscription_id == subscription_id)
    result = await db_session.execute(stmt)
    qr_token = result.scalar_one().qr_token

    # Scan QR - should work without events
    scan_resp = await client.get(f"/api/v1/checkin/scan?qr_token={qr_token}", headers=admin_headers)
    assert scan_resp.status_code == 200
    scan_data = scan_resp.json()
    assert scan_data["valid"] == True
    assert scan_data["member_name"] == "Member User"
    assert scan_data["access_type"] == "TIME_BASED"

    # --- TEST 4: Check-in via /check-in endpoint for TIME_BASED ---
    checkin_resp = await client.post(
        "/api/v1/checkin/check-in",
        json={"qr_token": qr_token},
        headers=admin_headers
    )
    assert checkin_resp.status_code == 200
    checkin_data = checkin_resp.json()
    assert checkin_data["success"] == True
    assert checkin_data["member_name"] == "Member User"
    assert checkin_data["check_in_time"] is not None

    # --- TEST 5: Verify attendance_count incremented ---
    sub_check = await client.get(f"/api/v1/sales/subscriptions/{subscription_id}", headers=member_headers)
    assert sub_check.status_code == 200
    sub_data_after = sub_check.json()
    assert sub_data_after["attendance_count"] == 1

    # --- TEST 6: Multiple check-ins (TIME_BASED should allow unlimited) ---
    for i in range(2, 6):
        checkin_resp = await client.post(
            "/api/v1/checkin/check-in",
            json={"qr_token": qr_token},
            headers=admin_headers
        )
        assert checkin_resp.status_code == 200

    # Verify attendance_count = 5
    sub_check = await client.get(f"/api/v1/sales/subscriptions/{subscription_id}", headers=member_headers)
    sub_data_after = sub_check.json()
    assert sub_data_after["attendance_count"] == 5

    # --- TEST 7: Check history shows "Zaman Bazlı Katılım" ---
    history_resp = await client.get("/api/v1/checkin/history", headers=member_headers)
    assert history_resp.status_code == 200
    history_data = history_resp.json()
    assert len(history_data) >= 5
    
    # Verify no event_id in response for TIME_BASED check-ins
    for record in history_data[:5]:
        assert record["event_id"] is None
        assert record["class_name"] == "Zaman Bazlı Katılım"

    # --- TEST 8: Check-in without event for SESSION_BASED (optional) ---
    # Create SESSION_BASED plan for comparison
    session_plan_resp = await client.post(
        "/api/v1/services/plans", 
        json={
            "name": "10 Pack", 
            "sessions_granted": 10,
            "validity_days": 60, 
            "cycle_period": "monthly",
            "access_type": "SESSION_BASED"
        }, 
        headers=admin_headers
    )
    assert session_plan_resp.status_code == 200
    session_plan_id = session_plan_resp.json()["id"]

    session_pkg_resp = await client.post(
        "/api/v1/services/packages", 
        json={
            "name": "Yoga 10 Pack", 
            "price": 300.0, 
            "category_id": category_id, 
            "offering_id": offering_id, 
            "plan_id": session_plan_id, 
            "is_active": True
        }, 
        headers=admin_headers
    )
    assert session_pkg_resp.status_code == 200
    session_package_id = session_pkg_resp.json()["id"]

    # Sell SESSION_BASED subscription
    session_sub_data = {
        "member_user_id": member_id,
        "package_id": session_package_id,
        "start_date": str(date.today()),
        "status": "active",
        "initial_payment": {
            "amount_paid": 300.0,
            "payment_method": "KREDI_KARTI"
        }
    }
    session_sub_resp = await client.post("/api/v1/sales/subscriptions-with-events", json=session_sub_data, headers=admin_headers)
    assert session_sub_resp.status_code == 200
    session_subscription_id = session_sub_resp.json()["id"]
    
    # Get QR for SESSION_BASED
    stmt_session = select(SubscriptionQrCode).where(SubscriptionQrCode.subscription_id == session_subscription_id)
    result_session = await db_session.execute(stmt_session)
    session_qr_token = result_session.scalar_one().qr_token

    # Check-in without event (should work since event_id is optional)
    session_checkin_resp = await client.post(
        "/api/v1/checkin/check-in",
        json={"qr_token": session_qr_token, "event_id": None},
        headers=admin_headers
    )
    assert session_checkin_resp.status_code == 200
    session_checkin_data = session_checkin_resp.json()
    assert session_checkin_data["success"] == True
    
    # Verify used_sessions incremented (SESSION_BASED uses used_sessions)
    session_sub_check = await client.get(f"/api/v1/sales/subscriptions/{session_subscription_id}", headers=member_headers)
    session_sub_data_after = session_sub_check.json()
    assert session_sub_data_after["used_sessions"] == 1

    print("[PASS] All TIME_BASED and SESSION_BASED tests passed!")
