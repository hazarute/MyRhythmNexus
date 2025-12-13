import uuid
from urllib.parse import urljoin

import pytest
import requests


BASE = "http://localhost:8000"
ENDPOINT = "/web/auth/register"


def make_payload():
    uid = uuid.uuid4().hex[:8]
    return {
        "first_name": "Test",
        "last_name": "User",
        "email": f"test.user+{uid}@example.com",
        "phone_number": "555123%04d" % (int(uid[:4], 16) % 10000),
        "password": "Password123",
        "password_confirm": "Password123",
        "terms": "on",
    }


@pytest.mark.integration
def test_register_endpoint():
    """Integration: POST /web/auth/register should redirect to login (302) and login page returns 200."""
    url = urljoin(BASE, ENDPOINT)
    payload = make_payload()

    s = requests.Session()
    resp = s.post(url, data=payload, allow_redirects=False, timeout=10)

    # Success may be implemented as a redirect (old handler) or render login template with success message.
    if resp.status_code in (301, 302, 303, 307, 308):
        loc = resp.headers.get("location") or resp.headers.get("Location")
        assert loc, "Missing Location header on redirect"
        assert "/web/auth/login" in loc or "/web/auth/login" in loc.lower()

        # Follow redirect and ensure login page loads
        follow = s.get(urljoin(BASE, loc), timeout=10)
        assert follow.status_code == 200
        assert "Giriş" in follow.text or "login" in follow.text.lower()
    else:
        # Handler rendered login template directly (200) — check that login UI is present
        assert resp.status_code == 200
        assert "Giriş" in resp.text or "login" in resp.text.lower()

