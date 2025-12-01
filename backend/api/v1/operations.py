from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.api.deps import get_db
from backend.models.operation import ClassTemplate, ClassEvent, Booking, Subscription, BookingPermission, SubscriptionStatus
from backend.models.user import Instructor, User
from backend.schemas.operations import (
    ClassTemplateCreate,
    ClassTemplateRead,
    ClassEventCreate,
    ClassEventRead,
    ClassEventUpdate,
    BookingCreate,
    BookingRead
)

router = APIRouter()

# --- Class Templates ---
@router.get("/templates", response_model=List[ClassTemplateRead])
async def list_class_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClassTemplate))
    return result.scalars().all()

@router.post("/templates", response_model=ClassTemplateRead)
async def create_class_template(
    template_in: ClassTemplateCreate, db: AsyncSession = Depends(get_db)
):
    template = ClassTemplate(**template_in.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template

@router.put("/templates/{template_id}", response_model=ClassTemplateRead)
async def update_class_template(
    template_id: str, 
    template_in: ClassTemplateCreate, 
    db: AsyncSession = Depends(get_db)
):
    template = await db.get(ClassTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Class Template not found")
    
    template.name = template_in.name
    await db.commit()
    await db.refresh(template)
    return template

@router.delete("/templates/{template_id}")
async def delete_class_template(
    template_id: str, 
    db: AsyncSession = Depends(get_db)
):
    template = await db.get(ClassTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Class Template not found")
    
    await db.delete(template)
    await db.commit()
    return {"message": "Class Template deleted"}

# --- Class Events ---
@router.get("/events", response_model=List[ClassEventRead])
async def list_class_events(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    instructor_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(ClassEvent)
        .options(selectinload(ClassEvent.template))
        .order_by(ClassEvent.start_time)
    )

    if start_date:
        query = query.where(ClassEvent.start_time >= start_date)
    if end_date:
        query = query.where(ClassEvent.end_time <= end_date)
    if instructor_id:
        query = query.where(ClassEvent.instructor_user_id == instructor_id)
        
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/events", response_model=ClassEventRead)
async def create_class_event(
    event_in: ClassEventCreate, db: AsyncSession = Depends(get_db)
):
    # Verify template exists
    template = await db.get(ClassTemplate, event_in.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Class Template not found")
        
    # Verify instructor exists
    instructor = await db.get(Instructor, event_in.instructor_user_id)
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")

    event = ClassEvent(**event_in.model_dump())
    db.add(event)
    await db.commit()
    await db.refresh(event)
    
    # Re-fetch to populate relationships
    query = (
        select(ClassEvent)
        .where(ClassEvent.id == event.id)
        .options(selectinload(ClassEvent.template))
    )
    result = await db.execute(query)
    return result.scalar_one()

@router.get("/events/{event_id}", response_model=ClassEventRead)
async def get_class_event(event_id: str, db: AsyncSession = Depends(get_db)):
    query = (
        select(ClassEvent)
        .where(ClassEvent.id == event_id)
        .options(selectinload(ClassEvent.template))
    )
    result = await db.execute(query)
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Class Event not found")
    return event

@router.put("/events/{event_id}", response_model=ClassEventRead)
async def update_class_event(
    event_id: str, event_in: ClassEventUpdate, db: AsyncSession = Depends(get_db)
):
    event = await db.get(ClassEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Class Event not found")
        
    update_data = event_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
        
    db.add(event)
    await db.commit()
    await db.refresh(event)
    
    # Re-fetch
    query = (
        select(ClassEvent)
        .where(ClassEvent.id == event.id)
        .options(selectinload(ClassEvent.template))
    )
    result = await db.execute(query)
    return result.scalar_one()

@router.delete("/events/{event_id}", response_model=ClassEventRead)
async def cancel_class_event(event_id: str, db: AsyncSession = Depends(get_db)):
    event = await db.get(ClassEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Class Event not found")
    
    event.is_cancelled = True
    db.add(event)
    await db.commit()
    await db.refresh(event)
    
    # Re-fetch
    query = (
        select(ClassEvent)
        .where(ClassEvent.id == event.id)
        .options(selectinload(ClassEvent.template))
    )
    result = await db.execute(query)
    return result.scalar_one()

# --- Bookings ---
@router.get("/events/{event_id}/bookings", response_model=List[BookingRead])
async def list_event_bookings(event_id: str, db: AsyncSession = Depends(get_db)):
    query = (
        select(Booking)
        .where(Booking.event_id == event_id)
        .options(selectinload(Booking.member))
    )
    result = await db.execute(query)
    bookings = result.scalars().all()
    
    # Map to schema with member name
    response = []
    for b in bookings:
        b_read = BookingRead.model_validate(b)
        if b.member:
            b_read.member_name = f"{b.member.first_name} {b.member.last_name}"
        response.append(b_read)
    return response

@router.post("/bookings", response_model=BookingRead)
async def create_booking(
    booking_in: BookingCreate, db: AsyncSession = Depends(get_db)
):
    # 1. Validate Event
    event = await db.get(ClassEvent, booking_in.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # 2. Validate Subscription
    sub = await db.get(Subscription, booking_in.subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
        
    if sub.member_user_id != booking_in.member_user_id:
        raise HTTPException(status_code=400, detail="Subscription does not belong to this user")
        
    if sub.status != SubscriptionStatus.active:
        raise HTTPException(status_code=400, detail="Subscription is not active")

    # 3. Check Permissions
    # (Simplified: Assuming if admin selects it, it's okay, OR we enforce it)
    # Let's enforce it for consistency
    perm_query = (
        select(BookingPermission)
        .where(
            BookingPermission.package_id == sub.package_id,
            BookingPermission.template_id == event.template_id
        )
    )
    perm_result = await db.execute(perm_query)
    if not perm_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Subscription does not cover this event type")

    # 4. Create Booking
    booking = Booking(
        member_user_id=booking_in.member_user_id,
        event_id=booking_in.event_id,
        subscription_id=booking_in.subscription_id,
        status="confirmed"
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    
    # Load member for response
    query = select(Booking).where(Booking.id == booking.id).options(selectinload(Booking.member))
    result = await db.execute(query)
    booking = result.scalar_one()
    
    b_read = BookingRead.model_validate(booking)
    if booking.member:
        b_read.member_name = f"{booking.member.first_name} {booking.member.last_name}"
    return b_read

@router.delete("/bookings/{booking_id}")
async def cancel_booking(booking_id: str, db: AsyncSession = Depends(get_db)):
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Hard delete or soft delete? Let's hard delete for now or set status
    # booking.status = "cancelled_by_admin"
    # db.add(booking)
    await db.delete(booking) # Simple remove
    await db.commit()
    return {"success": True}
