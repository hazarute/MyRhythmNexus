#!/usr/bin/env python3
"""
Create customer and license in the local license_server database from the terminal.

Usage examples:
  python license_server/scripts/create_license_cli.py \
    --name "ABC Pilates Studio" --email contact@abc.example \
    --contact "Ayşe" --phone "+90-555-000-1111" --days 365 \
    --features '{"qr_checkin": true, "finance": true, "max_members": 200}'

  python license_server/scripts/create_license_cli.py --name "ABC" --email a@b.com --expires 2026-12-04

The script will create or reuse a Customer (by email) and then create a License record
with a randomly generated license_key (format MRN-XXXX-XXXX-XXXX).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure repo root is on sys.path so this script can be run directly from this folder
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import json
import random
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from license_server import models
from license_server.database import SessionLocal


def generate_license_key(prefix: str = "MRN", parts: int = 3, part_len: int = 4) -> str:
    parts_list = []
    for _ in range(parts):
        part = "".join(random.choices(string.ascii_uppercase + string.digits, k=part_len))
        parts_list.append(part)
    return f"{prefix}-" + "-".join(parts_list)


def parse_features(s: Optional[str]) -> dict:
    if not s:
        return {}
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        # Try a simple key=val list separated by commas: qr_checkin=true,finance=true
        out = {}
        for pair in s.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                v = v.strip().lower()
                if v in ("true", "1", "yes"): v = True
                elif v in ("false", "0", "no"): v = False
                else:
                    try:
                        v = int(v)
                    except Exception:
                        pass
                out[k.strip()] = v
        return out


def create_customer_if_missing(db, name: str, email: str, contact_person: Optional[str], phone: Optional[str]):
    existing = db.query(models.Customer).filter(models.Customer.email == email).first()
    if existing:
        print(f"Reusing existing customer id={existing.id} email={existing.email}")
        return existing
    customer = models.Customer(
        name=name,
        email=email,
        contact_person=contact_person,
        phone=phone,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    print(f"Created customer id={customer.id} email={customer.email}")
    return customer


def create_license(db, customer_id: int, license_key: str, expires_at: datetime, features: dict):
    license_obj = models.License(
        license_key=license_key,
        customer_id=customer_id,
        expires_at=expires_at,
        features=features,
        is_active=True,
    )
    db.add(license_obj)
    db.commit()
    db.refresh(license_obj)
    return license_obj


def main():
    parser = argparse.ArgumentParser(description="Create customer & license in license_server DB")
    parser.add_argument("--name", help="Customer / Studio name")
    parser.add_argument("--email", help="Contact email (used to dedupe customers)")
    parser.add_argument("--contact", default=None, help="Contact person")
    parser.add_argument("--phone", default=None, help="Phone number")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--days", type=int, help="License validity in days from today (e.g. 365)")
    group.add_argument("--expires", help="Explicit expiration date YYYY-MM-DD")

    parser.add_argument("--features", default=None, help='Features JSON or simple k=v list. Example: "{"qr_checkin": true}"')
    parser.add_argument("--license-key", default=None, help="Optional custom license key")
    parser.add_argument("--prefix", default="MRN", help="License key prefix (default MRN)")

    args = parser.parse_args()

    # If required pieces not provided as args, prompt interactively.
    name = args.name or input("Customer / Studio name: ").strip()
    while not name:
        name = input("Customer / Studio name (required): ").strip()

    email = args.email or input("Contact email: ").strip()
    while not email:
        email = input("Contact email (required): ").strip()

    contact_person = args.contact
    if not contact_person:
        contact_person = input("Contact person (optional): ").strip() or None

    phone = args.phone
    if not phone:
        phone = input("Phone (optional): ").strip() or None

    # Expiration: prefer explicit --expires, then --days, else ask
    if args.expires:
        try:
            expires_at = datetime.fromisoformat(args.expires)
        except Exception as e:
            parser.error(f"Invalid --expires date: {e}")
    elif args.days:
        expires_at = datetime.utcnow() + timedelta(days=args.days)
    else:
        # interactive prompt for days or date
        ed = input("License validity in days (default 365) or enter date YYYY-MM-DD (leave blank for 365): ").strip()
        if not ed:
            expires_at = datetime.utcnow() + timedelta(days=365)
        else:
            # try parse int days first
            try:
                d = int(ed)
                expires_at = datetime.utcnow() + timedelta(days=d)
            except ValueError:
                try:
                    expires_at = datetime.fromisoformat(ed)
                except Exception:
                    print("Invalid input for expiration; using 365 days")
                    expires_at = datetime.utcnow() + timedelta(days=365)

    # features are optional and not asked interactively; default to empty if not provided
    if args.features:
        features = parse_features(args.features)
    else:
        features = {}

    license_key = args.license_key or generate_license_key(prefix=args.prefix)

    # Connect to DB
    db_gen = SessionLocal()
    try:
        customer = create_customer_if_missing(db_gen, name, email, contact_person, phone)
        lic = create_license(db_gen, customer.id, license_key, expires_at, features)
        print("\nLicense created:\n")
        print(f" id: {lic.id}")
        print(f" license_key: {lic.license_key}")
        print(f" customer_id: {lic.customer_id}")
        print(f" expires_at: {lic.expires_at}")
        print(f" features: {lic.features}")

        base_url = "http://localhost:8001/api/v1"
        print("\nSample client validation request (run on client machine):")
        payload = json.dumps({"license_key": lic.license_key, "hardware_id": "<MACHINE_ID>"})
        print(f"curl -X POST \"{base_url}/license/validate\" -H 'Content-Type: application/json' -d '{payload}'")

    finally:
        db_gen.close()


if __name__ == "__main__":
    main()
