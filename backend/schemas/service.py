from typing import Optional
from decimal import Decimal
from pydantic import BaseModel

# --- Service Category ---
class ServiceCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class ServiceCategoryCreate(ServiceCategoryBase):
    pass

class ServiceCategoryRead(ServiceCategoryBase):
    id: int

    class Config:
        from_attributes = True

# --- Service Offering ---
class ServiceOfferingBase(BaseModel):
    name: str
    description: Optional[str] = None
    default_duration_minutes: int

class ServiceOfferingCreate(ServiceOfferingBase):
    pass

class ServiceOfferingRead(ServiceOfferingBase):
    id: str

    class Config:
        from_attributes = True

# --- Plan Definition ---
class PlanDefinitionBase(BaseModel):
    name: str
    description: Optional[str] = None
    access_type: str = "SESSION_BASED"  # "SESSION_BASED" or "TIME_BASED"
    sessions_granted: Optional[int] = None
    cycle_period: str  # e.g. "MONTHLY", "WEEKLY", "FIXED"
    repeat_weeks: int = 1
    is_active: bool = True

class PlanDefinitionCreate(PlanDefinitionBase):
    pass

class PlanDefinitionRead(PlanDefinitionBase):
    id: str

    class Config:
        from_attributes = True

# --- Service Package ---
class ServicePackageBase(BaseModel):
    name: str
    category_id: int
    offering_id: str
    plan_id: str
    price: Decimal
    is_bookable: bool = True
    is_active: bool = True

class ServicePackageCreate(ServicePackageBase):
    pass

class ServicePackageUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    offering_id: Optional[str] = None
    plan_id: Optional[str] = None
    price: Optional[Decimal] = None
    is_bookable: Optional[bool] = None
    is_active: Optional[bool] = None

class ServicePackageRead(ServicePackageBase):
    id: str
    category: Optional[ServiceCategoryRead] = None
    offering: Optional[ServiceOfferingRead] = None
    plan: Optional[PlanDefinitionRead] = None

    class Config:
        from_attributes = True
