import uuid
import logging
from typing import Optional, Dict, Any
from desktop.core.config import DesktopConfig
from desktop.core.api_client import ApiClient

logger = logging.getLogger(__name__)

class LicenseManager:
    def __init__(self, api_client: ApiClient):
        self.api_client = api_client
        self._cached_features: Dict[str, Any] = {}
        self._license_status: Dict[str, Any] = {}

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

    def validate_license_sync(self) -> Dict[str, Any]:
        """Synchronous validation for startup checks"""
        key = self.get_license_key()
        if not key:
            return {"valid": False, "message": "No license key found."}

        machine_id = self.get_machine_id()
        
        try:
            # Using the underlying httpx client for a direct call if needed, 
            # or we can make ApiClient support sync calls. 
            # Since ApiClient uses httpx.Client (sync by default unless AsyncClient is used),
            # we can use it directly.
            
            response = self.api_client.client.post(
                "/api/v1/license/validate",
                json={"license_key": key, "machine_id": machine_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                self._license_status = data
                self._cached_features = data.get("features", {}) or {}
                return data
            else:
                try:
                    detail = response.json().get("detail", response.text)
                except:
                    detail = response.text
                return {"valid": False, "message": f"Validation failed: {detail}"}
        except Exception as e:
            logger.error(f"License validation error: {e}")
            return {"valid": False, "message": f"Connection error: {str(e)}"}

    def is_feature_enabled(self, feature_name: str) -> bool:
        # Check cache first
        if feature_name in self._cached_features:
            return bool(self._cached_features.get(feature_name, False))
        return False
