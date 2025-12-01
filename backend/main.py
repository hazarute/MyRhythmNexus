from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import warnings
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
    await init_db()
    scheduler.start()

    yield

    # Shutdown
    scheduler.stop()

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
async def root():
    return {"message": f"{settings.PROJECT_NAME} backend is healthy", "environment": settings.ENVIRONMENT}
