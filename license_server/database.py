from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import settings in a robust way so the module works when the package is
# installed (`license_server.core.config`) and when the files are copied
# directly into the image root (e.g. `core.config`).
try:
    from license_server.core.config import settings
except Exception:
    try:
        from core.config import settings
    except Exception:
        # Last resort: relative import (works when imported as a package)
        from .core.config import settings


# Support both SQLite (development) and PostgreSQL (production via DATABASE_URL)
database_url = settings.LICENSE_DATABASE_URL

# Normalize PostgreSQL URLs so SQLAlchemy uses the `psycopg` (psycopg3)
# driver when possible. Railway/other providers sometimes give a
# `postgres://` or `postgresql://` URL which defaults to the psycopg2
# dialect; rewriting to `postgresql+psycopg://` lets SQLAlchemy pick the
# psycopg (v3) DBAPI which we install via `psycopg[binary]`.
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

# SQLite requires the special connect_args; other DBs must not receive it.
connect_args = {}
if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
