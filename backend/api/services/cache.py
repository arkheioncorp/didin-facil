"""
Cache Service
Redis caching layer for products and copies
"""

import os
import json
import hashlib
from typing import Any, Optional
from datetime import timedelta

import redis.asyncio as aioredis


# Redis settings
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


async def get_redis():
    """Get Redis connection"""
    return await aioredis.from_url(REDIS_URL, decode_responses=True)


class CacheService:
    """Redis cache service for API responses"""
    
    def __init__(self):
        self.prefix = "tiktrend:"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        redis_client = await get_redis()
        full_key = f"{self.prefix}{key}"
        
        try:
            value = await redis_client.get(full_key)
            if value:
                return json.loads(value)
            return None
        finally:
            await redis_client.close()
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL (default 1 hour)"""
        redis_client = await get_redis()
        full_key = f"{self.prefix}{key}"
        
        try:
            serialized = json.dumps(value, default=str)
            await redis_client.setex(full_key, ttl, serialized)
            return True
        finally:
            await redis_client.close()
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        redis_client = await get_redis()
        full_key = f"{self.prefix}{key}"
        
        try:
            await redis_client.delete(full_key)
            return True
        finally:
            await redis_client.close()
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        redis_client = await get_redis()
        full_pattern = f"{self.prefix}{pattern}"
        
        try:
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
        finally:
            await redis_client.close()
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        redis_client = await get_redis()
        full_key = f"{self.prefix}{key}"
        
        try:
            return await redis_client.exists(full_key) > 0
        finally:
            await redis_client.close()
    
    async def ttl(self, key: str) -> int:
        """Get remaining TTL for key"""
        redis_client = await get_redis()
        full_key = f"{self.prefix}{key}"
        
        try:
            return await redis_client.ttl(full_key)
        finally:
            await redis_client.close()
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        redis_client = await get_redis()
        full_key = f"{self.prefix}{key}"
        
        try:
            return await redis_client.incrby(full_key, amount)
        finally:
            await redis_client.close()
    
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
    ) -> str:
        """Build cache key for product queries"""
        params = {
            "c": category or "all",
            "min_p": min_price,
            "max_p": max_price,
            "min_s": min_sales,
            "sort": sort_by,
            "p": page,
            "pp": per_page
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
        redis = await get_redis()
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
        redis = await get_redis()
        full_key = f"{self.prefix}{key}"
        
        current = await redis.get(full_key)
        
        if current is None:
            return limit
        
        return max(0, limit - int(current))


class QuotaService:
    """Monthly quota tracking using Redis"""
    
    def __init__(self):
        self.prefix = "quota:"
    
    async def get_quota(self, user_id: str, quota_type: str) -> dict:
        """Get current quota usage for user"""
        redis = await get_redis()
        key = f"{self.prefix}{quota_type}:{user_id}"
        
        data = await redis.hgetall(key)
        
        if not data:
            return {"used": 0, "limit": 0, "reset_date": None}
        
        return {
            "used": int(data.get(b"used", 0)),
            "limit": int(data.get(b"limit", 0)),
            "reset_date": data.get(b"reset_date", b"").decode()
        }
    
    async def increment_quota(self, user_id: str, quota_type: str, amount: int = 1) -> int:
        """Increment quota usage"""
        redis = await get_redis()
        key = f"{self.prefix}{quota_type}:{user_id}"
        
        return await redis.hincrby(key, "used", amount)
    
    async def reset_quota(self, user_id: str, quota_type: str, limit: int, reset_date: str):
        """Reset quota for new period"""
        redis = await get_redis()
        key = f"{self.prefix}{quota_type}:{user_id}"
        
        await redis.hset(key, mapping={
            "used": 0,
            "limit": limit,
            "reset_date": reset_date
        })
        
        # Set expiry to reset date + 1 day buffer
        await redis.expire(key, 32 * 24 * 60 * 60)  # 32 days
