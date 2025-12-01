import pytest
from httpx import AsyncClient
from sqlalchemy import select, func
from backend.models.user import User, Role
from backend.core.security import hash_password

@pytest.mark.asyncio
async def test_member_management_crud(client: AsyncClient, db_session):
    """Test complete member CRUD operations"""

    # Setup roles
    member_role = Role(role_name="MEMBER")
    db_session.add(member_role)
    await db_session.commit()

    # 1. Create member
    member_data = {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "5551234567",
        "password": "testpass123",
        "is_active": True
    }

    response = await client.post("/api/v1/members/", json=member_data)
    assert response.status_code == 200
    member = response.json()
    member_id = member["id"]

    # 2. Read member
    response = await client.get(f"/api/v1/members/{member_id}")
    assert response.status_code == 200
    retrieved_member = response.json()
    assert retrieved_member["email"] == member_data["email"]

    # 3. Update member
    update_data = {
        "first_name": "Updated",
        "last_name": "Name",
        "phone_number": "5559876543"
    }
    response = await client.put(f"/api/v1/members/{member_id}", json=update_data)
    assert response.status_code == 200
    updated_member = response.json()
    assert updated_member["first_name"] == "Updated"
    assert updated_member["phone_number"] == "555-987-6543"
    response = await client.get("/api/v1/members/")
    assert response.status_code == 200
    members = response.json()
    assert len(members) >= 1
    assert any(m["id"] == member_id for m in members)

    # 5. Deactivate member
    update_data = {"is_active": False}
    response = await client.put(f"/api/v1/members/{member_id}", json=update_data)
    assert response.status_code == 200

    # 6. Check inactive filtering
    response = await client.get("/api/v1/members/?include_inactive=true")
    assert response.status_code == 200
    all_members = response.json()
    inactive_member = next((m for m in all_members if m["id"] == member_id), None)
    assert inactive_member is not None
    assert inactive_member["is_active"] == False

    # Active only should not include inactive member
    response = await client.get("/api/v1/members/")
    assert response.status_code == 200
    active_members = response.json()
    assert not any(m["id"] == member_id for m in active_members)

    # 7. Delete member (hard delete)
    response = await client.delete(f"/api/v1/members/{member_id}")
    if response.status_code != 200:
        print(f"Delete failed: {response.status_code} - {response.text}")
    assert response.status_code == 200

    # 8. Verify member is gone
    response = await client.get(f"/api/v1/members/{member_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_member_validation_errors(client: AsyncClient, db_session):
    """Test member validation and error handling"""

    # Setup roles
    member_role = Role(role_name="MEMBER")
    db_session.add(member_role)
    await db_session.commit()

    # 1. Test duplicate email
    member_data = {
        "email": "duplicate@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "5551234567",
        "password": "testpass123",
        "is_active": True
    }

    # First creation should succeed
    response = await client.post("/api/v1/members/", json=member_data)
    assert response.status_code == 200

    # Second creation should fail
    response = await client.post("/api/v1/members/", json=member_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

    # 2. Test invalid email
    invalid_data = member_data.copy()
    invalid_data["email"] = "invalid-email"
    response = await client.post("/api/v1/members/", json=invalid_data)
    assert response.status_code == 422  # Validation error

    # 3. Test missing required fields
    incomplete_data = {"email": "test@example.com"}
    response = await client.post("/api/v1/members/", json=incomplete_data)
    assert response.status_code == 422

    # 4. Test invalid phone number format
    invalid_phone_data = member_data.copy()
    invalid_phone_data["email"] = "unique@example.com"
    invalid_phone_data["phone_number"] = "invalid-phone"
    response = await client.post("/api/v1/members/", json=invalid_phone_data)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_member_search_and_filtering(client: AsyncClient, db_session):
    """Test member search and filtering functionality"""

    # Setup roles
    member_role = Role(role_name="MEMBER")
    db_session.add(member_role)
    await db_session.commit()

    # Create test members
    members_data = [
        {
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "5551111111",
            "password": "test123",
            "is_active": True
        },
        {
            "email": "jane.smith@example.com",
            "first_name": "Jane",
            "last_name": "Smith",
            "phone_number": "5552222222",
            "password": "test123",
            "is_active": True
        },
        {
            "email": "bob.wilson@example.com",
            "first_name": "Bob",
            "last_name": "Wilson",
            "phone_number": "5553333333",
            "password": "test123",
            "is_active": False
        }
    ]

    created_members = []
    for member_data in members_data:
        response = await client.post("/api/v1/members/", json=member_data)
        assert response.status_code == 200
        created_members.append(response.json())

    # 1. Test search by first name
    response = await client.get("/api/v1/members/?search=John")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["first_name"] == "John"

    # 2. Test search by last name
    response = await client.get("/api/v1/members/?search=Smith")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["last_name"] == "Smith"

    # 3. Test search by email
    response = await client.get("/api/v1/members/?search=jane.smith")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert "jane.smith" in results[0]["email"]

    # 4. Test search by phone
    response = await client.get("/api/v1/members/?search=555-111")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert "555-111" in results[0]["phone_number"]

    # 5. Test case insensitive search
    response = await client.get("/api/v1/members/?search=JOHN")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1

    # 6. Test no results search
    response = await client.get("/api/v1/members/?search=nonexistent")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 0

    # 7. Test active only (should exclude Bob)
    response = await client.get("/api/v1/members/")
    assert response.status_code == 200
    active_results = response.json()
    assert len(active_results) == 2
    assert not any(m["first_name"] == "Bob" for m in active_results)

    # 8. Test include inactive
    response = await client.get("/api/v1/members/?include_inactive=true")
    assert response.status_code == 200
    all_results = response.json()
    assert len(all_results) == 3
    assert any(m["first_name"] == "Bob" for m in all_results)