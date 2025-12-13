#!/usr/bin/env python3
"""POST a registration with an invalid/absurd phone number to verify server validation."""
import requests
from urllib.parse import urljoin

BASE = "http://localhost:8000"
ENDPOINT = "/web/auth/register"

def main():
    payload = {
        "first_name": "Phone",
        "last_name": "Invalid",
        "email": "phone.invalid.test@example.com",
        "phone_number": "5123123123123123",
        "password": "Password123",
        "password_confirm": "Password123",
        "terms": "on",
    }
    url = urljoin(BASE, ENDPOINT)
    resp = requests.post(url, data=payload, timeout=10)
    print('status', resp.status_code)
    text = resp.text
    print('contains phone error?', 'Telefon numarası geçersiz' in text or 'Geçerli bir telefon numarası' in text)
    print('snippet:', text[:800])

if __name__ == '__main__':
    main()
