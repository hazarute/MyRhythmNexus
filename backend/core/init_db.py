from sqlalchemy import select
from sqlalchemy.exc import ProgrammingError
from backend.core.database import SessionLocal
from backend.core.config import settings
from backend.core.security import hash_password
from backend.models.user import User, Role, Instructor
from backend.models.operation import MeasurementType
import asyncio
import os
from alembic.config import Config
from alembic import command

async def init_db():
    async with SessionLocal() as db:
        # If DB tables are missing, run alembic migrations automatically
        try:
            result = await db.execute(select(Role).where(Role.role_name == "ADMIN"))
        except ProgrammingError:
            alembic_cfg = Config(os.path.join(os.getcwd(), "alembic.ini"))
            await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
            # re-run the query after migrations
            result = await db.execute(select(Role).where(Role.role_name == "ADMIN"))

        # 1. Create Roles
        admin_role = result.scalar_one_or_none()
        if not admin_role:
            admin_role = Role(role_name="ADMIN")
            db.add(admin_role)
            
        result = await db.execute(select(Role).where(Role.role_name == "MEMBER"))
        member_role = result.scalar_one_or_none()
        if not member_role:
            member_role = Role(role_name="MEMBER")
            db.add(member_role)
            
        await db.commit()
        
        # 2. Create Superuser
        result = await db.execute(select(User).where(User.email == settings.FIRST_SUPERUSER))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                email=settings.FIRST_SUPERUSER,
                first_name="Admin",
                last_name="User",
                password_hash=hash_password(settings.FIRST_SUPERUSER_PASSWORD),
                is_active=True,
            )
            
            # Re-fetch role to ensure it's attached to session
            result = await db.execute(select(Role).where(Role.role_name == "ADMIN"))
            admin_role = result.scalar_one()
            
            user.roles.append(admin_role)
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            # 3. Create Instructor Profile for Admin
            instructor = Instructor(user_id=user.id, bio="System Admin")
            db.add(instructor)
            await db.commit()
            
            print(f"Superuser created: {settings.FIRST_SUPERUSER}")
        else:
            print(f"Superuser already exists: {settings.FIRST_SUPERUSER}")
        
        # 4. Initialize Measurement Types
        measurement_types_data = [
            # Genel Vücut Ölçüleri
            {"type_key": "height", "type_name": "Boy", "unit": "cm"},
            {"type_key": "weight", "type_name": "Kilo", "unit": "kg"},
            # Üst Vücut
            {"type_key": "neck", "type_name": "Boyun", "unit": "cm"},
            {"type_key": "shoulder", "type_name": "Omuz", "unit": "cm"},
            {"type_key": "chest", "type_name": "Göğüs", "unit": "cm"},
            {"type_key": "arm_bicep", "type_name": "Kol (Pazu)", "unit": "cm"},
            {"type_key": "forearm", "type_name": "Ön Kol", "unit": "cm"},
            # Gövde
            {"type_key": "waist", "type_name": "Bel", "unit": "cm"},
            {"type_key": "love_handle", "type_name": "Simit", "unit": "cm"},
            {"type_key": "hip", "type_name": "Kalça", "unit": "cm"},
            {"type_key": "hip_seat", "type_name": "Basen", "unit": "cm"},
            # Alt Vücut
            {"type_key": "thigh", "type_name": "Bacak (Üst)", "unit": "cm"},
            {"type_key": "calf", "type_name": "Kalf (Baldır)", "unit": "cm"},
        ]
        
        for mt_data in measurement_types_data:
            result = await db.execute(select(MeasurementType).where(MeasurementType.type_key == mt_data["type_key"]))
            if not result.scalar_one_or_none():
                mt = MeasurementType(**mt_data)
                db.add(mt)
        
        await db.commit()
        print("Measurement types initialized.")
