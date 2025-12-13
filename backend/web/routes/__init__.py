"""
Web Routes Package - Member Portal (FastAPI)

Her route modülü kendi APIRouter'ını tanımlar ve main router'a include edilir.
"""

from fastapi import APIRouter

# Ana web router
router = APIRouter(prefix="/web", tags=["web"])

# Route modüllerini import et ve include et
from . import auth as auth_routes
from . import register as register_routes
from . import dashboard as dashboard_routes
from . import subscriptions as subscriptions_routes
from . import measurements as measurements_routes
from . import finance as finance_routes
from . import profile as profile_routes

# Tüm routerları main routera ekle
router.include_router(auth_routes.router)
router.include_router(register_routes.router)
router.include_router(dashboard_routes.router)
router.include_router(subscriptions_routes.router)
router.include_router(measurements_routes.router)
router.include_router(finance_routes.router)
router.include_router(profile_routes.router)

__all__ = ['router']