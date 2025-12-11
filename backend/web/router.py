from fastapi import APIRouter

from .routes.auth import router as auth_router
from .routes.dashboard import router as dashboard_router
from .routes.register import router as register_router

router = APIRouter(prefix="/web", tags=["web"])

router.include_router(auth_router)
router.include_router(dashboard_router)
router.include_router(register_router)
