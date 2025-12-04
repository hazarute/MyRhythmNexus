import requests
import time

BASE_URL = "http://localhost:8003/api/v1"

def test_rate_limit():
    print("🚀 Testing Rate Limiting (Limit: 5/minute)...")
    
    key = "MRN-TEST-2024-KEY"
    hwid = "HW-TEST-LIMIT"
    
    for i in range(1, 10):
        print(f"Request #{i}...", end=" ")
        try:
            resp = requests.post(
                f"{BASE_URL}/license/validate",
                json={"license_key": key, "hardware_id": hwid}
            )
            
            if resp.status_code == 200:
                print("✅ OK")
            elif resp.status_code == 429:
                print("🛑 BLOCKED (Rate Limit Exceeded)")
                print(f"Response: {resp.text}")
                break
            else:
                print(f"⚠️ Unexpected: {resp.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            
        time.sleep(0.2)

if __name__ == "__main__":
    test_rate_limit()
