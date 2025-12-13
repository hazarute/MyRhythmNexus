#!/usr/bin/env python3
"""List subscription counts per user and show sample subscriptions.

Usage: PYTHONPATH=. python scripts/list_subscriptions_summary.py
"""
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
import asyncio

from backend.core.database import SessionLocal
from backend.models.user import User
from backend.models.operation import Subscription


async def main():
    async with SessionLocal() as session:
        # list counts per user
        result = await session.execute(
            select(Subscription.member_user_id, func.count(Subscription.id)).group_by(Subscription.member_user_id)
        )
        rows = result.all()
        if not rows:
            print('No subscriptions found in DB')
            return

        print('Subscriptions summary (user_id -> count)')
        for user_id, cnt in rows:
            # fetch user email
            ures = await session.execute(select(User).where(User.id == user_id))
            user = ures.scalar_one_or_none()
            email = user.email if user else '<unknown>'
            print(f'- {user_id} | {email} : {cnt}')
            # fetch sample subscriptions
            sres = await session.execute(
                select(Subscription)
                .options(selectinload(Subscription.package).selectinload(Subscription.package.property.mapper.class_.plan))
                .where(Subscription.member_user_id == user_id)
                .order_by(Subscription.start_date.desc())
                .limit(5)
            )
            subs = sres.scalars().all()
            # Also print whether our route would classify these as active
            def status_value(s):
                try:
                    return s.status.value
                except Exception:
                    return s.status

            for s in subs:
                pkg = s.package.name if getattr(s, 'package', None) and s.package else '—'
                is_active = status_value(s) in ("active", "ongoing")
                print(f'    - id={s.id} pkg={pkg} status={s.status} active_by_route={is_active} start={s.start_date} end={s.end_date} used={s.used_sessions}')


if __name__ == '__main__':
    asyncio.run(main())
