# Alembic for `license_server`

This directory contains an independent Alembic setup for the `license_server` service.

Usage

- Install alembic in your environment: `pip install alembic`
- Set the database URL in `LICENSE_DATABASE_URL` (recommended) or edit `alembic.ini`:

```powershell
$env:LICENSE_DATABASE_URL = 'postgres://user:pass@host:5432/dbname'
alembic -c alembic.ini revision --autogenerate -m "first migration"
alembic -c alembic.ini upgrade head
```

Notes
- `env.py` will read `LICENSE_DATABASE_URL` environment variable and override `sqlalchemy.url` from `alembic.ini`.
- The script expects to import `license_server.models.Base` to obtain `target_metadata` for autogenerate. Ensure your Python path includes the repo root (running from repo root is recommended).
