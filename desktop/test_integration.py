import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from desktop.core.license_manager import LicenseManager
from desktop.core.api_client import ApiClient
from desktop.core.config import DesktopConfig

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_integration():
    print("🖥️  Testing Desktop License Integration...")
    
    # Mock ApiClient (not used for sync validation anymore, but needed for init)
    client = ApiClient() 
    manager = LicenseManager(client)
    
    # 1. Set Key
    key = "MRN-REAL-DEVICE-KEY"
    print(f"🔑 Setting License Key: {key}")
    manager.save_license_key(key)
    
    # 2. Online Validation
    print("\n🌍 Testing Online Validation...")
    result = manager.validate_license_sync()
    print(f"Result: {result}")
    
    if not result.get("valid"):
        print("❌ Online validation failed!")
        return

    print("✅ Online validation successful. Token should be saved.")
    
    # 3. Offline Validation (Simulated)
    print("\n🔌 Testing Offline Validation (Simulated)...")
    # Break the URL to force offline mode
    manager.LICENSE_SERVER_URL = "http://localhost:9999/api/v1"
    
    result_offline = manager.validate_license_sync()
    print(f"Result: {result_offline}")
    
    if result_offline.get("valid") and "License valid" in result_offline.get("message"):
        print("✅ Offline validation successful!")
    else:
        print("❌ Offline validation failed!")

if __name__ == "__main__":
    test_integration()
