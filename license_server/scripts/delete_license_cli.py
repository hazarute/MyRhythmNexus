#!/usr/bin/env python3
"""
Find and delete or deactivate a license for a customer by email.

Usage examples:
  python license_server/scripts/delete_license_cli.py
  python license_server/scripts/delete_license_cli.py --email contact@abc.example
  python license_server/scripts/delete_license_cli.py --email contact@abc.example --license-key MRN-XXXX-XXXX-XXXX
  python license_server/scripts/delete_license_cli.py --email contact@abc.example --license-key MRN-... --hard

By default the script performs a soft-delete (sets `is_active=False`). Use `--hard` to remove the DB row.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure repo root is on sys.path so this script can be run directly from this folder
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from typing import List

from license_server import models
from license_server.database import SessionLocal


def prompt_choose_license(lics: List[models.License]) -> List[models.License]:
    if not lics:
        return []
    print("Found the following licenses for this customer:")
    for i, l in enumerate(lics, start=1):
        print(f"  [{i}] {l.license_key}  expires={l.expires_at}  active={l.is_active}  hwid={'<none>' if not l.hardware_id else l.hardware_id}")

    print("Enter number to delete, comma-separated list (e.g. 1,3), 'all' to delete all, or 'none' to cancel")
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
    parser = argparse.ArgumentParser(description="Delete or deactivate license(s) by customer email")
    parser.add_argument("--email", help="Customer email (optional)")
    parser.add_argument("--license-key", help="Specific license_key to delete (optional)")
    parser.add_argument("--all", action="store_true", help="Delete all licenses for this customer (no interactive selection)")
    parser.add_argument("--hard", action="store_true", help="Perform hard delete (remove DB row). Default is soft-delete (is_active=False)")

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

        to_delete: List[models.License] = []
        if args.license_key:
            matched = [l for l in lics if l.license_key == args.license_key]
            if not matched:
                print(f"No license with key {args.license_key} for this customer.")
                return
            to_delete = matched
        elif args.all:
            to_delete = lics
        else:
            to_delete = prompt_choose_license(lics)

        if not to_delete:
            print("No licenses selected. Exiting.")
            return

        print("About to delete/deactivate the following licenses:")
        for l in to_delete:
            print(f"  - {l.license_key}  active={l.is_active}  hwid={'<none>' if not l.hardware_id else l.hardware_id}")

        confirm = input("Type 'yes' to confirm and proceed: ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            return

        # perform deletion / deactivation
        if args.hard:
            for l in to_delete:
                db.delete(l)
        else:
            for l in to_delete:
                l.is_active = False
                db.add(l)

        db.commit()

        if args.hard:
            print("Done. Licenses removed from DB.")
        else:
            print("Done. Licenses deactivated (is_active=False).")

    finally:
        db.close()


if __name__ == "__main__":
    main()
