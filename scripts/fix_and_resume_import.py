#!/usr/bin/env python3
"""Detect created users, send passwords as-is (no truncation), and (dry-run) show actions.
Also creates missing users if requested.

Backend now uses pbkdf2_sha256 for all passwords, so no 72-byte limit.

Usage:
  python scripts/fix_and_resume_import.py --in oldCustomerData/customers_cleaned.json --dry-run

Defaults for backend/admin/password are same as other scripts.
"""
import argparse
import json
import time
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import httpx


def login(client: httpx.Client, backend: str, username: str, password: str) -> str:
    resp = client.post("/api/v1/auth/login/access-token", data={"username": username, "password": password})
    resp.raise_for_status()
    return resp.json()["access_token"]


def truncate_password(pw: str, max_bytes: int = 999999) -> str:
    """Pass through: no truncation needed since backend uses pbkdf2_sha256."""
    return pw if pw else pw


def format_phone_for_search(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    digits = ''.join(ch for ch in phone if ch.isdigit())
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return digits


def fetch_all_members(client: httpx.Client, token: str, limit: int = 10000) -> List[dict]:
    headers = {"Authorization": f"Bearer {token}"}
    params = {"include_inactive": "true", "limit": limit}
    resp = client.get("/api/v1/members/", params=params, headers=headers)
    resp.raise_for_status()
    return resp.json()


def parse_iso(dtstr: str) -> Optional[datetime]:
    if not dtstr:
        return None
    try:
        # try fromisoformat
        dt = datetime.fromisoformat(dtstr)
        if dt.tzinfo is None:
            # assume UTC
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        try:
            # fallback: strip fractional seconds and try again
            base = dtstr.split('+')[0].split('Z')[0]
            dt = datetime.fromisoformat(base)
            return dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="infile", default="oldCustomerData/customers_cleaned.json")
    p.add_argument("--backend", default=None)
    p.add_argument("--admin", default=None)
    p.add_argument("--password", default=None)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--apply-updates", action="store_true", help="If set, perform PUT updates for found users' passwords")
    p.add_argument("--apply-creates", action="store_true", help="If set, perform POST creates for missing users")
    p.add_argument("--created-window-minutes", type=int, default=120,
                   help="How many minutes back to consider a found user as 'created during import'")
    p.add_argument("--delay", type=float, default=0.2, help="Delay seconds between requests (default 0.2)")
    p.add_argument("--jitter", type=float, default=0.1, help="Random jitter added to delay (default 0.1)")
    p.add_argument("--batch-size", type=int, default=50, help="Number of updates to send before a longer sleep")
    p.add_argument("--batch-sleep", type=float, default=5.0, help="Long sleep seconds after each batch")
    args = p.parse_args()

    backend = args.backend or "https://tugbadansvespor-production.up.railway.app"
    admin = args.admin or "hazarute@gmail.com"
    password = args.password or "2506914h"

    infile = Path(args.infile)
    if not infile.exists():
        print(f"Input file not found: {infile}")
        raise SystemExit(1)

    data = json.load(infile.open("r", encoding="utf-8"))
    if not isinstance(data, list):
        print("Input must be a JSON array of records")
        raise SystemExit(1)

    print(f"Loaded {len(data)} records from {infile}")

    window_minutes = args.created_window_minutes

    # Increased timeout to 60s to handle slow backend
    with httpx.Client(base_url=backend, timeout=60.0, verify=True) as client:
        try:
            token = login(client, backend, admin, password)
        except Exception as e:
            print(f"Login failed: {e}")
            raise SystemExit(1)

        print("Authenticated, token acquired")

        to_update = []
        to_create = []
        found_but_old = []
        
        now = datetime.now(timezone.utc)
        # Fetch all members once to avoid many requests
        print("Fetching existing members...")
        members = fetch_all_members(client, token, limit=max(5000, len(data)))
        print(f"Fetched {len(members)} existing members.")
        
        email_map = {}
        phone_map = {}
        for m in members:
            em = m.get('email')
            if em:
                email_map[em.lower()] = m
            mp = m.get('phone_number')
            if mp:
                phone_map[mp] = m

        print("Analyzing records...")
        for i, r in enumerate(data, 1):
            email = r.get('email')
            phone_raw = r.get('phone_number')
            phone_search = format_phone_for_search(phone_raw)
            matches = []
            # try direct maps
            if email and email.lower() in email_map:
                matches.append(email_map[email.lower()])
            if phone_search and phone_search in phone_map:
                matches.append(phone_map[phone_search])

            # find exact match by email or normalized phone
            matched = None
            for m in matches:
                # compare emails case-insensitive
                if email and m.get('email') and m.get('email').lower() == email.lower():
                    matched = m
                    break
                # compare phone normalized
                mp = m.get('phone_number')
                if phone_search and mp:
                    if mp == phone_search or mp.replace('-', '') == phone_search.replace('-', ''):
                        matched = m
                        break

            truncated_pw = truncate_password(r.get('password', ''))

            if matched:
                created_at = parse_iso(matched.get('created_at'))
                if created_at:
                    age_minutes = (now - created_at).total_seconds() / 60.0
                else:
                    age_minutes = None

                if age_minutes is None or age_minutes <= window_minutes:
                    to_update.append({
                        'record_index': i,
                        'email': email,
                        'phone': phone_raw,
                        'user_id': matched.get('id'),
                        'created_at': matched.get('created_at'),
                        'truncated_password': truncated_pw,
                    })
                else:
                    found_but_old.append({
                        'record_index': i,
                        'email': email,
                        'phone': phone_raw,
                        'user_id': matched.get('id'),
                        'created_at': matched.get('created_at'),
                    })
            else:
                # Store full record for creation
                to_create.append({
                    'record_index': i,
                    'first_name': r.get("first_name"),
                    'last_name': r.get("last_name"),
                    'email': email,
                    'phone_number': phone_raw,
                    'password': truncated_pw,
                    'is_active': r.get("is_active", True),
                })

        summary = {
            'total': len(data),
            'would_update_count': len(to_update),
            'would_create_count': len(to_create),
            'found_but_old_count': len(found_but_old),
        }

        print(json.dumps(summary, ensure_ascii=False, indent=2))

        # Print samples
        print('\nSample updates (first 5):')
        print(json.dumps(to_update[:5], ensure_ascii=False, indent=2))

        print('\nSample creates (first 5):')
        print(json.dumps(to_create[:5], ensure_ascii=False, indent=2))

        # --- UPDATES ---
        update_results = {"updated": 0, "failed": 0, "failures_sample": []}
        if args.apply_updates:
            if args.dry_run:
                print('\nApply-updates requested but --dry-run is set; no changes will be made.')
            else:
                print(f"\nApplying updates to {len(to_update)} users (updating password)...")
                headers = {"Authorization": f"Bearer {token}"}
                total = len(to_update)
                print(f"Starting updates: {total} users (delay={args.delay}s, jitter={args.jitter}s, batch={args.batch_size})")
                
                for idx, u in enumerate(to_update, 1):
                    user_id = u['user_id']
                    payload = {"password": u['truncated_password']}
                    
                    # Retry loop
                    max_retries = 5
                    backoff = 1.0
                    success = False
                    
                    for attempt in range(1, max_retries + 1):
                        try:
                            resp = client.put(f"/api/v1/members/{user_id}", json=payload, headers=headers)
                            if resp.status_code in (200, 201):
                                update_results['updated'] += 1
                                success = True
                                print(f"[UPDATE {idx}/{total}] OK: {u.get('email')}", flush=True)
                                break
                            else:
                                # Server error or rate limit
                                if resp.status_code >= 500 or resp.status_code == 429:
                                    if attempt < max_retries:
                                        sleep_time = backoff + random.uniform(0, 1.0)
                                        print(f"[UPDATE {idx}/{total}] RETRY {attempt} (Status {resp.status_code}): Sleeping {sleep_time:.2f}s", flush=True)
                                        time.sleep(sleep_time)
                                        backoff *= 2
                                        continue
                                
                                update_results['failed'] += 1
                                if len(update_results['failures_sample']) < 20:
                                    update_results['failures_sample'].append({"user_id": user_id, "status": resp.status_code, "msg": resp.text})
                                print(f"[UPDATE {idx}/{total}] FAIL: {u.get('email')} Status={resp.status_code}", flush=True)
                                break
                        except (httpx.ReadTimeout, httpx.ConnectError, httpx.TransportError) as e:
                            if attempt < max_retries:
                                sleep_time = backoff + random.uniform(0, 1.0)
                                print(f"[UPDATE {idx}/{total}] RETRY {attempt} (Error {e}): Sleeping {sleep_time:.2f}s", flush=True)
                                time.sleep(sleep_time)
                                backoff *= 2
                                continue
                            update_results['failed'] += 1
                            if len(update_results['failures_sample']) < 20:
                                update_results['failures_sample'].append({"user_id": user_id, "error": str(e)})
                            print(f"[UPDATE {idx}/{total}] ERROR: {u.get('email')} {e}", flush=True)
                    
                    # Delays
                    if args.delay:
                        time.sleep(args.delay + random.uniform(0, args.jitter))
                    if idx % args.batch_size == 0:
                        print(f"Batch sleep {args.batch_sleep}s...", flush=True)
                        time.sleep(args.batch_sleep)

        # --- CREATES ---
        create_results = {"created": 0, "failed": 0, "skipped": 0, "failures_sample": []}
        if args.apply_creates:
            if args.dry_run:
                print('\nApply-creates requested but --dry-run is set; no changes will be made.')
            else:
                print(f"\nApplying creates to {len(to_create)} users...")
                headers = {"Authorization": f"Bearer {token}"}
                total = len(to_create)
                print(f"Starting creates: {total} users")

                for idx, c in enumerate(to_create, 1):
                    payload = {
                        "first_name": c.get("first_name"),
                        "last_name": c.get("last_name"),
                        "email": c.get("email"),
                        "phone_number": c.get("phone_number"),
                        "password": c.get("password"),
                        "is_active": c.get("is_active", True),
                    }

                    max_retries = 5
                    backoff = 1.0
                    success = False

                    for attempt in range(1, max_retries + 1):
                        try:
                            resp = client.post("/api/v1/members/", json=payload, headers=headers)
                            if resp.status_code in (200, 201):
                                create_results['created'] += 1
                                success = True
                                print(f"[CREATE {idx}/{total}] OK: {c.get('email')}", flush=True)
                                break
                            elif resp.status_code in (409, 422):
                                create_results['skipped'] += 1
                                print(f"[CREATE {idx}/{total}] SKIP: {c.get('email')} (Status {resp.status_code})", flush=True)
                                break
                            else:
                                if resp.status_code >= 500 or resp.status_code == 429:
                                    if attempt < max_retries:
                                        sleep_time = backoff + random.uniform(0, 1.0)
                                        print(f"[CREATE {idx}/{total}] RETRY {attempt} (Status {resp.status_code}): Sleeping {sleep_time:.2f}s", flush=True)
                                        time.sleep(sleep_time)
                                        backoff *= 2
                                        continue
                                
                                create_results['failed'] += 1
                                if len(create_results['failures_sample']) < 20:
                                    create_results['failures_sample'].append({"email": c.get("email"), "status": resp.status_code, "msg": resp.text})
                                print(f"[CREATE {idx}/{total}] FAIL: {c.get('email')} Status={resp.status_code}", flush=True)
                                break
                        except (httpx.ReadTimeout, httpx.ConnectError, httpx.TransportError) as e:
                            if attempt < max_retries:
                                sleep_time = backoff + random.uniform(0, 1.0)
                                print(f"[CREATE {idx}/{total}] RETRY {attempt} (Error {e}): Sleeping {sleep_time:.2f}s", flush=True)
                                time.sleep(sleep_time)
                                backoff *= 2
                                continue
                            create_results['failed'] += 1
                            if len(create_results['failures_sample']) < 20:
                                create_results['failures_sample'].append({"email": c.get("email"), "error": str(e)})
                            print(f"[CREATE {idx}/{total}] ERROR: {c.get('email')} {e}", flush=True)

                    if args.delay:
                        time.sleep(args.delay + random.uniform(0, args.jitter))
                    if idx % args.batch_size == 0:
                        print(f"Batch sleep {args.batch_sleep}s...", flush=True)
                        time.sleep(args.batch_sleep)

        if not args.dry_run:
            if args.apply_updates:
                print('\nUpdate summary:')
                print(json.dumps(update_results, ensure_ascii=False, indent=2))
            if args.apply_creates:
                print('\nCreate summary:')
                print(json.dumps(create_results, ensure_ascii=False, indent=2))
            if not args.apply_updates and not args.apply_creates:
                print('\nNo apply flags set (--apply-updates or --apply-creates). No changes made.')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")
        import sys
        sys.exit(1)
