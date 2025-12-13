#!/usr/bin/env python3
"""Post to register with mismatched passwords to verify form values are preserved on error."""
import requests
from urllib.parse import urljoin
import uuid

BASE = "http://localhost:8000"
ENDPOINT = "/web/auth/register"

def main():
    uid = uuid.uuid4().hex[:6]
    payload = {
        "first_name": "ErrTest",
        "last_name": "User",
        "email": f"err.user+{uid}@example.com",
        "phone_number": "5550001234",
        "password": "Password123",
        "password_confirm": "Mismatch",
        "terms": "on",
    }
    url = urljoin(BASE, ENDPOINT)
    resp = requests.post(url, data=payload, timeout=10)
    print('status', resp.status_code)
    # crude checks: form values should appear in returned HTML when error
    contains_first = payload['first_name'] in resp.text
    contains_email = payload['email'] in resp.text
    print('first_name preserved in HTML:', contains_first)
    print('email preserved in HTML:', contains_email)
    snippet = resp.text[:800]
    print('body snippet:', snippet)

if __name__ == '__main__':
    main()
