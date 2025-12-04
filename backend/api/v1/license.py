from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db
from backend.schemas.license import LicenseValidate, LicenseValidateResponse
from backend.services.license import validate_license, check_feature

router = APIRouter(tags=["license"])

@router.post("/validate", response_model=LicenseValidateResponse)
async def validate_license_endpoint(
    data: LicenseValidate,
    db: AsyncSession = Depends(get_db)
):
    return await validate_license(db, data.license_key, data.machine_id)

@router.get("/check-feature/{feature_name}", response_model=bool)
async def check_feature_endpoint(
    feature_name: str,
    license_key: str,
    db: AsyncSession = Depends(get_db)
):
    return await check_feature(db, license_key, feature_name)
