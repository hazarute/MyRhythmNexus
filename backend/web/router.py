from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from jose import jwt, JWTError
import re
import logging

logger = logging.getLogger(__name__)

from backend.core.config import settings
from backend.core.database import get_db
from backend.core.security import verify_password, create_access_token
from backend.models.user import User
from backend.models.operation import Subscription, SubscriptionQrCode, SubscriptionStatus

from backend.models.service import ServicePackage, ServiceOffering, PlanDefinition

router = APIRouter(prefix="/web", tags=["web"])
templates = Jinja2Templates(directory="backend/web/templates")

async def get_current_user_from_cookie(request: Request, db: AsyncSession) -> Optional[User]:
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    # Remove "Bearer " prefix if present (though cookies usually just have the token)
    if token.startswith("Bearer "):
        token = token.split(" ")[1]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    
    user = await db.get(User, user_id)
    return user

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

@router.post("/login", response_class=HTMLResponse)
async def web_login(
    request: Request,
    phone_number: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # Normalize phone number for tolerant lookup
    clean = re.sub(r'\D', '', phone_number or '')
    if len(clean) == 10:
        phone_lookup = f"{clean[:3]}-{clean[3:6]}-{clean[6:]}"
    else:
        phone_lookup = clean

    logger.info("Web login attempt: raw=%s lookup=%s", phone_number, phone_lookup)

    # Try exact match with normalized form first
    result = await db.execute(select(User).where(User.phone_number == phone_lookup))
    user = result.scalar_one_or_none()

    # Fallbacks: try digits-only, then a suffix/contains match
    if not user and clean:
        result = await db.execute(select(User).where(User.phone_number == clean))
        user = result.scalar_one_or_none()

    if not user and clean:
        # try contains (e.g. stored as +90555... or with country code)
        try:
            result = await db.execute(select(User).where(User.phone_number.ilike(f"%{clean}")))
            user = result.scalar_one_or_none()
        except Exception:
            # If dialect doesn't support ilike for this column type, ignore
            pass

    if not user or not verify_password(password, str(user.password_hash)):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials"}
        )
    
    # Create token (use centralized setting so web and API behave consistently)
    access_token_expires = timedelta(minutes=getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7))
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )

    response = RedirectResponse(url="/web", status_code=status.HTTP_302_FOUND)
    # Use the same lifetime for the cookie (in seconds) as the token expiry
    response.set_cookie(
        key="access_token",
        value=f"{access_token}",
        httponly=True,
        max_age=int(access_token_expires.total_seconds())
    )
    return response

@router.get("/logout")
async def web_logout():
    response = RedirectResponse(url="/web", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response
