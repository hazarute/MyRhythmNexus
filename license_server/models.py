from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    contact_person = Column(String)
    phone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    licenses = relationship("License", back_populates="customer")

class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    
    # Hardware Locking
    hardware_id = Column(String, nullable=True)  # First activation locks this
    
    # Validity
    start_date = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Features (JSON)
    # Example: {"qr_checkin": true, "finance": true, "max_members": 100}
<<<<<<< HEAD
    # Use a callable default to avoid mutable default pitfalls
    features = Column(JSON, default=dict)
=======
    features = Column(JSON, default={})
>>>>>>> e4fab4fd669429a8657ad9bad273584201312c16
    
    last_checkin = Column(DateTime, nullable=True)
    
    customer = relationship("Customer", back_populates="licenses")
