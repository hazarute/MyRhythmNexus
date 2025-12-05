from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
from typing import List

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .core.config import settings
from . import models, schemas, database

# Create tables
models.Base.metadata.create_all(bind=database.engine)

# Setup Rate Limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title=settings.PROJECT_NAME)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Admin Endpoints ---

@app.post("/api/v1/customers/", response_model=schemas.Customer)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(database.get_db)):
    db_customer = models.Customer(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@app.post("/api/v1/licenses/", response_model=schemas.License)
def create_license(license: schemas.LicenseCreate, db: Session = Depends(database.get_db)):
    # Check if license key exists
    existing = db.query(models.License).filter(models.License.license_key == license.license_key).first()
    if existing:
        raise HTTPException(status_code=400, detail="License key already exists")
    
    db_license = models.License(**license.model_dump())
    db.add(db_license)
    db.commit()
    db.refresh(db_license)
    return db_license

@app.get("/api/v1/licenses/", response_model=List[schemas.License])
def list_licenses(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return db.query(models.License).offset(skip).limit(limit).all()

# --- Client Endpoints ---

@app.post("/api/v1/license/validate", response_model=schemas.LicenseValidateResponse)
@limiter.limit(settings.LICENSE_VALIDATE_RATE)
def validate_license(req: schemas.LicenseValidateRequest, request: Request, db: Session = Depends(database.get_db)):
    """
    Client sends License Key + Machine ID.
    Server checks DB, locks hardware if needed, and returns RSA-signed JWT.
    """
    license_obj = db.query(models.License).filter(models.License.license_key == req.license_key).first()
    
    # 1. Check existence
    if not license_obj:
        return {"valid": False, "message": "Invalid license key"}
    
    # 2. Check active status
    if not license_obj.is_active:
        return {"valid": False, "message": "License is inactive"}
        
    # 3. Check expiration
    if license_obj.expires_at < datetime.utcnow():
        return {"valid": False, "message": "License expired"}
    
    # 4. Hardware Locking Logic
    if license_obj.hardware_id is None:
        # First activation: Lock to this machine
        license_obj.hardware_id = req.hardware_id
        db.commit()
    elif license_obj.hardware_id != req.hardware_id:
        # Mismatch
        return {"valid": False, "message": "Hardware mismatch. License is locked to another device."}
    
    # 5. Update Check-in
    license_obj.last_checkin = datetime.utcnow()
    db.commit()
    
    # 6. Generate RSA Signed JWT
    payload = {
        "sub": license_obj.license_key,
        "hwid": license_obj.hardware_id,
        "exp": datetime.utcnow() + timedelta(days=settings.OFFLINE_TOKEN_EXPIRE_DAYS), # Token valid for offline period
        "features": license_obj.features,
        "customer": license_obj.customer.name if license_obj.customer else "Unknown",
    }
    
    token = jwt.encode(
        payload,
        settings.PRIVATE_KEY,
        algorithm=settings.ALGORITHM,
    )
    
    return {
        "valid": True, 
        "token": token,
        "message": "Validation successful"
    }

@app.get("/")
def read_root():
    return {"message": "MyRhythmNexus License Server is running"}
