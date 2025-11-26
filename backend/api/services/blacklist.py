"""
JWT Blacklist Service
Manage revoked tokens using Redis
"""

from api.services.redis import get_redis_pool


class BlacklistService:
    """Service to manage JWT blacklist"""
    
    def __init__(self):
        self.prefix = "blacklist:"
        
    async def add(self, token: str, ttl: int) -> bool:
        """
        Add token to blacklist
        
        Args:
            token: JWT token string
            ttl: Time to live in seconds (should match token expiration)
        """
        redis_client = await get_redis_pool()
        key = f"{self.prefix}{token}"
        await redis_client.setex(key, ttl, "revoked")
        return True
        
    async def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        redis_client = await get_redis_pool()
        key = f"{self.prefix}{token}"
        exists = await redis_client.exists(key)
        return exists > 0
