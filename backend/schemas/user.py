from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
import re

class RoleRead(BaseModel):
    id: int
    role_name: str

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    is_active: bool = True

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v):
        if v is not None:
            # Remove all non-digit characters for validation
            digits_only = re.sub(r'\D', '', v)
            # Check if it's a valid phone number (10-15 digits)
            if not 10 <= len(digits_only) <= 15:
                raise ValueError('Phone number must be between 10 and 15 digits')
            # Format as XXX-XXX-XXXX for US numbers or keep international format
            if len(digits_only) == 10:
                return f"{digits_only[:3]}-{digits_only[3:6]}-{digits_only[6:]}"
            else:
                return digits_only
        return v

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class UserRead(UserBase):
    id: str
    roles: List[RoleRead] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True