"""
Rate Limiting Middleware
Request rate limiting per user/IP
"""

import time
from typing import Dict
from collections import defaultdict

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.
    
    For production, use Redis-based rate limiting for distributed systems.
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Check rate limit
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window
        
        # Clean old requests
        self.request_counts[client_id] = [
            ts for ts in self.request_counts[client_id]
            if ts > window_start
        ]
        
        # Check if limit exceeded
        if len(self.request_counts[client_id]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute.",
                    "retry_after": int(60 - (current_time - self.request_counts[client_id][0]))
                }
            )
        
        # Record request
        self.request_counts[client_id].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(self.request_counts[client_id])
        )
        response.headers["X-RateLimit-Reset"] = str(int(window_start + 60))
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """
        Get unique client identifier.
        Uses user ID from JWT if available, otherwise IP address.
        """
        # Try to get user ID from authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # For production, decode JWT to get user ID
            # For now, use the token itself as identifier
            return f"user:{auth_header[7:32]}"
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        
        return f"ip:{request.client.host}" if request.client else "unknown"
