"""
Cache Service
Redis caching layer for products and copies

Note: Uses connection pool pattern - connections are managed by the pool,
not created/closed per operation. This avoids connection leaks and improves
performance.

Gracefully degrades when Redis is unavailable.

Features:
- Automatic cache key generation
- TTL-based expiration
- Pattern-based invalidation
- Decorator for easy endpoint caching
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional

from api.services.redis import get_redis_pool

logger = logging.getLogger(__name__)


# Cache TTL constants (in seconds)
CACHE_TTL_SHORT = 300      # 5 min - user session data
CACHE_TTL_MEDIUM = 3600    # 1 hour - product listings
CACHE_TTL_LONG = 86400     # 24 hours - static data


def cached(
    key_prefix: str,
    ttl: int = CACHE_TTL_MEDIUM,
    key_builder: Optional[Callable] = None
):
    """
    Decorator for caching async function results.
    
    Usage:
        @cached("products:list", ttl=3600)
        async def get_products(category: str, page: int):
            ...
    
    Args:
        key_prefix: Prefix for cache key
        ttl: Time-to-live in seconds
        key_builder: Optional function to build cache key from args
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = CacheService()
            
            # Build cache key
            if key_builder:
                cache_key = f"{key_prefix}:{key_builder(*args, **kwargs)}"
            else:
                # Auto-generate key from args
                params = {"args": args, "kwargs": kwargs}
                params_str = json.dumps(params, sort_keys=True, default=str)
                hash_key = hashlib.md5(params_str.encode()).hexdigest()[:12]
                cache_key = f"{key_prefix}:{hash_key}"
            
            # Try cache first
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_result
            
            # Execute function
            logger.debug(f"Cache MISS: {cache_key}")
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


class CacheService:
    """Redis cache service for API responses"""
    
    def __init__(self):
        self.prefix = "tiktrend:"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache. Returns None if Redis unavailable."""
        try:
            redis_client = await get_redis_pool()
            full_key = f"{self.prefix}{key}"
            
            value = await redis_client.get(full_key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Redis get failed for {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL. Fails silently if Redis unavailable."""
        try:
            redis_client = await get_redis_pool()
            full_key = f"{self.prefix}{key}"
            
            serialized = json.dumps(value, default=str)
            await redis_client.setex(full_key, ttl, serialized)
            return True
        except Exception as e:
            logger.warning(f"Redis set failed for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache. Fails silently if Redis unavailable."""
        try:
            redis_client = await get_redis_pool()
            full_key = f"{self.prefix}{key}"
            
            await redis_client.delete(full_key)
            return True
        except Exception as e:
            logger.warning(f"Redis delete failed for {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        redis_client = await get_redis_pool()
        full_pattern = f"{self.prefix}{pattern}"
        
        cursor = 0
        deleted = 0
        
        while True:
            cursor, keys = await redis_client.scan(
                cursor, match=full_pattern, count=100
            )
            if keys:
                await redis_client.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break
        
        return deleted
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        redis_client = await get_redis_pool()
        full_key = f"{self.prefix}{key}"
        
        return await redis_client.exists(full_key) > 0
    
    async def ttl(self, key: str) -> int:
        """Get remaining TTL for key"""
        redis_client = await get_redis_pool()
        full_key = f"{self.prefix}{key}"
        
        return await redis_client.ttl(full_key)
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        redis_client = await get_redis_pool()
        full_key = f"{self.prefix}{key}"
        
        return await redis_client.incrby(full_key, amount)
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter (alias for incr)"""
        return await self.incr(key, amount)
    
    async def sadd(self, key: str, *values) -> int:
        """Add values to a set"""
        redis_client = await get_redis_pool()
        full_key = f"{self.prefix}{key}"
        return await redis_client.sadd(full_key, *values)
    
    async def smembers(self, key: str) -> set:
        """Get all members of a set"""
        redis_client = await get_redis_pool()
        full_key = f"{self.prefix}{key}"
        return await redis_client.smembers(full_key)
    
    async def scard(self, key: str) -> int:
        """Get count of members in a set"""
        redis_client = await get_redis_pool()
        full_key = f"{self.prefix}{key}"
        return await redis_client.scard(full_key)

    async def get_or_set(self, key: str, factory, ttl: int = 3600) -> Any:
        """Get value from cache or compute and cache it"""
        value = await self.get(key)
        if value is not None:
            return value
        
        # Compute value
        if callable(factory):
            if hasattr(factory, '__await__'):
                value = await factory()
            else:
                value = factory()
        else:
            value = factory
        
        await self.set(key, value, ttl)
        return value
    
    def build_products_cache_key(
        self,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_sales: Optional[int] = None,
        sort_by: str = "sales_30d",
        page: int = 1,
        per_page: int = 20,
        source: Optional[str] = None,
    ) -> str:
        """Build cache key for product queries"""
        params = {
            "c": category or "all",
            "min_p": min_price,
            "max_p": max_price,
            "min_s": min_sales,
            "sort": sort_by,
            "p": page,
            "pp": per_page,
            "src": source,
        }
        
        # Create hash of params
        params_str = json.dumps(params, sort_keys=True)
        hash_key = hashlib.md5(params_str.encode()).hexdigest()[:12]
        
        return f"products:{hash_key}"
    
    def build_copy_cache_key(
        self,
        product_id: str,
        copy_type: str,
        tone: str,
        platform: str,
    ) -> str:
        """Build cache key for copy generation"""
        params = {
            "pid": product_id,
            "type": copy_type,
            "tone": tone,
            "platform": platform
        }
        
        params_str = json.dumps(params, sort_keys=True)
        hash_key = hashlib.md5(params_str.encode()).hexdigest()[:12]
        
        return f"copy:{hash_key}"


class RateLimitService:
    """Rate limiting using Redis"""
    
    def __init__(self):
        self.prefix = "ratelimit:"
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int = 60
    ) -> tuple[bool, int]:
        """
        Check if rate limit is exceeded.
        Returns (is_allowed, remaining_requests)
        """
        redis = await get_redis_pool()
        full_key = f"{self.prefix}{key}"
        
        current = await redis.get(full_key)
        
        if current is None:
            # First request in window
            await redis.setex(full_key, window, 1)
            return True, limit - 1
        
        current = int(current)
        
        if current >= limit:
            return False, 0
        
        # Increment counter
        await redis.incr(full_key)
        return True, limit - current - 1
    
    async def get_remaining(self, key: str, limit: int) -> int:
        """Get remaining requests for key"""
        redis = await get_redis_pool()
        full_key = f"{self.prefix}{key}"
        
        current = await redis.get(full_key)
        
        if current is None:
            return limit
        
        return max(0, limit - int(current))


class CreditsService:
    """Credits tracking using Redis for caching"""

    def __init__(self):
        self.prefix = "credits:"

    async def get_cached_credits(self, user_id: str) -> Optional[int]:
        """Get cached credits balance for user"""
        redis = await get_redis_pool()
        key = f"{self.prefix}{user_id}"
        value = await redis.get(key)
        return int(value) if value else None

    async def set_cached_credits(
        self, user_id: str, credits: int, ttl: int = 300
    ) -> bool:
        """Cache credits balance (5 min default TTL)"""
        redis = await get_redis_pool()
        key = f"{self.prefix}{user_id}"
        await redis.setex(key, ttl, credits)
        return True

    async def invalidate_credits(self, user_id: str) -> bool:
        """Invalidate cached credits after transaction"""
        redis = await get_redis_pool()
        key = f"{self.prefix}{user_id}"
        await redis.delete(key)
        return True


# Keep QuotaService for backwards compatibility (deprecated)
class QuotaService:
    """
    Monthly quota tracking using Redis.
    DEPRECATED: Use CreditsService instead.
    Kept for backwards compatibility.
    """

    def __init__(self):
        self.prefix = "quota:"

    async def get_quota(self, user_id: str, quota_type: str) -> dict:
        """Get current quota usage for user (deprecated)"""
        return {"used": 0, "limit": -1, "reset_date": None}

    async def increment_quota(
        self, user_id: str, quota_type: str, amount: int = 1
    ) -> int:
        """Increment quota usage (deprecated - no-op)"""
        return 0

    async def reset_quota(
        self, user_id: str, quota_type: str, limit: int, reset_date: str
    ):
        """Reset quota for new period (deprecated - no-op)"""
        pass
