#!/usr/bin/env python3
"""
Reset the `hardware_id` field for one or more licenses belonging to a customer found by email.

Usage:
  python license_server/scripts/reset_hwid_cli.py
  python license_server/scripts/reset_hwid_cli.py --email contact@abc.example
  python license_server/scripts/reset_hwid_cli.py --email contact@abc.example --license-key MRN-XXXX-XXXX-XXXX
  python license_server/scripts/reset_hwid_cli.py --email contact@abc.example --all

The script will prompt for missing values and ask for confirmation before making changes.
"""
from __future__ import annotations

import argparse
from typing import List

from license_server import models
from license_server.database import SessionLocal


def prompt_choose_license(lics: List[models.License]) -> List[models.License]:
    if not lics:
        return []
    print("Found the following licenses for this customer:")
    for i, l in enumerate(lics, start=1):
        print(f"  [{i}] {l.license_key}  expires={l.expires_at}  hwid={'<none>' if not l.hardware_id else l.hardware_id}")

    print("Enter number to reset, comma-separated list (e.g. 1,3), 'all' to reset all, or 'none' to cancel")
    choice = input("Selection: ").strip().lower()
    if choice in ("all", "a"):
        return lics
    if choice in ("none", "n", ""):
        return []

    selected = []
    for part in choice.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            idx = int(part)
            if 1 <= idx <= len(lics):
                selected.append(lics[idx - 1])
        except ValueError:
            # try match license_key
            matched = [l for l in lics if l.license_key.lower() == part.lower()]
            if matched:
                selected.extend(matched)

    return selected


def main():
    parser = argparse.ArgumentParser(description="Reset hardware_id for licenses by customer email")
    parser.add_argument("--email", help="Customer contact email (will be prompted if missing)")
    parser.add_argument("--license-key", help="Specific license_key to reset (optional)")
    parser.add_argument("--all", action="store_true", help="Reset all licenses for this customer (no interactive selection)")

    args = parser.parse_args()

    email = args.email or input("Customer email: ").strip()
    while not email:
        email = input("Customer email (required): ").strip()

    db = SessionLocal()
    try:
        customer = db.query(models.Customer).filter(models.Customer.email == email).first()
        if not customer:
            print(f"No customer found with email {email}")
            return

        lics = db.query(models.License).filter(models.License.customer_id == customer.id).all()
        if not lics:
            print("No licenses found for this customer.")
            return

        to_reset: List[models.License] = []
        if args.license_key:
            matched = [l for l in lics if l.license_key == args.license_key]
            if not matched:
                print(f"No license with key {args.license_key} for this customer.")
                return
            to_reset = matched
        elif args.all:
            to_reset = lics
        else:
            to_reset = prompt_choose_license(lics)

        if not to_reset:
            print("No licenses selected. Exiting.")
            return

        print("About to reset hardware_id for the following licenses:")
        for l in to_reset:
            print(f"  - {l.license_key}  current hwid={'<none>' if not l.hardware_id else l.hardware_id}")

        confirm = input("Type 'yes' to confirm and proceed: ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            return

        # perform updates
        for l in to_reset:
            l.hardware_id = None
            db.add(l)
        db.commit()

        print("Done. hardware_id reset for selected licenses.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
