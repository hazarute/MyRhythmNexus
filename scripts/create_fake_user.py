import asyncio
from sqlalchemy.future import select

from backend.core.database import SessionLocal
from backend.core.security import hash_password
from backend.models.user import User, Role


async def main():
    async with SessionLocal() as db:
        # Ensure MEMBER role exists
        result = await db.execute(select(Role).where(Role.role_name == "MEMBER"))
        member_role = result.scalar_one_or_none()
        if not member_role:
            member_role = Role(role_name="MEMBER")
            db.add(member_role)
            await db.commit()
            await db.refresh(member_role)

        # Check if user already exists
        result = await db.execute(select(User).where(User.email == "fake@example.com"))
        user = result.scalar_one_or_none()
        if user:
            print("User already exists: fake@example.com")
            return

        # Create fake active user
        user = User(
            email="fake@example.com",
            first_name="Test",
            last_name="User",
            phone_number="555-555-5555",
            password_hash=hash_password("Password123"),
            is_active=True,
        )

        user.roles.append(member_role)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        print("Created fake user: fake@example.com with password Password123")


if __name__ == "__main__":
    asyncio.run(main())
