"""
Rate Limiting Middleware
Request rate limiting per user/IP with granular endpoint limits.

Security features:
- Stricter limits for sensitive endpoints (auth, payments)
- Higher limits for read operations
- Per-endpoint rate limiting buckets
- Brute-force attack prevention
"""

import logging
import os
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Tuple

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limit per endpoint category."""
    requests: int
    window_seconds: int
    
    
# Rate limit configurations per endpoint category
RATE_LIMITS: Dict[str, RateLimitConfig] = {
    # Authentication - strict to prevent brute-force
    "auth": RateLimitConfig(requests=5, window_seconds=60),
    
    # Password operations - very strict
    "password": RateLimitConfig(requests=3, window_seconds=300),
    
    # Payment/webhooks - moderate
    "payment": RateLimitConfig(requests=20, window_seconds=60),
    
    # Write operations (POST/PUT/DELETE) - moderate
    "write": RateLimitConfig(requests=30, window_seconds=60),
    
    # Read operations (GET) - relaxed
    "read": RateLimitConfig(requests=120, window_seconds=60),
    
    # Search/scraping - prevent abuse
    "search": RateLimitConfig(requests=20, window_seconds=60),
    
    # Default fallback
    "default": RateLimitConfig(requests=60, window_seconds=60),
}

# Endpoint patterns for categorization
ENDPOINT_PATTERNS: list[Tuple[str, str]] = [
    # Auth endpoints - strict rate limiting
    (r"^/auth/login", "auth"),
    (r"^/auth/register", "auth"),
    (r"^/auth/token", "auth"),
    
    # Password operations - very strict
    (r"^/auth/password", "password"),
    (r"^/auth/reset", "password"),
    (r"^/auth/forgot", "password"),
    
    # Payment endpoints
    (r"^/webhooks?/", "payment"),
    (r"^/payment", "payment"),
    (r"^/subscription", "payment"),
    
    # Search/scraping endpoints
    (r"^/search", "search"),
    (r"^/scrape", "search"),
    (r"^/products/search", "search"),
]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory rate limiting middleware with granular endpoint limits.
    
    Security Features:
    - Stricter limits for authentication (prevents brute-force)
    - Very strict limits for password operations
    - Per-endpoint category rate limiting
    - Logging of rate limit violations
    
    For production with multiple instances, use Redis-based rate limiting.
    """
    
    def __init__(self, app, default_requests_per_minute: int = 60):
        super().__init__(app)
        self.default_limit = default_requests_per_minute
        # Bucket: {client_id:category: [timestamps]}
        self.request_counts: Dict[str, list] = defaultdict(list)
        self.testing = os.getenv("TESTING", "").lower() == "true"
        # Track blocked IPs for logging
        self.blocked_count: Dict[str, int] = defaultdict(int)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting in test environment
        if self.testing:
            return await call_next(request)
        
        # Skip rate limiting for health checks and docs
        skip_paths = {"/health", "/", "/docs", "/openapi.json", "/redoc"}
        if request.url.path in skip_paths:
            return await call_next(request)
        
        # Get client identifier and endpoint category
        client_id = self._get_client_id(request)
        category = self._get_endpoint_category(request)
        config = RATE_LIMITS.get(category, RATE_LIMITS["default"])
        
        # Create composite key for this client + category
        bucket_key = f"{client_id}:{category}"
        
        # Check rate limit
        current_time = time.time()
        window_start = current_time - config.window_seconds
        
        # Clean old requests
        self.request_counts[bucket_key] = [
            ts for ts in self.request_counts[bucket_key]
            if ts > window_start
        ]
        
        current_count = len(self.request_counts[bucket_key])
        
        # Check if limit exceeded
        if current_count >= config.requests:
            retry_after = int(config.window_seconds - (current_time - self.request_counts[bucket_key][0]))
            
            # Log rate limit violation (security event)
            self.blocked_count[client_id] += 1
            logger.warning(
                "rate_limit_exceeded",
                extra={
                    "client_id": client_id,
                    "category": category,
                    "path": request.url.path,
                    "method": request.method,
                    "blocked_count": self.blocked_count[client_id],
                    "limit": config.requests,
                    "window": config.window_seconds,
                }
            )
            
            # If repeated violations, return less info (anti-enumeration)
            if self.blocked_count[client_id] > 10:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"error": "Too many requests"},
                    headers={"Retry-After": str(retry_after)}
                )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded. Maximum {config.requests} requests per {config.window_seconds}s for this operation.",
                    "retry_after": retry_after,
                    "category": category,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(config.requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(window_start + config.window_seconds)),
                    "X-RateLimit-Category": category,
                }
            )
        
        # Record request
        self.request_counts[bucket_key].append(current_time)
        
        # Reset blocked count on successful request
        if client_id in self.blocked_count:
            self.blocked_count[client_id] = max(0, self.blocked_count[client_id] - 1)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = config.requests - len(self.request_counts[bucket_key])
        response.headers["X-RateLimit-Limit"] = str(config.requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(window_start + config.window_seconds))
        response.headers["X-RateLimit-Category"] = category
        
        return response
    
    def _get_endpoint_category(self, request: Request) -> str:
        """
        Categorize endpoint for rate limiting.
        Returns the category that determines rate limit config.
        """
        path = request.url.path.lower()
        
        # Check against patterns
        for pattern, category in ENDPOINT_PATTERNS:
            if re.match(pattern, path):
                return category
        
        # Fallback to method-based categorization
        if request.method == "GET":
            return "read"
        elif request.method in ("POST", "PUT", "PATCH", "DELETE"):
            return "write"
        
        return "default"
    
    def _get_client_id(self, request: Request) -> str:
        """
        Get unique client identifier.
        Uses user ID from JWT if available, otherwise IP address.
        
        Security: IP extraction handles X-Forwarded-For header properly.
        """
        # Try to get user ID from authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # Use hash of token to prevent token leakage in logs
            import hashlib
            token_hash = hashlib.sha256(auth_header[7:].encode()).hexdigest()[:16]
            return f"user:{token_hash}"
        
        # Fall back to IP address
        # Security: Only trust first IP in X-Forwarded-For (client IP)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # First IP is the original client
            client_ip = forwarded.split(",")[0].strip()
            return f"ip:{client_ip}"
        
        # Direct connection
        if request.client and request.client.host:
            return f"ip:{request.client.host}"
        
        return "ip:unknown"
