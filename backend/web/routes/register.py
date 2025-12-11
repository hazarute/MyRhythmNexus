from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import jwt, JWTError
import re
import logging

logger = logging.getLogger(__name__)

from backend.core.config import settings
from backend.core.database import get_db
from backend.core.security import hash_password
from backend.models.user import User, Role

router = APIRouter()
templates = Jinja2Templates(directory="backend/web/templates")

@router.get("/register", response_class=HTMLResponse)
async def web_register_page(request: Request):
    """Show the registration page"""
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register", response_class=HTMLResponse)
async def web_register(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Handle user registration from web form"""
    # Validate passwords match
    if password != password_confirm:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Şifreler eşleşmiyor"}
        )

    # Validate password length
    if len(password) < 8:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Şifre en az 8 karakter olmalıdır"}
        )

    # Check if user already exists by email
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Bu e-posta adresi zaten kayıtlı"}
        )

    # Normalize phone number
    clean_phone = re.sub(r'\D', '', phone_number or '')
    if len(clean_phone) == 10:
        normalized_phone = f"{clean_phone[:3]}-{clean_phone[3:6]}-{clean_phone[6:]}"
    else:
        normalized_phone = phone_number

    # Check if phone number already exists
    phone_query = select(User).where(User.phone_number == normalized_phone)
    phone_result = await db.execute(phone_query)
    if phone_result.scalar_one_or_none():
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Bu telefon numarası zaten kayıtlı"}
        )

    try:
        # Create new user (inactive - pending admin approval)
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=normalized_phone,
            password_hash=hash_password(password),
            is_active=False,  # Pending approval
        )

        # Assign MEMBER role
        role_query = select(Role).where(Role.role_name == "MEMBER")
        role_result = await db.execute(role_query)
        member_role = role_result.scalar_one_or_none()

        if not member_role:
            # Create role if not exists
            member_role = Role(role_name="MEMBER")
            db.add(member_role)
            await db.flush()

        user.roles.append(member_role)

        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"New user registered (pending approval): {email}")

        # Redirect to login with success message
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "success": "Kayıt başvurunuz alındı. Admin onayından sonra giriş yapabilirsiniz."}
        )

    except Exception as e:
        logger.error(f"Registration error: {e}")
        await db.rollback()
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Kayıt sırasında bir hata oluştu. Lütfen tekrar deneyin."}
        )