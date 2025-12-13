"""
Measurements Routes - Vücut Ölçümleri
FastAPI + SQLAlchemy AsyncSession
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from backend.core.database import get_db
from backend.models.user import User
from backend.models.operation import MeasurementSession, MeasurementType, MeasurementValue
from sqlalchemy.orm import selectinload
from .auth import get_current_user
import unicodedata
import re
import json

logger = logging.getLogger(__name__)

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="backend/web/templates")


@router.get("/measurements", response_class=HTMLResponse)
async def measurements(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Vücut ölçümlerini göster"""
    try:
        result = await db.execute(
            select(MeasurementSession).options(
                selectinload(MeasurementSession.measurement_values).selectinload(MeasurementValue.measurement_type)
            ).where(
                MeasurementSession.member_user_id == current_user.id
            ).order_by(MeasurementSession.session_date.desc())
        )
        measurement_sessions = result.scalars().all()
        # only keep the most recent 5 sessions for display
        if measurement_sessions:
            measurement_sessions = measurement_sessions[:5]

        # build simple lookup maps to make template rendering robust
        def _norm(s: str) -> str:
            if not s:
                return ""
            # normalize unicode and remove diacritics
            nk = unicodedata.normalize('NFKD', s)
            ascii_k = ''.join([c for c in nk if not unicodedata.combining(c)])
            # keep only alphanum characters
            compact = re.sub(r'[^0-9a-zA-Z]+', '', ascii_k).lower()
            return compact

        latest_map = {}
        prev_map = {}
        # prepare sessions_data for safe JSON embedding in template
        sessions_data = []
        if len(measurement_sessions) > 0:
            latest = measurement_sessions[0]
            for mv in latest.measurement_values:
                try:
                    v = float(mv.value)
                except Exception:
                    v = mv.value
                key_orig = (mv.measurement_type.type_name or '').lower()
                latest_map[key_orig] = v
                latest_map[_norm(mv.measurement_type.type_name or '')] = v

        if len(measurement_sessions) > 1:
            prev = measurement_sessions[1]
            for mv in prev.measurement_values:
                try:
                    v = float(mv.value)
                except Exception:
                    v = mv.value
                key_orig = (mv.measurement_type.type_name or '').lower()
                prev_map[key_orig] = v
                prev_map[_norm(mv.measurement_type.type_name or '')] = v

        # build sessions_data with normalized keys for Chart.js
        for s in measurement_sessions:
            vals = {}
            for mv in s.measurement_values:
                key = _norm(mv.measurement_type.type_name or '')
                try:
                    vals[key] = float(mv.value)
                except Exception:
                    vals[key] = mv.value
            sessions_data.append({
                "id": s.id,
                "label": s.session_date.strftime('%d %b') if s.session_date else None,
                "values": vals,
            })
        # create a quick map session_id -> values for template lookup
        session_maps = {entry['id']: entry['values'] for entry in sessions_data}

        context = {
            "request": request,
            "page_title": "Vücut Ölçümleri",
            "user": current_user,
            "current_user": current_user,
            "measurement_sessions": measurement_sessions,
            "latest_map": latest_map,
            "prev_map": prev_map,
            "sessions_json": json.dumps(sessions_data),
            "session_maps": session_maps,
        }

        # compute BMI from latest measurements if possible
        bmi_value = None
        bmi_category = None
        bmi_color = None
        try:
            # possible keys for weight and height
            weight = None
            for k in ('kilo','kg','weight'):
                if k in latest_map:
                    try:
                        weight = float(latest_map[k])
                        break
                    except Exception:
                        weight = None
            height_cm = None
            for k in ('boy','height','heightcm'):
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
                # categories per WHO
                if bmi_value <= 18.5:
                    bmi_category = 'Zayıf'
                    bmi_color = '#facc15'  # yellow-400
                elif 18.5 < bmi_value <= 24.9:
                    bmi_category = 'Normal'
                    bmi_color = '#16a34a'  # green-600
                elif 25.0 <= bmi_value <= 29.9:
                    bmi_category = 'Fazla kilolu'
                    bmi_color = '#f59e0b'  # yellow-500
                elif 30.0 <= bmi_value <= 34.9:
                    bmi_category = 'Obez (1. derece)'
                    bmi_color = '#dc2626'  # red-600
                elif 35.0 <= bmi_value <= 39.9:
                    bmi_category = 'Obez (2. derece)'
                    bmi_color = '#b91c1c'  # red-700
                else:
                    bmi_category = 'Obez (3. derece)'
                    bmi_color = '#991b1b'  # red-800

        except Exception:
            bmi_value = None
            bmi_category = None
            bmi_color = None

        context.update({
            "bmi_value": bmi_value,
            "bmi_category": bmi_category,
            "bmi_color_hex": bmi_color,
        })

        logger.info(f"Measurements: user={current_user.id} sessions_loaded={len(measurement_sessions)}")
        # return template with debug headers so the browser Network tab can reveal count
        response = templates.TemplateResponse("measurements.html", context)
        try:
            response.headers["X-Measurement-Count"] = str(len(measurement_sessions))
            if len(measurement_sessions) > 0:
                response.headers["X-Measurement-FirstID"] = str(measurement_sessions[0].id)
        except Exception:
            # don't fail rendering for header issues
            logger.debug("Could not set debug headers for measurements response")

        return response
        
    except Exception as e:
        logger.error(f"Measurements error: {e}")
        return templates.TemplateResponse(
            "measurements.html",
            {
                "request": request,
                "user": current_user,
                "current_user": current_user,
                "error": "Ölçümler yüklenirken hata oluştu",
                "page_title": "Vücut Ölçümleri"
            }
        )

@router.get("/debug/measurements", response_class=JSONResponse)
async def debug_measurements(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Debug endpoint: dönen ölçüm seanslarını JSON olarak verir (giriş yapmış kullanıcı için)."""
    try:
        result = await db.execute(
            select(MeasurementSession).options(
                selectinload(MeasurementSession.measurement_values).selectinload(MeasurementValue.measurement_type)
            ).where(
                MeasurementSession.member_user_id == current_user.id
            ).order_by(MeasurementSession.session_date.desc())
        )
        measurement_sessions = result.scalars().all()

        sessions = []
        for s in measurement_sessions:
            vals = []
            for mv in s.measurement_values:
                try:
                    v = float(mv.value)
                except Exception:
                    v = str(mv.value)
                vals.append({
                    "type_name": mv.measurement_type.type_name,
                    "unit": mv.measurement_type.unit,
                    "value": v,
                })
            sessions.append({
                "id": s.id,
                "session_date": s.session_date.isoformat() if s.session_date else None,
                "values": vals,
            })

        return JSONResponse({"count": len(sessions), "sessions": sessions[:20]})

    except Exception as e:
        logger.error(f"Debug measurements error: {e}")
        return JSONResponse({"error": "debug error", "detail": str(e)}, status_code=500)
