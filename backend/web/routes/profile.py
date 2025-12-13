"""
Profile Routes - Profil ve Ayarlar
FastAPI + SQLAlchemy AsyncSession
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from backend.core.database import get_db
from backend.models.user import User
from backend.core.security import hash_password, verify_password
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="backend/web/templates")


@router.get("/profile", response_class=HTMLResponse)
async def profile(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Kullanıcı profili göster"""
    try:
        context = {
            "request": request,
            "page_title": "Profilim",
            "user": current_user,
            "current_user": current_user,
        }
        
        return templates.TemplateResponse("profile.html", context)
        
    except Exception as e:
        logger.error(f"Profile error: {e}")
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "user": current_user,
                "current_user": current_user,
                "error": "Profil yüklenirken hata oluştu",
                "page_title": "Profilim"
            }
        )


@router.post("/profile/update", response_class=HTMLResponse)
async def update_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Profil bilgilerini güncelle"""
    try:
        form_data = await request.form()
        first_name = str(form_data.get("first_name", "")).strip()
        last_name = str(form_data.get("last_name", "")).strip()
        phone_number = str(form_data.get("phone_number", "")).strip()
        
        if first_name:
            current_user.first_name = first_name
        if last_name:
            current_user.last_name = last_name
        if phone_number:
            current_user.phone_number = phone_number
        
        db.add(current_user)
        await db.commit()
        
        context = {
            "request": request,
            "page_title": "Profilim",
            "user": current_user,
            "current_user": current_user,
            "success": "Profil başarıyla güncellendi",
        }
        
        return templates.TemplateResponse("profile.html", context)
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "user": current_user,
                "current_user": current_user,
                "error": "Profil güncellenirken hata oluştu",
                "page_title": "Profilim"
            }
        )


@router.post("/profile/change-password", response_class=HTMLResponse)
async def change_password(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Parola değiştir"""
    try:
        form_data = await request.form()
        old_password = str(form_data.get("old_password", "")).strip()
        new_password = str(form_data.get("new_password", "")).strip()
        new_password_confirm = str(form_data.get("new_password_confirm", "")).strip()
        
        # Eski parola kontrol et
        if not verify_password(old_password, str(current_user.password_hash)):
            return templates.TemplateResponse(
                "profile.html",
                {
                    "request": request,
                    "user": current_user,
                    "current_user": current_user,
                    "error": "Eski parola yanlış",
                    "page_title": "Profilim"
                }
            )
        
        # Yeni parolalar eşleş me kontrol et
        if new_password != new_password_confirm:
            return templates.TemplateResponse(
                "profile.html",
                {
                    "request": request,
                    "user": current_user,
                    "current_user": current_user,
                    "error": "Yeni parolalar eşleşmiyor",
                    "page_title": "Profilim"
                }
            )
        
        # Yeni parola hash'le ve kaydet
        new_password_hashed = hash_password(new_password)
        current_user.password_hash = new_password_hashed
        db.add(current_user)
        await db.commit()
        try:
            await db.refresh(current_user)
        except Exception:
            pass
        
        context = {
            "request": request,
            "page_title": "Profilim",
            "user": current_user,
            "current_user": current_user,
            "success": "Parola başarıyla değiştirildi",
        }
        
        return templates.TemplateResponse("profile.html", context)
        
    except Exception as e:
        logger.error(f"Password change error: {e}")
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "user": current_user,
                "current_user": current_user,
                "error": "Parola değiştirilirken hata oluştu",
                "page_title": "Profilim"
            }
        )


@router.post("/profile/delete")
async def delete_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Kullanıcının kendi hesabını silmesini sağlar (hard delete)."""
    try:
        # Instead of hard deleting (admin-only), mark the account as inactive (soft-delete)
        current_user.is_active = False
        # update timestamp if available
        try:
            from backend.core.time_utils import get_turkey_time
            current_user.updated_at = get_turkey_time()
        except Exception:
            pass
        db.add(current_user)
        await db.commit()
        response = RedirectResponse(url="/web/auth/login?account_deactivated=true", status_code=302)
        response.delete_cookie(key="access_token")
        logger.info(f"User {current_user.id} account deactivated via profile (is_active=False)")
        return response
    except Exception as e:
        await db.rollback()
        logger.error(f"Profile delete error: {e}")
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "user": current_user,
                "current_user": current_user,
                "error": "Hesap silinirken bir hata oluştu",
                "page_title": "Profilim"
            }
        )
