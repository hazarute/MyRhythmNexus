from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.api.deps import get_db, get_current_user
from backend.models.user import User
from backend.models.operation import MeasurementType, MeasurementSession, MeasurementValue
from backend.schemas.measurement import (
    MeasurementTypeCreate, MeasurementTypeRead,
    MeasurementSessionCreate, MeasurementSessionRead
)

router = APIRouter()

# --- Types ---
@router.get("/types", response_model=List[MeasurementTypeRead])
async def list_measurement_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MeasurementType))
    return result.scalars().all()

@router.post("/types", response_model=MeasurementTypeRead)
async def create_measurement_type(
    type_in: MeasurementTypeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user) # Only admin/staff
):
    # Check if exists
    query = select(MeasurementType).where(MeasurementType.type_key == type_in.type_key)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Measurement type key already exists")

    obj = MeasurementType(**type_in.dict())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

# --- Sessions ---
@router.get("/sessions", response_model=List[MeasurementSessionRead])
async def list_measurement_sessions(
    member_id: str,
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(MeasurementSession)
        .where(MeasurementSession.member_user_id == member_id)
        .options(
            selectinload(MeasurementSession.measurement_values)
            .selectinload(MeasurementValue.measurement_type)
        )
        .order_by(MeasurementSession.session_date.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/sessions", response_model=MeasurementSessionRead)
async def create_measurement_session(
    session_in: MeasurementSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create Session
    session = MeasurementSession(
        member_user_id=session_in.member_user_id,
        recorded_by_user_id=current_user.id,
        notes=session_in.notes
    )
    db.add(session)
    await db.flush()

    # Create Values
    for val in session_in.values:
        m_val = MeasurementValue(
            session_id=session.id,
            type_id=val.type_id,
            value=val.value
        )
        db.add(m_val)
    
    await db.commit()
    await db.refresh(session)
    
    # Re-fetch to load relationships
    query = (
        select(MeasurementSession)
        .where(MeasurementSession.id == session.id)
        .options(
            selectinload(MeasurementSession.measurement_values)
            .selectinload(MeasurementValue.measurement_type)
        )
    )
    result = await db.execute(query)
    return result.scalar_one()

@router.delete("/sessions/{session_id}")
async def delete_measurement_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if session exists
    query = select(MeasurementSession).where(MeasurementSession.id == session_id)
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Measurement session not found")
    
    # Delete session (cascade will delete values)
    await db.delete(session)
    await db.commit()
    
    return {"message": "Measurement session deleted successfully"}

