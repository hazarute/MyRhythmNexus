"""
Subscriptions Routes - Abonelik Yönetimi
FastAPI + SQLAlchemy AsyncSession
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import logging

from backend.core.database import get_db
from backend.models.user import User
from backend.models.operation import Subscription
from backend.models.service import ServicePackage
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="backend/web/templates")


@router.get("/subscriptions", response_class=HTMLResponse)
async def subscriptions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Kullanıcının aboneliklerini göster"""
    try:
        result = await db.execute(
            select(Subscription).options(
                # Eager-load package and its plan to avoid lazy-loading during template rendering
                selectinload(Subscription.package).selectinload(ServicePackage.plan)
            ).where(
                Subscription.member_user_id == current_user.id
            ).order_by(Subscription.start_date.desc())
        )
        all_subscriptions = result.scalars().all()
        # Debug: log current user and subscription ids for troubleshooting
        try:
            sub_ids = [s.id for s in all_subscriptions]
        except Exception:
            sub_ids = None
        logger.info(f"[DEBUG subscriptions] user_id={current_user.id} found_subscriptions={len(all_subscriptions)} ids={sub_ids}")
        print(f"[DEBUG subscriptions] user_id={current_user.id} found_subscriptions={len(all_subscriptions)} ids={sub_ids}")
        
        # Aktif vs pasif ayır (Subscription.status bir Enum olabilir -> .value ile kıyasla)
        def status_value(s):
            try:
                return s.status.value
            except Exception:
                return s.status

        active_subscriptions = [s for s in all_subscriptions if status_value(s) in ("active", "ongoing")]
        passive_subscriptions = [s for s in all_subscriptions if status_value(s) not in ("active", "ongoing")]
        
        context = {
            "request": request,
            "page_title": "Aboneliklerim",
            "user": current_user,
            "current_user": current_user,
            "active_subscriptions": active_subscriptions,
            "passive_subscriptions": passive_subscriptions,
        }
        
        return templates.TemplateResponse("my_subscriptions.html", context)
        
    except Exception as e:
        logger.error(f"Subscriptions error: {e}")
        return templates.TemplateResponse(
            "my_subscriptions.html",
            {
                "request": request,
                "user": current_user,
                "current_user": current_user,
                "error": "Abonelikler yüklenirken hata oluştu",
                "page_title": "Aboneliklerim"
            }
        )


@router.get("/subscriptions/{subscription_id}", response_class=HTMLResponse)
async def subscription_detail(
    subscription_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Abonelik detayı ve QR kod"""
    try:
        result = await db.execute(
            select(Subscription).options(
                selectinload(Subscription.package).selectinload(ServicePackage.plan),
                selectinload(Subscription.qr_code)
            ).where(
                Subscription.id == subscription_id,
                Subscription.member_user_id == current_user.id
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return templates.TemplateResponse(
                "subscription_detail_and_qr.html",
                {
                    "request": request,
                    "user": current_user,
                    "current_user": current_user,
                    "subscription": None,
                    "error": "Abonelik bulunamadı",
                    "page_title": "Abonelik Detayı"
                }
            )
        
        # Plan ve kullanım bilgisi
        percentage = 0
        total_sessions = None
        remaining_sessions = None
        plan_access_type = "SESSION_BASED"

        if subscription.package and subscription.package.plan:
            plan = subscription.package.plan
            plan_access_type = plan.access_type or "SESSION_BASED"
            if plan_access_type == "SESSION_BASED":
                # Seans bazlı: toplam seans ve kalan hesapla
                total_sessions = plan.sessions_granted or 0
                if total_sessions > 0:
                    percentage = (subscription.used_sessions / total_sessions) * 100
                    remaining_sessions = total_sessions - subscription.used_sessions
                else:
                    total_sessions = None
                    remaining_sessions = None
            else:
                # Zaman bazlı: sınırsız erişim boyunca kalan seans yok
                total_sessions = None
                remaining_sessions = None
        
        context = {
            "request": request,
            "page_title": "Abonelik Detayı",
            "user": current_user,
            "current_user": current_user,
            "subscription": subscription,
            "used_sessions": subscription.used_sessions,
            "total_sessions": total_sessions,
            "percentage": percentage,
            "remaining_sessions": remaining_sessions,
            "plan_access_type": plan_access_type,
        }
        
        return templates.TemplateResponse("subscription_detail_and_qr.html", context)
        
    except Exception as e:
        logger.error(f"Subscription detail error: {e}")
        return templates.TemplateResponse(
            "subscription_detail_and_qr.html",
            {
                "request": request,
                "user": current_user,
                "current_user": current_user,
                "error": "Detay yüklenirken hata oluştu",
                "page_title": "Abonelik Detayı"
            }
        )
