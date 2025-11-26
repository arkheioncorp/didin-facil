from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import os
import secrets

# Generate a session secret if not provided (fallback)
# In production, this should be passed from the Tauri app via env vars
APP_SECRET = os.getenv("APP_SECRET", "default-insecure-secret")

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Verify internal request signature/secret
        # This ensures requests come from the Tauri app (which knows the secret)
        # and not from external tools (unless they extract the secret)
        
        # Skip for docs and health check
        if request.url.path in ["/docs", "/openapi.json", "/health"]:
            return await call_next(request)

        # Check for the secret header
        # The frontend must send 'X-App-Secret' matching the env var
        # For now, we'll make it optional to avoid breaking dev flow immediately,
        # but in "heavy security" mode it should be mandatory.
        
        # Uncomment to enforce:
        # client_secret = request.headers.get("X-App-Secret")
        # if client_secret != APP_SECRET:
        #     raise HTTPException(status_code=403, detail="Access Denied")

        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
