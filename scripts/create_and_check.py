#!/usr/bin/env python3
"""Create a test user via HTTP POST then verify it exists in the DB."""
import uuid
import asyncio
from urllib.parse import urljoin

import requests
from sqlalchemy.future import select

from backend.models.user import User
from backend.core.database import SessionLocal

BASE = "http://localhost:8000"
ENDPOINT = "/web/auth/register"


def make_payload():
    uid = uuid.uuid4().hex[:8]
    email = f"debug.user+{uid}@example.com"
    phone = "555123%04d" % (int(uid[:4], 16) % 10000)
    return {
        "first_name": "Debug",
        "last_name": "User",
        "email": email,
        "phone_number": phone,
        "password": "Password123",
        "password_confirm": "Password123",
        "terms": "on",
    }


async def find_user(email: str):
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()


def main():
    payload = make_payload()
    print("Posting user email:", payload["email"])
    url = urljoin(BASE, ENDPOINT)
    resp = requests.post(url, data=payload, allow_redirects=False, timeout=10)
    print('status', resp.status_code)
    print('headers', dict(resp.headers))
    print('body snippet:', resp.text[:500])

    user = asyncio.run(find_user(payload["email"]))
    if user:
        print(f"DB: Found user id={user.id}, email={user.email}, active={user.is_active}")
    else:
        print("DB: User not found")


if __name__ == '__main__':
    main()
