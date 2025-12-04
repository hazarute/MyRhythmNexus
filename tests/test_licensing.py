import pytest
from datetime import datetime, timedelta
from backend.models.license import License
from backend.services.license import generate_license_key
from backend.core.time_utils import get_turkey_time

@pytest.mark.asyncio
async def test_license_lifecycle(client, db_session):
    # 1. Create a valid license directly in DB
    license_key = generate_license_key()
    machine_id = "TEST-MACHINE-ID-123"
    
    license_obj = License(
        license_key=license_key,
        client_name="Test Client",
        is_active=True,
        expires_at=get_turkey_time() + timedelta(days=30),
        features={"qr_checkin": True, "finance": False}
    )
    db_session.add(license_obj)
    await db_session.commit()
    
    # 2. Validate License (First time - Activation)
    response = await client.post("/api/v1/license/validate", json={
        "license_key": license_key,
        "machine_id": machine_id
    })
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["features"]["qr_checkin"] is True
    
    # Verify hardware_id is locked
    await db_session.refresh(license_obj)
    assert license_obj.hardware_id == machine_id

    # 3. Validate License (Same machine - Success)
    response = await client.post("/api/v1/license/validate", json={
        "license_key": license_key,
        "machine_id": machine_id
    })
    assert response.status_code == 200
    assert response.json()["valid"] is True

    # 4. Validate License (Different machine - Fail)
    response = await client.post("/api/v1/license/validate", json={
        "license_key": license_key,
        "machine_id": "DIFFERENT-MACHINE-ID"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "already used" in data["message"]

    # 5. Check Feature Endpoint
    response = await client.get(f"/api/v1/license/check-feature/qr_checkin?license_key={license_key}")
    assert response.status_code == 200
    assert response.json() is True
    
    response = await client.get(f"/api/v1/license/check-feature/finance?license_key={license_key}")
    assert response.status_code == 200
    assert response.json() is False

@pytest.mark.asyncio
async def test_expired_license(client, db_session):
    license_key = generate_license_key()
    machine_id = "TEST-MACHINE-ID-123"
    
    # Create expired license
    license_obj = License(
        license_key=license_key,
        client_name="Expired Client",
        is_active=True,
        expires_at=get_turkey_time() - timedelta(days=1),
        features={}
    )
    db_session.add(license_obj)
    await db_session.commit()

    response = await client.post("/api/v1/license/validate", json={
        "license_key": license_key,
        "machine_id": machine_id
    })
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "expired" in data["message"]

@pytest.mark.asyncio
async def test_inactive_license(client, db_session):
    license_key = generate_license_key()
    machine_id = "TEST-MACHINE-ID-123"
    
    # Create inactive license
    license_obj = License(
        license_key=license_key,
        client_name="Inactive Client",
        is_active=False,
        expires_at=get_turkey_time() + timedelta(days=30),
        features={}
    )
    db_session.add(license_obj)
    await db_session.commit()

    response = await client.post("/api/v1/license/validate", json={
        "license_key": license_key,
        "machine_id": machine_id
    })
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "inactive" in data["message"]
