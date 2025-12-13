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

router = APIRouter(prefix="/auth", tags=["auth"])
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
    phone_number: Optional[str] = Form(None),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Handle user registration from web form"""
    # Capture form values for re-rendering on error
    form_values = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone_number": phone_number,
    }

    # Validate passwords match
    if password != password_confirm:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Şifreler eşleşmiyor", "form": form_values, "errors": {"password_confirm": "Şifreler eşleşmiyor"}}
        )

    # Validate password length
    if len(password) < 8:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Şifre en az 8 karakter olmalıdır", "form": form_values, "errors": {"password": "Şifre en az 8 karakter olmalıdır"}}
        )

    # Check if user already exists by email (case-insensitive)
    query = select(User).where(User.email == email.lower())
    result = await db.execute(query)
    if result.scalar_one_or_none():
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Bu e-posta adresi zaten kayıtlı", "form": form_values, "errors": {"email": "Bu e-posta adresi zaten kayıtlı"}}
        )

    # Fallback: accept `phone` field if `phone_number` missing (defensive)
    if not phone_number:
        form_data = await request.form()
        phone_number = form_data.get("phone") or form_data.get("phone_number")

    # Normalize phone number
    clean_phone = re.sub(r'\D', '', phone_number or '')
    # Accept common Turkish forms: 10 digits (5xx...), optional leading 0 or country code 90
    if not clean_phone:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Telefon numarası geçersiz", "form": form_values, "errors": {"phone_number": "Telefon numarası gerekli"}}
        )

    # Reject obviously wrong numbers (too short or absurdly long)
    if len(clean_phone) < 10 or len(clean_phone) > 12:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Telefon numarası geçersiz", "form": form_values, "errors": {"phone_number": "Geçerli bir telefon numarası girin (ör. 5551234567 veya +905551234567)"}}
        )

    # Use last 10 digits as the national number for normalization
    national = clean_phone[-10:]
    normalized_phone = f"{national[:3]}-{national[3:6]}-{national[6:]}"

    # Check if phone number already exists
    phone_query = select(User).where(User.phone_number == normalized_phone)
    phone_result = await db.execute(phone_query)
    if phone_result.scalar_one_or_none():
        form_values["phone_number"] = normalized_phone
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Bu telefon numarası zaten kayıtlı", "form": form_values, "errors": {"phone_number": "Bu telefon numarası zaten kayıtlı"}}
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
            {"request": request, "error": "Kayıt sırasında bir hata oluştu. Lütfen tekrar deneyin.", "form": form_values}
        )
