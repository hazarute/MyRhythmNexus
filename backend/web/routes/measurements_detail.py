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
        weight = None
        height_cm = None
        for mv in session.measurement_values:
            tname = mv.measurement_type.type_name if mv.measurement_type else mv.type_name if hasattr(mv, 'type_name') else 'Ölçüm'
            unit = mv.measurement_type.unit if mv.measurement_type else ''
            # keep original value as-is (string or numeric)
            try:
                val = float(mv.value)
            except Exception:
                val = mv.value
            values.append({"type_name": tname, "unit": unit, "value": val})
            # detect weight/height keys heuristically
            lk = (tname or '').lower()
            if 'kilo' in lk or 'kg' in lk or 'weight' in lk:
                try:
                    weight = float(mv.value)
                except Exception:
                    pass
            if 'boy' in lk or 'height' in lk or 'cm' in lk:
                try:
                    height_cm = float(mv.value)
                except Exception:
                    pass

        bmi = None
        if weight is not None and height_cm is not None and height_cm > 0:
            try:
                height_m = height_cm / 100.0
                bmi_val = weight / (height_m * height_m)
                bmi_value = round(bmi_val, 1)
                if bmi_value <= 18.5:
                    bmi_category = 'Zayıf'
                elif 18.5 < bmi_value <= 24.9:
                    bmi_category = 'Normal'
                elif 25.0 <= bmi_value <= 29.9:
                    bmi_category = 'Fazla kilolu'
                elif 30.0 <= bmi_value <= 34.9:
                    bmi_category = 'Obez (1. derece)'
                elif 35.0 <= bmi_value <= 39.9:
                    bmi_category = 'Obez (2. derece)'
                else:
                    bmi_category = 'Obez (3. derece)'
                bmi = {"value": bmi_value, "category": bmi_category}
            except Exception:
                bmi = None

        context = {
            "request": request,
            "page_title": "Ölçüm Detayı",
            "user": current_user,
            "current_user": current_user,
            "session": session,
            "values": values,
        }
        if bmi is not None:
            context['bmi'] = bmi

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
