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
                     checkout, contact, content, copy, credits, crm, email,
                     favorites, instagram, integrations, license, marketplaces,
                     metrics, products, scheduler, scraper, seller_bot,
                     social_auth, status_webhooks, subscription,
                     template_library, templates, tiktok, tiktok_shop,
                     tiktok_shop_v2, users, webhooks, whatsapp, youtube)
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
    version="2.0.1",
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
app.include_router(contact.router, tags=["Contact & Support"])
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
    return {"status": "healthy", "version": "2.0.2"}


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
        
        # List all tables
        tables_result = await database.fetch_all(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )
        tables = [row["tablename"] for row in tables_result]
        
        # Try to count products if table exists
        product_count = 0
        if "products" in tables:
            count_result = await database.fetch_one(
                "SELECT COUNT(*) as count FROM products"
            )
            product_count = count_result["count"] if count_result else 0
        
        return {
            "status": "healthy" if "products" in tables else "needs_migration",
            "database": "connected",
            "tables": tables,
            "product_count": product_count,
            "database_url_set": bool(settings.DATABASE_URL),
            "database_url_preview": (
                settings.DATABASE_URL[:30] + "..."
                if settings.DATABASE_URL else None
            )
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()[-500:],
            "database_url_set": bool(settings.DATABASE_URL),
            "database_url_preview": (
                settings.DATABASE_URL[:30] + "..."
                if settings.DATABASE_URL else None
            )
        }


@app.post("/admin/init-db")
async def init_database_tables(secret: str = ""):
    """Initialize database with essential tables (emergency endpoint)"""
    from api.database.connection import database

    expected_secret = os.environ.get(
        "MIGRATION_SECRET", "tiktrend-migrate-2025"
    )
    if secret != expected_secret:
        return {"status": "error", "message": "Invalid secret"}

    try:
        if not database.is_connected:
            await database.connect()

        # Create alembic_version table first
        await database.execute("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """)

        # Create essential tables
        await database.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255),
                name VARCHAR(255),
                plan VARCHAR(50) NOT NULL DEFAULT 'free',
                is_active BOOLEAN DEFAULT true,
                is_admin BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await database.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tiktok_id VARCHAR(100) NOT NULL UNIQUE,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                price NUMERIC(10,2) NOT NULL,
                original_price NUMERIC(10,2),
                currency VARCHAR(10) DEFAULT 'BRL',
                category VARCHAR(100),
                seller_name VARCHAR(255),
                product_rating FLOAT,
                sales_count INTEGER DEFAULT 0,
                image_url VARCHAR(1000),
                product_url VARCHAR(1000) NOT NULL,
                is_trending BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await database.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id),
                license_key VARCHAR(50) NOT NULL UNIQUE,
                plan VARCHAR(50) NOT NULL,
                max_devices INTEGER DEFAULT 1,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Stamp alembic to latest migration
        await database.execute("""
            INSERT INTO alembic_version (version_num)
            VALUES ('db_polish_2025_12_04')
            ON CONFLICT (version_num) DO NOTHING
        """)

        return {
            "status": "success",
            "message": "Essential tables created and migration stamped"
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()[-1000:]
        }


@app.post("/admin/run-migrations")
async def run_migrations(secret: str = ""):
    """Run database migrations manually (emergency endpoint)"""
    import subprocess
    import traceback

    # Simple secret check (use settings.SECRET_KEY in production)
    expected_secret = os.environ.get(
        "MIGRATION_SECRET", "tiktrend-migrate-2025"
    )
    if secret != expected_secret:
        return {"status": "error", "message": "Invalid secret"}
    
    try:
        # Get the backend directory
        base_path = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
        
        # Run alembic upgrade in subprocess to avoid event loop conflict
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            cwd=base_path,
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "DATABASE_URL": settings.DATABASE_URL}
        )
        
        if result.returncode == 0:
            return {
                "status": "success",
                "message": "Migrations applied successfully",
                "output": result.stdout[-500:] if result.stdout else None
            }
        else:
            return {
                "status": "error",
                "message": "Migration failed",
                "stdout": result.stdout[-500:] if result.stdout else None,
                "stderr": result.stderr[-500:] if result.stderr else None
            }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Migration timed out after 120 seconds"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()[-1000:]
        }


@app.post("/admin/stamp-migrations")
async def stamp_migrations(secret: str = "", revision: str = "head"):
    """
    Mark migrations as applied without running them.
    Use when tables already exist in the database.
    """
    import subprocess
    import traceback

    expected_secret = os.environ.get(
        "MIGRATION_SECRET", "tiktrend-migrate-2025"
    )
    if secret != expected_secret:
        return {"status": "error", "message": "Invalid secret"}

    try:
        base_path = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        result = subprocess.run(
            ["alembic", "stamp", revision],
            capture_output=True,
            text=True,
            cwd=base_path,
            timeout=60,
            env={**os.environ, "DATABASE_URL": settings.DATABASE_URL}
        )

        if result.returncode == 0:
            return {
                "status": "success",
                "message": f"Stamped migrations at: {revision}",
                "output": result.stdout[-500:] if result.stdout else None
            }
        else:
            return {
                "status": "error",
                "message": "Stamp failed",
                "stdout": result.stdout[-500:] if result.stdout else None,
                "stderr": result.stderr[-500:] if result.stderr else None
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()[-500:]
        }


@app.get("/admin/db-tables")
async def list_database_tables(secret: str = ""):
    """List all tables in the database"""
    from api.database.connection import database

    expected_secret = os.environ.get(
        "MIGRATION_SECRET", "tiktrend-migrate-2025"
    )
    if secret != expected_secret:
        return {"status": "error", "message": "Invalid secret"}

    try:
        if not database.is_connected:
            await database.connect()

        result = await database.fetch_all("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        tables = [r["tablename"] for r in result]

        # Check alembic version
        try:
            version = await database.fetch_one(
                "SELECT version_num FROM alembic_version"
            )
            current_version = version["version_num"] if version else None
        except Exception:
            current_version = None

        return {
            "status": "success",
            "tables": tables,
            "table_count": len(tables),
            "alembic_version": current_version
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.post("/admin/seed-products")
async def seed_products(secret: str = "", count: int = 20):
    """Seed database with sample products for testing"""
    import random
    import uuid
    from datetime import datetime, timezone

    from api.database.connection import database

    expected_secret = os.environ.get(
        "MIGRATION_SECRET", "tiktrend-migrate-2025"
    )
    if secret != expected_secret:
        return {"status": "error", "message": "Invalid secret"}

    PRODUCTS = [
        ("Máscara de Cílios 4D Volume", "Beleza", 29.90, 15000),
        ("Sérum Vitamina C Clareador", "Beleza", 45.90, 12000),
        ("Fone Bluetooth TWS Pro", "Eletrônicos", 59.90, 25000),
        ("Ring Light Profissional 26cm", "Eletrônicos", 79.90, 18000),
        ("Organizador de Maquiagem Acrílico", "Casa", 49.90, 8000),
        ("Luz LED RGB Fita 5m", "Casa", 29.90, 22000),
        ("Bolsa Crossbody Mini Trendy", "Moda", 49.90, 11000),
        ("Óculos de Sol Vintage Retrô", "Moda", 39.90, 9000),
        ("Kit Faixa Elástica Fitness", "Fitness", 34.90, 14000),
        ("Garrafa Motivacional 2L", "Fitness", 24.90, 20000),
        ("Massageador Facial Elétrico", "Beleza", 69.90, 7500),
        ("Carregador Wireless 15W Rápido", "Eletrônicos", 39.90, 16000),
        ("Umidificador de Ar Aroma", "Casa", 59.90, 13000),
        ("Tênis Chunky Branco", "Moda", 119.90, 6000),
        ("Rolo Massageador Muscular", "Fitness", 29.90, 10000),
        ("Lip Gloss Hidratante Glossy", "Beleza", 19.90, 28000),
        ("Microfone USB Condensador", "Eletrônicos", 89.90, 5500),
        ("Espelho LED Aumento 10x", "Casa", 44.90, 9500),
        ("Bucket Hat Unissex Trend", "Moda", 24.90, 17000),
        ("Corda de Pular Profissional", "Fitness", 19.90, 21000),
        ("Kit Skincare Coreano 7 Steps", "Beleza", 129.90, 8500),
        ("Smartwatch Fitness Pro", "Eletrônicos", 149.90, 12000),
        ("Luminária Moon 3D", "Casa", 54.90, 15500),
        ("Jaqueta Corta Vento Unissex", "Moda", 79.90, 9800),
        ("Tapete Yoga Antiderrapante", "Fitness", 49.90, 11200),
    ]

    try:
        if not database.is_connected:
            await database.connect()

        inserted = 0
        for title, category, price, sales in PRODUCTS[:count]:
            product_id = str(uuid.uuid4())
            tiktok_id = f"TT{uuid.uuid4().hex[:12].upper()}"
            try:
                await database.execute(
                    """
                    INSERT INTO products (id, tiktok_id, title, description, price, 
                        original_price, currency, category, seller_name, 
                        product_rating, reviews_count, sales_count, sales_7d, sales_30d,
                        commission_rate, image_url, product_url, has_free_shipping, is_trending)
                    VALUES (:id, :tiktok_id, :title, :desc, :price, 
                        :original_price, :currency, :category, :seller_name,
                        :rating, :reviews, :sales, :sales_7d, :sales_30d,
                        :commission, :image_url, :product_url, :free_shipping, :is_trending)
                    """,
                    {
                        "id": product_id,
                        "tiktok_id": tiktok_id,
                        "title": title,
                        "desc": f"{title} - Produto viral do TikTok com milhares de vendas!",
                        "price": price,
                        "original_price": round(price * 1.3, 2),
                        "currency": "BRL",
                        "category": category,
                        "seller_name": f"TikTok Seller {random.randint(100, 999)}",
                        "rating": round(random.uniform(4.0, 5.0), 1),
                        "reviews": random.randint(100, 5000),
                        "sales": sales + random.randint(-1000, 1000),
                        "sales_7d": random.randint(100, 2000),
                        "sales_30d": random.randint(500, 8000),
                        "commission": round(random.uniform(5.0, 15.0), 1),
                        "image_url": f"https://placehold.co/400x400?text={title[:10].replace(' ', '+')}",
                        "product_url": f"https://tiktok.com/shop/product/{tiktok_id}",
                        "free_shipping": random.choice([True, False]),
                        "is_trending": random.choice([True, True, False]),
                    }
                )
                inserted += 1
            except Exception as e:
                logger.warning(f"Skip duplicate: {title} - {e}")

        # Get total count
        count_result = await database.fetch_one(
            "SELECT COUNT(*) as total FROM products"
        )
        total = count_result["total"] if count_result else 0

        return {
            "status": "success",
            "inserted": inserted,
            "total_products": total
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()[-500:]
        }


@app.get("/admin/products-schema")
async def get_products_schema(secret: str = ""):
    """Get products table schema for debugging"""
    from api.database.connection import database
    
    expected_secret = os.environ.get(
        "MIGRATION_SECRET", "tiktrend-migrate-2025"
    )
    if secret != expected_secret:
        return {"status": "error", "message": "Invalid secret"}
    
    try:
        if not database.is_connected:
            await database.connect()
        
        columns = await database.fetch_all(
            """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'products'
            ORDER BY ordinal_position
            """
        )
        
        return {
            "status": "success",
            "columns": [dict(c) for c in columns]
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()[-500:]
        }


@app.post("/admin/test-insert")
async def test_single_insert(secret: str = ""):
    """Test a single product insert with detailed error"""
    import uuid

    from api.database.connection import database
    
    expected_secret = os.environ.get(
        "MIGRATION_SECRET", "tiktrend-migrate-2025"
    )
    if secret != expected_secret:
        return {"status": "error", "message": "Invalid secret"}
    
    try:
        if not database.is_connected:
            await database.connect()
        
        product_id = str(uuid.uuid4())
        tiktok_id = f"TT{uuid.uuid4().hex[:12].upper()}"
        
        await database.execute(
            """
            INSERT INTO products (id, tiktok_id, title, description, price, 
                product_url, category, sales_count)
            VALUES (:id, :tiktok_id, :title, :desc, :price, 
                :product_url, :category, :sales)
            """,
            {
                "id": product_id,
                "tiktok_id": tiktok_id,
                "title": "Test Product",
                "desc": "Test description",
                "price": 29.90,
                "product_url": f"https://tiktok.com/shop/product/{tiktok_id}",
                "category": "Test",
                "sales": 1000,
            }
        )
        
        return {
            "status": "success",
            "message": f"Inserted product {product_id}",
            "tiktok_id": tiktok_id
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TikTrend Finder API",
        "docs": "/docs",
        "health": "/health"
    }
