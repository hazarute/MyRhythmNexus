from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)


class Base(DeclarativeBase):
    pass


# Database engine with Turkey timezone
connect_args = {}
if "postgresql" in str(settings.DATABASE_URL):
    connect_args = {
        "server_settings": {
            "timezone": "Europe/Istanbul"
        }
    }

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args=connect_args
)
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    future=True,
)


async def get_db():
    async with SessionLocal() as session:
        yield session
