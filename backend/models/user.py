import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String(320), unique=True, nullable=False, index=True)
    phone_number = Column(String(32))
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    roles = relationship("Role", secondary="user_roles", back_populates="users", overlaps="user_roles")
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan", overlaps="roles")
    instructor = relationship("Instructor", back_populates="user", uselist=False)
    subscriptions = relationship("Subscription", back_populates="member", cascade="all, delete-orphan")
    payments_recorded = relationship("Payment", back_populates="recorded_by", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="member", cascade="all, delete-orphan")
    session_check_ins = relationship(
        "SessionCheckIn", back_populates="member", foreign_keys="SessionCheckIn.member_user_id", cascade="all, delete-orphan"
    )
    verified_check_ins = relationship(
        "SessionCheckIn",
        back_populates="verified_by",
        foreign_keys="SessionCheckIn.verified_by_user_id",
        cascade="all, delete-orphan",
    )
    measurement_sessions = relationship(
        "MeasurementSession", 
        back_populates="member",
        foreign_keys="MeasurementSession.member_user_id",
        cascade="all, delete-orphan"
    )

    async def hard_delete(self, db: AsyncSession) -> None:
        """
        Perform a hard delete of the user and all related records.
        This method handles the complex cascade delete logic that cannot be
        fully managed by SQLAlchemy's cascade due to foreign key constraints.
        """
        try:
            # Delete subscription_qr_codes first (depends on subscriptions)
            await db.execute(
                text("DELETE FROM subscription_qr_codes WHERE subscription_id IN (SELECT id FROM subscriptions WHERE member_user_id = :user_id)"),
                {"user_id": self.id}
            )

            # Delete payments that reference subscriptions
            await db.execute(
                text("DELETE FROM payments WHERE subscription_id IN (SELECT id FROM subscriptions WHERE member_user_id = :user_id)"),
                {"user_id": self.id}
            )

            # Delete session_check_ins that reference subscriptions
            await db.execute(
                text("DELETE FROM session_check_ins WHERE subscription_id IN (SELECT id FROM subscriptions WHERE member_user_id = :user_id)"),
                {"user_id": self.id}
            )

            # Delete bookings that reference subscriptions (this will break event_id constraint temporarily)
            await db.execute(
                text("DELETE FROM bookings WHERE subscription_id IN (SELECT id FROM subscriptions WHERE member_user_id = :user_id)"),
                {"user_id": self.id}
            )

            # Delete class_events that are created by this user's subscriptions
            # Note: class_events don't have subscription_id, so we need to find events that have bookings from this user's subscriptions
            await db.execute(
                text("""
                    DELETE FROM class_events 
                    WHERE id IN (
                        SELECT DISTINCT ce.id 
                        FROM class_events ce
                        INNER JOIN bookings b ON ce.id = b.event_id
                        WHERE b.subscription_id IN (SELECT id FROM subscriptions WHERE member_user_id = :user_id)
                    )
                """),
                {"user_id": self.id}
            )

            # Now delete subscriptions
            await db.execute(
                text("DELETE FROM subscriptions WHERE member_user_id = :user_id"),
                {"user_id": self.id}
            )

            # Delete remaining session check-ins (member specific)
            await db.execute(
                text("DELETE FROM session_check_ins WHERE member_user_id = :user_id"),
                {"user_id": self.id}
            )

            # Delete remaining bookings (member specific)
            await db.execute(
                text("DELETE FROM bookings WHERE member_user_id = :user_id"),
                {"user_id": self.id}
            )

            # Delete measurement values first
            await db.execute(text('''
                DELETE FROM measurement_values 
                WHERE session_id IN (
                    SELECT id FROM measurement_sessions 
                    WHERE member_user_id = :user_id
                )
            '''), {"user_id": self.id})

            # Delete measurement sessions
            await db.execute(
                text("DELETE FROM measurement_sessions WHERE member_user_id = :user_id"),
                {"user_id": self.id}
            )

            # Delete payments (recorded by this user)
            await db.execute(
                text("DELETE FROM payments WHERE recorded_by_user_id = :user_id"),
                {"user_id": self.id}
            )

            # Delete instructor record if exists
            await db.execute(
                text("DELETE FROM instructors WHERE user_id = :user_id"),
                {"user_id": self.id}
            )

            # Delete user roles - Let SQLAlchemy handle this with cascade
            # await db.execute(
            #     text("DELETE FROM user_roles WHERE user_id = :user_id"),
            #     {"user_id": self.id}
            # )

            # Finally delete the user
            await db.delete(self)

        except Exception as e:
            await db.rollback()
            raise e


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(80), unique=True, nullable=False)

    users = relationship("User", secondary="user_roles", back_populates="roles", overlaps="user_roles")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan", overlaps="roles")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)

    user = relationship("User", back_populates="user_roles", overlaps="roles,user_roles,users")
    role = relationship("Role", back_populates="user_roles", overlaps="users,user_roles,roles")


class Instructor(Base):
    __tablename__ = "instructors"

    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    bio = Column(String)
    profile_picture_url = Column(String)

    user = relationship("User", back_populates="instructor")
    class_events = relationship("ClassEvent", back_populates="instructor")
