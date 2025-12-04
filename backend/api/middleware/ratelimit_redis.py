"""
Redis-based Rate Limiting Middleware
Distributed rate limiting for multi-instance deployments.

Uses Redis for storing rate limit counters, enabling consistent
rate limiting across multiple API instances.
"""

import hashlib
import logging
import os
import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

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
    (r"^/auth/login", "auth"),
    (r"^/auth/register", "auth"),
    (r"^/auth/token", "auth"),
    (r"^/auth/password", "password"),
    (r"^/auth/reset", "password"),
    (r"^/auth/forgot", "password"),
    (r"^/webhooks?/", "payment"),
    (r"^/payment", "payment"),
    (r"^/subscription", "payment"),
    (r"^/search", "search"),
    (r"^/scrape", "search"),
    (r"^/products/search", "search"),
]


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis-based rate limiting middleware with granular endpoint limits.
    
    Benefits over in-memory:
    - Works with multiple API instances (load balancing)
    - Persistent across restarts
    - Accurate counting in distributed environments
    
    Falls back to allowing requests if Redis is unavailable.
    """
    
    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self._redis = redis_client
        self.testing = os.getenv("TESTING", "").lower() == "true"
        self.prefix = "ratelimit:"
    
    async def _get_redis(self):
        """Lazy-load Redis connection."""
        if self._redis is None:
            try:
                from api.services.redis import get_redis_pool
                self._redis = await get_redis_pool()
            except Exception as e:
                logger.warning(f"Redis unavailable: {e}")
                return None
        return self._redis
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip in test environment
        if self.testing:
            return await call_next(request)
        
        # Skip for health checks and docs
        skip_paths = {"/health", "/", "/docs", "/openapi.json", "/redoc"}
        if request.url.path in skip_paths:
            return await call_next(request)
        
        redis = await self._get_redis()
        
        # Fallback to allowing if Redis unavailable
        if redis is None:
            response = await call_next(request)
            return response
        
        # Get identifiers
        client_id = self._get_client_id(request)
        category = self._get_endpoint_category(request)
        config = RATE_LIMITS.get(category, RATE_LIMITS["default"])
        
        # Check rate limit using sliding window
        is_allowed, remaining, reset_time = await self._check_limit(
            redis, client_id, category, config
        )
        
        if not is_allowed:
            retry_after = max(1, reset_time)
            logger.warning(
                f"Rate limit exceeded: {client_id} on {category} "
                f"({request.url.path})"
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": (
                        f"Rate limit exceeded. "
                        f"Max {config.requests} requests per "
                        f"{config.window_seconds}s."
                    ),
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(config.requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(config.requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response
    
    async def _check_limit(
        self,
        redis,
        client_id: str,
        category: str,
        config: RateLimitConfig,
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit using Redis sliding window.
        
        Returns:
            (is_allowed, remaining, reset_time_seconds)
        """
        import time
        
        key = f"{self.prefix}{category}:{client_id}"
        now = int(time.time())
        window_start = now - config.window_seconds
        
        try:
            # Use Redis pipeline for atomic operations
            pipe = redis.pipeline()
            
            # Remove old entries outside window
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            pipe.zcard(key)
            
            # Add current request with timestamp as score
            pipe.zadd(key, {f"{now}:{id(self)}": now})
            
            # Set expiry on key
            pipe.expire(key, config.window_seconds + 1)
            
            results = await pipe.execute()
            
            current_count = results[1]  # zcard result
            
            if current_count >= config.requests:
                # Get oldest entry to calculate reset time
                oldest = await redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    reset_time = int(oldest[0][1]) + config.window_seconds - now
                else:
                    reset_time = config.window_seconds
                
                return False, 0, max(1, reset_time)
            
            remaining = config.requests - current_count - 1
            reset_time = config.window_seconds
            
            return True, max(0, remaining), reset_time
            
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Allow on error (fail open)
            return True, config.requests, config.window_seconds
    
    def _get_endpoint_category(self, request: Request) -> str:
        """Categorize endpoint for rate limiting."""
        path = request.url.path.lower()
        
        for pattern, category in ENDPOINT_PATTERNS:
            if re.match(pattern, path):
                return category
        
        if request.method == "GET":
            return "read"
        elif request.method in ("POST", "PUT", "PATCH", "DELETE"):
            return "write"
        
        return "default"
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier."""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token_hash = hashlib.sha256(
                auth_header[7:].encode()
            ).hexdigest()[:16]
            return f"user:{token_hash}"
        
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
            return f"ip:{client_ip}"
        
        if request.client and request.client.host:
            return f"ip:{request.client.host}"
        
        return "ip:unknown"
