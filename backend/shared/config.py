"""
Application Configuration
Environment variables and settings

Detecta automaticamente se está rodando em Docker e usa URLs internas.
"""

import os
from typing import Optional

from pydantic import ConfigDict, field_validator
from pydantic_settings import BaseSettings


def _is_docker() -> bool:
    """Detecta se está rodando dentro de um container Docker"""
    return os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER", "") == "true"


# Define URLs baseadas no ambiente
_IN_DOCKER = _is_docker()

# URLs internas do Docker (rede tiktrend-network)
_DOCKER_URLS = {
    "database": "postgresql://tiktrend:tiktrend_dev@postgres:5432/tiktrend",
    "redis": "redis://redis:6379/0",
    "evolution": "http://evolution-api:8080",
    "chatwoot": "http://chatwoot:3000",
    "n8n": "http://n8n:5678",
    "api": "http://tiktrend-api:8000",
}

# URLs externas (localhost para desenvolvimento local)
_LOCAL_URLS = {
    "database": "postgresql://tiktrend:tiktrend_dev@localhost:5434/tiktrend",
    "redis": "redis://localhost:6379/0",
    "evolution": "http://localhost:8082",
    "chatwoot": "http://localhost:3000",
    "n8n": "http://localhost:5678",
    "api": "http://localhost:8000",
}

_URLS = _DOCKER_URLS if _IN_DOCKER else _LOCAL_URLS


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    IN_DOCKER: bool = _IN_DOCKER
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_URL: str = _URLS["api"]
    APP_URL: str = "http://localhost:1420"
    
    # Security
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_HOURS: int = 12
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Database
    DATABASE_URL: str = _URLS["database"]
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_postgres_url(cls, v: str) -> str:
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v
    
    # Redis
    REDIS_URL: str = _URLS["redis"]
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_MAX_TOKENS: int = 1000
    
    # Mercado Pago
    MERCADO_PAGO_ACCESS_TOKEN: Optional[str] = None
    MERCADO_PAGO_WEBHOOK_SECRET: Optional[str] = None
    MERCADOPAGO_ACCESS_TOKEN: Optional[str] = None
    MERCADOPAGO_PUBLIC_KEY: Optional[str] = None
    MERCADOPAGO_WEBHOOK_SECRET: Optional[str] = None
    
    # Mercado Pago Sandbox (para testes)
    MERCADOPAGO_SANDBOX_TOKEN: Optional[str] = None
    MERCADOPAGO_USE_SANDBOX: bool = False
    
    # Scraper
    SCRAPER_RATE_LIMIT: int = 5  # requests per second
    SCRAPER_RETRY_COUNT: int = 3
    PROXY_POOL_URL: Optional[str] = None
    
    # Evolution API (WhatsApp)
    EVOLUTION_API_URL: str = _URLS["evolution"]
    EVOLUTION_API_KEY: str = "429683C4C977415CAAFCCE10F7D57E11"
    EVOLUTION_INSTANCE: str = "didin-whatsapp"
    EVOLUTION_WEBHOOK_URL: str = f"{_URLS['api']}/webhooks/evolution"
    
    # Chatwoot (Customer Support)
    CHATWOOT_API_URL: str = _URLS["chatwoot"]
    CHATWOOT_ACCESS_TOKEN: Optional[str] = None
    CHATWOOT_ACCOUNT_ID: int = 1
    
    # n8n Integration
    N8N_API_URL: str = _URLS["n8n"]
    N8N_API_KEY: Optional[str] = None
    N8N_WEBHOOK_URL: str = f"{_URLS['n8n']}/webhook"
    N8N_WEBHOOK_SECRET: Optional[str] = None  # For webhook auth
    
    # General Webhook Security
    WEBHOOK_SECRET: Optional[str] = None  # Fallback for all webhooks
    
    # Typebot Integration
    TYPEBOT_API_URL: Optional[str] = None
    TYPEBOT_API_KEY: Optional[str] = None
    TYPEBOT_PUBLIC_ID: Optional[str] = None
    
    # Social Media OAuth
    INSTAGRAM_CLIENT_ID: Optional[str] = None
    INSTAGRAM_CLIENT_SECRET: Optional[str] = None
    TIKTOK_CLIENT_KEY: Optional[str] = None
    TIKTOK_CLIENT_SECRET: Optional[str] = None
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None  # Para YouTube Data API
    
    # TikTok Shop API (Partner Center)
    TIKTOK_SHOP_APP_KEY: Optional[str] = None
    TIKTOK_SHOP_APP_SECRET: Optional[str] = None
    TIKTOK_SHOP_SERVICE_ID: Optional[str] = None
    
    # Instagram Credentials
    INSTAGRAM_USERNAME: Optional[str] = None
    INSTAGRAM_PASSWORD: Optional[str] = None
    
    # Data Directory
    DATA_DIR: str = "data"
    
    # CDN / Storage
    CDN_URL: str = "https://cdn.tiktrend.app"
    R2_BUCKET_NAME: str = "tiktrend-images"
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_ENDPOINT: Optional[str] = None
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    POSTHOG_API_KEY: Optional[str] = None
    
    # Hub Alerts - Notification Webhooks
    SLACK_WEBHOOK_URL: Optional[str] = None
    DISCORD_WEBHOOK_URL: Optional[str] = None
    ALERT_WEBHOOK_URL: Optional[str] = None
    ALERT_DEDUP_WINDOW: int = 300  # 5 minutes
    ALERT_MAX_PER_MINUTE: int = 10
    
    # Email / SMTP
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    SMTP_TLS: bool = True
    
    # Resend (alternative email service)
    RESEND_API_KEY: Optional[str] = None
    
    # Contact & Support Configuration
    SUPPORT_EMAIL: str = "suporte@didinfacil.com.br"
    CONTACT_EMAIL: str = "contato@didinfacil.com.br"
    NOREPLY_EMAIL: str = "noreply@didinfacil.com.br"
    COMPANY_NAME: str = "Didin Fácil"
    COMPANY_WEBSITE: str = "https://didinfacil.com.br"
    COMPANY_ADDRESS: str = "São Paulo, Brasil"
    
    # MercadoPago (alias for compatibility)
    MP_ACCESS_TOKEN: Optional[str] = None
    MP_PUBLIC_KEY: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:1420,http://localhost:3000,tauri://localhost,https://didin-facil.vercel.app"
    CORS_ORIGIN_REGEX: Optional[str] = r"https://.*\.vercel\.app"
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @property
    def database(self):
        class DBConfig:
            url = self.DATABASE_URL
            min_connections = self.DATABASE_POOL_SIZE
            max_connections = self.DATABASE_POOL_SIZE + self.DATABASE_MAX_OVERFLOW
            host = self.DATABASE_URL.split("@")[1].split(":")[0] if "@" in self.DATABASE_URL else "localhost"
            port = self.DATABASE_URL.split(":")[2].split("/")[0] if ":" in self.DATABASE_URL and "/" in self.DATABASE_URL else "5432"
            name = self.DATABASE_URL.split("/")[-1] if "/" in self.DATABASE_URL else "tiktrend"
        return DBConfig()

    @property
    def redis(self):
        class RedisConfig:
            url = self.REDIS_URL
            host = self.REDIS_URL.split("//")[1].split(":")[0] if "//" in self.REDIS_URL else "localhost"
            port = self.REDIS_URL.split(":")[2].split("/")[0] if ":" in self.REDIS_URL and "/" in self.REDIS_URL else "6379"
        return RedisConfig()

    @property
    def cors_origins_list(self) -> list:
        """Parse CORS origins as list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT == "development"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance (for dependency injection compatibility)"""
    return settings
