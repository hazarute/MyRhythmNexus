import httpx
import jwt
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

from .config import get_backend_url


class ApiClient:
    def __init__(self, base_url: Optional[str] = None):
        # Prefer config-defined backend URL, otherwise use provided base_url or fallback to localhost
        cfg_url = get_backend_url()
        if base_url:
            self.base_url = base_url
        elif cfg_url:
            self.base_url = cfg_url
        else:
            self.base_url = "http://localhost:8000"
        self.token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.client = httpx.Client(base_url=self.base_url, timeout=10.0)
        self._refresh_margin = timedelta(minutes=5)

    def _convert_datetime_strings(self, data: Any) -> Any:
        """Recursively convert UTC datetime strings to local time."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key.endswith('_time') or key.endswith('_date') or key == 'check_in_time':
                    if isinstance(value, str) and ('T' in value or ' ' in value):
                        try:
                            converted = self._parse_and_convert_datetime(value)
                            if converted:
                                result[key] = converted
                                continue
                        except:
                            pass
                result[key] = self._convert_datetime_strings(value)
            return result
        if isinstance(data, list):
            return [self._convert_datetime_strings(item) for item in data]
        return data

    def _parse_and_convert_datetime(self, time_str: str) -> Optional[str]:
        try:
            if time_str.endswith('Z'):
                utc_time = datetime.fromisoformat(time_str[:-1])
            elif 'T' in time_str:
                utc_time = datetime.fromisoformat(time_str)
            else:
                utc_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            local_time = utc_time + timedelta(hours=3)
            return local_time.strftime('%Y-%m-%dT%H:%M:%S')
        except:
            return None

    def _store_token(self, token: str):
        self.token = token
        self.client.headers.update({"Authorization": f"Bearer {token}"})
        self.token_expiry = self._decode_expiry(token)

    def _decode_expiry(self, token: str) -> Optional[datetime]:
        try:
            payload = jwt.decode(token, options={"verify_signature": False}, algorithms=["HS256"])
            exp = payload.get("exp")
            if exp:
                return datetime.utcfromtimestamp(exp)
        except jwt.PyJWTError:
            pass
        return None

    def _ensure_token_fresh(self):
        if not self.token or not self.token_expiry:
            return
        if datetime.utcnow() + self._refresh_margin >= self.token_expiry:
            self.refresh_token()

    def set_token(self, token: str):
        self._store_token(token)

    def login(self, username: str, password: str) -> bool:
        try:
            response = self.client.post(
                "/api/v1/auth/login/access-token",
                data={"username": username, "password": password}
            )
            response.raise_for_status()
            data = response.json()
            self.set_token(data["access_token"])
            return True
        except Exception as e:
            print(f"Login failed: {e}")
            return False

    def refresh_token(self):
        try:
            response = self.client.post("/api/v1/auth/refresh-token")
            response.raise_for_status()
            data = response.json()
            self.set_token(data["access_token"])
            return data
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Request failed: {e}")
            raise

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        self._ensure_token_fresh()
        try:
            response = self.client.get(path, params=params)
            response.raise_for_status()
            data = response.json()
            return self._convert_datetime_strings(data)
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Request failed: {e}")
            raise

    def post(self, path: str, json: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Any:
        self._ensure_token_fresh()
        try:
            response = self.client.post(path, json=json, data=data)
            response.raise_for_status()
            data = response.json()
            return self._convert_datetime_strings(data)
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Request failed: {e}")
            raise

    def put(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        self._ensure_token_fresh()
        try:
            response = self.client.put(path, json=json)
            response.raise_for_status()
            data = response.json()
            return self._convert_datetime_strings(data)
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Request failed: {e}")
            raise

    def patch(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        self._ensure_token_fresh()
        try:
            response = self.client.patch(path, json=json)
            response.raise_for_status()
            data = response.json()
            return self._convert_datetime_strings(data)
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Request failed: {e}")
            raise

    def delete(self, path: str) -> Any:
        self._ensure_token_fresh()
        try:
            response = self.client.delete(path)
            response.raise_for_status()
            if response.status_code == 204:
                return None
            data = response.json()
            return self._convert_datetime_strings(data)
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Request failed: {e}")
            raise
