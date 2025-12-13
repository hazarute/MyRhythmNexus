#!/usr/bin/env python3
"""Find subscriptions whose status doesn't match their date window and fix them.

Rules applied:
- if end_date < now and status != expired -> set expired
- if start_date > now and status != pending -> set pending
- if start_date <= now <= end_date and status != active -> set active

Run with: PYTHONPATH=. python scripts/fix_subscription_statuses.py
"""
import asyncio
from sqlalchemy.future import select
from sqlalchemy import update
from backend.core.database import SessionLocal
from backend.models.operation import Subscription, SubscriptionStatus
from backend.core.time_utils import get_turkey_time


async def main():
    now = get_turkey_time()
    async with SessionLocal() as session:
        result = await session.execute(select(Subscription))
        subs = result.scalars().all()
        changed = 0
        for s in subs:
            desired = None
            if s.end_date < now:
                desired = SubscriptionStatus.expired
            elif s.start_date > now:
                desired = SubscriptionStatus.pending
            else:
                desired = SubscriptionStatus.active

            # Compare by .value if Enum
            cur = s.status
            cur_val = cur.value if hasattr(cur, 'value') else cur
            des_val = desired.value if hasattr(desired, 'value') else desired
            if cur_val != des_val:
                print(f"Fixing subscription {s.id}: {cur_val} -> {des_val}")
                await session.execute(update(Subscription).where(Subscription.id == s.id).values(status=desired))
                changed += 1

        if changed:
            await session.commit()
        print(f"Done. Updated {changed} subscriptions.")


if __name__ == '__main__':
    asyncio.run(main())
