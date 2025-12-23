#!/usr/bin/env python3
"""Test script: create a member, create a subscription, create check-ins, delete subscription,
and verify that related SessionCheckIn records are removed from the backend.

Usage: python backend/scripts/test_subscription_checkin_cleanup.py

This script calls the running backend API on localhost:8000 by default.
"""
import requests
import uuid
import os
from datetime import datetime

BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

ADMIN_EMAIL = "hazarute@gmail.com"
ADMIN_PASSWORD = "123123"


def login(email: str, password: str):
    url = f"{BASE_URL}/api/v1/auth/login/access-token"
    resp = requests.post(url, data={"username": email, "password": password})
    resp.raise_for_status()
    return resp.json().get("access_token")


def list_packages(token: str):
    url = f"{BASE_URL}/api/v1/services/packages"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    return resp.json()


def create_member(token: str, email: str):
    url = f"{BASE_URL}/api/v1/members"
    payload = {
        "email": email,
        "first_name": "Dummy",
        "last_name": "User",
        "phone_number": "0000000000",
        "password": "dummy-pass",
        "is_active": True,
    }
    resp = requests.post(url, json=payload, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    return resp.json()


def create_subscription(token: str, member_id: str, package_id: str):
    url = f"{BASE_URL}/api/v1/sales/subscriptions-with-events"
    payload = {
        "member_user_id": member_id,
        "package_id": package_id,
        "start_date": datetime.utcnow().isoformat(),
    }
    resp = requests.post(url, json=payload, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    return resp.json()


def get_qr_token(token: str, subscription_id: str):
    url = f"{BASE_URL}/api/v1/checkin/subscriptions/{subscription_id}/qr-code"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    return resp.json().get("qr_token")


def do_checkin(token: str, qr_token: str, event_id=None):
    url = f"{BASE_URL}/api/v1/checkin/check-in"
    payload = {"qr_token": qr_token}
    if event_id:
        payload["event_id"] = event_id
    resp = requests.post(url, json=payload, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    return resp.json()


def list_checkins(token: str, member_id: str):
    url = f"{BASE_URL}/api/v1/checkin/history?member_id={member_id}"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    return resp.json()


def delete_subscription(token: str, subscription_id: str):
    url = f"{BASE_URL}/api/v1/sales/subscriptions/{subscription_id}"
    resp = requests.delete(url, headers={"Authorization": f"Bearer {token}"})
    if resp.status_code not in (200, 204):
        resp.raise_for_status()


def main():
    print("Logging in...")
    token = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    print("Token acquired")

    print("Listing packages...")
    packages = list_packages(token)
    if not packages:
        print("No packages available. Create a package first.")
        return
    package = packages[0]
    print(f"Using package: {package.get('id')} - {package.get('name')}")

    # Create unique member
    unique_email = f"dummy+{uuid.uuid4().hex[:8]}@example.com"
    print(f"Creating member {unique_email}...")
    member = create_member(token, unique_email)
    member_id = member.get("id")
    print(f"Member created: {member_id}")

    # Create subscription
    print("Creating subscription...")
    subscription = create_subscription(token, member_id, package.get('id'))
    sub_id = subscription.get('id')
    print(f"Subscription created: {sub_id}")

    # Get QR token for check-in
    print("Fetching QR token...")
    qr_token = get_qr_token(token, sub_id)
    print(f"QR token: {qr_token}")

    # Perform a couple check-ins
    print("Performing 2 check-ins...")
    for i in range(2):
        res = do_checkin(token, qr_token)
        print(f"Check-in {i+1}: {res.get('message')} at {res.get('check_in_time')}")

    # List checkins before deletion
    pre = list_checkins(token, member_id)
    print(f"Check-ins before delete: {len(pre)}")

    # Delete subscription
    print("Deleting subscription...")
    delete_subscription(token, sub_id)
    print("Subscription deleted.")

    # List checkins after deletion
    post = list_checkins(token, member_id)
    print(f"Check-ins after delete: {len(post)}")

    if len(post) == 0:
        print("SUCCESS: Related check-ins were removed from DB.")
    else:
        print("FAIL: Related check-ins remain in DB.")


if __name__ == '__main__':
    main()
