#!/usr/bin/env python3
"""Hızlı debug scripti:
 - verilen kullanıcı bilgisiyle /web/auth/login formunu POST eder
 - ardından /web/debug/measurements endpoint'ini çağırır ve sonucu yazdırır

Kullanım: python scripts/debug_measurements.py
"""
import sys
import requests

BASE = "http://127.0.0.1:8000"

def main():
    email = "test@test.com"
    password = "admin123"

    s = requests.Session()
    login_url = f"{BASE}/web/auth/login"
    debug_url = f"{BASE}/web/debug/measurements"

    print(f"POST {login_url} -> attempting login for {email}")
    r = s.post(login_url, data={"email": email, "password": password}, allow_redirects=False)
    print("Login status:", r.status_code)
    print("Response headers:")
    for k,v in r.headers.items():
        if k.lower().startswith("x-login") or k.lower().startswith("set-cookie") or k.lower().startswith("location"):
            print(f"  {k}: {v}")

    # show cookies in session
    print("Session cookies:", s.cookies.get_dict())

    # If login redirected, follow with session
    print(f"GET {debug_url} -> fetching debug measurements")
    r2 = s.get(debug_url)
    print("Debug status:", r2.status_code)
    # try to print JSON prettily
    try:
        print(r2.json())
    except Exception:
        print(r2.text[:2000])

    # Also fetch rendered measurements page to inspect server-side rendering
    page_url = f"{BASE}/web/measurements"
    print(f"GET {page_url} -> fetching rendered HTML")
    r3 = s.get(page_url)
    print("Page status:", r3.status_code)
    # print relevant headers and a small HTML snippet
    print("Response headers:")
    for k,v in r3.headers.items():
        if k.lower().startswith("x-measurement") or k.lower().startswith("set-cookie"):
            print(f"  {k}: {v}")
    print('\nHTML snippet (first 1200 chars):')
    print(r3.text[:1200])
    # Cross-check that latest numeric values appear in rendered HTML
    try:
        j = r2.json()
        if j.get('count', 0) > 0:
            latest = j['sessions'][0]
            print('\nCross-check latest session values in rendered HTML:')
            for v in latest['values']:
                sval = str(v['value'])
                found = sval in r3.text
                print(f"  {v['type_name']}={sval} -> {'FOUND' if found else 'MISSING'}")
    except Exception:
        pass
    # Print the section around 'Güncel Kilo' to see rendered values
    try:
        idx = r3.text.find('Güncel Kilo')
        if idx != -1:
            start = max(0, idx-200)
            end = min(len(r3.text), idx+800)
            print('\nHTML around "Güncel Kilo":')
            print(r3.text[start:end])
        else:
            print('\nCould not find "Güncel Kilo" text in HTML')
    except Exception:
        pass

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("Error:", e, file=sys.stderr)
        sys.exit(1)
