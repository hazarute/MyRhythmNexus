#!/usr/bin/env python3
"""
Set repository secrets for GitHub via the REST API.

Usage:
  python scripts/set_github_secrets.py --repo hazarute/MyRhythmNexus --secrets LICENSE_DATABASE_URL RAILWAY_TOKEN LICENSE_PRIVATE_KEY

The script will prompt for a GitHub Personal Access Token (with `repo` scope) and for each secret's value.
"""
from __future__ import annotations

import argparse
import getpass
import json
import subprocess
import sys
from typing import List


def ensure_packages():
    try:
        import requests  # type: ignore
        import nacl.public  # type: ignore
    except Exception:
        print("Installing required packages: requests pynacl")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "pynacl"])


def encrypt_secret(public_key_b64: str, secret_value: str) -> str:
    from base64 import b64decode, b64encode
    from nacl import public, encoding

    public_key = public.PublicKey(b64decode(public_key_b64), encoder=encoding.RawEncoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")


def set_secret(token: str, owner: str, repo: str, name: str, value: str) -> bool:
    import requests

    base = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}

    # Get public key
    r = requests.get(f"{base}/actions/secrets/public-key", headers=headers)
    if r.status_code != 200:
        print(f"Failed to fetch public key: {r.status_code} {r.text}")
        return False
    key_info = r.json()
    key_id = key_info["key_id"]
    key = key_info["key"]

    encrypted_value = encrypt_secret(key, value)

    payload = {"encrypted_value": encrypted_value, "key_id": key_id}
    put = requests.put(f"{base}/actions/secrets/{name}", headers=headers, json=payload)
    if put.status_code in (201, 204):
        print(f"Secret {name} set successfully")
        return True
    else:
        print(f"Failed to set secret {name}: {put.status_code} {put.text}")
        return False


def main(argv: List[str] | None = None) -> int:
    ensure_packages()
    import requests  # noqa: E402

    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--secrets", nargs="+", required=True, help="Secret names to set")
    args = parser.parse_args(argv)

    owner_repo = args.repo.split("/")
    if len(owner_repo) != 2:
        print("--repo must be in the form owner/repo")
        return 2
    owner, repo = owner_repo

    token = getpass.getpass("Paste GitHub Personal Access Token (input hidden): ")
    if not token:
        print("No token provided, aborting")
        return 2

    for name in args.secrets:
        val = getpass.getpass(f"Paste value for secret {name} (input hidden): ")
        if not val:
            print(f"Skipping {name} (empty)")
            continue
        ok = set_secret(token, owner, repo, name, val)
        if not ok:
            print("Aborting due to failure")
            return 1

    print("All done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
