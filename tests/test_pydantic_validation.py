from decimal import Decimal
from backend.schemas.sales import PaymentCreate
from backend.models.operation import PaymentMethod
from pydantic import ValidationError

try:
    p = PaymentCreate(
        subscription_id="123",
        amount_paid=Decimal("123456789.00"), # > 100,000,000
        payment_method=PaymentMethod.NAKIT
    )
    print("Validation PASSED (Unexpected)")
except ValidationError as e:
    print("Validation FAILED as expected:")
    print(e)
except Exception as e:
    print(f"Unexpected error: {e}")
