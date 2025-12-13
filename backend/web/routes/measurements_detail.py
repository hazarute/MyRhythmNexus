"""
Measurement detail route moved to its own module.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from backend.core.database import get_db
from backend.models.user import User
from backend.models.operation import MeasurementSession, MeasurementValue
from sqlalchemy.orm import selectinload
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["web"]) 
templates = Jinja2Templates(directory="backend/web/templates")


@router.get("/measurements/{session_id}", response_class=HTMLResponse)
async def measurement_detail(
    request: Request,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Tek bir ölçüm seansının detay sayfası"""
    try:
        result = await db.execute(
            select(MeasurementSession).options(
                selectinload(MeasurementSession.measurement_values).selectinload(MeasurementValue.measurement_type)
            ).where(
                MeasurementSession.id == session_id
            )
        )
        session = result.scalars().first()
        if not session or session.member_user_id != current_user.id:
            return templates.TemplateResponse("measurements_detail.html", {
                "request": request,
                "user": current_user,
                "current_user": current_user,
                "error": "Bu ölçüm bulunamadı veya erişiminiz yok.",
                "page_title": "Ölçüm Detayı"
            })

        values = []
        # build a small lookup map similar to measurements route to compute BMI reliably
        def _norm(s: str) -> str:
            if not s:
                return ""
            nk = __import__('unicodedata').normalize('NFKD', s)
            ascii_k = ''.join([c for c in nk if not __import__('unicodedata').combining(c)])
            compact = __import__('re').sub(r'[^0-9a-zA-Z]+', '', ascii_k).lower()
            return compact

        latest_map = {}
        for mv in session.measurement_values:
            tname = mv.measurement_type.type_name if getattr(mv, 'measurement_type', None) else getattr(mv, 'type_name', '')
            unit = mv.measurement_type.unit if getattr(mv, 'measurement_type', None) else ''
            try:
                val = float(mv.value)
            except Exception:
                val = mv.value
            values.append({"type_name": tname, "unit": unit, "value": val})
            key_orig = (tname or '').lower()
            latest_map[key_orig] = val
            latest_map[_norm(tname or '')] = val

        # compute BMI using the same logic as measurements route
        bmi_value = None
        bmi_category = None
        bmi_color = None
        try:
            weight = None
            for k in ('kilo', 'kg', 'weight'):
                if k in latest_map:
                    try:
                        weight = float(latest_map[k])
                        break
                    except Exception:
                        weight = None
            height_cm = None
            for k in ('boy', 'height', 'heightcm'):
                if k in latest_map:
                    try:
                        height_cm = float(latest_map[k])
                        break
                    except Exception:
                        height_cm = None

            if weight is not None and height_cm is not None and height_cm > 0:
                height_m = height_cm / 100.0
                bmi = weight / (height_m * height_m)
                bmi_value = round(bmi, 1)
                if bmi_value <= 18.5:
                    bmi_category = 'Zayıf'
                    bmi_color = '#facc15'
                elif 18.5 < bmi_value <= 24.9:
                    bmi_category = 'Normal'
                    bmi_color = '#16a34a'
                elif 25.0 <= bmi_value <= 29.9:
                    bmi_category = 'Fazla kilolu'
                    bmi_color = '#f59e0b'
                elif 30.0 <= bmi_value <= 34.9:
                    bmi_category = 'Obez (1. derece)'
                    bmi_color = '#dc2626'
                elif 35.0 <= bmi_value <= 39.9:
                    bmi_category = 'Obez (2. derece)'
                    bmi_color = '#b91c1c'
                else:
                    bmi_category = 'Obez (3. derece)'
                    bmi_color = '#991b1b'
        except Exception:
            bmi_value = None
            bmi_category = None
            bmi_color = None

        context = {
            "request": request,
            "page_title": "Ölçüm Detayı",
            "user": current_user,
            "current_user": current_user,
            "session": session,
            "values": values,
        }
        if bmi_value is not None:
            context['bmi_value'] = bmi_value
            context['bmi_category'] = bmi_category
            context['bmi_color_hex'] = bmi_color
            # keep older 'bmi' key for backward compatibility
            context['bmi'] = {"value": bmi_value, "category": bmi_category}

        return templates.TemplateResponse("measurements_detail.html", context)

    except Exception as e:
        logger.error(f"Measurement detail error: {e}")
        return templates.TemplateResponse("measurements_detail.html", {
            "request": request,
            "user": current_user,
            "current_user": current_user,
            "error": "Detay yüklenirken hata oluştu",
            "page_title": "Ölçüm Detayı"
        })
