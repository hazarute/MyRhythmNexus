import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.future import select

from backend.core.database import SessionLocal
from backend.models.user import User
from backend.models.service import ServiceCategory, ServiceOffering, PlanDefinition, ServicePackage
from backend.models.operation import Subscription, SubscriptionQrCode, SubscriptionStatus


async def main():
    async with SessionLocal() as db:
        # Find fake user
        result = await db.execute(select(User).where(User.email == "fake@example.com"))
        user = result.scalar_one_or_none()
        if not user:
            print("Fake user not found. Run create_fake_user.py first.")
            return

        # Create plan
        plan = PlanDefinition(name="Test Plan", access_type="SESSION_BASED", sessions_granted=10, cycle_period="once", repeat_weeks=1, is_active=True)
        db.add(plan)
        await db.commit()
        await db.refresh(plan)

        # Create category and offering
        category = ServiceCategory(name="Test Category", description="Auto-created for testing")
        offering = ServiceOffering(name="Test Offering", description="Auto offering", default_duration_minutes=60)
        db.add_all([category, offering])
        await db.commit()
        await db.refresh(category)
        await db.refresh(offering)

        # Create package
        package = ServicePackage(name="Test Package", category_id=category.id, offering_id=offering.id, plan_id=plan.id, price=Decimal("100.00"))
        db.add(package)
        await db.commit()
        await db.refresh(package)

        # Create subscription
        start = datetime.utcnow()
        end = start + timedelta(days=30)
        subscription = Subscription(member_user_id=user.id, package_id=package.id, purchase_price=Decimal("100.00"), start_date=start, end_date=end, status=SubscriptionStatus.active, access_type="SESSION_BASED", used_sessions=2)
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)

        # Create QR code
        qr = SubscriptionQrCode(subscription_id=subscription.id, qr_token="FAKEQRTOKEN123")
        db.add(qr)
        await db.commit()
        await db.refresh(qr)

        print(f"Created subscription {subscription.id} and QR {qr.qr_token} for user {user.email}")


if __name__ == "__main__":
    asyncio.run(main())
