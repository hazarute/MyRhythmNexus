import uuid

from sqlalchemy import Boolean, Column, DECIMAL, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.core.database import Base


class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), unique=True, nullable=False)
    description = Column(String)

    packages = relationship(
        "ServicePackage", back_populates="category", cascade="all, delete-orphan"
    )


class ServiceOffering(Base):
    __tablename__ = "service_offerings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(160), unique=True, nullable=False)
    description = Column(String)
    default_duration_minutes = Column(Integer, nullable=False)

    packages = relationship("ServicePackage", back_populates="offering")


class PlanDefinition(Base):
    __tablename__ = "plan_definitions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(180), unique=True, nullable=False)
    description = Column(String)
    access_type = Column(String(20), nullable=False, default="SESSION_BASED")
    sessions_granted = Column(Integer, nullable=True)
    cycle_period = Column(String(64), nullable=False)
    repeat_weeks = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)

    service_packages = relationship("ServicePackage", back_populates="plan")


class ServicePackage(Base):
    __tablename__ = "service_packages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True, nullable=False)
    category_id = Column(Integer, ForeignKey("service_categories.id"), nullable=False)
    offering_id = Column(String(36), ForeignKey("service_offerings.id"), nullable=False)
    plan_id = Column(String(36), ForeignKey("plan_definitions.id"), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    is_bookable = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)

    category = relationship("ServiceCategory", back_populates="packages")
    offering = relationship("ServiceOffering", back_populates="packages")
    plan = relationship("PlanDefinition", back_populates="service_packages")
    subscriptions = relationship("Subscription", back_populates="package")
    booking_permissions = relationship(
        "BookingPermission", back_populates="package", cascade="all, delete-orphan"
    )
