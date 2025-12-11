#!/usr/bin/env python3
"""
Database Reset Script for MyRhythmNexus

This script resets the local database by:
1. Dropping all tables
2. Re-running all Alembic migrations
3. Creating initial admin user

USAGE:
    python backend/reset_db.py

WARNING: This will DELETE ALL DATA in the database!
Only run this in development environments.

The script will:
- Check if ENVIRONMENT=development in settings
- Ask for confirmation before proceeding
- Drop all tables with CASCADE
- Run 'alembic upgrade head'
- Create admin user with credentials from settings
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from alembic.config import Config
from alembic import command

from backend.core.config import settings
from backend.core.database import Base
from backend.core.security import hash_password
from backend.models.user import User, Role


async def reset_database():
    """Reset the database completely"""

    # Safety check - only allow in development
    if settings.ENVIRONMENT != "development":
        print("❌ ERROR: Database reset only allowed in development environment!")
        print(f"Current environment: {settings.ENVIRONMENT}")
        sys.exit(1)

    print("🔄 Starting database reset...")
    print(f"Database URL: {settings.DATABASE_URL}")
    print("⚠️  WARNING: This will delete ALL data!")

    # Confirm
    try:
        confirm = input("Are you sure you want to continue? (type 'yes' to confirm): ")
        if confirm.lower() != 'yes':
            print("❌ Operation cancelled.")
            return
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled.")
        return

    try:
        # Create async engine
        engine = create_async_engine(settings.DATABASE_URL, echo=False)

        async with engine.begin() as conn:
            print("🗑️  Dropping all tables...")

            # Get all table names and drop them with CASCADE
            result = await conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' AND tablename != 'spatial_ref_sys'
            """))
            tables = result.fetchall()
            
            for table in tables:
                table_name = table[0]
                await conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
                
            print("✅ All tables dropped.")

        # Close engine
        await engine.dispose()

        print("🔄 Running Alembic migrations...")

        # Run Alembic migrations using subprocess (sync)
        import subprocess
        import os
        
        env = os.environ.copy()
        env['PYTHONPATH'] = str(project_root)
        
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=project_root,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Alembic migration failed: {result.stderr}")
            raise Exception("Migration failed")
        
        print("✅ Migrations completed.")

        # Create admin user
        await create_admin_user()

        print("🎉 Database reset completed successfully!")
        print("You can now start the backend server.")

    except Exception as e:
        print(f"❌ ERROR during database reset: {e}")
        sys.exit(1)


async def create_admin_user():
    """Create initial admin user if it doesn't exist"""
    print("👤 Creating admin user...")

    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        # Check if admin user exists
        result = await conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": settings.FIRST_SUPERUSER}
        )
        existing = result.fetchone()

        if existing:
            print("ℹ️  Admin user already exists.")
            return

        # Create admin role if not exists
        await conn.execute(
            text("""
                INSERT INTO roles (role_name)
                VALUES ('ADMIN')
                ON CONFLICT (role_name) DO NOTHING
            """)
        )

        # Get admin role id
        result = await conn.execute(
            text("SELECT id FROM roles WHERE role_name = 'ADMIN'")
        )
        role_row = result.fetchone()
        if not role_row:
            raise Exception("Failed to create/get admin role")

        admin_role_id = role_row[0]

        # Create admin user
        hashed_password = hash_password(settings.FIRST_SUPERUSER_PASSWORD)
        import uuid
        user_id = str(uuid.uuid4())

        result = await conn.execute(
            text("""
                INSERT INTO users (id, first_name, last_name, email, password_hash, is_active, created_at, updated_at)
                VALUES (:id, :first_name, :last_name, :email, :password, true, NOW(), NOW())
                RETURNING id
            """),
            {
                "id": user_id,
                "first_name": "Admin",
                "last_name": "User",
                "email": settings.FIRST_SUPERUSER,
                "password": hashed_password
            }
        )

        user_row = result.fetchone()
        if not user_row:
            raise Exception("Failed to create admin user")

        user_id = user_row[0]

        # Assign admin role
        await conn.execute(
            text("""
                INSERT INTO user_roles (user_id, role_id)
                VALUES (:user_id, :role_id)
            """),
            {"user_id": user_id, "role_id": admin_role_id}
        )

    await engine.dispose()
    print("✅ Admin user created.")
    print(f"   Email: {settings.FIRST_SUPERUSER}")
    print(f"   Password: {settings.FIRST_SUPERUSER_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(reset_database())