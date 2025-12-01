import uuid
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    DECIMAL,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.core.database import Base


class SubscriptionStatus(PyEnum):
    active = "active"
    expired = "expired"
    cancelled = "cancelled"
    pending = "pending"
    suspended = "suspended"


class PaymentMethod(PyEnum):
    NAKIT = "NAKIT"
    KREDI_KARTI = "KREDI_KARTI"
    HAVALE_EFT = "HAVALE_EFT"
    DIGER = "DIGER"


class BookingStatus(PyEnum):
    confirmed = "confirmed"
    cancelled_by_member = "cancelled_by_member"
    cancelled_by_admin = "cancelled_by_admin"
    no_show = "no_show"
    completed = "completed"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    member_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    package_id = Column(String(36), ForeignKey("service_packages.id"), nullable=False)
    purchase_price = Column(DECIMAL(10, 2), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(
        Enum(SubscriptionStatus, name="subscription_status", native_enum=False), nullable=False
    )
    access_type = Column(String(20), nullable=False, default="SESSION_BASED")
    used_sessions = Column(Integer, nullable=False, default=0)
    attendance_count = Column(Integer, nullable=False, default=0)

    member = relationship("User", back_populates="subscriptions")
    package = relationship("ServicePackage", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="subscription")
    qr_code = relationship("SubscriptionQrCode", back_populates="subscription", uselist=False)
    session_check_ins = relationship("SessionCheckIn", back_populates="subscription")
    class_events = relationship("ClassEvent", back_populates="subscription", cascade="all, delete-orphan")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=False)
    recorded_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    amount_paid = Column(DECIMAL(10, 2), nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    payment_method = Column(
        Enum(PaymentMethod, name="payment_method", native_enum=False), nullable=False
    )
    refund_amount = Column(DECIMAL(10, 2))
    refund_date = Column(DateTime(timezone=True))
    refund_reason = Column(String)

    subscription = relationship("Subscription", back_populates="payments")
    recorded_by = relationship("User", back_populates="payments_recorded")


class ClassTemplate(Base):
    __tablename__ = "class_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(160), nullable=False)

    booking_permissions = relationship("BookingPermission", back_populates="template")
    class_events = relationship("ClassEvent", back_populates="template")


class BookingPermission(Base):
    __tablename__ = "booking_permissions"

    package_id = Column(String(36), ForeignKey("service_packages.id"), primary_key=True)
    template_id = Column(String(36), ForeignKey("class_templates.id"), primary_key=True)

    package = relationship("ServicePackage", back_populates="booking_permissions")
    template = relationship("ClassTemplate", back_populates="booking_permissions")


class ClassEvent(Base):
    __tablename__ = "class_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id = Column(String(36), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=True)
    template_id = Column(String(36), ForeignKey("class_templates.id"), nullable=False)
    instructor_user_id = Column(String(36), ForeignKey("instructors.user_id"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    capacity = Column(Integer, nullable=False)
    is_cancelled = Column(Boolean, nullable=False, default=False)

    subscription = relationship("Subscription", back_populates="class_events")
    template = relationship("ClassTemplate", back_populates="class_events")
    instructor = relationship("Instructor", back_populates="class_events")
    bookings = relationship("Booking", back_populates="event")
    session_check_ins = relationship("SessionCheckIn", back_populates="event")


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("member_user_id", "event_id", name="uq_booking_member_event"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    member_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    event_id = Column(String(36), ForeignKey("class_events.id"), nullable=False)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=False)
    status = Column(
        Enum(BookingStatus, name="booking_status", native_enum=False),
        nullable=False,
        server_default="confirmed",
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    member = relationship("User", back_populates="bookings")
    event = relationship("ClassEvent", back_populates="bookings")
    subscription = relationship("Subscription", back_populates="bookings")
    session_check_ins = relationship("SessionCheckIn", back_populates="booking")


class SubscriptionQrCode(Base):
    __tablename__ = "subscription_qr_codes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=False, unique=True)
    qr_token = Column(String(128), nullable=False, unique=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    subscription = relationship("Subscription", back_populates="qr_code")


class SessionCheckIn(Base):
    __tablename__ = "session_check_ins"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=False)
    member_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    event_id = Column(String(36), ForeignKey("class_events.id"), nullable=True)  # Nullable for TIME_BASED subscriptions
    verified_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    check_in_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    booking_id = Column(String(36), ForeignKey("bookings.id"), unique=True)

    subscription = relationship("Subscription", back_populates="session_check_ins")
    member = relationship("User", back_populates="session_check_ins", foreign_keys=[member_user_id])
    event = relationship("ClassEvent", back_populates="session_check_ins")
    verified_by = relationship("User", back_populates="verified_check_ins", foreign_keys=[verified_by_user_id])
    booking = relationship("Booking", back_populates="session_check_ins")


class MeasurementSession(Base):
    __tablename__ = "measurement_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    member_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    recorded_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    session_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    notes = Column(Text)

    member = relationship("User", back_populates="measurement_sessions", foreign_keys=[member_user_id])
    recorded_by = relationship("User", foreign_keys=[recorded_by_user_id])
    measurement_values = relationship("MeasurementValue", back_populates="session", cascade="all, delete-orphan")


class MeasurementType(Base):
    __tablename__ = "measurement_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_key = Column(String(64), unique=True, nullable=False)
    type_name = Column(String(120), nullable=False)
    unit = Column(String(32), nullable=False)

    values = relationship("MeasurementValue", back_populates="measurement_type")


class MeasurementValue(Base):
    __tablename__ = "measurement_values"
    __table_args__ = (
        UniqueConstraint("session_id", "type_id", name="uq_measurement_session_type"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("measurement_sessions.id"), nullable=False)
    type_id = Column(Integer, ForeignKey("measurement_types.id"), nullable=False)
    value = Column(DECIMAL(10, 2), nullable=False)

    session = relationship("MeasurementSession", back_populates="measurement_values")
    measurement_type = relationship("MeasurementType", back_populates="values")
