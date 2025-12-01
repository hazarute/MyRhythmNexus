import asyncio
import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from backend.core.database import SessionLocal
from backend.models.operation import Subscription, Payment, SubscriptionStatus, PaymentMethod
from backend.models.user import User
from backend.models.service import ServicePackage
from sqlalchemy.exc import DataError

async def reproduce_error():
    member_id = "3b7fee62-7eff-41ab-8868-3e82a545075f"
    package_id = "af264b0d-5799-4e0a-9eea-30c28f06efed"
    
    async with SessionLocal() as db:
        # Create a subscription first
        sub_id = str(uuid.uuid4())
        subscription = Subscription(
            id=sub_id,
            member_user_id=member_id,
            package_id=package_id,
            purchase_price=Decimal("100.00"),
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            status=SubscriptionStatus.active,
            used_sessions=0
        )
        db.add(subscription)
        
        # Create a payment with a VERY LARGE amount
        payment = Payment(
            subscription_id=sub_id,
            recorded_by_user_id=member_id, # Using member as recorder for simplicity
            amount_paid=Decimal("123456789012345.00"), # Exceeds (10, 2)
            payment_method=PaymentMethod.NAKIT
        )
        db.add(payment)
        
        print("Attempting to commit large payment...")
        try:
            await db.commit()
            print("Commit SUCCESS (Unexpected)")
        except Exception as e:
            print(f"Commit FAILED as expected.")
            print(f"Error type: {type(e)}")
            print(f"Error message: {e}")
            
            # Check if we can catch it specifically
            if "numeric field overflow" in str(e) or isinstance(e, DataError):
                print("Caught Numeric Overflow!")
            else:
                print("Caught generic exception.")

if __name__ == "__main__":
    asyncio.run(reproduce_error())
