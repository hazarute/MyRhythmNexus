from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

# --- Class Template ---
class ClassTemplateBase(BaseModel):
    name: str

class ClassTemplateCreate(ClassTemplateBase):
    pass

class ClassTemplateRead(ClassTemplateBase):
    id: str

    class Config:
        from_attributes = True

# --- Class Event ---
class ClassEventBase(BaseModel):
    template_id: str
    instructor_user_id: str
    start_time: datetime
    end_time: datetime
    capacity: int
    is_cancelled: bool = False

class ClassEventCreate(ClassEventBase):
    pass

class ClassEventUpdate(BaseModel):
    template_id: Optional[str] = None
    instructor_user_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    capacity: Optional[int] = None
    is_cancelled: Optional[bool] = None

class ClassEventRead(ClassEventBase):
    id: str
    template: Optional[ClassTemplateRead] = None
    # We might want to include instructor details here, but for now let's keep it simple or add a nested UserRead if needed.
    # instructor: Optional[UserRead] = None 

    class Config:
        from_attributes = True

# --- Booking ---
class BookingBase(BaseModel):
    member_user_id: str
    event_id: str
    subscription_id: str

class BookingCreate(BookingBase):
    pass

class BookingRead(BookingBase):
    id: str
    status: str
    member_name: Optional[str] = None # Computed field for convenience

    class Config:
        from_attributes = True
