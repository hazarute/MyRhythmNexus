from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from jose import jwt, JWTError

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
    
    # Find active subscriptions
    query = (
        select(Subscription)
        .where(
            Subscription.member_user_id == user.id,
            Subscription.status == SubscriptionStatus.active
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
    
    if len(subscriptions) == 1:
        # If only one card, redirect to detail
        return RedirectResponse(url=f"/web/cards/{subscriptions[0].id}", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "my_cards.html", 
        {"request": request, "user": user, "subscriptions": subscriptions}
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
    # Authenticate
    result = await db.execute(select(User).where(User.phone_number == phone_number))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(password, str(user.password_hash)):
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Invalid credentials"}
        )
    
    # Create token
    access_token_expires = timedelta(minutes=60 * 24 * 7) # 1 week for web
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/web", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token", 
        value=f"{access_token}", 
        httponly=True,
        max_age=60 * 60 * 24 * 7
    )
    return response

@router.get("/logout")
async def web_logout():
    response = RedirectResponse(url="/web", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response
