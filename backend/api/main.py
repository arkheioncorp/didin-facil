"""
TikTrend Finder - API Gateway
FastAPI application entry point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import auth, products, copy, license, webhooks
from .middleware.ratelimit import RateLimitMiddleware
from .middleware.security import SecurityHeadersMiddleware
from .database.connection import init_database, close_database
from .utils.security import security_monitor
from .utils.integrity import IntegrityChecker
from shared.config import settings
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Security Checks
    security_monitor.start()
    
    # Integrity Check
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    integrity = IntegrityChecker(base_path)
    if not integrity.verify_integrity():
        logger.warning("Integrity check failed! Critical files may have been modified.")
        # In strict mode, we might want to exit:
        # os._exit(1)

    # Startup
    await init_database()
    yield
    # Shutdown
    await close_database()
    security_monitor.stop()


app = FastAPI(
    title="TikTrend Finder API",
    description="Backend API for TikTrend Finder desktop application",
    version="2.0.0",
    lifespan=lifespan,
)

# Security Middleware (Should be first)
app.add_middleware(SecurityHeadersMiddleware)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(copy.router, prefix="/copy", tags=["AI Copy Generation"])
app.include_router(license.router, prefix="/license", tags=["License Management"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TikTrend Finder API",
        "docs": "/docs",
        "health": "/health"
    }
