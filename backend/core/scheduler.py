from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
import zoneinfo

from backend.core.database import get_db
from backend.core.time_utils import get_turkey_time
from backend.models.user import User, Role
from backend.models.operation import Subscription, SubscriptionStatus, SubscriptionQrCode
from backend.models.service import PlanDefinition, ServicePackage


class UserActivityScheduler:
    """Kullanıcı aktivite durumunu yöneten scheduler"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def deactivate_inactive_members(self):
        """2 aydan fazla paket satın almamış MEMBER rolü kullanıcıları inaktif yap"""
        cutoff_date = get_turkey_time() - timedelta(days=60)  # 2 ay = 60 gün

        async for db in get_db():
            try:
                # MEMBER rolüne sahip, 2 aydan eski updated_at'e sahip aktif kullanıcıları bul
                query = (
                    select(User.id)
                    .join(User.roles)
                    .where(
                        Role.role_name == "MEMBER",
                        User.is_active == True,
                        User.updated_at < cutoff_date
                    )
                )

                result = await db.execute(query)
                inactive_user_ids = result.scalars().all()

                if inactive_user_ids:
                    # Bulk update
                    update_query = (
                        update(User)
                        .where(User.id.in_(inactive_user_ids))
                        .values(is_active=False)
                    )
                    await db.execute(update_query)
                    await db.commit()

                    print(f"[{get_turkey_time()}] Deactivated {len(inactive_user_ids)} inactive members")
                    print(f"Inactive member IDs: {inactive_user_ids}")

                else:
                    print(f"[{get_turkey_time()}] No inactive members found")

            except Exception as e:
                await db.rollback()
                print(f"[{get_turkey_time()}] Error deactivating members: {e}")

    async def expire_subscriptions(self):
        """Süresi dolmuş veya hakkı bitmiş abonelikleri expired olarak işaretle"""
        now = get_turkey_time()

        async for db in get_db():
            try:
                expired_count = 0

                # 1. Zaman bazlı kontrol: end_date geçmiş olanlar
                time_based_expired = (
                    select(Subscription.id)
                    .where(
                        Subscription.status == SubscriptionStatus.active,
                        Subscription.end_date < now
                    )
                )

                time_result = await db.execute(time_based_expired)
                time_expired_ids = time_result.scalars().all()

                if time_expired_ids:
                    time_update = (
                        update(Subscription)
                        .where(Subscription.id.in_(time_expired_ids))
                        .values(status=SubscriptionStatus.expired)
                    )
                    await db.execute(time_update)
                    expired_count += len(time_expired_ids)
                    print(f"[{now}] Expired {len(time_expired_ids)} subscriptions due to end_date")

                # 2. Seans bazlı kontrol: used_sessions >= sessions_granted olanlar
                # Correctly join ServicePackage -> PlanDefinition to evaluate session-based expiry
                session_based_expired = (
                    select(Subscription.id)
                    .join(Subscription.package)
                    .join(PlanDefinition, ServicePackage.plan_id == PlanDefinition.id)
                    .where(
                        Subscription.status == SubscriptionStatus.active,
                        PlanDefinition.access_type == "SESSION_BASED",
                        PlanDefinition.sessions_granted.isnot(None),
                        Subscription.used_sessions >= PlanDefinition.sessions_granted
                    )
                )

                session_result = await db.execute(session_based_expired)
                session_expired_ids = session_result.scalars().all()

                if session_expired_ids:
                    session_update = (
                        update(Subscription)
                        .where(Subscription.id.in_(session_expired_ids))
                        .values(status=SubscriptionStatus.expired)
                    )
                    await db.execute(session_update)
                    expired_count += len(session_expired_ids)
                    print(f"[{now}] Expired {len(session_expired_ids)} subscriptions due to used sessions")

                # Deactivate QR codes for any subscriptions that were marked expired
                expired_ids = []
                if time_expired_ids:
                    expired_ids.extend(time_expired_ids)
                if session_expired_ids:
                    expired_ids.extend(session_expired_ids)

                if expired_ids:
                    try:
                        qr_update = (
                            update(SubscriptionQrCode)
                            .where(SubscriptionQrCode.subscription_id.in_(expired_ids))
                            .values(is_active=False)
                        )
                        await db.execute(qr_update)
                        print(f"[{now}] Deactivated QR codes for {len(expired_ids)} expired subscriptions")
                    except Exception as e:
                        # Log but continue; we'll rollback overall if commit fails below
                        print(f"[{now}] Error deactivating QR codes: {e}")

                if expired_count > 0:
                    await db.commit()
                    print(f"[{now}] Total expired subscriptions: {expired_count}")
                else:
                    print(f"[{now}] No subscriptions to expire")

            except Exception as e:
                await db.rollback()
                print(f"[{now}] Error expiring subscriptions: {e}")

    def start(self):
        """Scheduler'ı başlat"""
        # Her gün saat 02:00'de çalıştır (Türkiye saati)
        self.scheduler.add_job(
            self.deactivate_inactive_members,
            CronTrigger(hour=2, minute=0),
            id="deactivate_inactive_members",
            name="Deactivate Inactive Members",
            timezone=zoneinfo.ZoneInfo('Europe/Istanbul')
        )
        
        # Her gün saat 02:30'da çalıştır (Türkiye saati) - Abonelik expiry kontrolü
        self.scheduler.add_job(
            self.expire_subscriptions,
            CronTrigger(hour=2, minute=30),
            id="expire_subscriptions",
            name="Expire Subscriptions",
            timezone=zoneinfo.ZoneInfo('Europe/Istanbul')
        )
        
        self.scheduler.start()
        print("UserActivityScheduler started - will run daily at 02:00 and 02:30 Turkey time")

    def stop(self):
        """Scheduler'ı durdur"""
        self.scheduler.shutdown()
        print("UserActivityScheduler stopped - both member deactivation and subscription expiry jobs stopped")