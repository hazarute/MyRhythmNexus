from datetime import datetime, time, timedelta, timezone
from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, and_, case, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.api import deps
from backend.models.operation import (
    ClassEvent, 
    Subscription, 
    SubscriptionStatus, 
    Payment, 
    SessionCheckIn
)
from backend.models.user import User, Role, UserRole
from backend.schemas.stats import DashboardStats, ScheduleItem, ActivityItem, DebtMember

router = APIRouter()

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get dashboard statistics including active members, today's classes, revenue, schedule and activity feed.
    """
    
    # 1. Active Members (Count active users with member role only)
    result = await db.execute(
        select(func.count(User.id)).where(
            and_(
                User.is_active == True,
                User.id.in_(
                    select(UserRole.user_id).where(
                        UserRole.role_id.in_(
                            select(Role.id).where(Role.role_name == "MEMBER")
                        )
                    )
                )
            )
        )
    )
    active_members_count = result.scalar() or 0

    # 2. Today's Classes Count
    now = datetime.now(timezone.utc)
    today_start = datetime.combine(now.date(), time.min).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(now.date(), time.max).replace(tzinfo=timezone.utc)
    
    result = await db.execute(
        select(func.count(ClassEvent.id)).where(
            and_(
                ClassEvent.start_time >= today_start,
                ClassEvent.start_time <= today_end,
                ClassEvent.is_cancelled == False
            )
        )
    )
    todays_classes_count = result.scalar() or 0

    # 3. Total Debt (Purchase price - paid amount for all subscriptions)
    # Subquery: Total paid per subscription
    paid_subquery = (
        select(
            Payment.subscription_id,
            func.sum(Payment.amount_paid).label("total_paid")
        )
        .group_by(Payment.subscription_id)
        .subquery()
    )
    
    # Main query: Subscriptions with debt calculation
    debt_query = (
        select(
            Subscription.id,
            Subscription.member_user_id,
            Subscription.purchase_price,
            func.coalesce(paid_subquery.c.total_paid, 0).label("paid")
        )
        .outerjoin(paid_subquery, Subscription.id == paid_subquery.c.subscription_id)
        .where(Subscription.status.in_([SubscriptionStatus.active, SubscriptionStatus.pending, SubscriptionStatus.expired]))
    )
    
    debt_result = await db.execute(debt_query)
    total_debt = 0.0
    debt_members: set[str] = set()
    for row in debt_result:
        debt = float(row.purchase_price) - float(row.paid)
        if debt > 0:
            total_debt += debt
            member_id = getattr(row, "member_user_id", None)
            if member_id:
                debt_members.add(member_id)
    
    pending_payments_amount = total_debt

    # 4. Monthly Revenue
    first_day_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    result = await db.execute(
        select(func.sum(Payment.amount_paid)).where(
            Payment.payment_date >= first_day_of_month
        )
    )
    monthly_revenue = result.scalar() or 0.0

    # 5. Today's Schedule (Detailed)
    schedule_query = select(ClassEvent).options(
        selectinload(ClassEvent.template),
        selectinload(ClassEvent.bookings)
    ).where(
        and_(
            ClassEvent.start_time >= today_start,
            ClassEvent.start_time <= today_end,
            ClassEvent.is_cancelled == False
        )
    ).order_by(ClassEvent.start_time)
    
    schedule_result = await db.execute(schedule_query)
    todays_events = schedule_result.scalars().all()
    
    todays_schedule_list = []
    for event in todays_events:
        participant_count = len(event.bookings)
        occupancy_str = f"{participant_count}/{event.capacity}"
        if participant_count >= event.capacity:
            occupancy_str = "Dolu"
            
        todays_schedule_list.append(ScheduleItem(
            id=str(event.id),
            title=event.template.name,
            start_time=event.start_time,
            end_time=event.end_time,
            occupancy=occupancy_str,
            status="active"
        ))

    # 6. Activity Feed (Check-ins)
    activities = []

    # Check-ins
    checkins_result = await db.execute(
        select(SessionCheckIn).options(
            selectinload(SessionCheckIn.member), 
            selectinload(SessionCheckIn.event).selectinload(ClassEvent.template),
            selectinload(SessionCheckIn.subscription).selectinload(Subscription.package)
        ).order_by(SessionCheckIn.check_in_time.desc()).limit(20)
    )
    for ci in checkins_result.scalars():
        if ci.member:
            # Add subscription info if available
            subscription_info = ""
            if ci.subscription and ci.subscription.package:
                if ci.subscription.access_type == "TIME_BASED":
                    subscription_info = f"{ci.subscription.package.name} (sınırsız)"
                else:
                    remaining_sessions = ci.subscription.used_sessions - ci.subscription.attendance_count
                    subscription_info = f"{ci.subscription.package.name} - {remaining_sessions} seansa katıldı."
            else:
                subscription_info = "Abonelik bilgisi bulunamadı"
            
            # Add event info if available
            event_info = ""
            if ci.event and ci.event.template:
                event_info = f" ({ci.event.template.name} dersi)"
            
            description = subscription_info + event_info
            
            activities.append(ActivityItem(
                id=f"checkin_{ci.id}",
                type="checkin",
                description=description,
                timestamp=ci.check_in_time,
                user_name=f"{ci.member.first_name} {ci.member.last_name}"
            ))

    # Sort by timestamp desc and take top 10
    activities.sort(key=lambda x: x.timestamp, reverse=True)
    recent_activities = activities[:20]

    return DashboardStats(
        active_members=active_members_count,
        todays_classes=todays_classes_count,
        pending_payments_amount=float(pending_payments_amount),
        debt_members_count=len(debt_members),
        monthly_revenue=float(monthly_revenue),
        todays_schedule=todays_schedule_list,
        recent_activities=recent_activities
    )


@router.get("/debt-members", response_model=List[DebtMember])
async def get_debt_members(db: AsyncSession = Depends(deps.get_db)) -> Any:
    paid_subquery = (
        select(
            Payment.subscription_id,
            func.sum(Payment.amount_paid).label("total_paid")
        )
        .group_by(Payment.subscription_id)
        .subquery()
    )

    debt_subquery = (
        select(
            Subscription.member_user_id.label("member_id"),
            (
                func.coalesce(Subscription.purchase_price, 0)
                - func.coalesce(paid_subquery.c.total_paid, 0)
            ).label("debt")
        )
        .outerjoin(paid_subquery, Subscription.id == paid_subquery.c.subscription_id)
        .where(Subscription.status.in_([SubscriptionStatus.active, SubscriptionStatus.pending, SubscriptionStatus.expired]))
        .subquery()
    )

    debt_amount_expr = func.sum(
        case((debt_subquery.c.debt > 0, debt_subquery.c.debt), else_=0)
    ).label("debt_amount")

    debt_members_query = (
        select(
            User.id.label("id"),
            User.first_name,
            User.last_name,
            debt_amount_expr,
        )
        .join(User, User.id == debt_subquery.c.member_id)
        .group_by(User.id, User.first_name, User.last_name)
        .having(debt_amount_expr > 0)
        .order_by(debt_amount_expr.desc())
    )

    result = await db.execute(debt_members_query)
    return [
        DebtMember(
            id=str(row.id),
            first_name=row.first_name,
            last_name=row.last_name,
            debt_amount=float(row.debt_amount or 0),
        )
        for row in result.fetchall()
    ]
