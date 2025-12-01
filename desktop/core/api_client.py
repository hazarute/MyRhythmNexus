import httpx
from typing import Any, Optional, Dict
from datetime import datetime, timedelta


class ApiClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.client = httpx.Client(base_url=base_url, timeout=10.0)

    def _convert_datetime_strings(self, data: Any) -> Any:
        """
        Recursively convert UTC datetime strings to local time (Turkey UTC+3)
        Handles nested dict/list structures
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key.endswith('_time') or key.endswith('_date') or key == 'check_in_time':
                    # Convert datetime strings
                    if isinstance(value, str) and ('T' in value or ' ' in value):
                        try:
                            converted = self._parse_and_convert_datetime(value)
                            if converted:
                                result[key] = converted
                                continue
                        except:
                            pass  # Keep original if conversion fails
                result[key] = self._convert_datetime_strings(value)
            return result
        elif isinstance(data, list):
            return [self._convert_datetime_strings(item) for item in data]
        else:
            return data

    def _parse_and_convert_datetime(self, time_str: str) -> Optional[str]:
        """
        Parse datetime string and convert UTC to Turkey timezone (UTC+3)
        """
        try:
            if time_str.endswith('Z'):
                # ISO format with Z: "2025-11-30T08:45:47.763468Z"
                utc_time = datetime.fromisoformat(time_str[:-1])
            elif 'T' in time_str:
                # ISO format without Z: "2025-11-30T08:45:47.763468"
                utc_time = datetime.fromisoformat(time_str)
            else:
                # Simple format: "2025-11-30 08:45:37"
                utc_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            
            # Convert to Turkey timezone (UTC+3)
            local_time = utc_time + timedelta(hours=3)
            return local_time.strftime('%Y-%m-%dT%H:%M:%S')
        except:
            return None

    def set_token(self, token: str):
        self.token = token
        self.client.headers.update({"Authorization": f"Bearer {token}"})

    def login(self, username: str, password: str) -> bool:
        try:
            # OAuth2PasswordRequestForm expects form data: username, password
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

    def get(self, path: str, params: Dict[str, Any] = None) -> Any:
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

    def post(self, path: str, json: dict = None, data: dict = None) -> Any:
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

    def put(self, path: str, json: dict = None) -> Any:
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

    def patch(self, path: str, json: dict = None) -> Any:
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
