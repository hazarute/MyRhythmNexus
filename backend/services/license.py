import secrets
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.license import License
from backend.schemas.license import LicenseValidateResponse
from backend.core.time_utils import get_turkey_time

def generate_license_key() -> str:
    """
    Generates a license key in the format MRN-XXXX-XXXX-XXXX.
    """
    part1 = secrets.token_hex(2).upper()
    part2 = secrets.token_hex(2).upper()
    part3 = secrets.token_hex(2).upper()
    return f"MRN-{part1}-{part2}-{part3}"

async def validate_license(
    db: AsyncSession, license_key: str, machine_id: str
) -> LicenseValidateResponse:
    """
    Validates the license key against the database and machine ID.
    """
    result = await db.execute(select(License).where(License.license_key == license_key))
    license_obj = result.scalar_one_or_none()

    if not license_obj:
        return LicenseValidateResponse(valid=False, message="License key not found.")

    if not license_obj.is_active:
        return LicenseValidateResponse(valid=False, message="License is inactive.")

    now = get_turkey_time()
    
    # Ensure expires_at is timezone aware or comparable
    expires_at = license_obj.expires_at
    
    # Handle naive datetime from SQLite/DB
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=now.tzinfo)
    
    if expires_at < now:
        return LicenseValidateResponse(valid=False, message="License has expired.", expires_at=expires_at)

    # Hardware ID check
    if license_obj.hardware_id is None:
        # First time activation, lock to this machine
        license_obj.hardware_id = machine_id
        license_obj.last_check_in = now
        
        await db.commit()
        await db.refresh(license_obj)
    elif license_obj.hardware_id != machine_id:
        return LicenseValidateResponse(valid=False, message="License is already used on another machine.")
    else:
        # Update last check-in
        license_obj.last_check_in = now
        await db.commit()
        await db.refresh(license_obj)

    return LicenseValidateResponse(
        valid=True,
        message="License is valid.",
        expires_at=license_obj.expires_at,
        features=license_obj.features
    )

async def check_feature(
    db: AsyncSession, license_key: str, feature_name: str
) -> bool:
    """
    Checks if a specific feature is enabled for the license.
    """
    result = await db.execute(select(License).where(License.license_key == license_key))
    license_obj = result.scalar_one_or_none()

    if not license_obj or not license_obj.is_active:
        return False
    
    if not license_obj.features:
        return False
        
    features = license_obj.features
    # Assuming features is a dict like {"module_a": true, "module_b": false}
    if isinstance(features, dict):
        return features.get(feature_name, False)
    return False
