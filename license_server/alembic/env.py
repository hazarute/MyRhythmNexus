from __future__ import with_statement

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# ensure repo root is importable so we can import package modules
current_dir = os.path.dirname(__file__)
repo_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# this Alembic Config object provides access to the values within the .ini file
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your model's MetaData object here
try:
    from license_server.models import Base
    target_metadata = Base.metadata
except Exception:
    target_metadata = None


def get_url() -> str:
    return os.environ.get("LICENSE_DATABASE_URL") or config.get_main_option("sqlalchemy.url")


# override sqlalchemy.url from env when present
config.set_main_option("sqlalchemy.url", get_url())


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
