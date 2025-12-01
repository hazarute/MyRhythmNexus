from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "MyRhythmNexus"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/mydb"

    # Security
    SECRET_KEY: str = "change-me-in-production"
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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()


settings = Settings()
