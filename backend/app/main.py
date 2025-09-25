"""
RetailXAI Dashboard Backend
FastAPI application with full observability and RBAC
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_client import make_asgi_app

from app.api import auth, audit, drafts, endpoints, health, jobs, settings
from app.core.config import settings as app_settings
from app.core.database import engine
from app.core.observability import setup_observability, instrument_fastapi
from app.core.middleware import LoggingMiddleware, SecurityHeadersMiddleware
from app.core.metrics import MetricsMiddleware, APP_INFO
from app.models import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting RetailXAI Dashboard Backend")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Setup observability
    setup_observability()
    
    # Set app info
    APP_INFO.info({
        'version': '1.0.0',
        'name': 'retailxai-dashboard',
        'environment': 'production'
    })
    
    yield
    
    # Shutdown
    logger.info("Shutting down RetailXAI Dashboard Backend")


# Create FastAPI app
app = FastAPI(
    title="RetailXAI Dashboard API",
    description="Backend API for RetailXAI Dashboard",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Add middleware (order matters - last added is first executed)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(MetricsMiddleware)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.github.io", "*.retailxai.com"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://retailxai.github.io",
        "https://retailxai.github.io/Precipice",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(drafts.router, prefix="/api/drafts", tags=["drafts"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(endpoints.router, prefix="/api/endpoints", tags=["endpoints"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])

# Add Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Instrument FastAPI for tracing
instrument_fastapi(app)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "RetailXAI Dashboard API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


@app.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
