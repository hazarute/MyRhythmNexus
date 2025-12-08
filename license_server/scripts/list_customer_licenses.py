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
import sys
from pathlib import Path


def _ensure_repo_root():
    import importlib, types

    p = Path(__file__).resolve().parent
    repo_root = None
    for _ in range(6):
        if (p / "models.py").exists() and (p / "database.py").exists():
            repo_root = p
            break
        if (p / "license_server").is_dir():
            repo_root = p
            break
        if p.parent == p:
            break
        p = p.parent
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    try:
        top_models = importlib.import_module("models")
        top_database = importlib.import_module("database")
        top_schemas = importlib.import_module("schemas")
        pkg = types.ModuleType("license_server")
        pkg.models = top_models
        pkg.database = top_database
        pkg.schemas = top_schemas
        pkg.__path__ = [str(repo_root)]
        sys.modules["license_server"] = pkg
        sys.modules["license_server.models"] = top_models
        sys.modules["license_server.database"] = top_database
        sys.modules["license_server.schemas"] = top_schemas
    except Exception:
        pass


_ensure_repo_root()

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

    # If no args provided, enter interactive step-by-step mode
    if not args.all and not args.email:
        print("Interaktif mod: Lütfen aşağıdaki seçeneklerden birini seçin.")
        print("  [a] Tüm müşterileri listele")
        print("  [e] E-posta ile sorgula")
        print("  [q] Çıkış")
        choice = input("Seçiminiz [a/e/q] (varsayılan a): ").strip().lower()
        if choice in ("q", "quit"):
            print("Çıkış.")
            return

        if choice in ("e", "email"):
            email = input("Müşteri e-posta adresi: ").strip()
            while not email:
                email = input("E-posta (zorunlu): ").strip()
            all_flag = False
        else:
            email = None
            all_flag = True

        active_only = input("Sadece aktif lisansları göster? (y/N): ").strip().lower() in ("y", "yes")
    else:
        all_flag = args.all
        email = args.email
        active_only = args.active_only

    db = SessionLocal()
    try:
        if all_flag:
            list_all(db, active_only=active_only)
        else:
            list_by_email(db, email, active_only=active_only)
    finally:
        db.close()


if __name__ == "__main__":
    main()
