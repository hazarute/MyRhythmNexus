# Import all models to ensure they are registered with SQLAlchemy
from .user import User, Role, UserRole, Instructor
from .service import ServiceCategory, ServiceOffering, PlanDefinition, ServicePackage
from .operation import (
    Subscription,
    Payment,
    ClassTemplate,
    BookingPermission,
    ClassEvent,
    Booking,
    SubscriptionQrCode,
    SessionCheckIn,
    MeasurementSession,
    MeasurementType,
    MeasurementValue,
    SubscriptionStatus
)