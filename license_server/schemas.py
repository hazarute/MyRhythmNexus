from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

# Customer Schemas
class CustomerBase(BaseModel):
    name: str
    email: EmailStr
    contact_person: Optional[str] = None
    phone: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# License Schemas
class LicenseBase(BaseModel):
    expires_at: datetime
    features: Dict[str, Any] = {}
    is_active: bool = True

class LicenseCreate(LicenseBase):
    customer_id: int
    license_key: str # MRN-XXXX...

class License(LicenseBase):
    id: int
    license_key: str
    customer_id: int
    hardware_id: Optional[str] = None
    start_date: datetime
    last_checkin: Optional[datetime] = None

    class Config:
        from_attributes = True

# Validation Request/Response
class LicenseValidateRequest(BaseModel):
    license_key: str
    hardware_id: str

class LicenseValidateResponse(BaseModel):
    valid: bool
    token: Optional[str] = None # JWT Signed Token
    message: Optional[str] = None
