from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
import zoneinfo

from backend.core.database import get_db
from backend.models.user import User, Role


class UserActivityScheduler:
    """Kullanıcı aktivite durumunu yöneten scheduler"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def deactivate_inactive_members(self):
        """2 aydan fazla paket satın almamış MEMBER rolü kullanıcıları inaktif yap"""
        turkey_tz = zoneinfo.ZoneInfo('Europe/Istanbul')
        cutoff_date = datetime.now(turkey_tz) - timedelta(days=60)  # 2 ay = 60 gün

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

                    print(f"[{datetime.now(turkey_tz)}] Deactivated {len(inactive_user_ids)} inactive members")
                    print(f"Inactive member IDs: {inactive_user_ids}")

                else:
                    print(f"[{datetime.now(turkey_tz)}] No inactive members found")

            except Exception as e:
                await db.rollback()
                print(f"[{datetime.now(turkey_tz)}] Error deactivating members: {e}")

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
        self.scheduler.start()
        print("UserActivityScheduler started - will run daily at 02:00 Turkey time")

    def stop(self):
        """Scheduler'ı durdur"""
        self.scheduler.shutdown()
        print("UserActivityScheduler stopped")