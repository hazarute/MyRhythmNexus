import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "MyRhythmNexus License Server"
    API_V1_STR: str = "/api/v1"
    
    # Database
    LICENSE_DATABASE_URL: str = "sqlite:///./license_server.db"
    
    # Security
    SECRET_KEY: str = "CHANGE_THIS_IN_PRODUCTION_SECRET_KEY"
    ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # Offline token expiry (days) - how long a client-saved JWT remains valid
    OFFLINE_TOKEN_EXPIRE_DAYS: int = 7

    # Rate limiting for license validation endpoint (SlowAPI format, e.g. "5/minute")
    LICENSE_VALIDATE_RATE: str = "5/minute"
    
    # RSA Keys
    # Prefer secrets passed via environment (LICENSE_PRIVATE_KEY / LICENSE_PUBLIC_KEY)
    # Fallback to file paths for local development
    PRIVATE_KEY_PATH: str = "license_server/private.pem"
    PUBLIC_KEY_PATH: str = "license_server/public.pem"

    LICENSE_PRIVATE_KEY: Optional[str] = None  # Full PEM string (set as secret in prod)
    LICENSE_PUBLIC_KEY: Optional[str] = None   # Full PEM string (optional)

    _private_key: Optional[bytes] = None
    _public_key: Optional[bytes] = None

    @property
    def PRIVATE_KEY(self) -> bytes:
        # 1) If LICENSE_PRIVATE_KEY env var provided, use that (keeps key out of repo)
        if self.LICENSE_PRIVATE_KEY:
            return self.LICENSE_PRIVATE_KEY.encode()

        # 2) Else, load from file paths (development fallback)
        if self._private_key is None:
            path = Path(self.PRIVATE_KEY_PATH)
            if path.exists():
                self._private_key = path.read_bytes()
            else:
                alt_path = Path("license_server") / "private.pem"
                if alt_path.exists():
                    self._private_key = alt_path.read_bytes()
                else:
                    raise FileNotFoundError(f"Private key not found at {self.PRIVATE_KEY_PATH} and LICENSE_PRIVATE_KEY not set")
        return self._private_key

    @property
    def PUBLIC_KEY(self) -> bytes:
        # 1) If LICENSE_PUBLIC_KEY env var provided, use that
        if self.LICENSE_PUBLIC_KEY:
            return self.LICENSE_PUBLIC_KEY.encode()

        # 2) Else, load from file paths (development fallback)
        if self._public_key is None:
            path = Path(self.PUBLIC_KEY_PATH)
            if path.exists():
                self._public_key = path.read_bytes()
            else:
                alt_path = Path("license_server") / "public.pem"
                if alt_path.exists():
                    self._public_key = alt_path.read_bytes()
                else:
                    raise FileNotFoundError(f"Public key not found at {self.PUBLIC_KEY_PATH} and LICENSE_PUBLIC_KEY not set")
        return self._public_key

    class Config:
        # Ensure we load the license_server/.env regardless of the current working directory
        env_file = str(Path(__file__).resolve().parent.parent / ".env")
        extra = "ignore"

settings = Settings()

