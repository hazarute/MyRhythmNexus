from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .core.config import settings

<<<<<<< HEAD
# Support both SQLite (development) and PostgreSQL (production via DATABASE_URL)
database_url = settings.LICENSE_DATABASE_URL

# SQLite requires the special connect_args; other DBs must not receive it.
connect_args = {}
if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(database_url, connect_args=connect_args)
=======
engine = create_engine(
    settings.LICENSE_DATABASE_URL, connect_args={"check_same_thread": False}
)
>>>>>>> e4fab4fd669429a8657ad9bad273584201312c16
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
