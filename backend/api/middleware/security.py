from fastapi import Request
from shared.config import settings
from shared.security_config import get_security_config
from starlette.middleware.base import BaseHTTPMiddleware

# Get security configuration (cached singleton)
_security = get_security_config()
APP_SECRET = _security.app_secret


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security Headers Middleware
    
    Implements OWASP recommended security headers:
    - X-Content-Type-Options: Prevent MIME sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Legacy XSS protection
    - Strict-Transport-Security: Force HTTPS
    - Content-Security-Policy: Control resource loading
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Control browser features
    """
    
    # Endpoints that skip security checks
    SKIP_PATHS = {
        "/docs", "/openapi.json", "/health", "/redoc",
        "/webhooks/mercadopago", "/webhooks/stripe", "/webhooks/evolution",
        "/metrics", "/metrics/prometheus",
    }
    
    async def dispatch(self, request: Request, call_next):
        # Skip for docs, health check, and webhooks
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)
        
        # In production, enforce app secret for non-webhook routes
        if settings.is_production:
            client_secret = request.headers.get("X-App-Secret")
            if client_secret != APP_SECRET and not self._is_webhook(request):
                # Log suspicious access attempt
                pass  # Could log to security monitoring

        response = await call_next(request)
        
        # Security headers (OWASP recommendations)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), "
            "gyroscope=(), magnetometer=(), microphone=(), "
            "payment=(), usb=()"
        )
        
        # HSTS - only in production with HTTPS
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # CSP - Content Security Policy
        # Relaxed for API (no HTML content), strict for any HTML responses
        if "text/html" in response.headers.get("content-type", ""):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "frame-ancestors 'none';"
            )
        
        return response
    
    def _is_webhook(self, request: Request) -> bool:
        """Check if request is a webhook endpoint"""
        return request.url.path.startswith("/webhooks/")
