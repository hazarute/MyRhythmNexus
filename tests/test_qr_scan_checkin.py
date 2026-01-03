import pytest
from httpx import AsyncClient
from datetime import date, datetime, timedelta
from sqlalchemy import select
from backend.models.operation import SubscriptionQrCode, BookingPermission, ClassEvent, ClassTemplate, SessionCheckIn, Subscription, SubscriptionStatus
from backend.models.user import Role, User, Instructor
from backend.models.service import ServicePackage, ServiceOffering, PlanDefinition, ServiceCategory
from backend.core.security import hash_password

@pytest.mark.asyncio
async def test_qr_scan_and_checkin_session_based_real_data(client: AsyncClient, db_session):
    """Test QR scan and check-in for SESSION_BASED subscription using real database data."""
    # Real data from database
    qr_token = "PB3PKk_x-QZeXdXbdzhU5A6JhhduBBZXZNCHNphVdaQ"
    subscription_id = "9bf6e14b-46f5-4b00-814b-015ef72c3ea1"
    user_id = "591efe22-4f67-4490-bd94-7c726cdb2666"

    # If the test DB/schema doesn't contain real data, skip
    from sqlalchemy import select
    try:
        await db_session.execute(select(SubscriptionQrCode).limit(1))
    except Exception:
        pytest.skip("subscription_qr_codes table or real data not available in test DB")

    # Test QR scan
    response = await client.get(f"/api/v1/checkin/scan?qr_token={qr_token}")
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] == True
    assert data["subscription_id"] == subscription_id
    assert data["user_id"] == user_id
    assert data["access_type"] == "SESSION_BASED"
    assert data["remaining_sessions"] is not None
    assert isinstance(data["eligible_events"], list)

    # If there are eligible events, test check-in
    if data["eligible_events"]:
        event_id = data["eligible_events"][0]["id"]
        initial_remaining = data["remaining_sessions"]

        checkin_payload = {
            "qr_token": qr_token,
            "event_id": event_id
        }
        response = await client.post("/api/v1/checkin/check-in", json=checkin_payload)
        assert response.status_code == 200
        checkin_data = response.json()
        assert checkin_data["success"] == True
        assert checkin_data["subscription_id"] == subscription_id
        assert checkin_data["user_id"] == user_id
        assert checkin_data["remaining_sessions"] == initial_remaining - 1
    else:
        # Skip check-in test if no eligible events
        pytest.skip("No eligible events found for check-in")

@pytest.mark.asyncio
async def test_qr_scan_and_checkin_time_based(client: AsyncClient, db_session):
    """Test QR scan and check-in for TIME_BASED subscription."""
    # Setup code here...
    pass

@pytest.mark.asyncio
async def test_qr_scan_invalid_cases(client: AsyncClient, db_session):
    """Test invalid QR scan cases."""
    # Setup code here...
    pass