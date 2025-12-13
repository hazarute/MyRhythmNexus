"""
Finance Routes - Ödeme Geçmişi
FastAPI + SQLAlchemy AsyncSession
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, timezone
import logging
import io
import csv
import json
from pathlib import Path

from backend.core.database import get_db
from backend.models.user import User
from backend.models.operation import Payment, Subscription
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="backend/web/templates")


@router.get("/finance", response_class=HTMLResponse)
async def finance(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Ödeme geçmişini göster"""
    try:
        # Kullanıcının aboneliklerini al
        sub_result = await db.execute(
            select(Subscription).where(
                Subscription.member_user_id == current_user.id
            )
        )
        subscriptions = sub_result.scalars().all()
        subscription_ids = [s.id for s in subscriptions]
        
        # Ödemeleri al
        payment_result = await db.execute(
            select(Payment)
            .options(selectinload(Payment.subscription).selectinload(Subscription.package))
            .where(
                Payment.subscription_id.in_(subscription_ids),
                Payment.amount_paid > 0
            )
            .order_by(Payment.payment_date.desc())
        )
        payments = payment_result.scalars().all()
        
        # Compute summary numbers (use timezone-aware UTC to avoid naive/aware comparison)
        now = datetime.now(timezone.utc)
        last_year = now - timedelta(days=365)

        total_paid = 0.0
        total_paid_12mo = 0.0
        try:
            if payments:
                total_paid = sum([float(p.amount_paid) for p in payments])
                # only count payments with a valid payment_date
                total_paid_12mo = sum([
                    float(p.amount_paid) for p in payments
                    if getattr(p, 'payment_date', None) is not None and p.payment_date >= last_year
                ])
        except Exception:
            # In case of any datetime issues, fall back to simple sums
            try:
                total_paid = sum([float(p.amount_paid) for p in payments]) if payments else 0.0
            except Exception:
                total_paid = 0.0
            total_paid_12mo = 0.0

        # Determine next payment from user's active subscriptions (earliest end_date in future)
        next_payment_amount = 0.0
        next_payment_date = None
        try:
            future_subs = [s for s in subscriptions if hasattr(s, 'end_date') and s.end_date and s.end_date > now]
            if future_subs:
                next_sub = sorted(future_subs, key=lambda s: s.end_date)[0]
                next_payment_amount = float(getattr(next_sub, 'purchase_price', 0) or 0)
                next_payment_date = next_sub.end_date
        except Exception:
            pass

        # Compute balance: total subscriptions purchase_price - total_paid
        total_due = 0.0
        try:
            if subscriptions:
                total_due = sum([float(s.purchase_price) for s in subscriptions if getattr(s, 'purchase_price', None) is not None])
        except Exception:
            total_due = 0.0

        balance = total_due - total_paid

        # Build activities: payments (from DB) + outstanding debts (subscriptions with unpaid remainder)
        activities = []

        # map payments by subscription id
        payments_by_sub = {}
        for p in payments:
            payments_by_sub.setdefault(getattr(p, 'subscription_id', None), []).append(p)

        # payments activities
        for p in payments:
            try:
                activities.append({
                    "id": getattr(p, 'id', None),
                    "type": "payment",
                    "date": getattr(p, 'payment_date', None),
                    "description": (p.subscription.package.name if getattr(p, 'subscription', None) and getattr(p.subscription, 'package', None) else 'Ödeme'),
                    "amount": float(p.amount_paid) if getattr(p, 'amount_paid', None) is not None else 0.0,
                    "status": "paid"
                })
            except Exception:
                continue

        # debts: compute outstanding per subscription
        for s in subscriptions:
            try:
                paid_sum = sum([float(x.amount_paid) for x in payments_by_sub.get(s.id, [])]) if payments_by_sub.get(s.id) else 0.0
                purchase_price = float(getattr(s, 'purchase_price', 0) or 0)
                outstanding = purchase_price - paid_sum
                if outstanding > 0:
                    activities.append({
                        "id": s.id,
                        "type": "debt",
                        "date": getattr(s, 'end_date', None) or getattr(s, 'start_date', None),
                        "description": (s.package.name if getattr(s, 'package', None) else 'Abonelik'),
                        "amount": outstanding,
                        "status": "due"
                    })
            except Exception:
                continue

        # sort activities by date desc (None dates go last)
        activities = sorted(activities, key=lambda a: a.get('date') or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

        context = {
            "request": request,
            "page_title": "Mali İşlemler",
            "user": current_user,
            "current_user": current_user,
            "payments": payments,
            "total_paid": total_paid,
            "total_paid_12mo": total_paid_12mo,
            "balance": balance,
            "next_payment_amount": next_payment_amount,
            "next_payment_date": next_payment_date,
            "activities": activities,
        }
        
        return templates.TemplateResponse("finance.html", context)
        
    except Exception as e:
        logger.error(f"Finance error: {e}")
        # Return template with default context keys so template rendering won't fail
        return templates.TemplateResponse(
            "finance.html",
            {
                "request": request,
                "user": current_user,
                "current_user": current_user,
                "payments": [],
                "total_paid": 0.0,
                "total_paid_12mo": 0.0,
                "balance": 0.0,
                "next_payment_amount": 0.0,
                "next_payment_date": None,
                "error": "Mali işlemler yüklenirken hata oluştu",
                "page_title": "Mali İşlemler"
            }
        )


@router.get("/finance/export")
async def finance_export(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export last 20 activities as CSV (most recent first)"""
    # filesystem cache: store per-user generated CSV once per UTC day
    cache_dir = Path(__file__).parent / "export_cache"
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    cache_file = cache_dir / f"export_{current_user.id}.json"

    # return cached CSV if same UTC day
    try:
        if cache_file.exists():
            with cache_file.open('r', encoding='utf-8') as fh:
                payload = json.load(fh)
            gen_iso = payload.get('generated_at')
            if gen_iso:
                gen_dt = datetime.fromisoformat(gen_iso)
                if gen_dt.date() == datetime.now(timezone.utc).date():
                    filename = payload.get('filename') or f"finance_activities_{gen_dt.strftime('%Y%m%d')}.csv"
                    return Response(payload.get('csv', ''), media_type='text/csv', headers={"Content-Disposition": f"attachment; filename=\"{filename}\""})
    except Exception:
        logger.debug("Failed to read export cache, regenerating")

    # cache miss: generate CSV now (will hit DB)
    try:
        sub_result = await db.execute(select(Subscription).where(Subscription.member_user_id == current_user.id))
        subscriptions = sub_result.scalars().all()
        subscription_ids = [s.id for s in subscriptions]

        payment_result = await db.execute(
            select(Payment)
            .options(selectinload(Payment.subscription).selectinload(Subscription.package))
            .where(Payment.subscription_id.in_(subscription_ids), Payment.amount_paid > 0)
            .order_by(Payment.payment_date.desc())
        )
        payments = payment_result.scalars().all()

        activities = []
        payments_by_sub = {}
        for p in payments:
            payments_by_sub.setdefault(getattr(p, 'subscription_id', None), []).append(p)

        for p in payments:
            try:
                activities.append({
                    "id": getattr(p, 'id', None),
                    "type": "payment",
                    "date": getattr(p, 'payment_date', None),
                    "description": (p.subscription.package.name if getattr(p, 'subscription', None) and getattr(p.subscription, 'package', None) else 'Ödeme'),
                    "amount": float(p.amount_paid) if getattr(p, 'amount_paid', None) is not None else 0.0,
                    "status": "paid"
                })
            except Exception:
                continue

        for s in subscriptions:
            try:
                paid_sum = sum([float(x.amount_paid) for x in payments_by_sub.get(s.id, [])]) if payments_by_sub.get(s.id) else 0.0
                purchase_price = float(getattr(s, 'purchase_price', 0) or 0)
                outstanding = purchase_price - paid_sum
                if outstanding > 0:
                    activities.append({
                        "id": s.id,
                        "type": "debt",
                        "date": getattr(s, 'end_date', None) or getattr(s, 'start_date', None),
                        "description": (s.package.name if getattr(s, 'package', None) else 'Abonelik'),
                        "amount": outstanding,
                        "status": "due"
                    })
            except Exception:
                continue

        activities = sorted(activities, key=lambda a: a.get('date') or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        export_rows = activities[:20]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["type", "date", "description", "amount", "status"])
        for a in export_rows:
            date_str = a.get('date').astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S') if a.get('date') else ''
            writer.writerow([a.get('type'), date_str, a.get('description'), "{:.2f}".format(float(a.get('amount') or 0.0)), a.get('status')])

        filename = f"finance_activities_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"
        content = output.getvalue()

        # write cache
        try:
            with cache_file.open('w', encoding='utf-8') as fh:
                json.dump({
                    'generated_at': datetime.now(timezone.utc).isoformat(),
                    'filename': filename,
                    'csv': content
                }, fh)
        except Exception:
            logger.debug("Failed to write export cache")

        return Response(content, media_type='text/csv', headers={"Content-Disposition": f"attachment; filename=\"{filename}\""})

    except Exception as e:
        logger.error(f"Finance export error: {e}")
        return Response("", media_type='text/csv')
