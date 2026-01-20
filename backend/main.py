from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import logging
import warnings
from urllib.parse import quote
from sqlalchemy.exc import SAWarning

from backend.api.api import api_router
from backend.web.router import router as web_router
from backend.core.init_db import init_db
from backend.core.scheduler import UserActivityScheduler
from backend.core.config import settings

# Configure logging to reduce verbosity
logging.basicConfig(
    level=logging.WARNING,  # Only show WARNING and above
    format='%(levelname)s: %(name)s: %(message)s'
)

# Completely disable SQLAlchemy logging by using null handler
class NullHandler(logging.Handler):
    def emit(self, record):
        pass

null_handler = NullHandler()
logging.getLogger('sqlalchemy').addHandler(null_handler)
logging.getLogger('sqlalchemy').setLevel(logging.CRITICAL)
logging.getLogger('sqlalchemy.engine').addHandler(null_handler)
logging.getLogger('sqlalchemy.engine').setLevel(logging.CRITICAL)
logging.getLogger('sqlalchemy.pool').addHandler(null_handler)
logging.getLogger('sqlalchemy.pool').setLevel(logging.CRITICAL)
logging.getLogger('sqlalchemy.dialects').addHandler(null_handler)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.CRITICAL)
logging.getLogger('sqlalchemy.orm').addHandler(null_handler)
logging.getLogger('sqlalchemy.orm').setLevel(logging.CRITICAL)

# Reduce APScheduler verbosity
logging.getLogger('apscheduler').setLevel(logging.WARNING)

# Suppress SQLAlchemy warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sqlalchemy")
warnings.filterwarnings("ignore", category=SAWarning, module="sqlalchemy")

# Global scheduler instance
scheduler = UserActivityScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await init_db()
        scheduler.start()
    except Exception as exc:
        # Log full traceback so we can see exact startup failure in production logs
        logging.exception("Unhandled exception during application startup:")
        # Re-raise so process exit / restart behavior remains unchanged
        raise

    yield

    # Shutdown
    try:
        scheduler.stop()
    except Exception:
        logging.exception("Exception during scheduler shutdown:")

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None
)

# CORS settings - Desktop app için gerekli
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_router)
app.include_router(web_router)


@app.get("/")
async def root(request: Request):
    """
    Kök dizin yönlendirmesi.
    Eğer mobil cihazdan ve In-App (Instagram vb.) veya Safari tarayıcıdan geliniyorsa 
    QR Bridge sayfasına yönlendirerek Chrome'u zorlar.
    """
    user_agent = request.headers.get("user-agent", "").lower()
    target_url = "/web/auth/login"
    
    # Mobil cihaz kontrolü (Genel)
    is_mobile = "mobile" in user_agent or "android" in user_agent or "iphone" in user_agent
    
    # Sadece mobilde bu zorlamayı yapıyoruz
    if is_mobile:
        # Chrome kontrolü (Android'de 'chrome', iOS'ta 'crios')
        # DİKKAT: Samsung, Edge, Opera vb. Android tarayıcıları da "Chrome" stringini içerir.
        # Bu yüzden "Gerçek Chrome" olduğunu anlamak için diğerlerini dışlamalıyız.
        has_chrome_token = "chrome" in user_agent or "crios" in user_agent
        
        excluded_browsers = ["samsungbrowser", "edga", "opr", "miuibrowser", "ucbrowser", "yabrowser"]
        is_generic_browser = any(browser in user_agent for browser in excluded_browsers)
        
        is_real_chrome = has_chrome_token and not is_generic_browser
        
        # Safari kontrolü (Chrome olmayan Safari)
        # Not: Chrome on iOS (CriOS) da 'Safari' stringini içerir, bu yüzden 'is_real_chrome' false olmalı.
        is_safari = "safari" in user_agent and not is_real_chrome and not "android" in user_agent
        
        # In-App Browser tespiti (Instagram, Facebook, WhatsApp vb.)
        in_app_keywords = ["instagram", "fbav", "fban", "line", "twitter", "linkedin", "discord", "wv", "whatsapp"]
        is_in_app = any(keyword in user_agent for keyword in in_app_keywords)
        
        # Eğer uygulama içi tarayıcıdaysa VEYA Safari/Samsung/Edge vb. ise -> Chrome'a zorla
        # Yani: Gerçek Chrome DEĞİLSE yönlendir.
        if not is_real_chrome:
            # Hedef URL'yi encode edip bridge'e gönderiyoruz
            encoded_target = quote(target_url)
            return RedirectResponse(url=f"/web/qr-bridge?target={encoded_target}", status_code=307)
            
    # Diğer tüm durumlarda (Desktop, Mobile Chrome vb.) direkt login'e git
    return RedirectResponse(url=target_url, status_code=307)

