from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

class LicenseBase(BaseModel):
    client_name: str
    contact_email: Optional[EmailStr] = None
    is_active: bool = True
    expires_at: datetime
    features: Optional[Dict[str, Any]] = None

class LicenseCreate(LicenseBase):
    license_key: Optional[str] = None

class LicenseUpdate(BaseModel):
    client_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None
    features: Optional[Dict[str, Any]] = None
    hardware_id: Optional[str] = None

class LicenseRead(LicenseBase):
    id: str
    license_key: str
    hardware_id: Optional[str] = None
    last_check_in: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LicenseValidate(BaseModel):
    license_key: str
    machine_id: str

class LicenseValidateResponse(BaseModel):
    valid: bool
    message: str
    expires_at: Optional[datetime] = None
    features: Optional[Dict[str, Any]] = None
