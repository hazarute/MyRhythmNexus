from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from typing import Optional
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "MyRhythmNexus"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/mydb"

    # Security
    # SECRET_KEY is required in production; this makes Settings validation fail if absent.
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS - Desktop app için gerekli
    CORS_ORIGINS: list = [
        "http://localhost:8000",  # Development
        "https://yourdomain.com",  # Production domain
        "app://rhythm-nexus"  # Desktop app custom protocol (optional)
    ]

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Admin user
    FIRST_SUPERUSER: str = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "admin123"

    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production

    # Timezone
    TIMEZONE: str = "Europe/Istanbul"  # Turkey timezone for all operations

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

# Normalize DATABASE_URL coming from environment providers (e.g. Railway) which
# may provide a plain `postgres://` or `postgresql://` URL. SQLAlchemy async
# engine expects an async driver (asyncpg) when using `create_async_engine`.
# If the URL doesn't explicitly specify the asyncpg driver, convert it to
# `postgresql+asyncpg://...` so the already-installed `asyncpg` package is used
# and we avoid importing `psycopg2`.
try:
    raw_db = settings.DATABASE_URL
    if isinstance(raw_db, str):
        if raw_db.startswith("postgres://"):
            raw_db = raw_db.replace("postgres://", "postgresql+asyncpg://", 1)
        elif raw_db.startswith("postgresql://") and "+asyncpg" not in raw_db:
            raw_db = raw_db.replace("postgresql://", "postgresql+asyncpg://", 1)
        settings.DATABASE_URL = raw_db
except Exception:
    # If anything goes wrong, leave settings as-is and let the application fail
    # with a clear error later. We don't want to mask configuration problems.
    pass
