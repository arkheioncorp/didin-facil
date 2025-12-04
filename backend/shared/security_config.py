"""
Security Configuration
======================
Centralized security configuration with proper secret handling.

This module ensures that:
1. Secrets are never hardcoded in production
2. Development mode has safe defaults
3. Missing secrets in production cause immediate failure
"""

import logging
import os
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)


class SecurityConfigError(Exception):
    """Raised when security configuration is invalid."""
    pass


class SecurityConfig:
    """
    Centralized security configuration.
    
    Usage:
        from shared.security_config import get_security_config
        
        config = get_security_config()
        jwt_secret = config.jwt_secret_key
    """
    
    def __init__(self):
        self._environment = os.environ.get("ENVIRONMENT", "development")
        self._is_production = self._environment == "production"
        self._is_testing = os.environ.get("TESTING", "").lower() == "true"
        
        # Validate required secrets in production
        if self._is_production:
            self._validate_production_secrets()
    
    def _validate_production_secrets(self) -> None:
        """Ensure all required secrets are configured in production."""
        required_secrets = [
            "JWT_SECRET_KEY",
            "DATABASE_URL",
        ]
        
        missing = [s for s in required_secrets if not os.environ.get(s)]
        
        if missing:
            raise SecurityConfigError(
                f"Missing required secrets in production: {', '.join(missing)}"
            )
    
    @property
    def environment(self) -> str:
        """Current environment (development, staging, production)."""
        return self._environment
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self._is_production
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self._environment == "development"
    
    @property
    def is_testing(self) -> bool:
        """Check if running tests."""
        return self._is_testing
    
    @property
    def jwt_secret_key(self) -> str:
        """
        JWT secret key for token signing.
        
        In production: Must be set via environment variable.
        In development: Uses a development-only key.
        In testing: Uses a test-only key.
        """
        if self._is_testing:
            return "test-secret-key-for-testing-only-12345"
        
        env_secret = os.environ.get("JWT_SECRET_KEY")
        
        if env_secret:
            return env_secret
        
        if self._is_production:
            raise SecurityConfigError(
                "JWT_SECRET_KEY is required in production. "
                "Set it via environment variable."
            )
        
        # Development fallback - log warning
        logger.warning(
            "⚠️ Using development JWT secret. "
            "Set JWT_SECRET_KEY for production."
        )
        return "dev-only-jwt-secret-not-for-production-use"
    
    @property
    def jwt_algorithm(self) -> str:
        """JWT signing algorithm."""
        return os.environ.get("JWT_ALGORITHM", "HS256")
    
    @property
    def jwt_expiration_hours(self) -> int:
        """JWT token expiration in hours."""
        return int(os.environ.get("JWT_EXPIRATION_HOURS", "12"))
    
    @property
    def app_secret(self) -> Optional[str]:
        """
        Application secret for internal request validation.
        
        Optional in development, recommended in production.
        """
        secret = os.environ.get("APP_SECRET")
        
        if not secret and self._is_production:
            logger.warning(
                "⚠️ APP_SECRET not set in production. "
                "Internal request validation may be weakened."
            )
        
        return secret
    
    @property
    def encryption_key(self) -> Optional[str]:
        """
        Encryption key for sensitive data at rest.
        
        Used for encrypting stored credentials, tokens, etc.
        """
        return os.environ.get("ENCRYPTION_KEY")
    
    @property
    def cors_origins(self) -> list[str]:
        """Allowed CORS origins."""
        origins = os.environ.get(
            "CORS_ORIGINS",
            "http://localhost:1420,http://localhost:5173,tauri://localhost"
        )
        return [o.strip() for o in origins.split(",") if o.strip()]
    
    @property
    def rate_limit_enabled(self) -> bool:
        """Check if rate limiting is enabled."""
        return os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
    
    @property
    def rate_limit_per_minute(self) -> int:
        """Default rate limit per minute per IP."""
        return int(os.environ.get("RATE_LIMIT_PER_MINUTE", "60"))
    
    def __repr__(self) -> str:
        return (
            f"SecurityConfig("
            f"environment={self._environment}, "
            f"is_production={self._is_production})"
        )


@lru_cache(maxsize=1)
def get_security_config() -> SecurityConfig:
    """
    Get cached security configuration instance.
    
    Returns:
        SecurityConfig: Singleton security configuration.
    
    Example:
        config = get_security_config()
        print(config.jwt_secret_key)
    """
    return SecurityConfig()


# Convenience exports
def get_jwt_secret() -> str:
    """Get JWT secret key."""
    return get_security_config().jwt_secret_key


def get_jwt_algorithm() -> str:
    """Get JWT algorithm."""
    return get_security_config().jwt_algorithm


def is_production() -> bool:
    """Check if running in production."""
    return get_security_config().is_production
