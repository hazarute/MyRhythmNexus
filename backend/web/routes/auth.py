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
from backend.core.security import verify_password, create_access_token
from backend.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="backend/web/templates")

@router.get("/login", response_class=HTMLResponse)
async def web_login_page(request: Request):
    """Show the login page"""
    return templates.TemplateResponse("login.html", {"request": request})

async def get_current_user_from_cookie(request: Request, db: AsyncSession) -> Optional[User]:
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    # Remove "Bearer " prefix if present (though cookies usually just have the token)
    if token.startswith("Bearer "):
        token = token.split(" ")[1]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    
    user = await db.get(User, user_id)
    return user

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

    logger.info("Web login attempt: raw=%s clean=%s lookup=%s", phone_number, clean, phone_lookup)

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
    
    logger.info(f"DEBUG: Login successful for user: {user.email}")
    # Create token (use centralized setting so web and API behave consistently)
    access_token_expires = timedelta(minutes=getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7))
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )

    # For HTMX requests, return HTML with HX-Redirect header
    if request.headers.get("HX-Request"):
        response = HTMLResponse(content="", status_code=status.HTTP_200_OK)
        response.headers["HX-Redirect"] = "/web"
        response.set_cookie(
            key="access_token",
            value=f"{access_token}",
            httponly=True,
            max_age=int(access_token_expires.total_seconds())
        )
        return response
    else:
        # For regular requests, use redirect
        response = RedirectResponse(url="/web", status_code=status.HTTP_302_FOUND)
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