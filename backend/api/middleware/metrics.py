"""
Metrics Collection Middleware
Records API request metrics for Prometheus
"""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from shared.redis import redis_client
import logging

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect API request metrics
    
    Tracks:
    - Total requests
    - Request counts by status code
    - Response time sliding window
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics" or request.url.path.startswith("/metrics/"):
            return await call_next(request)
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Record metrics asynchronously
            try:
                await self._record_metrics(
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    response_time_ms=response_time_ms
                )
            except Exception as e:
                logger.debug(f"Failed to record metrics: {e}")
            
            return response
            
        except Exception as e:
            # Record error
            response_time_ms = (time.time() - start_time) * 1000
            try:
                await self._record_metrics(
                    method=request.method,
                    path=request.url.path,
                    status_code=500,
                    response_time_ms=response_time_ms
                )
            except Exception:
                pass
            raise e
    
    async def _record_metrics(
        self,
        method: str,
        path: str,
        status_code: int,
        response_time_ms: float
    ):
        """Record metrics to Redis"""
        try:
            # Total requests counter
            await redis_client.incr("metrics:api:requests:total")
            
            # Status code counters
            if 500 <= status_code < 600:
                await redis_client.incr("metrics:api:requests:5xx")
            elif 400 <= status_code < 500:
                await redis_client.incr("metrics:api:requests:4xx")
            elif 200 <= status_code < 300:
                await redis_client.incr("metrics:api:requests:2xx")
            
            # Response time sliding window (keep last 100)
            await redis_client.lpush("metrics:api:response_times", str(response_time_ms))
            await redis_client.ltrim("metrics:api:response_times", 0, 99)
            
            # Per-endpoint metrics
            endpoint_key = f"metrics:api:endpoint:{method}:{self._normalize_path(path)}"
            await redis_client.incr(endpoint_key)
            
        except Exception as e:
            logger.debug(f"Redis metrics error: {e}")
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize path to group similar endpoints
        
        e.g., /products/123 -> /products/:id
        """
        parts = path.strip("/").split("/")
        normalized = []
        
        for part in parts:
            # Check if it looks like an ID (numeric or UUID-like)
            if part.isdigit() or (len(part) == 36 and "-" in part):
                normalized.append(":id")
            else:
                normalized.append(part)
        
        return "/" + "/".join(normalized)
