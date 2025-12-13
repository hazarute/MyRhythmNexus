#!/usr/bin/env python3
"""Delete a user by id from the local database.

Usage:
  PYTHONPATH=. python scripts/delete_user.py <user_id> [--admin-email email] [--admin-pass pass]

If admin credentials are provided they will be verified before deletion.
"""
import sys
import asyncio
import argparse

from sqlalchemy.future import select

from backend.core.database import SessionLocal
from backend.models.user import User
from backend.core.security import verify_password


async def delete_user(user_id: str, admin_email: str | None, admin_pass: str | None):
    async with SessionLocal() as session:
        # if admin creds provided, verify
        if admin_email and admin_pass:
            q = select(User).where(User.email == admin_email.lower())
            res = await session.execute(q)
            admin = res.scalar_one_or_none()
            if not admin:
                print(f"Admin user not found: {admin_email}")
                return 2
            if not verify_password(admin_pass, admin.password_hash):
                print("Admin password verification failed")
                return 2
            print(f"Admin verified: {admin_email}")

        # load target user
        q = select(User).where(User.id == user_id)
        res = await session.execute(q)
        user = res.scalar_one_or_none()
        if not user:
            print(f"User not found: {user_id}")
            return 1

        print(f"Deleting user: id={user.id}, email={user.email}")
        try:
            # Use hard_delete if available
            if hasattr(user, 'hard_delete'):
                await user.hard_delete(session)
            else:
                await session.delete(user)

            await session.commit()
            print("User deleted successfully")
            return 0
        except Exception as e:
            await session.rollback()
            print(f"Error deleting user: {e}")
            return 3


def main():
    parser = argparse.ArgumentParser(description='Delete user by id (local DB)')
    parser.add_argument('user_id')
    parser.add_argument('--admin-email', default='admin@example.com')
    parser.add_argument('--admin-pass', default='admin123')
    args = parser.parse_args()

    code = asyncio.run(delete_user(args.user_id, args.admin_email, args.admin_pass))
    sys.exit(code)


if __name__ == '__main__':
    main()
