"""
TikTrend Finder - API Gateway
FastAPI application entry point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import (
    auth, products, copy, license, webhooks, bot,
    whatsapp, chatwoot, instagram, tiktok, youtube, content, scheduler,
    integrations, social_auth, metrics, status_webhooks, checkout,
    analytics, templates, accounts, api_docs, marketplaces,
    subscription, analytics_social, chatbot, automation
)
from .middleware.ratelimit import RateLimitMiddleware
from .middleware.security import SecurityHeadersMiddleware
from .middleware.metrics import MetricsMiddleware
from .database.connection import init_database, close_database
from .utils.security import security_monitor
from .utils.integrity import IntegrityChecker
from shared.config import settings
from shared.sentry import sentry
from shared.storage import storage
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Sentry (before app creation)
if sentry.init():
    logger.info("🔍 Sentry monitoring enabled")
else:
    logger.info("⚠️ Sentry monitoring disabled (not configured)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Security Checks
    security_monitor.start()
    
    # Integrity Check
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    integrity = IntegrityChecker(base_path)
    if not integrity.verify_integrity():
        logger.warning(
            "Integrity check failed! Critical files may have been modified."
        )
        # In strict mode, we might want to exit:
        # os._exit(1)

    # Startup
    logger.info(f"🚀 Starting TikTrend API (env: {settings.ENVIRONMENT})")
    await init_database()
    
    # Log storage status
    if storage.is_configured:
        logger.info("📦 Cloudflare R2 storage enabled")
    else:
        logger.info("⚠️ Cloudflare R2 storage disabled (not configured)")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down TikTrend API")
    await close_database()
    security_monitor.stop()
    
    # Flush Sentry before exit
    if sentry.is_initialized:
        sentry.flush(timeout=2.0)


app = FastAPI(
    title="TikTrend Finder API",
    description="Backend API for TikTrend Finder desktop application",
    version="2.0.0",
    lifespan=lifespan,
)

# Security Middleware (Should be first)
app.add_middleware(SecurityHeadersMiddleware)

# Metrics Collection Middleware
app.add_middleware(MetricsMiddleware)

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
app.include_router(bot.router, tags=["Seller Bot (Premium)"])
app.include_router(whatsapp.router, prefix="/whatsapp", tags=["WhatsApp Automation"])
app.include_router(chatwoot.router, prefix="/chatwoot", tags=["Customer Support"])
app.include_router(instagram.router, prefix="/instagram", tags=["Instagram Automation"])
app.include_router(tiktok.router, prefix="/tiktok", tags=["TikTok Automation"])
app.include_router(youtube.router, prefix="/youtube", tags=["YouTube Automation"])
app.include_router(content.router, prefix="/content", tags=["Content Generator"])
app.include_router(
    scheduler.router, prefix="/scheduler", tags=["Post Scheduler"]
)
app.include_router(
    integrations.router,
    prefix="/integrations",
    tags=["n8n & Typebot Integrations"]
)
app.include_router(
    social_auth.router,
    prefix="/social-auth",
    tags=["Social Media OAuth"]
)
app.include_router(
    metrics.router,
    tags=["Observability"]
)
app.include_router(
    status_webhooks.router,
    prefix="/status",
    tags=["Status Webhooks"]
)
app.include_router(
    checkout.router,
    prefix="/checkout",
    tags=["Checkout & Payments"]
)
app.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["Analytics & Metrics"]
)
app.include_router(
    templates.router,
    prefix="/templates",
    tags=["Content Templates"]
)
app.include_router(
    accounts.router,
    prefix="/accounts",
    tags=["Multi-Account Management"]
)
app.include_router(
    api_docs.router,
    prefix="/api-docs",
    tags=["API Documentation"]
)
app.include_router(
    marketplaces.router,
    tags=["Marketplace Integrations"]
)

# New routes for monetization, analytics, chatbot, and automation
app.include_router(
    subscription.router,
    prefix="/subscription",
    tags=["Subscription & Plans"]
)
app.include_router(
    analytics_social.router,
    prefix="/analytics/social",
    tags=["Social Analytics"]
)
app.include_router(
    chatbot.router,
    prefix="/chatbot",
    tags=["Chatbot (Typebot)"]
)
app.include_router(
    automation.router,
    prefix="/automation",
    tags=["Automation (n8n)"]
)


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
