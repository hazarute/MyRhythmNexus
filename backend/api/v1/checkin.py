from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func

from backend.api.deps import get_db, get_current_user
from backend.models.user import User, Instructor
from backend.models.operation import (
    SubscriptionQrCode,
    Subscription,
    ClassEvent,
    SessionCheckIn,
    BookingPermission,
    SubscriptionStatus,
)
from backend.models.service import ServicePackage, PlanDefinition
from backend.schemas.checkin import CheckInRequest, CheckInResponse, CheckInHistoryRead, ScanResult, EligibleEvent

router = APIRouter()

@router.get("/scan", response_model=ScanResult)
async def scan_qr_code(
    qr_token: str,
    db: AsyncSession = Depends(get_db),
):
    # 1. Find Subscription by QR Token
    query = (
        select(SubscriptionQrCode)
        .where(SubscriptionQrCode.qr_token == qr_token, SubscriptionQrCode.is_active == True)
        .options(
            selectinload(SubscriptionQrCode.subscription).options(
                selectinload(Subscription.package).selectinload(ServicePackage.plan),
                selectinload(Subscription.member)
            )
        )
    )
    result = await db.execute(query)
    qr_code = result.scalar_one_or_none()

    if not qr_code:
        return ScanResult(valid=False, message="Geçersiz veya pasif QR kod.")
    
    subscription = qr_code.subscription
    member = subscription.member

    # 2. Validate Subscription Status
    if subscription.status != SubscriptionStatus.active:
        return ScanResult(valid=False, message=f"Abonelik durumu: {subscription.status.value}")
    
    now = datetime.now()
    if subscription.end_date.replace(tzinfo=None) < now:
        return ScanResult(valid=False, message="Abonelik süresi dolmuş.")

    plan = subscription.package.plan
    
    # Kalan hak hesaplama: access_type'a göre ayrıştır
    if plan.access_type == "SESSION_BASED":
        remaining = plan.sessions_granted - subscription.used_sessions if plan.sessions_granted > 0 else 9999
        # SESSION_BASED: Seans sınırı kontrol
        if remaining <= 0:
            return ScanResult(valid=False, message="Kalan hak yok.")
    else:
        # TIME_BASED: Sınırsız, katılım sayısını göster (opsiyonel)
        remaining = 9999

    # 3. Find Eligible Events (Happening now or starting soon)
    # Logic: Starts within next 60 mins OR Started less than 30 mins ago (late entry)
    # Adjust time window as needed
    time_window_start = now - timedelta(minutes=30)
    time_window_end = now + timedelta(minutes=60)
    
    events_query = (
        select(ClassEvent)
        .where(
            ClassEvent.start_time >= time_window_start,
            ClassEvent.start_time <= time_window_end,
            ClassEvent.is_cancelled == False
        )
        .options(
            selectinload(ClassEvent.template),
            selectinload(ClassEvent.instructor).selectinload(Instructor.user)
        )
    )
    events_result = await db.execute(events_query)
    potential_events = events_result.scalars().all()
    
    eligible_events = []
    for event in potential_events:
        # Check permission
        perm_query = (
            select(BookingPermission)
            .where(
                BookingPermission.package_id == subscription.package_id,
                BookingPermission.template_id == event.template_id
            )
        )
        perm_result = await db.execute(perm_query)
        if perm_result.scalar_one_or_none():
            eligible_events.append(EligibleEvent(
                id=event.id,
                name=event.template.name,
                start_time=event.start_time,
                end_time=event.end_time,
                instructor_name=f"{event.instructor.user.first_name} {event.instructor.user.last_name}"
            ))

    return ScanResult(
        valid=True,
        message="QR Kod Geçerli",
        member_name=f"{member.first_name} {member.last_name}",
        subscription_name=subscription.package.name,
        remaining_sessions=remaining,
        access_type=plan.access_type,
        attendance_count=subscription.attendance_count,
        eligible_events=eligible_events
    )

@router.get("/history", response_model=List[CheckInHistoryRead])
async def list_checkin_history(
    member_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(SessionCheckIn)
        .options(
            selectinload(SessionCheckIn.event).selectinload(ClassEvent.template),
            selectinload(SessionCheckIn.verified_by),
            selectinload(SessionCheckIn.subscription).selectinload(Subscription.package).selectinload(ServicePackage.plan)
        )
        .order_by(SessionCheckIn.check_in_time.desc())
    )

    if member_id:
        query = query.where(SessionCheckIn.member_user_id == member_id)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    checkins = result.scalars().all()

    response = []
    for c in checkins:
        # Handle NULL event_id (for TIME_BASED or SESSION_BASED check-ins without event)
        if c.event and c.event.template:
            event_name = c.event.template.name
            class_name = event_name
        else:
            # Check subscription access_type to determine the type
            access_type = c.subscription.package.plan.access_type if c.subscription and c.subscription.package and c.subscription.package.plan else "UNKNOWN"
            if access_type == "TIME_BASED":
                event_name = "Zaman Bazlı Katılım"
                class_name = "Zaman Bazlı Katılım"
            elif access_type == "SESSION_BASED":
                event_name = "Seans Bazlı Giriş"
                class_name = "Seans Bazlı Giriş"
            else:
                event_name = "Bilinmeyen Giriş"
                class_name = "Bilinmeyen Giriş"
        
        response.append({
            "id": c.id,
            "check_in_time": c.check_in_time,
            "event_id": c.event_id,
            "event_name": event_name,
            "class_name": class_name,
            "subscription_name": c.subscription.package.name if c.subscription and c.subscription.package else "Bilinmeyen Paket",
            "verified_by_name": f"{c.verified_by.first_name} {c.verified_by.last_name}" if c.verified_by else "Sistem"
        })
    
    return response

@router.post("/check-in", response_model=CheckInResponse)
async def check_in_member(
    checkin_in: CheckInRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Find Subscription by QR Token
    query = (
        select(SubscriptionQrCode)
        .where(SubscriptionQrCode.qr_token == checkin_in.qr_token, SubscriptionQrCode.is_active == True)
        .options(
            selectinload(SubscriptionQrCode.subscription).options(
                selectinload(Subscription.package).selectinload(ServicePackage.plan),
                selectinload(Subscription.member)
            )
        )
    )
    result = await db.execute(query)
    qr_code = result.scalar_one_or_none()

    if not qr_code:
        raise HTTPException(status_code=404, detail="Invalid or inactive QR code")
    
    subscription = qr_code.subscription
    member = subscription.member

    # 2. Validate Subscription Status and Date
    if subscription.status != SubscriptionStatus.active:
        raise HTTPException(status_code=400, detail=f"Subscription is {subscription.status.value}")
    
    now = datetime.now()
    # Naive vs Aware datetime check might be needed depending on DB setup. 
    # Assuming DB returns aware or we handle it. For now simple comparison.
    if subscription.end_date.replace(tzinfo=None) < now:
        raise HTTPException(status_code=400, detail="Subscription has expired")

    # 3. Find Event (if provided)
    event = None
    if checkin_in.event_id:
        query = (
            select(ClassEvent)
            .where(ClassEvent.id == checkin_in.event_id)
            .options(selectinload(ClassEvent.template))
        )
        result = await db.execute(query)
        event = result.scalar_one_or_none()

        if not event:
            raise HTTPException(status_code=404, detail="Class Event not found")
        
        if event.is_cancelled == True: # type: ignore
            raise HTTPException(status_code=400, detail="Class Event is cancelled")

        # 4. Validate Permissions (Does this package allow this class template?)
        perm_query = (
            select(BookingPermission)
            .where(
                BookingPermission.package_id == subscription.package_id,
                BookingPermission.template_id == event.template_id
            )
        )
        perm_result = await db.execute(perm_query)
        permission = perm_result.scalar_one_or_none()

        if not permission:
            raise HTTPException(status_code=403, detail="This subscription does not cover this class type")

        # 5. Validate Event Capacity
        count_query = select(func.count(SessionCheckIn.id)).where(SessionCheckIn.event_id == event.id)
        count_result = await db.execute(count_query)
        current_checkins = count_result.scalar()

        if current_checkins is not None and current_checkins >= event.capacity: # type: ignore
            raise HTTPException(status_code=400, detail="Class is full")

        # 7. Check if already checked in for this event
        existing_checkin_query = (
            select(SessionCheckIn)
            .where(
                SessionCheckIn.subscription_id == subscription.id,
                SessionCheckIn.event_id == event.id
            )
        )
        existing_result = await db.execute(existing_checkin_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Member already checked in to this event")

    # 6. Validate Session Limits (only for SESSION_BASED packages)
    plan = subscription.package.plan
    
    # SESSION_BASED: Kontrol et, TIME_BASED: Pas
    if plan.access_type == "SESSION_BASED":
        if plan.sessions_granted > 0:
            if subscription.used_sessions >= plan.sessions_granted:
                raise HTTPException(status_code=400, detail="No sessions remaining in this subscription")

    # 8. Perform Check-in
    check_in = SessionCheckIn(
        subscription_id=subscription.id,
        member_user_id=member.id,
        event_id=event.id if event else None,
        verified_by_user_id=current_user.id,
    )
    db.add(check_in)
    
    # Capture values before commit to avoid MissingGreenlet on expired objects
    member_first_name = member.first_name
    member_last_name = member.last_name
    sessions_granted = plan.sessions_granted
    access_type = plan.access_type
    
    # Güncelleme mantığı: access_type'a göre ayrıştır
    if access_type == "SESSION_BASED":
        # SESSION_BASED: used_sessions düş
        subscription.used_sessions += 1
        new_used_sessions = subscription.used_sessions
    else:
        # TIME_BASED: attendance_count artır, used_sessions'a dokunma
        subscription.attendance_count += 1
        new_used_sessions = subscription.attendance_count

    db.add(subscription)

    await db.commit()
    await db.refresh(check_in)

    # Remaining gösterme mantığı
    if access_type == "SESSION_BASED":
        remaining = sessions_granted - new_used_sessions if sessions_granted > 0 else 9999
    else:
        # TIME_BASED: sınırsız, sadece katılım sayısını göster (opsiyonel)
        remaining = 9999

    return CheckInResponse(
        success=True,
        message="Check-in successful",
        member_name=f"{member_first_name} {member_last_name}",
        remaining_sessions=remaining,
        check_in_time=check_in.check_in_time.strftime("%Y-%m-%d %H:%M:%S")
    )


@router.get("/subscriptions/{subscription_id}/qr-code")
async def get_subscription_qr_code(
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Abonelik için QR kodunu (token) döndür.
    Desktop UI'dan package detail'de QR OKUT butonu için kullanılır.
    """
    # 1. Find Subscription
    query = (
        select(Subscription)
        .where(Subscription.id == subscription_id)
        .options(selectinload(Subscription.qr_code))
    )
    result = await db.execute(query)
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(status_code=404, detail="Abonelik bulunamadı")

    # 2. Get or check QR Code
    if not subscription.qr_code:
        raise HTTPException(status_code=404, detail="Bu abonelik için QR kod bulunamadı")

    return {
        "subscription_id": subscription.id,
        "qr_token": subscription.qr_code.qr_token,
        "is_active": subscription.qr_code.is_active
    }


@router.post("/check-in/time-based")
async def check_in_time_based(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    TIME_BASED subscriptions için check-in endpoint.
    Event seçimi gerekmez - sadece katılım sayılır.
    """
    qr_token = body.get('qr_token')
    # 1. Find Subscription by QR Token
    qr_query = select(SubscriptionQrCode).where(SubscriptionQrCode.qr_token == qr_token)
    qr_result = await db.execute(qr_query)
    qr_code = qr_result.scalar_one_or_none()

    if not qr_code:
        raise HTTPException(status_code=404, detail="QR kod geçersiz veya süresi dolmuş")

    subscription_id = qr_code.subscription_id
    subscription_query = (
        select(Subscription)
        .where(Subscription.id == subscription_id)
        .options(
            selectinload(Subscription.member),
            selectinload(Subscription.package).selectinload(ServicePackage.plan)
        )
    )
    subscription_result = await db.execute(subscription_query)
    subscription = subscription_result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(status_code=404, detail="Abonelik bulunamadı")

    member = subscription.member
    plan = subscription.package.plan

    # 2. Validate Subscription Status and Type
    if plan.access_type != "TIME_BASED":
        raise HTTPException(status_code=400, detail="Bu endpoint sadece TIME_BASED abonelikler için")

    # 3. Create SessionCheckIn WITHOUT event (NULL event_id)
    # TIME_BASED subscriptions don't require events
    check_in = SessionCheckIn(
        subscription_id=subscription.id,
        member_user_id=member.id,
        event_id=None,  # TIME_BASED doesn't need event
        verified_by_user_id=current_user.id,
    )
    db.add(check_in)
    
    # 4. Increment attendance_count
    subscription.attendance_count += 1
    db.add(subscription)

    # Capture values before commit
    member_first_name = member.first_name
    member_last_name = member.last_name

    await db.commit()
    await db.refresh(check_in)

    return CheckInResponse(
        success=True,
        message="TIME_BASED check-in successful",
        member_name=f"{member_first_name} {member_last_name}",
        remaining_sessions=9999,
        check_in_time=check_in.check_in_time.strftime("%Y-%m-%d %H:%M:%S")
    )


@router.delete("/history/{checkin_id}", status_code=204)
async def delete_checkin(
    checkin_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a check-in record from history.
    Only staff members can delete check-in records.
    """
    # 1. Find the check-in record
    query = (
        select(SessionCheckIn)
        .where(SessionCheckIn.id == checkin_id)
        .options(
            selectinload(SessionCheckIn.subscription).options(
                selectinload(Subscription.package).selectinload(ServicePackage.plan)
            )
        )
    )
    result = await db.execute(query)
    checkin = result.scalar_one_or_none()

    if not checkin:
        raise HTTPException(status_code=404, detail="Check-in record not found")

    subscription = checkin.subscription
    plan = subscription.package.plan

    # 2. Reverse the effects of the check-in
    if plan.access_type == "SESSION_BASED":
        # Decrease used_sessions count
        if subscription.used_sessions > 0:
            subscription.used_sessions -= 1
            db.add(subscription)
    elif plan.access_type == "TIME_BASED":
        # Decrease attendance_count
        if subscription.attendance_count > 0:
            subscription.attendance_count -= 1
            db.add(subscription)

    # 3. Delete the check-in record
    await db.delete(checkin)
    await db.commit()
