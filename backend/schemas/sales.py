from typing import Optional, List
from decimal import Decimal
from datetime import datetime, time
from pydantic import BaseModel, field_validator
from backend.models.operation import SubscriptionStatus, PaymentMethod
from backend.schemas.service import ServicePackageRead

# --- ClassEvent Schemas for Subscription ---
class DayAndTime(BaseModel):
    """Day of week and time for a ClassEvent"""
    day: str  # "monday", "tuesday", ..., "sunday"
    time: str  # Time in "HH:MM" format (e.g., "14:00")

class ClassEventCreate(BaseModel):
    """Parameters for creating ClassEvent(s) with a subscription"""
    days_and_times: List[DayAndTime]  # List of {day, time} pairs
    instructor_user_id: str  # Instructor user ID
    repeat_weeks: int = 1  # Number of weeks to repeat
    capacity: int = 10  # Class capacity

# --- Payment Schemas ---
class PaymentBase(BaseModel):
    amount_paid: Decimal
    payment_method: PaymentMethod
    refund_amount: Optional[Decimal] = None
    refund_reason: Optional[str] = None

    @field_validator('amount_paid')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v >= Decimal("100000000"):
            raise ValueError('Tutar 100.000.000 TL den küçük olmalıdır.')
        return v

class PaymentCreate(PaymentBase):
    subscription_id: str

class PaymentRead(PaymentBase):
    id: str
    subscription_id: str
    recorded_by_user_id: str
    payment_date: datetime
    refund_date: Optional[datetime] = None
    
    # Extra fields for UI display
    member_name: Optional[str] = None
    package_name: Optional[str] = None

    class Config:
        from_attributes = True

class PaymentPagination(BaseModel):
    total: int
    page: int
    size: int
    pages: int
    items: List[PaymentRead]

# --- Subscription Schemas ---
class SubscriptionBase(BaseModel):
    member_user_id: str
    package_id: str
    start_date: datetime
    # end_date is usually calculated, but can be overridden if needed
    status: SubscriptionStatus = SubscriptionStatus.active

class SubscriptionCreate(SubscriptionBase):
    # Optional: Create a payment along with subscription
    initial_payment: Optional[PaymentBase] = None
    purchase_price_override: Optional[Decimal] = None  # Optional: Override package price with custom amount

class SubscriptionCreateWithEvents(SubscriptionBase):
    """Create subscription with optional ClassEvent(s) for SESSION_BASED plans"""
    initial_payment: Optional[PaymentBase] = None
    class_events: Optional[ClassEventCreate] = None  # Optional ClassEvent parameters
    purchase_price_override: Optional[Decimal] = None  # Optional: Override package price with custom amount

class SubscriptionRead(SubscriptionBase):
    id: str
    purchase_price: Decimal
    end_date: datetime
    used_sessions: int
    access_type: str = "SESSION_BASED"
    attendance_count: int = 0
    payments: List[PaymentRead] = []
    package: Optional[ServicePackageRead] = None

    class Config:
        from_attributes = True
