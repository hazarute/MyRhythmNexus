import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8001/api/v1"

def create_license():
    print("Creating a new license for real device testing...")
    
    # 1. Create Customer (if not exists, or just use existing ID 1)
    # We'll assume ID 1 exists from previous test
    
    # 2. Create License
    key = "MRN-REAL-DEVICE-KEY"
    license_data = {
        "customer_id": 1,
        "license_key": key,
        "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        "features": {"qr": True, "finance": True, "real_device": True},
        "is_active": True
    }
    
    resp = requests.post(f"{BASE_URL}/licenses/", json=license_data)
    if resp.status_code == 200:
        print(f"✅ License Created: {key}")
    elif resp.status_code == 400 and "already exists" in resp.text:
        print(f"⚠️ License {key} already exists.")
    else:
        print(f"❌ Failed: {resp.text}")

if __name__ == "__main__":
    create_license()
