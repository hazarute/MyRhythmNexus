#!/usr/bin/env python3
"""Check whether a user with given email exists in DB (async)."""
import sys
import asyncio

from sqlalchemy.future import select

from backend.models.user import User
from backend.core.database import SessionLocal


async def find_user(email: str):
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email.lower()))
        user = result.scalar_one_or_none()
        if not user:
            print(f"User not found: {email}")
        else:
            print(f"Found user: id={user.id}, email={user.email}, active={user.is_active}")


def main():
    if len(sys.argv) < 2:
        print("Usage: check_user.py <email>")
        sys.exit(2)
    email = sys.argv[1]
    asyncio.run(find_user(email))


if __name__ == '__main__':
    main()
