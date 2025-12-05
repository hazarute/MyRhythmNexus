import uuid
import logging
import jwt
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from desktop.core.config import DesktopConfig
from desktop.core.api_client import ApiClient

logger = logging.getLogger(__name__)

class LicenseManager:
    def __init__(self, api_client: ApiClient):
        self.api_client = api_client
        self._cached_features: Dict[str, Any] = {}
        self._license_status: Dict[str, Any] = {}
        # Keep default, but prefer the config value at runtime (allows override via config.json)
        self.LICENSE_SERVER_URL = DesktopConfig.LICENSE_SERVER_URL

    def _get_license_server_url(self) -> str:
        """Return the effective license server URL: prefer config override, otherwise default."""
        try:
            # DesktopConfig.load_license_server_url reads config and falls back to default
            return DesktopConfig.load_license_server_url()
        except Exception:
            return self.LICENSE_SERVER_URL

    def get_machine_id(self) -> str:
        """Generates a unique machine ID based on hardware."""
        # Use UUIDv5 to generate a stable, full-length UUID based on the MAC address.
        # This hides the raw MAC address and avoids the "0000..." padding look.
        node = uuid.getnode()
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "myrhythmnexus.com")
        return str(uuid.uuid5(namespace, str(node)))

    def get_license_key(self) -> Optional[str]:
        return DesktopConfig.get_value("license_key")

    def save_license_key(self, key: str):
        DesktopConfig.set_value("license_key", key)

    def get_license_token(self) -> Optional[str]:
        return DesktopConfig.get_value("license_token")

    def save_license_token(self, token: str):
        DesktopConfig.set_value("license_token", token)

    def validate_license_sync(self) -> Dict[str, Any]:
        """
        Validates license with Offline-First strategy.
        1. Try to reach License Server -> Get Token -> Save Token -> Verify
        2. If unreachable -> Load Token -> Verify
        """
        key = self.get_license_key()
        if not key:
            return {"valid": False, "message": "No license key found."}

        machine_id = self.get_machine_id()
        
        # 1. Try Online Validation
        try:
            url = self._get_license_server_url()
            response = requests.post(
                f"{url}/license/validate",
                json={"license_key": key, "hardware_id": machine_id},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("valid") and data.get("token"):
                    # Save token
                    self.save_license_token(data["token"])
                    return self._verify_token(data["token"], machine_id)
                else:
                    return {"valid": False, "message": data.get("message", "Validation failed")}
        except Exception as e:
            logger.warning(f"Online validation failed ({e}). Switching to offline mode.")

        # 2. Offline Validation
        token = self.get_license_token()
        if token:
            return self._verify_token(token, machine_id)
        
        return {"valid": False, "message": "License validation failed. Internet connection required for first activation."}

    def _verify_token(self, token: str, machine_id: str) -> Dict[str, Any]:
        try:
            # Load Public Key
            pub_key_path = Path(__file__).parent.parent / "assets" / "public.pem"
            if not pub_key_path.exists():
                 return {"valid": False, "message": "Security error: Public key missing."}
                 
            public_key = pub_key_path.read_bytes()
            
            # Decode & Verify
            payload = jwt.decode(token, public_key, algorithms=["RS256"])
            
            # Check Hardware ID
            if payload.get("hwid") != machine_id:
                 return {"valid": False, "message": "License is locked to another device."}
            
            # Success
            self._cached_features = payload.get("features", {})
            return {"valid": True, "message": "License valid", "features": self._cached_features}
            
        except jwt.ExpiredSignatureError:
            return {"valid": False, "message": "License token expired. Please connect to internet."}
        except jwt.InvalidTokenError as e:
            return {"valid": False, "message": f"Invalid license token: {e}"}
        except Exception as e:
            return {"valid": False, "message": f"Verification error: {e}"}

    def is_feature_enabled(self, feature_name: str) -> bool:
        # For now, features are not enforced by the desktop app.
        # Return True to avoid accidentally disabling functionality
        # if `features` payload is missing or not used yet.
        return True
