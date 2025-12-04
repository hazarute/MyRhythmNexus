import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import Boolean, DateTime, String, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from backend.core.database import Base

class License(Base):
    __tablename__ = "licenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    license_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hardware_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_check_in: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    features: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
