"""
Redis Connection Manager
Async Redis connection pool and utilities
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from redis.asyncio import ConnectionPool, Redis

from .config import settings


class RedisManager:
    """Manage Redis connections"""
    
    _instance: Optional["RedisManager"] = None
    _pool: Optional[ConnectionPool] = None
    _client: Optional[Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def init(self):
        """Initialize Redis connection pool"""
        if self._pool is not None:
            return
        
        self._pool = ConnectionPool.from_url(
            settings.redis.url,
            max_connections=20,
            decode_responses=True,
        )
        
        self._client = Redis(connection_pool=self._pool)
        
        # Test connection
        try:
            await self._client.ping()
            print(f"[Redis] Connected to {settings.redis.host}:{settings.redis.port}")
        except Exception as e:
            print(f"[Redis] Connection failed: {e}")
            raise
    
    async def close(self):
        """Close Redis connections"""
        if self._client:
            await self._client.close()
            self._client = None
        
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
        
        print("[Redis] Connection closed")
    
    @property
    def client(self) -> Redis:
        """Get Redis client"""
        if self._client is None:
            raise RuntimeError("Redis not initialized. Call init() first.")
        return self._client
    
    # High-level methods for direct use
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        client = self.client
        return await client.get(key)
    
    async def set(
        self,
        key: str,
        value: str,
        ex: Optional[int] = None,
        expire: Optional[int] = None,
    ) -> bool:
        """Set value in Redis with optional expiration"""
        client = self.client
        ttl = ex or expire or 3600
        return await client.set(key, value, ex=ttl)
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys from Redis"""
        client = self.client
        return await client.delete(*keys)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        client = self.client
        return await client.exists(key) > 0
    
    async def keys(self, pattern: str) -> list:
        """Get keys matching pattern"""
        client = self.client
        return await client.keys(pattern)
    
    async def smembers(self, key: str) -> set:
        """Get all members of a set"""
        client = self.client
        return await client.smembers(key)
    
    async def sadd(self, key: str, *values) -> int:
        """Add one or more members to a set"""
        client = self.client
        return await client.sadd(key, *values)
    
    async def srem(self, key: str, *values) -> int:
        """Remove one or more members from a set"""
        client = self.client
        return await client.srem(key, *values)
    
    async def sismember(self, key: str, value: str) -> bool:
        """Check if value is a member of a set"""
        client = self.client
        return await client.sismember(key, value)
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field value"""
        client = self.client
        return await client.hget(key, field)
    
    async def hset(self, key: str, field: str = None, value: str = None, mapping: dict = None) -> int:
        """Set hash field value or multiple fields from mapping"""
        client = self.client
        if mapping:
            return await client.hset(key, mapping=mapping)
        return await client.hset(key, field, value)
    
    async def hgetall(self, key: str) -> dict:
        """Get all hash fields and values"""
        client = self.client
        return await client.hgetall(key)
    
    async def hdel(self, key: str, *fields: str) -> int:
        """Delete one or more hash fields"""
        client = self.client
        return await client.hdel(key, *fields)


# Global manager instance
_manager = RedisManager()


# Alias for redis client (for backwards compatibility)
redis_client = _manager


async def init_redis():
    """Initialize Redis connection"""
    await _manager.init()


async def close_redis():
    """Close Redis connection"""
    await _manager.close()


async def get_redis() -> Redis:
    """Get Redis client instance"""
    if _manager._client is None:
        await _manager.init()
    return _manager.client


@asynccontextmanager
async def redis_connection():
    """Context manager for Redis connection"""
    client = await get_redis()
    try:
        yield client
    finally:
        pass  # Pool manages connections


class RedisCache:
    """High-level Redis cache operations"""
    
    def __init__(self, prefix: str = "cache"):
        self.prefix = prefix
    
    def _key(self, key: str) -> str:
        """Generate prefixed key"""
        return f"{self.prefix}:{key}"
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        client = await get_redis()
        return await client.get(self._key(key))
    
    async def set(
        self,
        key: str,
        value: str,
        expire: int = 3600,
    ) -> bool:
        """Set value in cache with expiration"""
        client = await get_redis()
        return await client.set(self._key(key), value, ex=expire)
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        client = await get_redis()
        return await client.delete(self._key(key)) > 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        client = await get_redis()
        return await client.exists(self._key(key)) > 0
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        client = await get_redis()
        return await client.incrby(self._key(key), amount)
    
    async def decr(self, key: str, amount: int = 1) -> int:
        """Decrement counter"""
        client = await get_redis()
        return await client.decrby(self._key(key), amount)
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration"""
        client = await get_redis()
        return await client.expire(self._key(key), seconds)
    
    async def ttl(self, key: str) -> int:
        """Get time to live"""
        client = await get_redis()
        return await client.ttl(self._key(key))
    
    async def get_many(self, keys: list) -> dict:
        """Get multiple values"""
        client = await get_redis()
        prefixed_keys = [self._key(k) for k in keys]
        values = await client.mget(prefixed_keys)
        return dict(zip(keys, values))
    
    async def set_many(
        self,
        mapping: dict,
        expire: int = 3600,
    ) -> bool:
        """Set multiple values"""
        client = await get_redis()
        
        pipe = client.pipeline()
        for key, value in mapping.items():
            pipe.set(self._key(key), value, ex=expire)
        
        results = await pipe.execute()
        return all(results)
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        client = await get_redis()
        
        cursor = 0
        deleted = 0
        full_pattern = self._key(pattern)
        
        while True:
            cursor, keys = await client.scan(cursor, match=full_pattern)
            
            if keys:
                deleted += await client.delete(*keys)
            
            if cursor == 0:
                break
        
        return deleted


class RedisQueue:
    """Redis-based job queue"""
    
    def __init__(self, name: str):
        self.name = f"queue:{name}"
    
    async def push(self, data: str) -> int:
        """Push item to queue"""
        client = await get_redis()
        return await client.lpush(self.name, data)
    
    async def pop(self, timeout: int = 0) -> Optional[str]:
        """Pop item from queue"""
        client = await get_redis()
        
        if timeout > 0:
            result = await client.brpop(self.name, timeout=timeout)
            return result[1] if result else None
        else:
            return await client.rpop(self.name)
    
    async def length(self) -> int:
        """Get queue length"""
        client = await get_redis()
        return await client.llen(self.name)
    
    async def peek(self, count: int = 1) -> list:
        """Peek at queue items without removing"""
        client = await get_redis()
        return await client.lrange(self.name, -count, -1)
    
    async def clear(self) -> bool:
        """Clear the queue"""
        client = await get_redis()
        return await client.delete(self.name) > 0


class RedisLock:
    """Distributed lock using Redis"""
    
    def __init__(self, name: str, timeout: int = 30):
        self.name = f"lock:{name}"
        self.timeout = timeout
        self._token: Optional[str] = None
    
    async def acquire(self, blocking: bool = True, wait_timeout: int = 10) -> bool:
        """Acquire the lock"""
        import uuid
        
        client = await get_redis()
        self._token = str(uuid.uuid4())
        
        if blocking:
            end_time = asyncio.get_event_loop().time() + wait_timeout
            
            while asyncio.get_event_loop().time() < end_time:
                if await client.set(
                    self.name,
                    self._token,
                    nx=True,
                    ex=self.timeout
                ):
                    return True
                await asyncio.sleep(0.1)
            
            return False
        else:
            return await client.set(
                self.name,
                self._token,
                nx=True,
                ex=self.timeout
            )
    
    async def release(self) -> bool:
        """Release the lock"""
        if self._token is None:
            return False
        
        client = await get_redis()
        
        # Only release if we own the lock
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        result = await client.eval(script, 1, self.name, self._token)
        self._token = None
        return result == 1
    
    async def __aenter__(self):
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()


class RedisPubSub:
    """Redis Pub/Sub wrapper"""
    
    def __init__(self):
        self._pubsub = None
    
    async def subscribe(self, *channels):
        """Subscribe to channels"""
        client = await get_redis()
        self._pubsub = client.pubsub()
        await self._pubsub.subscribe(*channels)
    
    async def unsubscribe(self, *channels):
        """Unsubscribe from channels"""
        if self._pubsub:
            await self._pubsub.unsubscribe(*channels)
    
    async def publish(self, channel: str, message: str) -> int:
        """Publish message to channel"""
        client = await get_redis()
        return await client.publish(channel, message)
    
    async def listen(self):
        """Listen for messages"""
        if self._pubsub:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    yield message
    
    async def close(self):
        """Close pubsub connection"""
        if self._pubsub:
            await self._pubsub.close()
