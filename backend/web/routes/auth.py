"""
Kimlik Doğrulama Route'ları - Login, Register, Logout
FastAPI + SQLAlchemy AsyncSession
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
import logging

from backend.core.database import get_db
from backend.models.user import User
from backend.core.security import (
    verify_password,
    hash_password,
    create_access_token,
)
from backend.core.config import settings
from jose import jwt, JWTError

logger = logging.getLogger(__name__)

# Router tanımla
router = APIRouter(prefix="/auth", tags=["auth"])

# Template engine
templates = Jinja2Templates(directory="backend/web/templates")

ALGORITHM = "HS256"

def decode_token(token: str):
    """JWT token'ı decode et"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return {}


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    JWT token'dan user döndür (optional).
    Token yoksa veya invalid ise None döndür.
    """
    token = request.cookies.get("access_token")
    
    if not token:
        return None
    
    try:
        payload = decode_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user
    except Exception as e:
        logger.debug(f"Token validation error: {e}")
        return None


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    JWT token'dan user döndür (gerekli).
    Token yoksa veya invalid ise 401 error döndür.
    """
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz kimlik doğrulama"
        )
    
    try:
        payload = decode_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Geçersiz token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Geçersiz token"
            )
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Kullanıcı bulunamadı"
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz token"
        )


@router.get("/login", response_class=HTMLResponse)
async def login_get(
    request: Request,
    current_user = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Login sayfasını göster"""
    if current_user:
        return RedirectResponse(url="/web/dashboard", status_code=302)
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "page_title": "Giriş Yap"
    })


@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Kullanıcı login'i işle"""
    try:
        form_data = await request.form()
        email = str(form_data.get("email", "")).strip()
        password = str(form_data.get("password", "")).strip()
        # Ensure we always emit visible debug output for browser tests
        logger.info(f"Login attempt received: email={email}, password_provided={'yes' if password else 'no'}")
        
        if not email or not password:
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": "Email ve şifre gereklidir",
                    "page_title": "Giriş Yap"
                }
            )
        
        result = await db.execute(
            select(User).where(User.email == email.lower())
        )
        user = result.scalar_one_or_none()
        logger.info(f"User lookup result: {'found' if user else 'not found'} for email={email}")
        
        password_ok = False
        if user:
            try:
                password_ok = verify_password(password, str(user.password_hash))
            except Exception as _e:
                logger.info(f"Password verify error for user {user.id}: {_e}")

        if not user or not password_ok:
            logger.info(f"Login failed for {email}: user_found={bool(user)}, password_ok={password_ok}")
            # Return template with diagnostic headers so browser network tab shows reason
            headers = {"X-Login-Status": "failed", "X-Login-UserFound": str(bool(user)), "X-Login-PasswordOK": str(password_ok)}
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": "Geçersiz email veya şifre",
                    "email": email,
                    "page_title": "Giriş Yap"
                },
                headers=headers
            )
        
        is_active = bool(user.is_active) if user.is_active is not None else False
        if not is_active:
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": "Hesabınız deaktif edilmiştir",
                    "page_title": "Giriş Yap"
                }
            )
        
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        # Add visible header so browser network tab can detect redirect from server
        response = RedirectResponse(url="/web/dashboard", status_code=302, headers={"X-Login-Redirect": "true"})
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=settings.ENVIRONMENT == "production" if hasattr(settings, 'ENVIRONMENT') else False,
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        logger.info(f"User {user.id} logged in successfully")
        return response
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Bir hata oluştu. Lütfen tekrar deneyiniz",
                "page_title": "Giriş Yap"
            }
        )





@router.post("/logout")
async def logout(
    current_user = Depends(get_current_user)
):
    """Kullanıcı logout'ını işle"""
    response = RedirectResponse(url="/web/auth/login?logged_out=true", status_code=302)
    response.delete_cookie(key="access_token")
    logger.info(f"User {current_user.id} logged out")
    return response