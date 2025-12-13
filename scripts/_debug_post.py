import uuid
from urllib.parse import urljoin
import requests

BASE = "http://localhost:8000"
ENDPOINT = "/web/auth/register"

def make_payload():
    uid = uuid.uuid4().hex[:8]
    return {
        "first_name": "Debug",
        "last_name": "User",
        "email": f"debug.user+{uid}@example.com",
        "phone_number": "555123%04d" % (int(uid[:4], 16) % 10000),
        "password": "Password123",
        "password_confirm": "Password123",
        "terms": "on",
    }

def main():
    url = urljoin(BASE, ENDPOINT)
    payload = make_payload()
    s = requests.Session()
    resp = s.post(url, data=payload, allow_redirects=False, timeout=10)
    print('status', resp.status_code)
    print('headers', resp.headers)
    print('body snippet:', resp.text[:2000])

if __name__ == '__main__':
    main()
