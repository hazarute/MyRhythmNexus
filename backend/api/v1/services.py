from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from backend.api.deps import get_db
from backend.models.service import (
    ServiceCategory,
    ServiceOffering,
    PlanDefinition,
    ServicePackage,
)
from backend.schemas.service import (
    ServiceCategoryCreate,
    ServiceCategoryRead,
    ServiceOfferingCreate,
    ServiceOfferingRead,
    PlanDefinitionCreate,
    PlanDefinitionRead,
    ServicePackageCreate,
    ServicePackageRead,
    ServicePackageUpdate,
)

router = APIRouter()

# --- Categories ---
@router.get("/categories", response_model=List[ServiceCategoryRead])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceCategory))
    return result.scalars().all()

@router.post("/categories", response_model=ServiceCategoryRead)
async def create_category(
    category_in: ServiceCategoryCreate, db: AsyncSession = Depends(get_db)
):
    category = ServiceCategory(**category_in.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category

@router.delete("/categories/{category_id}", status_code=204)
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)):
    category = await db.get(ServiceCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Kategori bulunamadı")
    
    # Check if any ServicePackage uses this category
    result = await db.execute(
        select(ServicePackage).where(ServicePackage.category_id == category_id).limit(1)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail="Bu kategori kullanımda olduğu için silinemez. Önce bu kategoriye ait paketleri silin."
        )
    
    try:
        await db.delete(category)
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, 
            detail="Bu kategori silinemez. İlişkili kayıtlar mevcut."
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- Offerings ---
@router.get("/offerings", response_model=List[ServiceOfferingRead])
async def list_offerings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceOffering))
    return result.scalars().all()

@router.post("/offerings", response_model=ServiceOfferingRead)
async def create_offering(
    offering_in: ServiceOfferingCreate, db: AsyncSession = Depends(get_db)
):
    offering = ServiceOffering(**offering_in.model_dump())
    db.add(offering)
    await db.commit()
    await db.refresh(offering)
    return offering

@router.delete("/offerings/{offering_id}", status_code=204)
async def delete_offering(offering_id: str, db: AsyncSession = Depends(get_db)):
    offering = await db.get(ServiceOffering, offering_id)
    if not offering:
        raise HTTPException(status_code=404, detail="Hizmet bulunamadı")
    
    # Check if any ServicePackage uses this offering
    result = await db.execute(
        select(ServicePackage).where(ServicePackage.offering_id == offering_id).limit(1)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail="Bu hizmet kullanımda olduğu için silinemez. Önce bu hizmete ait paketleri silin."
        )
    
    try:
        await db.delete(offering)
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, 
            detail="Bu hizmet silinemez. İlişkili kayıtlar mevcut."
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- Plans ---
@router.get("/plans", response_model=List[PlanDefinitionRead])
async def list_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlanDefinition))
    return result.scalars().all()

@router.post("/plans", response_model=PlanDefinitionRead)
async def create_plan(
    plan_in: PlanDefinitionCreate, db: AsyncSession = Depends(get_db)
):
    plan = PlanDefinition(**plan_in.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan

@router.delete("/plans/{plan_id}", status_code=204)
async def delete_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    plan = await db.get(PlanDefinition, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan bulunamadı")
    
    # Check if any ServicePackage uses this plan
    result = await db.execute(
        select(ServicePackage).where(ServicePackage.plan_id == plan_id).limit(1)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail="Bu plan kullanımda olduğu için silinemez. Önce bu plana ait paketleri silin."
        )
    
    try:
        await db.delete(plan)
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, 
            detail="Bu plan silinemez. İlişkili kayıtlar mevcut."
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- Packages ---
@router.get("/packages", response_model=List[ServicePackageRead])
async def list_packages(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    query = (
        select(ServicePackage)
        .options(
            selectinload(ServicePackage.category),
            selectinload(ServicePackage.offering),
            selectinload(ServicePackage.plan),
        )
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/packages", response_model=ServicePackageRead)
async def create_package(
    package_in: ServicePackageCreate, db: AsyncSession = Depends(get_db)
):
    # Ensure package name is unique before inserting so we can return a friendly error
    existing = await db.execute(
        select(ServicePackage).where(ServicePackage.name == package_in.name).limit(1)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Aynı isimde ('{package_in.name}') bir paket zaten var. Başka bir isim kullanın.",
        )

    # Verify foreign keys exist
    category = await db.get(ServiceCategory, package_in.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    offering = await db.get(ServiceOffering, package_in.offering_id)
    if not offering:
        raise HTTPException(status_code=404, detail="Offering not found")
        
    plan = await db.get(PlanDefinition, package_in.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    package = ServicePackage(**package_in.model_dump())
    db.add(package)
    await db.commit()
    await db.refresh(package)
    
    # Re-fetch with relationships for response
    query = (
        select(ServicePackage)
        .where(ServicePackage.id == package.id)
        .options(
            selectinload(ServicePackage.category),
            selectinload(ServicePackage.offering),
            selectinload(ServicePackage.plan),
        )
    )
    result = await db.execute(query)
    return result.scalar_one()

@router.get("/packages/{package_id}", response_model=ServicePackageRead)
async def get_package(package_id: str, db: AsyncSession = Depends(get_db)):
    query = (
        select(ServicePackage)
        .where(ServicePackage.id == package_id)
        .options(
            selectinload(ServicePackage.category),
            selectinload(ServicePackage.offering),
            selectinload(ServicePackage.plan),
        )
    )
    result = await db.execute(query)
    package = result.scalar_one_or_none()
    if not package:
        raise HTTPException(status_code=404, detail="Service Package not found")
    return package

@router.put("/packages/{package_id}", response_model=ServicePackageRead)
async def update_package(
    package_id: str, package_in: ServicePackageUpdate, db: AsyncSession = Depends(get_db)
):
    package = await db.get(ServicePackage, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Service Package not found")
        
    update_data = package_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(package, field, value)
        
    db.add(package)
    await db.commit()
    await db.refresh(package)
    
    # Re-fetch with relationships
    query = (
        select(ServicePackage)
        .where(ServicePackage.id == package.id)
        .options(
            selectinload(ServicePackage.category),
            selectinload(ServicePackage.offering),
            selectinload(ServicePackage.plan),
        )
    )
    result = await db.execute(query)
    return result.scalar_one()

@router.delete("/packages/{package_id}", status_code=204)
async def delete_package(package_id: str, db: AsyncSession = Depends(get_db)):
    package = await db.get(ServicePackage, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Service Package not found")
        
    try:
        await db.delete(package)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400, 
            detail="Bu paket kullanımda olduğu için silinemez. (Bağlı abonelikler mevcut)"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
