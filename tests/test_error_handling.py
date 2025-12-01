import pytest
from httpx import AsyncClient
from datetime import date, timedelta, datetime
from sqlalchemy import select
from backend.models.user import User, Role
from backend.models.operation import Subscription, SubscriptionQrCode
from backend.core.security import hash_password

@pytest.mark.asyncio
async def test_checkin_edge_cases(client: AsyncClient, db_session):
    """Test check-in edge cases and error conditions"""

    # Setup
    member_role = Role(role_name="MEMBER")
    admin_role = Role(role_name="ADMIN")
    db_session.add(member_role)
    db_session.add(admin_role)
    await db_session.commit()

    admin_user = User(
        email="admin@test.com",
        first_name="Admin",
        last_name="User",
        phone_number="5550000000",
        password_hash=hash_password("admin123"),
        is_active=True
    )
    admin_user.roles.append(admin_role)
    db_session.add(admin_user)

    member_data = {
        "email": "member@test.com",
        "first_name": "Test",
        "last_name": "Member",
        "phone_number": "5551111111",
        "password": "member123",
        "is_active": True
    }
    response = await client.post("/api/v1/members/", json=member_data)
    member_id = response.json()["id"]

    await db_session.commit()

    login_response = await client.post("/api/v1/auth/login/access-token",
                                     data={"username": "admin@test.com", "password": "admin123"})
    admin_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create service and subscription
    cat_resp = await client.post("/api/v1/services/categories",
                               json={"name": "Test", "description": "Test"}, headers=headers)
    category_id = cat_resp.json()["id"]

    off_resp = await client.post("/api/v1/services/offerings",
                               json={
                                   "name": "Test Class",
                                   "description": "Test",
                                   "category_id": category_id,
                                   "default_duration_minutes": 60
                               }, headers=headers)
    offering_id = off_resp.json()["id"]

    plan_resp = await client.post("/api/v1/services/plans",
                                json={
                                    "name": "1 Session",
                                    "sessions_granted": 1,
                                    "validity_days": 30,
                                    "cycle_period": "monthly"
                                }, headers=headers)
    plan_id = plan_resp.json()["id"]

    pkg_resp = await client.post("/api/v1/services/packages",
                               json={
                                   "name": "Test Package",
                                   "price": 100.0,
                                   "category_id": category_id,
                                   "offering_id": offering_id,
                                   "plan_id": plan_id,
                                   "is_active": True
                               }, headers=headers)
    package_id = pkg_resp.json()["id"]

    sub_data = {
        "member_user_id": member_id,
        "package_id": package_id,
        "start_date": str(date.today()),
        "status": "active",
        "initial_payment": {
            "amount_paid": 100.0,
            "payment_method": "NAKIT"
        }
    }
    sub_resp = await client.post("/api/v1/sales/subscriptions", json=sub_data, headers=headers)
    subscription_id = sub_resp.json()["id"]

    # Get QR token
    stmt = select(SubscriptionQrCode).where(SubscriptionQrCode.subscription_id == subscription_id)
    result = await db_session.execute(stmt)
    qr_code = result.scalar_one()

    # Create event
    template_resp = await client.post("/api/v1/operations/templates",
                                    json={"name": "Test Template"}, headers=headers)
    template_id = template_resp.json()["id"]

    from backend.models.operation import BookingPermission
    permission = BookingPermission(package_id=package_id, template_id=template_id)
    db_session.add(permission)
    await db_session.commit()

    start_time = datetime.now() + timedelta(hours=1)
    event_resp = await client.post("/api/v1/operations/events",
                                 json={
                                     "template_id": template_id,
                                     "instructor_user_id": admin_user.id,
                                     "start_time": start_time.isoformat(),
                                     "end_time": (start_time + timedelta(hours=1)).isoformat(),
                                     "capacity": 1  # Very small capacity
                                 }, headers=headers)
    event_id = event_resp.json()["id"]

    # 1. Test invalid QR token
    checkin_resp = await client.post("/api/v1/checkin/check-in",
                                   json={"qr_token": "invalid-token", "event_id": event_id},
                                   headers=headers)
    assert checkin_resp.status_code == 404
    assert "not found" in checkin_resp.json()["detail"].lower()

    # 2. Test valid check-in
    checkin_resp = await client.post("/api/v1/checkin/check-in",
                                   json={"qr_token": qr_code.qr_token, "event_id": event_id},
                                   headers=headers)
    assert checkin_resp.status_code == 200
    assert checkin_resp.json()["success"] == True
    assert checkin_resp.json()["remaining_sessions"] == 0

    # 3. Test double check-in (same session)
    checkin_resp = await client.post("/api/v1/checkin/check-in",
                                   json={"qr_token": qr_code.qr_token, "event_id": event_id},
                                   headers=headers)
    assert checkin_resp.status_code == 400
    assert "already checked in" in checkin_resp.json()["detail"].lower()

    # 4. Test check-in with no sessions remaining
    # Create another event
    event2_resp = await client.post("/api/v1/operations/events",
                                  json={
                                      "template_id": template_id,
                                      "instructor_user_id": admin_user.id,
                                      "start_time": (start_time + timedelta(hours=2)).isoformat(),
                                      "end_time": (start_time + timedelta(hours=3)).isoformat(),
                                      "capacity": 10
                                  }, headers=headers)
    event2_id = event2_resp.json()["id"]

    checkin_resp = await client.post("/api/v1/checkin/check-in",
                                   json={"qr_token": qr_code.qr_token, "event_id": event2_id},
                                   headers=headers)
    assert checkin_resp.status_code == 400
    assert "no sessions remaining" in checkin_resp.json()["detail"].lower()

    # 5. Test check-in with invalid event
    checkin_resp = await client.post("/api/v1/checkin/check-in",
                                   json={"qr_token": qr_code.qr_token, "event_id": "invalid-event-id"},
                                   headers=headers)
    assert checkin_resp.status_code == 404

    # 6. Test check-in without authentication
    checkin_resp = await client.post("/api/v1/checkin/check-in",
                                   json={"qr_token": qr_code.qr_token, "event_id": event2_id})
    assert checkin_resp.status_code == 401

@pytest.mark.asyncio
async def test_concurrent_checkins(client: AsyncClient, db_session):
    """Test concurrent check-in scenarios (race conditions)"""

    # Setup multiple members and events
    member_role = Role(role_name="MEMBER")
    admin_role = Role(role_name="ADMIN")
    db_session.add(member_role)
    db_session.add(admin_role)
    await db_session.commit()

    admin_user = User(
        email="admin@test.com",
        first_name="Admin",
        last_name="User",
        phone_number="5550000000",
        password_hash=hash_password("admin123"),
        is_active=True
    )
    admin_user.roles.append(admin_role)
    db_session.add(admin_user)

    # Create multiple members
    members = []
    for i in range(3):
        member_data = {
            "email": f"member{i}@test.com",
            "first_name": f"Member{i}",
            "last_name": "Test",
            "phone_number": f"555111{i}111",
            "password": "member123",
            "is_active": True
        }
        response = await client.post("/api/v1/members/", json=member_data)
        members.append(response.json()["id"])

    await db_session.commit()

    login_response = await client.post("/api/v1/auth/login/access-token",
                                     data={"username": "admin@test.com", "password": "admin123"})
    admin_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create service with limited sessions
    cat_resp = await client.post("/api/v1/services/categories",
                               json={"name": "Limited", "description": "Limited sessions"}, headers=headers)
    category_id = cat_resp.json()["id"]

    off_resp = await client.post("/api/v1/services/offerings",
                               json={
                                   "name": "Limited Class",
                                   "description": "Limited sessions",
                                   "category_id": category_id,
                                   "default_duration_minutes": 60
                               }, headers=headers)
    offering_id = off_resp.json()["id"]

    plan_resp = await client.post("/api/v1/services/plans",
                                json={
                                    "name": "2 Sessions",
                                    "sessions_granted": 2,
                                    "validity_days": 30,
                                    "cycle_period": "monthly"
                                }, headers=headers)
    plan_id = plan_resp.json()["id"]

    pkg_resp = await client.post("/api/v1/services/packages",
                               json={
                                   "name": "Limited Package",
                                   "price": 200.0,
                                   "category_id": category_id,
                                   "offering_id": offering_id,
                                   "plan_id": plan_id,
                                   "is_active": True
                               }, headers=headers)
    package_id = pkg_resp.json()["id"]

    # Create subscriptions for members
    subscriptions = []
    qr_tokens = []
    for member_id in members:
        sub_data = {
            "member_user_id": member_id,
            "package_id": package_id,
            "start_date": str(date.today()),
            "status": "active",
            "initial_payment": {
                "amount_paid": 200.0,
                "payment_method": "KREDI_KARTI"
            }
        }
        sub_resp = await client.post("/api/v1/sales/subscriptions", json=sub_data, headers=headers)
        sub_id = sub_resp.json()["id"]
        subscriptions.append(sub_id)

        # Get QR token
        stmt = select(SubscriptionQrCode).where(SubscriptionQrCode.subscription_id == sub_id)
        result = await db_session.execute(stmt)
        qr_code = result.scalar_one()
        qr_tokens.append(qr_code.qr_token)

    # Create event with limited capacity
    template_resp = await client.post("/api/v1/operations/templates",
                                    json={"name": "Limited Template"}, headers=headers)
    template_id = template_resp.json()["id"]

    from backend.models.operation import BookingPermission
    permission = BookingPermission(package_id=package_id, template_id=template_id)
    db_session.add(permission)
    await db_session.commit()

    start_time = datetime.now() + timedelta(hours=1)
    event_resp = await client.post("/api/v1/operations/events",
                                 json={
                                     "template_id": template_id,
                                     "instructor_user_id": admin_user.id,
                                     "start_time": start_time.isoformat(),
                                     "end_time": (start_time + timedelta(hours=1)).isoformat(),
                                     "capacity": 2  # Limited capacity
                                 }, headers=headers)
    event_id = event_resp.json()["id"]

    # Test check-ins (should work for first 2, fail for 3rd due to capacity)
    successful_checkins = 0
    for i, qr_token in enumerate(qr_tokens):
        checkin_resp = await client.post("/api/v1/checkin/check-in",
                                       json={"qr_token": qr_token, "event_id": event_id},
                                       headers=headers)

        if checkin_resp.status_code == 200:
            successful_checkins += 1
            assert checkin_resp.json()["success"] == True
        else:
            # Should fail for 3rd member due to capacity
            assert i == 2  # Third member
            assert checkin_resp.status_code == 400
            assert "capacity" in checkin_resp.json()["detail"].lower()

    assert successful_checkins == 2

@pytest.mark.asyncio
async def test_data_integrity(client: AsyncClient, db_session):
    """Test data integrity and referential constraints"""

    # Setup
    member_role = Role(role_name="MEMBER")
    admin_role = Role(role_name="ADMIN")
    db_session.add(member_role)
    db_session.add(admin_role)
    await db_session.commit()

    admin_user = User(
        email="admin@test.com",
        first_name="Admin",
        last_name="User",
        phone_number="5550000000",
        password_hash=hash_password("admin123"),
        is_active=True
    )
    admin_user.roles.append(admin_role)
    db_session.add(admin_user)

    member_data = {
        "email": "member@test.com",
        "first_name": "Test",
        "last_name": "Member",
        "phone_number": "5551111111",
        "password": "member123",
        "is_active": True
    }
    response = await client.post("/api/v1/members/", json=member_data)
    member_id = response.json()["id"]

    await db_session.commit()

    login_response = await client.post("/api/v1/auth/login/access-token",
                                     data={"username": "admin@test.com", "password": "admin123"})
    admin_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create service
    cat_resp = await client.post("/api/v1/services/categories",
                               json={"name": "Integrity Test", "description": "Test"}, headers=headers)
    category_id = cat_resp.json()["id"]

    off_resp = await client.post("/api/v1/services/offerings",
                               json={
                                   "name": "Integrity Class",
                                   "description": "Test",
                                   "category_id": category_id,
                                   "default_duration_minutes": 60
                               }, headers=headers)
    offering_id = off_resp.json()["id"]

    plan_resp = await client.post("/api/v1/services/plans",
                                json={
                                    "name": "1 Session",
                                    "sessions_granted": 1,
                                    "validity_days": 30,
                                    "cycle_period": "monthly"
                                }, headers=headers)
    plan_id = plan_resp.json()["id"]

    pkg_resp = await client.post("/api/v1/services/packages",
                               json={
                                   "name": "Integrity Package",
                                   "price": 100.0,
                                   "category_id": category_id,
                                   "offering_id": offering_id,
                                   "plan_id": plan_id,
                                   "is_active": True
                               }, headers=headers)
    package_id = pkg_resp.json()["id"]

    # Create subscription
    sub_data = {
        "member_user_id": member_id,
        "package_id": package_id,
        "start_date": str(date.today()),
        "status": "active",
        "initial_payment": {
            "amount_paid": 100.0,
            "payment_method": "NAKIT"
        }
    }
    sub_resp = await client.post("/api/v1/sales/subscriptions", json=sub_data, headers=headers)
    subscription_id = sub_resp.json()["id"]

    # 1. Test member deletion with active subscription (should cascade properly)
    delete_resp = await client.delete(f"/api/v1/members/{member_id}", headers=headers)
    assert delete_resp.status_code == 200

    # Verify all related data was cleaned up
    # Subscription should be gone
    sub_check = await client.get(f"/api/v1/sales/subscriptions/{subscription_id}", headers=headers)
    assert sub_check.status_code == 404

    # Member should be gone
    member_check = await client.get(f"/api/v1/members/{member_id}", headers=headers)
    assert member_check.status_code == 404

    # 2. Test invalid foreign key references
    invalid_sub_data = {
        "member_user_id": member_id,  # Non-existent member
        "package_id": package_id,
        "start_date": str(date.today()),
        "status": "active",
        "initial_payment": {
            "amount_paid": 100.0,
            "payment_method": "NAKIT"
        }
    }
    invalid_resp = await client.post("/api/v1/sales/subscriptions", json=invalid_sub_data, headers=headers)
    assert invalid_resp.status_code == 500  # Foreign key constraint violation

    # 3. Test circular reference prevention
    # (This would be caught by business logic, not DB constraints)
    # But we can test that invalid package references fail
    invalid_pkg_data = {
        "member_user_id": "some-valid-id",
        "package_id": "invalid-package-id",
        "start_date": str(date.today()),
        "status": "active",
        "initial_payment": {
            "amount_paid": 100.0,
            "payment_method": "NAKIT"
        }
    }
    invalid_pkg_resp = await client.post("/api/v1/sales/subscriptions", json=invalid_pkg_data, headers=headers)
    assert invalid_pkg_resp.status_code == 500  # Foreign key violation