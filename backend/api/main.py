"""
TikTrend Finder - API Gateway
FastAPI application entry point
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.config import settings
from shared.redis import close_redis, init_redis
from shared.sentry import sentry
from shared.storage import storage

from .database.connection import close_database, init_database
from .middleware.metrics import MetricsMiddleware
from .middleware.ratelimit import RateLimitMiddleware
from .middleware.security import SecurityHeadersMiddleware
from .routers import crm_advanced  # CRM Advanced Services
from .routes import hub_health  # Hub monitoring & health checks
from .routes import \
    websocket_notifications  # WebSocket real-time notifications
from .routes import whatsapp_analytics  # WhatsApp Analytics API
from .routes import whatsapp_chatbot  # WhatsApp Chatbot routes
from .routes import whatsapp_v2  # WhatsApp Hub V2 routes
from .routes import whatsapp_webhook  # WhatsApp Real Webhook (Evolution API)
from .routes import (accounting, accounts,  # New financial routes + favorites
                     analytics, analytics_social, api_docs, auth, automation,
                     automation_dashboard, bot, campaigns, chatbot, chatwoot,
                     checkout, content, copy, credits, crm, email, favorites,
                     instagram, integrations, license, marketplaces, metrics,
                     products, scheduler, scraper, seller_bot, social_auth,
                     status_webhooks, subscription, template_library,
                     templates, tiktok, tiktok_shop, tiktok_shop_v2, users,
                     webhooks, whatsapp, youtube)
from .utils.integrity import IntegrityChecker
from .utils.security import security_monitor

# Automation scheduler imports
try:
    from modules.automation import (get_orchestrator, start_scheduler,
                                    stop_scheduler)
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False

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

    # Run database migrations on startup
    logger.info("📦 Running database migrations...")
    try:
        from alembic import command
        from alembic.config import Config
        
        alembic_cfg = Config(os.path.join(base_path, "alembic.ini"))
        alembic_cfg.set_main_option(
            "script_location", 
            os.path.join(base_path, "alembic")
        )
        
        # Set the database URL
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        
        command.upgrade(alembic_cfg, "head")
        logger.info("✅ Database migrations applied successfully")
    except Exception as e:
        logger.error(f"⚠️ Migration error (may be already up to date): {e}")

    # Startup
    logger.info(f"🚀 Starting TikTrend API (env: {settings.ENVIRONMENT})")
    logger.info(f"🔌 PORT env var: {os.environ.get('PORT', 'Not Set')}")
    try:
        await init_database()
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    try:
        await init_redis()
        logger.info("🔴 Redis initialized")
    except Exception as e:
        logger.error(f"❌ Redis initialization failed: {e}")
    
    # Log storage status
    if storage.is_configured:
        logger.info("📦 Cloudflare R2 storage enabled")
    else:
        logger.info("⚠️ Cloudflare R2 storage disabled (not configured)")
    
    # Start automation scheduler
    if SCHEDULER_AVAILABLE:
        try:
            orchestrator = get_orchestrator()
            await start_scheduler(orchestrator)
            logger.info("🤖 Automation scheduler started")
        except Exception as e:
            logger.warning(f"⚠️ Automation scheduler failed to start: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down TikTrend API")
    
    # Stop automation scheduler
    if SCHEDULER_AVAILABLE:
        try:
            await stop_scheduler()
            logger.info("🤖 Automation scheduler stopped")
        except Exception as e:
            logger.warning(f"⚠️ Error stopping scheduler: {e}")
    
    await close_database()
    await close_redis()
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
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(favorites.router, prefix="/favorites", tags=["Favorites"])
app.include_router(copy.router, prefix="/copy", tags=["AI Copy Generation"])
app.include_router(license.router, prefix="/license", tags=["License"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(bot.router, tags=["Seller Bot (Premium)"])
app.include_router(whatsapp.router, prefix="/whatsapp", tags=["WhatsApp"])
app.include_router(chatwoot.router, prefix="/chatwoot", tags=["Support"])
app.include_router(instagram.router, prefix="/instagram", tags=["Instagram"])
app.include_router(tiktok.router, prefix="/tiktok", tags=["TikTok"])
app.include_router(youtube.router, prefix="/youtube", tags=["YouTube"])
app.include_router(content.router, prefix="/content", tags=["Content"])
app.include_router(scraper.router, prefix="/scraper", tags=["Scraper"])
app.include_router(
    scheduler.router, prefix="/scheduler", tags=["Scheduler"]
)
app.include_router(
    integrations.router,
    prefix="/integrations",
    tags=["n8n & Typebot"]
)
app.include_router(
    social_auth.router,
    prefix="/social-auth",
    tags=["Social Media OAuth"]
)
app.include_router(
    tiktok_shop.router,
    prefix="/tiktok-shop",
    tags=["TikTok Shop API"]
)
app.include_router(
    tiktok_shop_v2.router,
    prefix="/tiktok-shop-v2",
    tags=["TikTok Shop V2"]
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
    tags=["Checkout"]
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
# SaaS Hybrid Subscription System
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
app.include_router(
    automation_dashboard.router,
    prefix="/automation/dashboard",
    tags=["Automation Dashboard"]
)
app.include_router(
    template_library.router,
    prefix="/templates/library",
    tags=["Template Library"]
)

# Email Marketing routes
app.include_router(
    email.router,
    prefix="/email",
    tags=["Email Marketing"]
)
app.include_router(
    campaigns.router,
    prefix="/campaigns",
    tags=["Email Campaigns"]
)

# CRM routes
app.include_router(
    crm.router,
    prefix="/crm",
    tags=["CRM"]
)

# CRM Advanced Services (Risk Detection, Next Best Action, Workflows)
app.include_router(crm_advanced.router)

# Professional Seller Bot
app.include_router(
    seller_bot.router,
    tags=["Professional Seller Bot"]
)

# Accounting & Credits (Financial)
app.include_router(
    accounting.router,
    prefix="/admin/accounting",
    tags=["Admin Accounting"]
)
app.include_router(
    credits.router,
    prefix="/credits",
    tags=["Credits Purchase"]
)

# Hub Monitoring & Health Checks
app.include_router(
    hub_health.router,
    tags=["Hub Monitoring"]
)

# WhatsApp Hub V2 (Evolution API Integration)
app.include_router(
    whatsapp_v2.router,
    prefix="/api",
    tags=["WhatsApp Hub V2"]
)

# WhatsApp Chatbot (Bot Logic)
app.include_router(
    whatsapp_chatbot.router,
    prefix="/api",
    tags=["WhatsApp Chatbot"]
)

# WhatsApp Real Webhook (Evolution API Integration)
app.include_router(
    whatsapp_webhook.router,
    prefix="/api",
    tags=["WhatsApp Webhook"]
)

# WhatsApp Analytics API
app.include_router(
    whatsapp_analytics.router,
    prefix="/api",
    tags=["WhatsApp Analytics"]
)

# WebSocket Real-time Notifications
app.include_router(
    websocket_notifications.router,
    tags=["WebSocket Notifications"]
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/health/db")
async def health_check_db():
    """Database health check endpoint"""
    import traceback

    from api.database.connection import database
    from shared.config import settings
    
    try:
        # Check if database is connected
        if not database.is_connected:
            await database.connect()
        
        # Simple query to test connection
        result = await database.fetch_one("SELECT 1 as test")
        
        # Count products
        count_result = await database.fetch_one("SELECT COUNT(*) as count FROM products")
        product_count = count_result["count"] if count_result else 0
        
        return {
            "status": "healthy",
            "database": "connected",
            "product_count": product_count,
            "database_url_set": bool(settings.DATABASE_URL),
            "database_url_preview": settings.DATABASE_URL[:30] + "..." if settings.DATABASE_URL else None
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()[-500:],
            "database_url_set": bool(settings.DATABASE_URL),
            "database_url_preview": settings.DATABASE_URL[:30] + "..." if settings.DATABASE_URL else None
        }


@app.post("/admin/run-migrations")
async def run_migrations(secret: str = ""):
    """Run database migrations manually (emergency endpoint)"""
    import traceback

    # Simple secret check (use settings.SECRET_KEY in production)
    expected_secret = os.environ.get(
        "MIGRATION_SECRET", "tiktrend-migrate-2025"
    )
    if secret != expected_secret:
        return {"status": "error", "message": "Invalid secret"}
    
    try:
        from alembic import command
        from alembic.config import Config
        
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alembic_cfg = Config(os.path.join(base_path, "alembic.ini"))
        alembic_cfg.set_main_option(
            "script_location",
            os.path.join(base_path, "alembic")
        )
        
        # Set the database URL (sync version for alembic)
        db_url = settings.DATABASE_URL
        # Alembic needs sync driver, not asyncpg
        if "+asyncpg" in db_url:
            db_url = db_url.replace("+asyncpg", "")
        
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        
        command.upgrade(alembic_cfg, "head")
        
        return {
            "status": "success",
            "message": "Migrations applied successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()[-1000:]
        }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TikTrend Finder API",
        "docs": "/docs",
        "health": "/health"
    }
