from fastapi import APIRouter
from backend.api.v1 import auth, members, services, sales, operations, checkin, stats, staff, measurements, license, admin

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
api_router.include_router(members.router, prefix="/api/v1/members", tags=["members"])
api_router.include_router(services.router, prefix="/api/v1/services", tags=["services"])
api_router.include_router(sales.router, prefix="/api/v1/sales", tags=["sales"])
api_router.include_router(operations.router, prefix="/api/v1/operations", tags=["operations"])
api_router.include_router(checkin.router, prefix="/api/v1/checkin", tags=["checkin"])
api_router.include_router(stats.router, prefix="/api/v1/stats", tags=["stats"])
api_router.include_router(staff.router, prefix="/api/v1/staff", tags=["staff"])
api_router.include_router(measurements.router, prefix="/api/v1/measurements", tags=["measurements"])
api_router.include_router(license.router, prefix="/api/v1/license", tags=["license"])
api_router.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
