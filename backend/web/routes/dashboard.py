from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import logging

logger = logging.getLogger(__name__)

from backend.core.database import get_db
from backend.models.user import User
from backend.models.operation import Subscription, SubscriptionQrCode, SubscriptionStatus
from backend.models.service import ServicePackage, ServiceOffering, PlanDefinition
from .auth import get_current_user_from_cookie

router = APIRouter()
templates = Jinja2Templates(directory="backend/web/templates")

@router.get("/", response_class=HTMLResponse)
async def web_index(
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user_from_cookie(request, db)
    
    if not user:
        return templates.TemplateResponse("login.html", {"request": request})
    
    # Find all subscriptions for this member and split active/expired in code
    query = (
        select(Subscription)
        .where(
            Subscription.member_user_id == user.id
        )
        .options(
            selectinload(Subscription.package).selectinload(ServicePackage.offering),
            selectinload(Subscription.package).selectinload(ServicePackage.plan),
            selectinload(Subscription.qr_code)
        )
        .order_by(Subscription.end_date.desc())
    )
    result = await db.execute(query)
    subscriptions = result.scalars().all()

    # Split into active and expired lists so template can show past subscriptions separately
    active_subs = [s for s in subscriptions if getattr(s, "status", None) == SubscriptionStatus.active]
    expired_subs = [s for s in subscriptions if getattr(s, "status", None) == SubscriptionStatus.expired]

    if len(active_subs) == 1 and not expired_subs:
        # If only one active card and no expired ones, redirect to detail
        return RedirectResponse(url=f"/web/cards/{active_subs[0].id}", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(
        "my_cards.html", 
        {"request": request, "user": user, "subscriptions_active": active_subs, "subscriptions_expired": expired_subs}
    )

@router.get("/cards/{subscription_id}", response_class=HTMLResponse)
async def card_detail(
    request: Request,
    subscription_id: str,
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/web", status_code=status.HTTP_302_FOUND)

    query = (
        select(Subscription)
        .where(
            Subscription.id == subscription_id,
            Subscription.member_user_id == user.id
        )
        .options(
            selectinload(Subscription.package).selectinload(ServicePackage.offering),
            selectinload(Subscription.package).selectinload(ServicePackage.plan),
            selectinload(Subscription.qr_code)
        )
    )
    result = await db.execute(query)
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        return RedirectResponse(url="/web", status_code=status.HTTP_302_FOUND)
        
    qr_token = subscription.qr_code.qr_token if subscription.qr_code else None

    return templates.TemplateResponse(
        "card_detail.html", 
        {"request": request, "user": user, "subscription": subscription, "qr_token": qr_token}
    )