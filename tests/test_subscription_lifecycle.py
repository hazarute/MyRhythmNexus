import pytest
from httpx import AsyncClient
from datetime import date, timedelta
from sqlalchemy import select
from backend.models.user import User, Role
from backend.models.operation import Subscription, SubscriptionQrCode, Payment
from backend.core.security import hash_password

@pytest.mark.asyncio
async def test_subscription_lifecycle(client: AsyncClient, db_session):
    """Test complete subscription lifecycle: creation, usage, expiration"""

    # Setup roles and users
    member_role = Role(role_name="MEMBER")
    admin_role = Role(role_name="ADMIN")
    db_session.add(member_role)
    db_session.add(admin_role)
    await db_session.commit()

    # Create admin user
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

    # Create member
    member_data = {
        "email": "member@test.com",
        "first_name": "Test",
        "last_name": "Member",
        "phone_number": "5551111111",
        "password": "member123",
        "is_active": True
    }
    response = await client.post("/api/v1/members/", json=member_data)
    assert response.status_code == 200
    member = response.json()
    member_id = member["id"]

    await db_session.commit()
    await db_session.refresh(admin_user)

    # Login as admin
    login_response = await client.post("/api/v1/auth/login/access-token",
                                     data={"username": "admin@test.com", "password": "admin123"})
    assert login_response.status_code == 200
    admin_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create service structure
    # Category
    cat_resp = await client.post("/api/v1/services/categories",
                               json={"name": "Pilates", "description": "Pilates Classes"},
                               headers=headers)
    assert cat_resp.status_code == 200
    category_id = cat_resp.json()["id"]

    # Offering
    off_resp = await client.post("/api/v1/services/offerings",
                               json={
                                   "name": "Group Pilates",
                                   "description": "Group Pilates Session",
                                   "category_id": category_id,
                                   "default_duration_minutes": 60
                               }, headers=headers)
    assert off_resp.status_code == 200
    offering_id = off_resp.json()["id"]

    # Plan (5 sessions, 30 days validity)
    plan_resp = await client.post("/api/v1/services/plans",
                                json={
                                    "name": "5 Session Pack",
                                    "sessions_granted": 5,
                                    "validity_days": 30,
                                    "cycle_period": "monthly"
                                }, headers=headers)
    assert plan_resp.status_code == 200
    plan_id = plan_resp.json()["id"]

    # Package
    pkg_resp = await client.post("/api/v1/services/packages",
                               json={
                                   "name": "Pilates 5-Pack",
                                   "price": 500.0,
                                   "category_id": category_id,
                                   "offering_id": offering_id,
                                   "plan_id": plan_id,
                                   "is_active": True
                               }, headers=headers)
    assert pkg_resp.status_code == 200
    package_id = pkg_resp.json()["id"]

    # 1. Create subscription
    start_date = date.today()
    sub_data = {
        "member_user_id": member_id,
        "package_id": package_id,
        "start_date": str(start_date),
        "status": "active",
        "initial_payment": {
            "amount_paid": 500.0,
            "payment_method": "KREDI_KARTI"
        }
    }

    sub_resp = await client.post("/api/v1/sales/subscriptions-with-events", json=sub_data, headers=headers)
    assert sub_resp.status_code == 200
    subscription = sub_resp.json()
    subscription_id = subscription["id"]

    # Verify subscription was created with correct data
    assert subscription["member_user_id"] == member_id
    assert subscription["package_id"] == package_id
    assert subscription["status"] == "active"
    assert subscription["used_sessions"] == 0  # Should start with 0 used sessions

    # Verify QR code was generated
    stmt = select(SubscriptionQrCode).where(SubscriptionQrCode.subscription_id == subscription_id)
    result = await db_session.execute(stmt)
    qr_code = result.scalar_one_or_none()
    assert qr_code is not None
    assert qr_code.qr_token is not None
    qr_token_str = qr_code.qr_token

    # Verify payment was recorded
    stmt = select(Payment).where(Payment.subscription_id == subscription_id)
    result = await db_session.execute(stmt)
    payment = result.scalar_one_or_none()
    assert payment is not None
    assert payment.amount_paid == 500.0
    assert payment.payment_method.value == "KREDI_KARTI"

    # 2. Test check-in (use one session)
    # Create a class event first
    from backend.models.operation import ClassTemplate, ClassEvent
    from backend.models.user import Instructor

    # Create instructor
    # Fetch admin user again to avoid MissingGreenlet
    stmt = select(User).where(User.email == "admin@test.com")
    result = await db_session.execute(stmt)
    admin_user = result.scalar_one()
    admin_user_id = admin_user.id
    
    instructor = Instructor(user_id=admin_user_id, bio="Pilates Instructor")
    db_session.add(instructor)
    await db_session.commit()

    # Create template
    template_resp = await client.post("/api/v1/operations/templates",
                                    json={"name": "Morning Pilates"}, headers=headers)
    assert template_resp.status_code == 200
    template_id = template_resp.json()["id"]

    # Create booking permission
    from backend.models.operation import BookingPermission
    permission = BookingPermission(package_id=package_id, template_id=template_id)
    db_session.add(permission)
    await db_session.commit()

    # Create event
    from datetime import datetime
    start_time = datetime.now() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=1)

    event_resp = await client.post("/api/v1/operations/events",
                                 json={
                                     "template_id": template_id,
                                     "instructor_user_id": admin_user_id,
                                     "start_time": start_time.isoformat(),
                                     "end_time": end_time.isoformat(),
                                     "capacity": 10
                                 }, headers=headers)
    assert event_resp.status_code == 200
    event_id = event_resp.json()["id"]

    # Check-in
    checkin_data = {
        "qr_token": qr_token_str,
        "event_id": event_id
    }
    checkin_resp = await client.post("/api/v1/checkin/check-in", json=checkin_data, headers=headers)
    assert checkin_resp.status_code == 200
    checkin_result = checkin_resp.json()
    assert checkin_result["success"] == True
    assert checkin_result["remaining_sessions"] == 4

    # 3. Test subscription status after usage
    sub_detail_resp = await client.get(f"/api/v1/sales/subscriptions/{subscription_id}", headers=headers)
    assert sub_detail_resp.status_code == 200
    updated_sub = sub_detail_resp.json()
    assert updated_sub["used_sessions"] == 1
    assert updated_sub["status"] == "active"

    # 4. Test multiple check-ins
    for i in range(3):  # Use 3 more sessions
        # Create new event for each check-in
        event_time = start_time + timedelta(days=i+1)
        event_end = event_time + timedelta(hours=1)

        event_resp = await client.post("/api/v1/operations/events",
                                     json={
                                         "template_id": template_id,
                                         "instructor_user_id": admin_user_id,
                                         "start_time": event_time.isoformat(),
                                         "end_time": event_end.isoformat(),
                                         "capacity": 10
                                     }, headers=headers)
        assert event_resp.status_code == 200
        event_id = event_resp.json()["id"]

        checkin_resp = await client.post("/api/v1/checkin/check-in",
                                       json={"qr_token": qr_token_str, "event_id": event_id},
                                       headers=headers)
        assert checkin_resp.status_code == 200
        assert checkin_resp.json()["remaining_sessions"] == 3 - i

    # 5. Test subscription completion (all sessions used)
    # Create final event
    start_time = start_time + timedelta(days=10)
    event_resp = await client.post("/api/v1/operations/events",
                                 json={
                                     "template_id": template_id,
                                     "instructor_user_id": admin_user_id,
                                     "start_time": start_time.isoformat(),
                                     "end_time": (start_time + timedelta(hours=1)).isoformat(),
                                     "capacity": 10
                                 }, headers=headers)
    event_id = event_resp.json()["id"]

    final_checkin_resp = await client.post("/api/v1/checkin/check-in",
                                         json={"qr_token": qr_token_str, "event_id": event_id},
                                         headers=headers)
    assert final_checkin_resp.status_code == 200, final_checkin_resp.text
    assert final_checkin_resp.json()["remaining_sessions"] == 0

    # Check final subscription status
    final_sub_resp = await client.get(f"/api/v1/sales/subscriptions/{subscription_id}", headers=headers)
    assert final_sub_resp.status_code == 200
    final_sub = final_sub_resp.json()
    assert final_sub["used_sessions"] == 5
    # Status might remain active until expiration date even if sessions are used
    assert final_sub["status"] in ["active", "completed"]

@pytest.mark.asyncio
async def test_subscription_expiration(client: AsyncClient, db_session):
    """Test subscription expiration scenarios"""

    # Setup similar to above test
    member_role = Role(role_name="MEMBER")
    admin_role = Role(role_name="ADMIN")
    db_session.add(member_role)
    db_session.add(admin_role)
    await db_session.commit()

    # Create admin user
    admin_user = User(
        email="admin2@test.com",
        first_name="Admin",
        last_name="User",
        phone_number="5550000001",
        password_hash=hash_password("admin123"),
        is_active=True
    )
    admin_user.roles.append(admin_role)
    db_session.add(admin_user)
    await db_session.commit()  # Commit to get the ID
    await db_session.refresh(admin_user)
    admin_user_id = admin_user.id

    # Create instructor record
    from backend.models.user import Instructor
    instructor = Instructor(user_id=admin_user_id, bio="Test Instructor")
    db_session.add(instructor)
    await db_session.commit()

    member_data = {
        "email": "member2@test.com",
        "first_name": "Test",
        "last_name": "Member2",
        "phone_number": "5551111112",
        "password": "member123",
        "is_active": True
    }
    response = await client.post("/api/v1/members/", json=member_data)
    member_id = response.json()["id"]

    await db_session.commit()
    await db_session.refresh(admin_user)

    # Login
    login_response = await client.post("/api/v1/auth/login/access-token",
                                     data={"username": "admin2@test.com", "password": "admin123"})
    admin_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create service (short validity: 1 day)
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
                                    "name": "1 Day 1 Session",
                                    "sessions_granted": 1,
                                    "validity_days": 1,  # Very short validity
                                    "cycle_period": "daily"
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

    # Create subscription with past end date (expired)
    yesterday = date.today() - timedelta(days=1)
    sub_data = {
        "member_user_id": member_id,
        "package_id": package_id,
        "start_date": str(yesterday - timedelta(days=1)),
        "status": "active",
        "initial_payment": {
            "amount_paid": 100.0,
            "payment_method": "NAKIT"
        }
    }

    sub_resp = await client.post("/api/v1/sales/subscriptions-with-events", json=sub_data, headers=headers)
    assert sub_resp.status_code == 200
    subscription_id = sub_resp.json()["id"]

    # Manually set end date to yesterday (expired)
    stmt = select(Subscription).where(Subscription.id == subscription_id)
    result = await db_session.execute(stmt)
    subscription = result.scalar_one()
    subscription.end_date = yesterday
    await db_session.commit()

    # Get QR token
    stmt = select(SubscriptionQrCode).where(SubscriptionQrCode.subscription_id == subscription_id)
    result = await db_session.execute(stmt)
    qr_code = result.scalar_one()

    # Try to check-in with expired subscription
    # Create event first
    template_resp = await client.post("/api/v1/operations/templates",
                                    json={"name": "Test Template"}, headers=headers)
    template_id = template_resp.json()["id"]

    # Fetch admin user again
    stmt = select(User).where(User.email == "admin2@test.com")
    result = await db_session.execute(stmt)
    admin_user = result.scalar_one()
    admin_user_id = admin_user.id

    from datetime import datetime
    start_time = datetime.now() + timedelta(hours=1)
    event_resp = await client.post("/api/v1/operations/events",
                                 json={
                                     "template_id": template_id,
                                     "instructor_user_id": admin_user_id,
                                     "start_time": start_time.isoformat(),
                                     "end_time": (start_time + timedelta(hours=1)).isoformat(),
                                     "capacity": 10
                                 }, headers=headers)
    assert event_resp.status_code == 200, event_resp.text
    event_id = event_resp.json()["id"]

    # Attempt check-in (should fail due to expiration)
    checkin_resp = await client.post("/api/v1/checkin/check-in",
                                   json={"qr_token": qr_code.qr_token, "event_id": event_id},
                                   headers=headers)
    assert checkin_resp.status_code == 400
    assert "expired" in checkin_resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_subscription_renewal(client: AsyncClient, db_session):
    """Test subscription renewal scenarios"""

    # Setup
    member_role = Role(role_name="MEMBER")
    admin_role = Role(role_name="ADMIN")
    db_session.add(member_role)
    db_session.add(admin_role)
    await db_session.commit()

    admin_user = User(
        email="admin3@test.com",
        first_name="Admin",
        last_name="User",
        phone_number="5550000003",
        password_hash=hash_password("admin123"),
        is_active=True
    )
    admin_user.roles.append(admin_role)
    db_session.add(admin_user)
    await db_session.commit()  # Commit to get the ID

    member_data = {
        "email": "member3@test.com",
        "first_name": "Test",
        "last_name": "Member3",
        "phone_number": "5551111113",
        "password": "member123",
        "is_active": True
    }
    response = await client.post("/api/v1/members/", json=member_data)
    member_id = response.json()["id"]

    await db_session.commit()

    login_response = await client.post("/api/v1/auth/login/access-token",
                                     data={"username": "admin3@test.com", "password": "admin123"})
    admin_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create renewable service
    cat_resp = await client.post("/api/v1/services/categories",
                               json={"name": "Renewable", "description": "Renewable service"}, headers=headers)
    category_id = cat_resp.json()["id"]

    off_resp = await client.post("/api/v1/services/offerings",
                               json={
                                   "name": "Monthly Pilates",
                                   "description": "Monthly subscription",
                                   "category_id": category_id,
                                   "default_duration_minutes": 60
                               }, headers=headers)
    offering_id = off_resp.json()["id"]

    plan_resp = await client.post("/api/v1/services/plans",
                                json={
                                    "name": "Monthly Unlimited",
                                    "sessions_granted": 30,  # High number for monthly
                                    "validity_days": 30,
                                    "cycle_period": "monthly"
                                }, headers=headers)
    plan_id = plan_resp.json()["id"]

    pkg_resp = await client.post("/api/v1/services/packages",
                               json={
                                   "name": "Monthly Pilates",
                                   "price": 800.0,
                                   "category_id": category_id,
                                   "offering_id": offering_id,
                                   "plan_id": plan_id,
                                   "is_active": True
                               }, headers=headers)
    package_id = pkg_resp.json()["id"]

    # Create initial subscription
    start_date = date.today()
    sub_data = {
        "member_user_id": member_id,
        "package_id": package_id,
        "start_date": str(start_date),
        "status": "active",
        "initial_payment": {
            "amount_paid": 800.0,
            "payment_method": "KREDI_KARTI"
        }
    }

    sub_resp = await client.post("/api/v1/sales/subscriptions-with-events", json=sub_data, headers=headers)
    assert sub_resp.status_code == 200
    subscription_id = sub_resp.json()["id"]

    # Use some sessions (simulate 10 sessions used)
    stmt = select(Subscription).where(Subscription.id == subscription_id)
    result = await db_session.execute(stmt)
    subscription = result.scalar_one()
    subscription.sessions_remaining = 20  # 30 - 10 = 20
    await db_session.commit()

    # Test renewal (create new subscription for same member/package)
    renewal_data = {
        "member_user_id": member_id,
        "package_id": package_id,
        "start_date": str(start_date + timedelta(days=30)),  # Next month
        "status": "active",
        "initial_payment": {
            "amount_paid": 800.0,
            "payment_method": "KREDI_KARTI"
        }
    }

    renewal_resp = await client.post("/api/v1/sales/subscriptions-with-events", json=renewal_data, headers=headers)
    assert renewal_resp.status_code == 200
    renewal_sub = renewal_resp.json()

    # Verify renewal
    assert renewal_sub["member_user_id"] == member_id
    assert renewal_sub["package_id"] == package_id
    assert renewal_sub["used_sessions"] == 0  # Fresh subscription starts with 0 used sessions
    assert renewal_sub["start_date"].startswith(str(start_date + timedelta(days=30)))

    # Verify both subscriptions exist
    subs_resp = await client.get(f"/api/v1/sales/subscriptions?member_id={member_id}", headers=headers)
    assert subs_resp.status_code == 200
    subscriptions = subs_resp.json()
    assert len(subscriptions) == 2

    # Active subscription should be the renewal (later start date)
    active_subs = [s for s in subscriptions if s["status"] == "active"]
    # Both subscriptions are active because of the grace period overlap
    assert len(active_subs) == 2
    # Verify renewal is in the list
    renewal_in_list = any(s["id"] == renewal_sub["id"] for s in active_subs)
    assert renewal_in_list is True

@pytest.mark.asyncio
async def test_create_subscription_with_price_override(client: AsyncClient, db_session):
    """Test creating subscription with custom purchase price override"""

    # Setup roles and users
    member_role = Role(role_name="MEMBER")
    admin_role = Role(role_name="ADMIN")
    db_session.add(member_role)
    db_session.add(admin_role)
    await db_session.commit()

    # Create admin user
    admin_user = User(
        email="admin_override@test.com",
        first_name="Admin",
        last_name="Override",
        phone_number="5550000004",
        password_hash=hash_password("admin123"),
        is_active=True
    )
    admin_user.roles.append(admin_role)
    db_session.add(admin_user)

    # Create member
    member_data = {
        "email": "member_override@test.com",
        "first_name": "Test",
        "last_name": "Override",
        "phone_number": "5551111114",
        "password": "member123",
        "is_active": True
    }
    response = await client.post("/api/v1/members/", json=member_data)
    assert response.status_code == 200
    member = response.json()
    member_id = member["id"]

    await db_session.commit()

    # Login as admin
    login_response = await client.post("/api/v1/auth/login/access-token",
                                     data={"username": "admin_override@test.com", "password": "admin123"})
    assert login_response.status_code == 200
    admin_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create service structure
    # Category
    cat_resp = await client.post("/api/v1/services/categories",
                               json={"name": "Override Test", "description": "Price Override Test"},
                               headers=headers)
    assert cat_resp.status_code == 200
    category_id = cat_resp.json()["id"]

    # Offering
    off_resp = await client.post("/api/v1/services/offerings",
                               json={
                                   "name": "Override Offering",
                                   "description": "Test offering",
                                   "category_id": category_id,
                                   "default_duration_minutes": 60
                               }, headers=headers)
    assert off_resp.status_code == 200
    offering_id = off_resp.json()["id"]

    # Plan
    plan_resp = await client.post("/api/v1/services/plans",
                                json={
                                    "name": "Override Plan",
                                    "sessions_granted": 10,
                                    "validity_days": 30,
                                    "cycle_period": "monthly"
                                }, headers=headers)
    assert plan_resp.status_code == 200
    plan_id = plan_resp.json()["id"]

    # Package with price 500
    pkg_resp = await client.post("/api/v1/services/packages",
                               json={
                                   "name": "Override Package",
                                   "price": 500.0,
                                   "category_id": category_id,
                                   "offering_id": offering_id,
                                   "plan_id": plan_id,
                                   "is_active": True
                               }, headers=headers)
    assert pkg_resp.status_code == 200
    package_id = pkg_resp.json()["id"]

    # Test 1: Create subscription without price override (should use package price)
    start_date = date.today()
    sub_data_normal = {
        "member_user_id": member_id,
        "package_id": package_id,
        "start_date": str(start_date),
        "status": "active",
        "initial_payment": {
            "amount_paid": 500.0,
            "payment_method": "KREDI_KARTI"
        }
    }

    sub_resp_normal = await client.post("/api/v1/sales/subscriptions-with-events", json=sub_data_normal, headers=headers)
    assert sub_resp_normal.status_code == 200
    subscription_normal = sub_resp_normal.json()
    assert subscription_normal["purchase_price"] == "500.00"  # Should use package price

    # Test 2: Create subscription with price override (discounted price)
    sub_data_override = {
        "member_user_id": member_id,
        "package_id": package_id,
        "start_date": str(start_date),
        "status": "active",
        "purchase_price_override": 400.0,  # Discounted price
        "initial_payment": {
            "amount_paid": 400.0,
            "payment_method": "NAKIT"
        }
    }

    sub_resp_override = await client.post("/api/v1/sales/subscriptions-with-events", json=sub_data_override, headers=headers)
    assert sub_resp_override.status_code == 200
    subscription_override = sub_resp_override.json()
    assert subscription_override["purchase_price"] == "400.00"  # Should use override price

    # Test 3: Try invalid price override (negative)
    sub_data_invalid = {
        "member_user_id": member_id,
        "package_id": package_id,
        "start_date": str(start_date),
        "status": "active",
        "purchase_price_override": -100.0,  # Invalid negative price
        "initial_payment": {
            "amount_paid": 500.0,
            "payment_method": "NAKIT"
        }
    }

    sub_resp_invalid = await client.post("/api/v1/sales/subscriptions-with-events", json=sub_data_invalid, headers=headers)
    assert sub_resp_invalid.status_code == 400
    assert "must be greater than 0" in sub_resp_invalid.json()["detail"]

    # Test 4: Try price override too high (more than double)
    sub_data_too_high = {
        "member_user_id": member_id,
        "package_id": package_id,
        "start_date": str(start_date),
        "status": "active",
        "purchase_price_override": 1200.0,  # More than double (500 * 2 = 1000)
        "initial_payment": {
            "amount_paid": 1200.0,
            "payment_method": "NAKIT"
        }
    }

    sub_resp_too_high = await client.post("/api/v1/sales/subscriptions-with-events", json=sub_data_too_high, headers=headers)
    assert sub_resp_too_high.status_code == 400
    assert "cannot be more than double" in sub_resp_too_high.json()["detail"]

    # Test 5: Test with subscriptions-with-events endpoint
    sub_data_with_events = {
        "member_user_id": member_id,
        "package_id": package_id,
        "start_date": str(start_date),
        "status": "active",
        "purchase_price_override": 450.0,  # Another valid override
        "initial_payment": {
            "amount_paid": 450.0,
            "payment_method": "HAVALE_EFT"
        }
        # No class_events for this test
    }

    sub_resp_with_events = await client.post("/api/v1/sales/subscriptions-with-events", json=sub_data_with_events, headers=headers)
    assert sub_resp_with_events.status_code == 200
    subscription_with_events = sub_resp_with_events.json()
    assert subscription_with_events["purchase_price"] == "450.00"  # Should use override price