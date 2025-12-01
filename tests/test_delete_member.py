import pytest
from httpx import AsyncClient
from sqlalchemy import select
from backend.models.user import User, Role

@pytest.mark.asyncio
async def test_delete_member(client: AsyncClient, db_session):
    # Seed roles
    admin_role = Role(role_name="ADMIN")
    member_role = Role(role_name="MEMBER")
    db_session.add(admin_role)
    db_session.add(member_role)
    await db_session.commit()

    # Create admin user
    from backend.core.security import hash_password
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

    # Create member user
    member_user = User(
        email="member@example.com",
        first_name="Member",
        last_name="User",
        phone_number="5559998877",
        password_hash=hash_password("memberpassword"),
        is_active=True
    )
    member_user.roles.append(member_role)
    db_session.add(member_user)
    await db_session.commit()
    await db_session.refresh(member_user)
    member_id = member_user.id

    # Login as admin
    login_data = {"username": "admin@example.com", "password": "adminpassword"}
    response = await client.post("/api/v1/auth/login/access-token", data=login_data)
    assert response.status_code == 200
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Delete member
    delete_resp = await client.delete(f"/api/v1/members/{member_id}", headers=admin_headers)
    assert delete_resp.status_code == 200
    
    # Verify response contains the soft deleted user
    deleted_data = delete_resp.json()
    assert deleted_data["id"] == member_id
    assert deleted_data["is_active"] == False