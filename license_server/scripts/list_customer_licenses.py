#!/usr/bin/env python3
"""List customers and their associated licenses.

Usage:
  python license_server/scripts/list_customer_licenses.py --all
  python license_server/scripts/list_customer_licenses.py --email contact@abc.example
  python license_server/scripts/list_customer_licenses.py --email contact@abc.example --active-only

This is a read-only admin helper that prints customers and license info.
"""
from __future__ import annotations

import argparse
from typing import Optional

from license_server import models
from license_server.database import SessionLocal


def print_license(l: models.License) -> None:
    hw = l.hardware_id or "<none>"
    feat = l.features if getattr(l, "features", None) is not None else {}
    print(f"    - {l.license_key} | active={l.is_active} | expires={l.expires_at} | hwid={hw} | features={feat}")


def list_by_email(db, email: str, active_only: bool = False) -> None:
    customer = db.query(models.Customer).filter(models.Customer.email == email).first()
    if not customer:
        print(f"No customer found with email: {email}")
        return

    print(f"Customer: id={customer.id} name={customer.name or '<none>'} email={customer.email}")
    lics = db.query(models.License).filter(models.License.customer_id == customer.id)
    if active_only:
        lics = lics.filter(models.License.is_active == True)
    lics = lics.all()

    if not lics:
        print("  (no licenses)")
        return

    for l in lics:
        print_license(l)


def list_all(db, active_only: bool = False) -> None:
    customers = db.query(models.Customer).order_by(models.Customer.email).all()
    if not customers:
        print("No customers found.")
        return

    for c in customers:
        print(f"Customer: id={c.id} name={c.name or '<none>'} email={c.email}")
        lics_q = db.query(models.License).filter(models.License.customer_id == c.id)
        if active_only:
            lics_q = lics_q.filter(models.License.is_active == True)
        lics = lics_q.all()
        if not lics:
            print("  (no licenses)")
        else:
            for l in lics:
                print_license(l)


def main():
    parser = argparse.ArgumentParser(description="List customers and licenses")
    parser.add_argument("--email", help="Filter by customer email", default=None)
    parser.add_argument("--all", help="List all customers", action="store_true")
    parser.add_argument("--active-only", help="Show only active licenses", action="store_true")

    args = parser.parse_args()

    if not args.all and not args.email:
        parser.error("Specify --all or --email <address>")

    db = SessionLocal()
    try:
        if args.all:
            list_all(db, active_only=args.active_only)
        else:
            list_by_email(db, args.email, active_only=args.active_only)
    finally:
        db.close()


if __name__ == "__main__":
    main()
