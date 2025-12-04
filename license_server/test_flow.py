import requests
import jwt
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8001/api/v1"

def test_flow():
    print("🚀 Starting License Server Flow Test...")

    # 1. Create Customer
    print("\n1️⃣  Creating Customer...")
    customer_data = {
        "name": "FitLife Studio",
        "email": "contact@fitlife.com",
        "contact_person": "John Doe",
        "phone": "+905551234567"
    }
    resp = requests.post(f"{BASE_URL}/customers/", json=customer_data)
    if resp.status_code != 200:
        print(f"❌ Failed to create customer: {resp.text}")
        return
    customer = resp.json()
    print(f"✅ Customer Created: ID={customer['id']}, Name={customer['name']}")

    # 2. Create License
    print("\n2️⃣  Creating License...")
    license_data = {
        "customer_id": customer['id'],
        "license_key": "MRN-TEST-2024-KEY",
        "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        "features": {"qr": True, "finance": True},
        "is_active": True
    }
    resp = requests.post(f"{BASE_URL}/licenses/", json=license_data)
    if resp.status_code != 200:
        print(f"❌ Failed to create license: {resp.text}")
        return
    license_obj = resp.json()
    print(f"✅ License Created: Key={license_obj['license_key']}")

    # 3. Validate License (Client Side Simulation)
    print("\n3️⃣  Validating License (Client)...")
    hardware_id = "HW-1234-5678-90"
    validate_data = {
        "license_key": "MRN-TEST-2024-KEY",
        "hardware_id": hardware_id
    }
    resp = requests.post(f"{BASE_URL}/license/validate", json=validate_data)
    if resp.status_code != 200:
        print(f"❌ Validation request failed: {resp.text}")
        return
    
    validation = resp.json()
    if not validation['valid']:
        print(f"❌ License invalid: {validation['message']}")
        return
    
    token = validation['token']
    print(f"✅ Validation Successful!")
    print(f"🔑 Received JWT Token: {token[:20]}...")

    # 4. Verify Token (Offline Check)
    print("\n4️⃣  Verifying Token (Offline Check)...")
    try:
        with open("license_server/public.pem", "rb") as f:
            public_key = f.read()
        
        decoded = jwt.decode(token, public_key, algorithms=["RS256"])
        print(f"✅ Token Verified Successfully!")
        print(f"📜 Payload: {decoded}")
        
        if decoded['hwid'] == hardware_id:
            print("✅ Hardware ID matches!")
        else:
            print("❌ Hardware ID mismatch!")
            
    except Exception as e:
        print(f"❌ Token verification failed: {e}")

if __name__ == "__main__":
    test_flow()
