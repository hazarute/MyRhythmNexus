#!/usr/bin/env python3
"""
Add an additional license for an existing customer (selected by email).

Usage examples:
  python license_server/scripts/add_license_for_customer.py
  python license_server/scripts/add_license_for_customer.py --email contact@abc.example

If the customer does not exist, the script optionally offers to create it.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure repo root is on sys.path so this script can be run directly from this folder
# Use parents[2] to point to repository root (one level above `license_server`)
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import json
import random
import string
from datetime import datetime, timedelta
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
    except Exception:
        return {}


def prompt_create_customer(db, email: str):
    print(f"Customer with email {email} not found.")
    do = input("Create new customer? (y/N): ").strip().lower()
    if do != "y":
        return None
    name = input("Customer / Studio name: ").strip()
    contact = input("Contact person (optional): ").strip() or None
    phone = input("Phone (optional): ").strip() or None
    cust = models.Customer(name=name, email=email, contact_person=contact, phone=phone)
    db.add(cust)
    db.commit()
    db.refresh(cust)
    print(f"Created customer id={cust.id} email={cust.email}")
    return cust


def main():
    parser = argparse.ArgumentParser(description="Add license for a customer by email")
    parser.add_argument("--email", help="Customer email (optional)")
    parser.add_argument("--days", type=int, help="Validity in days (optional)")
    parser.add_argument("--license-key", help="Optional license key")
    parser.add_argument("--prefix", default="MRN", help="License key prefix")
    args = parser.parse_args()

    email = args.email or input("Customer email: ").strip()
    while not email:
        email = input("Customer email (required): ").strip()

    db = SessionLocal()
    try:
        customer = db.query(models.Customer).filter(models.Customer.email == email).first()
        if not customer:
            customer = prompt_create_customer(db, email)
            if not customer:
                print("No customer. Exiting.")
                return

        # Show existing licenses
        lics = db.query(models.License).filter(models.License.customer_id == customer.id).all()
        if lics:
            print("Existing licenses for this customer:")
            for l in lics:
                print(f" - {l.license_key}  expires={l.expires_at}  hwid={'<none>' if not l.hardware_id else l.hardware_id}")
        else:
            print("No existing licenses for this customer.")

        # Expiration
        if args.days:
            expires_at = datetime.utcnow() + timedelta(days=args.days)
        else:
            ed = input("License validity in days (default 365): ").strip()
            try:
                days = int(ed) if ed else 365
            except Exception:
                days = 365
            expires_at = datetime.utcnow() + timedelta(days=days)

        # Features optional
        features_input = input("Features JSON (optional, leave blank for none): ").strip()
        features = parse_features(features_input) if features_input else {}

        license_key = args.license_key or generate_license_key(prefix=args.prefix)

        lic = models.License(license_key=license_key, customer_id=customer.id, expires_at=expires_at, features=features, is_active=True)
        db.add(lic)
        db.commit()
        db.refresh(lic)

        print("\nNew license created:")
        print(f" id: {lic.id}")
        print(f" license_key: {lic.license_key}")
        print(f" customer_id: {lic.customer_id}")
        print(f" expires_at: {lic.expires_at}")
        print(f" features: {lic.features}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
