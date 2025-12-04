from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.api.deps import get_db, get_current_active_admin
from backend.models.user import User
from backend.models.license import License
from backend.schemas.license import LicenseCreate, LicenseRead, LicenseUpdate
from backend.services.license import generate_license_key

router = APIRouter(tags=["admin"])

@router.post("/licenses", response_model=LicenseRead)
async def create_license(
    license_in: LicenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    license_key = license_in.license_key or generate_license_key()
    
    db_license = License(
        license_key=license_key,
        client_name=license_in.client_name,
        contact_email=license_in.contact_email,
        is_active=license_in.is_active,
        expires_at=license_in.expires_at,
        features=license_in.features
    )
    db.add(db_license)
    await db.commit()
    await db.refresh(db_license)
    return db_license

@router.get("/licenses", response_model=List[LicenseRead])
async def list_licenses(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    result = await db.execute(select(License).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/licenses/{license_id}", response_model=LicenseRead)
async def get_license(
    license_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    result = await db.execute(select(License).where(License.id == license_id))
    license_obj = result.scalar_one_or_none()
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    return license_obj

@router.patch("/licenses/{license_id}", response_model=LicenseRead)
async def update_license(
    license_id: str,
    license_in: LicenseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    result = await db.execute(select(License).where(License.id == license_id))
    license_obj = result.scalar_one_or_none()
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")

    update_data = license_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(license_obj, field, value)

    await db.commit()
    await db.refresh(license_obj)
    return license_obj

@router.delete("/licenses/{license_id}")
async def delete_license(
    license_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    result = await db.execute(select(License).where(License.id == license_id))
    license_obj = result.scalar_one_or_none()
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")

    await db.delete(license_obj)
    await db.commit()
    return {"message": "License deleted"}
