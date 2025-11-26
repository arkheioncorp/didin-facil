"""
Application Configuration
Environment variables and settings
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_URL: str = "http://localhost:8000"
    APP_URL: str = "http://localhost:1420"
    
    # Security
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_HOURS: int = 12
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Database
    DATABASE_URL: str = "postgresql://tiktrend:tiktrend_dev@localhost:5432/tiktrend"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
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
    
    # Scraper
    SCRAPER_RATE_LIMIT: int = 5  # requests per second
    SCRAPER_RETRY_COUNT: int = 3
    PROXY_POOL_URL: Optional[str] = None
    
    # CDN / Storage
    CDN_URL: str = "https://cdn.tiktrend.app"
    R2_BUCKET_NAME: str = "tiktrend-images"
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_ENDPOINT: Optional[str] = None
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    POSTHOG_API_KEY: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: str = "tauri://localhost,http://localhost:1420,http://localhost:5173"
    FRONTEND_URL: str = "http://localhost:5173"
    API_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

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
