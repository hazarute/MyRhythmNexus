from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class ActivityItem(BaseModel):
    id: str  # Unique ID for frontend key (e.g., "sale_123")
    type: str  # 'checkin', 'sale', 'booking'
    description: str
    timestamp: datetime
    user_name: str

class ScheduleItem(BaseModel):
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    occupancy: str  # "3/10" or "Dolu"
    status: str # 'active', 'cancelled'

class DashboardStats(BaseModel):
    active_members: int
    todays_classes: int
    pending_payments_amount: float
    debt_members_count: int
    monthly_revenue: float
    todays_schedule: List[ScheduleItem]
    recent_activities: List[ActivityItem]


class DebtMember(BaseModel):
    id: str
    first_name: str
    last_name: str
    debt_amount: float
