from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

# --- Measurement Type ---
class MeasurementTypeBase(BaseModel):
    type_key: str
    type_name: str
    unit: str

class MeasurementTypeCreate(MeasurementTypeBase):
    pass

class MeasurementTypeRead(MeasurementTypeBase):
    id: int

    class Config:
        from_attributes = True

# --- Measurement Value ---
class MeasurementValueBase(BaseModel):
    type_id: int
    value: Decimal

class MeasurementValueCreate(MeasurementValueBase):
    pass

class MeasurementValueRead(MeasurementValueBase):
    id: str
    measurement_type: MeasurementTypeRead

    class Config:
        from_attributes = True

# --- Measurement Session ---
class MeasurementSessionBase(BaseModel):
    member_user_id: str
    notes: Optional[str] = None

class MeasurementSessionCreate(MeasurementSessionBase):
    values: List[MeasurementValueCreate]

class MeasurementSessionRead(MeasurementSessionBase):
    id: str
    session_date: datetime
    recorded_by_user_id: str
    measurement_values: List[MeasurementValueRead]

    class Config:
        from_attributes = True
