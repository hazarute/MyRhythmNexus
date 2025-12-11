from fastapi import APIRouter
from backend.api.v1.auth import router as auth_router
from backend.api.v1.members import router as members_router
from backend.api.v1.services import router as services_router
from backend.api.v1.sales import router as sales_router
from backend.api.v1.operations import router as operations_router
from backend.api.v1.checkin import router as checkin_router
from backend.api.v1.stats import router as stats_router
from backend.api.v1.staff import router as staff_router
from backend.api.v1.measurements import router as measurements_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
api_router.include_router(members_router, prefix="/api/v1/members", tags=["members"])
api_router.include_router(services_router, prefix="/api/v1/services", tags=["services"])
api_router.include_router(sales_router, prefix="/api/v1/sales", tags=["sales"])
api_router.include_router(operations_router, prefix="/api/v1/operations", tags=["operations"])
api_router.include_router(checkin_router, prefix="/api/v1/checkin", tags=["checkin"])
api_router.include_router(stats_router, prefix="/api/v1/stats", tags=["stats"])
api_router.include_router(staff_router, prefix="/api/v1/staff", tags=["staff"])
api_router.include_router(measurements_router, prefix="/api/v1/measurements", tags=["measurements"])
