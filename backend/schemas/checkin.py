from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class CheckInRequest(BaseModel):
    qr_token: str
    event_id: Optional[str] = None  # NULL for TIME_BASED or when no event available

class CheckInResponse(BaseModel):
    success: bool
    message: str
    member_name: str
    remaining_sessions: int
    check_in_time: str

class CheckInHistoryRead(BaseModel):
    id: str
    check_in_time: datetime
    event_id: Optional[str] = None
    event_name: str
    class_name: str  # "Zaman Bazlı Katılım" for TIME_BASED with no event
    subscription_name: str  # Package name for the subscription used
    verified_by_name: str

    class Config:
        from_attributes = True

class EligibleEvent(BaseModel):
    id: str
    name: str
    start_time: datetime
    end_time: datetime
    instructor_name: str

class ScanResult(BaseModel):
    valid: bool
    message: str
    member_name: Optional[str] = None
    subscription_name: Optional[str] = None
    remaining_sessions: Optional[int] = None
    access_type: Optional[str] = None
    attendance_count: Optional[int] = None
    eligible_events: List[EligibleEvent] = []
