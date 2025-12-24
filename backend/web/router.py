from fastapi import APIRouter

from .routes.auth import router as auth_router
from .routes.dashboard import router as dashboard_router
from .routes.subscriptions import router as subscriptions_router
from .routes.measurements import router as measurements_router
from .routes.measurements_detail import router as measurements_detail_router
from .routes.finance import router as finance_router
from .routes.profile import router as profile_router
from .routes.register import router as register_router
from .routes.legal import router as legal_router

router = APIRouter(prefix="/web", tags=["web"])

router.include_router(auth_router)
router.include_router(register_router)
router.include_router(dashboard_router)
router.include_router(legal_router)
router.include_router(subscriptions_router)
router.include_router(measurements_router)
router.include_router(measurements_detail_router)
router.include_router(finance_router)
router.include_router(profile_router)
