"""
Dashboard Route - Anasayfa
FastAPI + SQLAlchemy AsyncSession
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime
import logging

from backend.core.database import get_db
from backend.models.user import User, Instructor
from backend.models.operation import Booking, Subscription, ClassEvent
from backend.models.service import ServicePackage
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="backend/web/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Member dashboard'unu göster"""
    try:
        # Kullanıcının en fazla 2 aktif subscription'ını al
        result = await db.execute(
            select(Subscription).options(
                selectinload(Subscription.package).selectinload(ServicePackage.plan)
            ).where(
                Subscription.member_user_id == current_user.id,
                Subscription.status.in_(["active", "ongoing"]),
            ).order_by(Subscription.start_date.desc()).limit(2)
        )
        subscriptions_rows = result.scalars().all()
        # Debug: log subscription metadata to help troubleshoot missing items
        try:
            sub_ids = [s.id for s in subscriptions_rows]
        except Exception:
            sub_ids = None
        logger.warning(f"[DEBUG dashboard] user_id={current_user.id} found_subscriptions={len(subscriptions_rows)} ids={sub_ids}")
        try:
            for s in subscriptions_rows:
                status_val = getattr(s.status, 'value', s.status)
                pkg_id = getattr(s, 'package_id', None)
                access_type = getattr(s, 'access_type', None)
                plan = getattr(getattr(s, 'package', None), 'plan', None)
                plan_sessions = getattr(plan, 'sessions_granted', None) if plan is not None else None
                plan_access = getattr(plan, 'access_type', None) if plan is not None else None
                logger.warning(
                    f"[DEBUG dashboard] sub_id={s.id} status={status_val} access_type={access_type} package_id={pkg_id} plan_sessions={plan_sessions} plan_access={plan_access}"
                )
        except Exception:
            logger.exception("[DEBUG dashboard] error while logging subscription details")
        subscription = subscriptions_rows[0] if subscriptions_rows else None
        
        # Sonraki class booking'ini al
        next_booking = None
        if subscription:
            booking_result = await db.execute(
                select(Booking).options(
                    selectinload(Booking.event).selectinload(ClassEvent.template),
                    selectinload(Booking.event).selectinload(ClassEvent.instructor).selectinload(Instructor.user),
                ).where(
                    Booking.subscription_id == subscription.id,
                    Booking.status == "confirmed"
                ).order_by(Booking.created_at.desc()).limit(1)
            )
            next_booking = booking_result.scalar_one_or_none()
        
        # Abonelik bilgilerini hazırlama (en fazla 2)
        subscriptions = []
        for sub in subscriptions_rows:
            used = getattr(sub, 'used_sessions', 0) or 0
            total = None
            remaining = None
            percentage = 0
            access_type = getattr(sub, 'access_type', 'SESSION_BASED') or 'SESSION_BASED'
            if sub.package and getattr(sub.package, 'plan', None) and hasattr(sub.package.plan, 'sessions_granted'):
                sess = sub.package.plan.sessions_granted or 0
                if access_type == 'SESSION_BASED' and sess > 0:
                    total = sess
                    remaining = max(sess - used, 0)
                    percentage = (used / total) * 100 if total > 0 else 0
                else:
                    total = None
                    remaining = None
            subscriptions.append({
                'id': sub.id,
                'plan_name': sub.package.name if sub.package and getattr(sub.package, 'name', None) else sub.package_id,
                'end_date': sub.end_date.strftime('%d/%m/%Y') if sub.end_date else '',
                'used_sessions': used,
                'total_sessions': total,
                'remaining_sessions': remaining,
                'percentage': percentage,
                'access_type': access_type,
            })
        
        # Map to template keys expected by dashboard.html
        next_class = None
        if next_booking and getattr(next_booking, 'event', None):
            ev = next_booking.event
            template_name = ev.template.name if getattr(ev, 'template', None) else ''
            instructor_name = ''
            if getattr(ev, 'instructor', None) and getattr(ev.instructor, 'user', None):
                u = ev.instructor.user
                instructor_name = getattr(u, 'full_name', None) or f"{getattr(u, 'first_name', '')} {getattr(u, 'last_name', '')}".strip()
            next_class = {
                'name': template_name,
                'instructor': instructor_name,
                'date': ev.start_time.strftime('%d %b %Y') if ev.start_time else '',
                'time': ev.start_time.strftime('%H:%M') if ev.start_time else '',
            }

        context = {
            "request": request,
            "page_title": "Dashboard",
            "user": current_user,
            "current_user": current_user,
            "subscription": subscription,
            "primary_subscription": subscription,
            # list for template (max 2)
            "subscriptions": subscriptions,
            "used_sessions": subscriptions[0]['used_sessions'] if subscriptions else 0,
            "total_sessions": subscriptions[0]['total_sessions'] if subscriptions and subscriptions[0]['total_sessions'] is not None else 0,
            "percentage": subscriptions[0]['percentage'] if subscriptions else 0,
            "next_booking": next_booking,
            "next_class": next_class,
        }
        
        return templates.TemplateResponse("dashboard.html", context)
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": current_user,
                "current_user": current_user,
                "error": "Dashboard yüklenirken hata oluştu",
                "page_title": "Dashboard"
            }
        )
