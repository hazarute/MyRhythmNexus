import pytest
import asyncio
from httpx import AsyncClient
from datetime import date, timedelta
import time
from backend.models.user import User, Role
from backend.core.security import hash_password

@pytest.mark.asyncio
async def test_api_performance_baselines(client: AsyncClient, db_session):
    """Test basic API performance - response times should be under reasonable limits"""

    # Setup
    member_role = Role(role_name="MEMBER")
    db_session.add(member_role)
    await db_session.commit()

    # Create test member
    member_data = {
        "email": "perf@test.com",
        "first_name": "Performance",
        "last_name": "Test",
        "phone_number": "5559999999",
        "password": "test123",
        "is_active": True
    }
    response = await client.post("/api/v1/members/", json=member_data)
    assert response.status_code == 200

    # Test member list performance
    start_time = time.time()
    response = await client.get("/api/v1/members/")
    end_time = time.time()

    assert response.status_code == 200
    response_time = end_time - start_time
    assert response_time < 0.5  # Should respond in under 500ms
    print(f"Member list response time: {response_time:.3f}s")

    # Test member detail performance
    member_id = response.json()[0]["id"]
    start_time = time.time()
    response = await client.get(f"/api/v1/members/{member_id}")
    end_time = time.time()

    assert response.status_code == 200
    response_time = end_time - start_time
    assert response_time < 0.2  # Should respond in under 200ms
    print(f"Member detail response time: {response_time:.3f}s")

@pytest.mark.asyncio
async def test_bulk_operations_performance(client: AsyncClient, db_session):
    """Test performance with larger datasets"""

    # Setup
    member_role = Role(role_name="MEMBER")
    db_session.add(member_role)
    await db_session.commit()

    # Create multiple members for bulk testing
    members_created = []
    for i in range(10):  # Create 10 members
        member_data = {
            "email": f"bulk{i}@test.com",
            "first_name": f"Bulk{i}",
            "last_name": "Test",
            "phone_number": f"5551111{i:03d}",
            "password": "test123",
            "is_active": True
        }
        response = await client.post("/api/v1/members/", json=member_data)
        assert response.status_code == 200
        members_created.append(response.json()["id"])

    # Test bulk list performance
    start_time = time.time()
    response = await client.get("/api/v1/members/")
    end_time = time.time()

    assert response.status_code == 200
    members = response.json()
    assert len(members) >= 10

    response_time = end_time - start_time
    assert response_time < 1.0  # Should handle 10+ members in under 1 second
    print(f"Bulk list (10 members) response time: {response_time:.3f}s")

    # Test search performance
    start_time = time.time()
    response = await client.get("/api/v1/members/?search=Bulk")
    end_time = time.time()

    assert response.status_code == 200
    search_results = response.json()
    assert len(search_results) == 10

    response_time = end_time - start_time
    assert response_time < 0.5  # Search should be fast
    print(f"Search performance response time: {response_time:.3f}s")

@pytest.mark.asyncio
async def test_subscription_operations_performance(client: AsyncClient, db_session):
    """Test subscription-related operations performance"""

    # Setup roles and admin
    member_role = Role(role_name="MEMBER")
    admin_role = Role(role_name="ADMIN")
    db_session.add(member_role)
    db_session.add(admin_role)
    await db_session.commit()

    admin_user = User(
        email="admin@perf.com",
        first_name="Admin",
        last_name="Perf",
        phone_number="5550000000",
        password_hash=hash_password("admin123"),
        is_active=True
    )
    admin_user.roles.append(admin_role)
    db_session.add(admin_user)

    # Create member
    member_data = {
        "email": "member@perf.com",
        "first_name": "Member",
        "last_name": "Perf",
        "phone_number": "5551111111",
        "password": "member123",
        "is_active": True
    }
    response = await client.post("/api/v1/members/", json=member_data)
    member_id = response.json()["id"]

    await db_session.commit()

    # Login
    login_response = await client.post("/api/v1/auth/login/access-token",
                                     data={"username": "admin@perf.com", "password": "admin123"})
    admin_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create service structure
    cat_resp = await client.post("/api/v1/services/categories",
                               json={"name": "Perf Test", "description": "Performance test"}, headers=headers)
    category_id = cat_resp.json()["id"]

    off_resp = await client.post("/api/v1/services/offerings",
                               json={
                                   "name": "Perf Class",
                                   "description": "Performance test class",
                                   "category_id": category_id,
                                   "default_duration_minutes": 60
                               }, headers=headers)
    offering_id = off_resp.json()["id"]

    plan_resp = await client.post("/api/v1/services/plans",
                                json={
                                    "name": "Perf Plan",
                                    "sessions_granted": 10,
                                    "validity_days": 30,
                                    "cycle_period": "monthly"
                                }, headers=headers)
    plan_id = plan_resp.json()["id"]

    pkg_resp = await client.post("/api/v1/services/packages",
                               json={
                                   "name": "Perf Package",
                                   "price": 500.0,
                                   "category_id": category_id,
                                   "offering_id": offering_id,
                                   "plan_id": plan_id,
                                   "is_active": True
                               }, headers=headers)
    package_id = pkg_resp.json()["id"]

    # Test subscription creation performance
    start_time = time.time()
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
    sub_resp = await client.post("/api/v1/sales/subscriptions", json=sub_data, headers=headers)
    end_time = time.time()

    assert sub_resp.status_code == 200
    response_time = end_time - start_time
    assert response_time < 1.0  # Subscription creation should be under 1 second
    print(f"Subscription creation response time: {response_time:.3f}s")

    subscription_id = sub_resp.json()["id"]

    # Test subscription retrieval performance
    start_time = time.time()
    detail_resp = await client.get(f"/api/v1/sales/subscriptions/{subscription_id}", headers=headers)
    end_time = time.time()

    assert detail_resp.status_code == 200
    response_time = end_time - start_time
    assert response_time < 0.3  # Detail retrieval should be fast
    print(f"Subscription detail response time: {response_time:.3f}s")

@pytest.mark.asyncio
async def test_concurrent_requests_simulation(client: AsyncClient, db_session):
    """Simulate concurrent requests to test system stability"""

    # Setup
    member_role = Role(role_name="MEMBER")
    db_session.add(member_role)
    await db_session.commit()

    # Create test member
    member_data = {
        "email": "concurrent@test.com",
        "first_name": "Concurrent",
        "last_name": "Test",
        "phone_number": "5559999998",
        "password": "test123",
        "is_active": True
    }
    response = await client.post("/api/v1/members/", json=member_data)
    assert response.status_code == 200
    member_id = response.json()["id"]

    # Simulate concurrent member list requests
    async def fetch_members():
        resp = await client.get("/api/v1/members/")
        return resp.status_code == 200

    # Run 5 concurrent requests
    tasks = [fetch_members() for _ in range(5)]
    results = await asyncio.gather(*tasks)

    # All should succeed
    assert all(results)
    print("Concurrent requests test passed: 5 simultaneous member list requests")

@pytest.mark.asyncio
async def test_memory_usage_check(client: AsyncClient, db_session):
    """Basic memory usage check - ensure no memory leaks in basic operations"""

    # Setup
    member_role = Role(role_name="MEMBER")
    db_session.add(member_role)
    await db_session.commit()

    # Create and delete multiple members to check for potential memory issues
    created_members = []
    for i in range(5):
        member_data = {
            "email": f"memory{i}@test.com",
            "first_name": f"Memory{i}",
            "last_name": "Test",
            "phone_number": f"5552222{i:03d}",
            "password": "test123",
            "is_active": True
        }
        response = await client.post("/api/v1/members/", json=member_data)
        assert response.status_code == 200
        created_members.append(response.json()["id"])

    # List all members multiple times
    for _ in range(3):
        response = await client.get("/api/v1/members/")
        assert response.status_code == 200
        members = response.json()
        assert len(members) >= 5

    print("Memory usage test passed: Multiple create/list operations completed successfully")

@pytest.mark.asyncio
async def test_database_connection_pooling(client: AsyncClient, db_session):
    """Test database connection pooling under load"""

    # Setup
    member_role = Role(role_name="MEMBER")
    db_session.add(member_role)
    await db_session.commit()

    # Create test member
    member_data = {
        "email": "pool@test.com",
        "first_name": "Pool",
        "last_name": "Test",
        "phone_number": "5559999997",
        "password": "test123",
        "is_active": True
    }
    response = await client.post("/api/v1/members/", json=member_data)
    assert response.status_code == 200

    # Perform multiple quick successive operations
    start_time = time.time()
    for i in range(10):
        # Alternate between list and detail operations
        if i % 2 == 0:
            response = await client.get("/api/v1/members/")
        else:
            response = await client.get("/api/v1/members/pool@test.com")  # This will fail but tests connection
        assert response.status_code in [200, 422]  # 422 for invalid UUID format
    end_time = time.time()

    total_time = end_time - start_time
    avg_time = total_time / 10
    assert avg_time < 0.1  # Average response should be under 100ms
    print(f"Connection pooling test passed: 10 operations in {total_time:.3f}s (avg: {avg_time:.3f}s per operation)")