from datetime import timedelta, datetime, timezone
import zoneinfo
from typing import List, Optional, cast
import secrets
import string
import math
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.api.deps import get_db, get_current_user
from backend.models.user import User, Instructor
from backend.models.service import ServicePackage, PlanDefinition, ServiceOffering
from backend.models.operation import (
    Subscription,
    Payment,
    SubscriptionStatus,
    SubscriptionQrCode,
    Booking,
    SessionCheckIn,
    ClassTemplate,
    ClassEvent,
    BookingPermission,
)
from backend.schemas.sales import (
    SubscriptionCreate,
    SubscriptionCreateWithEvents,
    SubscriptionRead,
    PaymentCreate,
    PaymentRead,
    PaymentPagination,
)
from backend.core.date_utils import calculate_end_date
from backend.core.time_utils import get_turkey_time, convert_to_turkey_time

router = APIRouter()

@router.post("/subscriptions", response_model=SubscriptionRead)
async def create_subscription(
    sub_in: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Get Package and Plan
    package = await db.get(ServicePackage, sub_in.package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Service Package not found")
    
    # Ensure package is loaded with plan
    # If not loaded, we might need to query it or rely on lazy loading (but async requires explicit load usually)
    # Let's query plan separately to be safe if not eager loaded, or use options on package query if we did that.
    # Since we used get(), we might not have relationships.
    plan = await db.get(PlanDefinition, package.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan Definition not found")

    # 2. Normalize start_date to Turkey timezone and calculate End Date
    start_date = convert_to_turkey_time(sub_in.start_date)
    repeat_weeks = cast(int, plan.repeat_weeks) or 1
    end_date = calculate_end_date(start_date, str(plan.cycle_period), repeat_weeks)

    # 2.1 Normalize status based on dates: prevent creating an "active" subscription
    # for periods that are already expired or otherwise outside current time window.
    now = get_turkey_time()
    # If end_date is before now -> expired
    if end_date < now:
        enforced_status = SubscriptionStatus.expired
    else:
        # start_date <= now <= end_date -> active
        enforced_status = SubscriptionStatus.active

    # 3. Create Subscription
    # Determine purchase price: use override if provided, otherwise package price
    purchase_price = sub_in.purchase_price_override if sub_in.purchase_price_override is not None else package.price
    
    # Validate purchase_price_override if provided
    if sub_in.purchase_price_override is not None:
        if sub_in.purchase_price_override <= 0:
            raise HTTPException(status_code=400, detail="Purchase price must be greater than 0")
        package_price = float(package.price)
        if float(sub_in.purchase_price_override) > package_price * 2:
            raise HTTPException(status_code=400, detail="Purchase price cannot be more than double the package price")
    
    # Use enforced status regardless of client-supplied status to keep business rules consistent
    subscription = Subscription(
        member_user_id=sub_in.member_user_id,
        package_id=sub_in.package_id,
        purchase_price=purchase_price,
        start_date=start_date,
        end_date=end_date,
        status=enforced_status,
        access_type=plan.access_type or "SESSION_BASED",
        used_sessions=0,
    )
    db.add(subscription)
    await db.flush() # Flush to get ID

    # 4. Handle Initial Payment
    if sub_in.initial_payment:
        payment = Payment(
            subscription_id=subscription.id,
            recorded_by_user_id=current_user.id,
            amount_paid=sub_in.initial_payment.amount_paid,
            payment_method=sub_in.initial_payment.payment_method,
            refund_amount=sub_in.initial_payment.refund_amount,
            refund_reason=sub_in.initial_payment.refund_reason,
        )
        db.add(payment)
    
    # 5. Generate QR Code
    qr_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    qr_code = SubscriptionQrCode(
        subscription_id=subscription.id,
        qr_token=qr_token,
        is_active=True
    )
    db.add(qr_code)

    # 6. Update User updated_at timestamp
    member_user = await db.get(User, sub_in.member_user_id)
    if member_user:
        member_user.updated_at = get_turkey_time()
        db.add(member_user)

    try:
        await db.commit()
        await db.refresh(subscription)
    except DBAPIError as e:
        await db.rollback()
        # Extract the original error message if possible
        error_str = str(e.orig) if hasattr(e, 'orig') and e.orig else str(e)
        if "numeric field overflow" in error_str:
             raise HTTPException(status_code=400, detail="Ödeme tutarı çok yüksek. Lütfen daha küçük bir tutar giriniz.")
        raise HTTPException(status_code=400, detail=f"Veritabanı hatası: {error_str}")
    except Exception as e:
        await db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Beklenmeyen hata: {str(e)}")
    
    # Re-fetch with payments
    query = (
        select(Subscription)
        .where(Subscription.id == subscription.id)
        .options(
            selectinload(Subscription.payments),
            selectinload(Subscription.class_events).selectinload(ClassEvent.template),
            selectinload(Subscription.package).selectinload(ServicePackage.category),
            selectinload(Subscription.package).selectinload(ServicePackage.offering),
            selectinload(Subscription.package).selectinload(ServicePackage.plan)
        )
    )
    result = await db.execute(query)
    return result.scalar_one()

@router.get("/subscriptions", response_model=List[SubscriptionRead])
async def list_subscriptions(
    skip: int = 0, 
    limit: int = 100, 
    member_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Subscription).options(
        selectinload(Subscription.payments),
        selectinload(Subscription.class_events).selectinload(ClassEvent.template),
        selectinload(Subscription.package).selectinload(ServicePackage.category),
        selectinload(Subscription.package).selectinload(ServicePackage.offering),
        selectinload(Subscription.package).selectinload(ServicePackage.plan)
    )
    
    if member_id:
        query = query.where(Subscription.member_user_id == member_id)
        
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    subscriptions = result.scalars().all()

    # Filter out payments with zero amount from returned subscriptions
    for s in subscriptions:
        try:
            s.payments = [p for p in (s.payments or []) if p.amount_paid is not None and float(p.amount_paid) != 0.0]
        except Exception:
            # If conversion fails, keep original payments to avoid data loss
            pass

    return subscriptions

@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionRead)
async def get_subscription(
    subscription_id: str,
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Subscription)
        .where(Subscription.id == subscription_id)
        .options(
            selectinload(Subscription.payments),
            selectinload(Subscription.class_events).selectinload(ClassEvent.template),
            selectinload(Subscription.package).selectinload(ServicePackage.category),
            selectinload(Subscription.package).selectinload(ServicePackage.offering),
            selectinload(Subscription.package).selectinload(ServicePackage.plan)
        )
    )
    result = await db.execute(query)
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    try:
        subscription.payments = [p for p in (subscription.payments or []) if p.amount_paid is not None and float(p.amount_paid) != 0.0]
    except Exception:
        pass
    return subscription

@router.post("/payments", response_model=PaymentRead)
async def create_payment(
    payment_in: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subscription = await db.get(Subscription, payment_in.subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    payment = Payment(
        subscription_id=payment_in.subscription_id,
        recorded_by_user_id=current_user.id,
        amount_paid=payment_in.amount_paid,
        payment_method=payment_in.payment_method,
        refund_amount=payment_in.refund_amount,
        refund_reason=payment_in.refund_reason,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment

@router.get("/payments", response_model=PaymentPagination)
async def list_payments(
    page: int = 1,
    size: int = 10,
    member_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    skip = (page - 1) * size
    
    # Base query joining necessary tables for filtering and display
    query = (
        select(Payment)
        .join(Subscription)
        .join(User, Subscription.member_user_id == User.id)
        .join(ServicePackage, Subscription.package_id == ServicePackage.id)
    )
    
    if member_id:
        query = query.where(Subscription.member_user_id == member_id)
        
    # Count total
    # We use a subquery to count correctly with joins
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Fetch items with eager loading
    query = query.options(
        selectinload(Payment.subscription).selectinload(Subscription.member),
        selectinload(Payment.subscription).selectinload(Subscription.package)
    ).order_by(Payment.payment_date.desc()).offset(skip).limit(size)
    
    result = await db.execute(query)
    payments = result.scalars().all()
    
    # Map to schema with extra fields
    payment_reads = []
    for p in payments:
        # Create Pydantic model from ORM
        p_read = PaymentRead.model_validate(p)
        
        # Manually populate extra fields
        if p.subscription and p.subscription.member:
            p_read.member_name = f"{p.subscription.member.first_name} {p.subscription.member.last_name}"
        if p.subscription and p.subscription.package:
            p_read.package_name = p.subscription.package.name
            
        payment_reads.append(p_read)
        
    total_pages = math.ceil((total or 0) / size) if size > 0 else 0
    
    return PaymentPagination(
        total=total or 0,
        page=page,
        size=size,
        pages=total_pages,
        items=payment_reads
    )

@router.delete("/subscriptions/{subscription_id}", status_code=204)
async def delete_subscription(
    subscription_id: str,
    db: AsyncSession = Depends(get_db)
):
    subscription = await db.get(Subscription, subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # IMPORTANT: Delete in correct order to avoid FK constraint violations
    # 1. Delete SessionCheckIn (references Booking and ClassEvent)
    await db.execute(delete(SessionCheckIn).where(SessionCheckIn.subscription_id == subscription_id))
    
    # 2. Delete Booking (references ClassEvent and Subscription)
    await db.execute(delete(Booking).where(Booking.subscription_id == subscription_id))
    
    # 3. Delete ClassEvent (now safe after Bookings are removed)
    await db.execute(delete(ClassEvent).where(ClassEvent.subscription_id == subscription_id))
    
    # 4. Delete Payment (references Subscription)
    await db.execute(delete(Payment).where(Payment.subscription_id == subscription_id))
    
    # 5. Delete SubscriptionQrCode (references Subscription)
    await db.execute(delete(SubscriptionQrCode).where(SubscriptionQrCode.subscription_id == subscription_id))
    
    # 6. Finally delete the Subscription itself
    await db.delete(subscription)
    await db.commit()

@router.delete("/payments/{payment_id}", status_code=204)
async def delete_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db)
):
    payment = await db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    await db.delete(payment)
    await db.commit()


@router.post("/subscriptions-with-events", response_model=SubscriptionRead)
async def create_subscription_with_events(
    sub_in: SubscriptionCreateWithEvents,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a subscription with optional automatic ClassEvent(s) for SESSION_BASED plans.
    
    If class_events is provided with days_and_times:
    - Creates ClassEvent(s) repeating weekly for the specified number of weeks
    - For each selected day of week and time, creates repeat_weeks ClassEvent(s)
    Total ClassEvents = len(days_and_times) × repeat_weeks
    
    Example:
    days_and_times: [{day: "monday", time: "14:00"}, {day: "wednesday", time: "14:00"}]
    repeat_weeks: 4
    → 8 ClassEvent(s) total (2 days × 4 weeks)
    """
    
    # 1. Get Package and Plan
    package = await db.get(ServicePackage, sub_in.package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Service Package not found")
    
    plan = await db.get(PlanDefinition, package.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan Definition not found")

    # 2. Normalize start_date to Turkey timezone and calculate End Date
    start_date = convert_to_turkey_time(sub_in.start_date)
    repeat_weeks = cast(int, plan.repeat_weeks) or 1
    end_date = calculate_end_date(start_date, str(plan.cycle_period), repeat_weeks)

    # 3. Create Subscription
    # Determine purchase price: use override if provided, otherwise package price
    purchase_price = sub_in.purchase_price_override if sub_in.purchase_price_override is not None else package.price
    
    # Validate purchase_price_override if provided
    if sub_in.purchase_price_override is not None:
        if sub_in.purchase_price_override <= 0:
            raise HTTPException(status_code=400, detail="Purchase price must be greater than 0")
        package_price = float(package.price)
        if float(sub_in.purchase_price_override) > package_price * 2:
            raise HTTPException(status_code=400, detail="Purchase price cannot be more than double the package price")
    
    # Determine effective status for new subscription (override client value when necessary)
    now = get_turkey_time()
    if end_date < now:
        enforced_status = SubscriptionStatus.expired
    else:
        enforced_status = SubscriptionStatus.active

    subscription = Subscription(
        member_user_id=sub_in.member_user_id,
        package_id=sub_in.package_id,
        purchase_price=purchase_price,
        start_date=start_date,
        end_date=end_date,
        status=enforced_status,
        access_type=plan.access_type or "SESSION_BASED",
        used_sessions=0,
    )
    db.add(subscription)
    await db.flush()  # Flush to get ID

    # 4. Handle Initial Payment
    if sub_in.initial_payment:
        payment = Payment(
            subscription_id=subscription.id,
            recorded_by_user_id=current_user.id,
            amount_paid=sub_in.initial_payment.amount_paid,
            payment_method=sub_in.initial_payment.payment_method,
            refund_amount=sub_in.initial_payment.refund_amount,
            refund_reason=sub_in.initial_payment.refund_reason,
        )
        db.add(payment)
    
    # 5. Generate QR Code
    qr_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    qr_code = SubscriptionQrCode(
        subscription_id=subscription.id,
        qr_token=qr_token,
        is_active=True
    )
    db.add(qr_code)

    # 6. Update User updated_at timestamp
    member_user = await db.get(User, sub_in.member_user_id)
    if member_user:
        member_user.updated_at = get_turkey_time()
        db.add(member_user)

    # 7. Create ClassEvent(s) if requested
    if sub_in.class_events:
        # Validate Instructor - instructor_user_id is a User ID with INSTRUCTOR role
        instructor_user_id = sub_in.class_events.instructor_user_id
        
        # Check if user exists with eager loading of roles
        result = await db.execute(
            select(User)
            .where(User.id == instructor_user_id)
            .options(selectinload(User.roles))
        )
        instructor_user = result.scalar_one_or_none()
        if not instructor_user:
            await db.rollback()
            raise HTTPException(status_code=404, detail="Instructor not found")
        
        # Verify user has INSTRUCTOR role
        has_instructor_role = any(role.role_name == "INSTRUCTOR" for role in instructor_user.roles)
        if not has_instructor_role:
            await db.rollback()
            raise HTTPException(status_code=400, detail="User does not have INSTRUCTOR role")
        
        # Create Instructor record if it doesn't exist
        instructor_record = await db.get(Instructor, instructor_user_id)
        if not instructor_record:
            instructor_record = Instructor(user_id=instructor_user_id)
            db.add(instructor_record)
            await db.flush()
        
        # Get ServiceOffering name from package
        offering = await db.get(ServiceOffering, package.offering_id)
        if not offering:
            await db.rollback()
            raise HTTPException(status_code=404, detail="Service Offering not found")
        
        # Get or create ClassTemplate with ServiceOffering name
        template_result = await db.execute(
            select(ClassTemplate).where(ClassTemplate.name == offering.name)
        )
        template = template_result.scalar_one_or_none()
        if not template:
            # Create ClassTemplate with offering name if it doesn't exist
            template = ClassTemplate(name=offering.name)
            db.add(template)
            await db.flush()
        
        # Create BookingPermission for this package + template combination
        # First check if permission already exists
        permission_result = await db.execute(
            select(BookingPermission).where(
                (BookingPermission.package_id == sub_in.package_id) &
                (BookingPermission.template_id == template.id)
            )
        )
        existing_permission = permission_result.scalar_one_or_none()
        if not existing_permission:
            booking_permission = BookingPermission(
                package_id=sub_in.package_id,
                template_id=template.id
            )
            db.add(booking_permission)
        
        # Map day names to weekday numbers (0=Monday, 6=Sunday)
        day_name_to_weekday = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6
        }
        
        start_datetime = start_date
        
        # Create ClassEvent(s) for each day_and_time pair and each week
        for day_time in sub_in.class_events.days_and_times:
            day_key = day_time.day.lower()
            target_weekday = day_name_to_weekday.get(day_key)
            
            if target_weekday is None:
                await db.rollback()
                raise HTTPException(status_code=400, detail=f"Invalid day: {day_time.day}")
            
            # Parse time
            try:
                time_hour, time_min = map(int, day_time.time.split(":"))
            except (ValueError, AttributeError):
                await db.rollback()
                raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")
            
            # Current start date's weekday
            current_weekday = start_datetime.weekday()
            
            # Calculate how many days to add to reach target_weekday
            days_offset = (target_weekday - current_weekday) % 7
            first_occurrence = start_datetime + timedelta(days=days_offset)
            
            # Create ClassEvent(s) for each week
            for week in range(sub_in.class_events.repeat_weeks):
                # Calculate event date
                event_date = first_occurrence + timedelta(weeks=week)
                
                # Set start_time (1 hour duration by default)
                event_start = event_date.replace(hour=time_hour, minute=time_min, second=0, microsecond=0)
                event_end = event_start + timedelta(hours=1)
                
                # Create ClassEvent
                class_event = ClassEvent(
                    subscription_id=subscription.id,
                    template_id=template.id,
                    instructor_user_id=sub_in.class_events.instructor_user_id,
                    start_time=event_start,
                    end_time=event_end,
                    capacity=sub_in.class_events.capacity,
                    is_cancelled=False,
                )
                db.add(class_event)
                await db.flush()  # Flush to get ID
                
                # Auto-create Booking if BookingPermission allows
                permission = await db.execute(
                    select(BookingPermission).where(
                        (BookingPermission.package_id == sub_in.package_id) &
                        (BookingPermission.template_id == template.id)
                    )
                )
                if permission.scalar_one_or_none():
                    booking = Booking(
                        member_user_id=sub_in.member_user_id,
                        event_id=class_event.id,
                        subscription_id=subscription.id,
                        status="confirmed",
                    )
                    db.add(booking)

    try:
        await db.commit()
        await db.refresh(subscription)
    except DBAPIError as e:
        await db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') and e.orig else str(e)
        if "numeric field overflow" in error_str:
            raise HTTPException(status_code=400, detail="Ödeme tutarı çok yüksek. Lütfen daha küçük bir tutar giriniz.")
        raise HTTPException(status_code=400, detail=f"Veritabanı hatası: {error_str}")
    except Exception as e:
        await db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Beklenmeyen hata: {str(e)}")
    
    # Re-fetch with relationships
    query = (
        select(Subscription)
        .where(Subscription.id == subscription.id)
        .options(
            selectinload(Subscription.payments),
            selectinload(Subscription.class_events).selectinload(ClassEvent.template),
            selectinload(Subscription.package).selectinload(ServicePackage.category),
            selectinload(Subscription.package).selectinload(ServicePackage.offering),
            selectinload(Subscription.package).selectinload(ServicePackage.plan)
        )
    )
    result = await db.execute(query)
    return result.scalar_one()
