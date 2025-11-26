"""
Redis Connection Pool
Singleton Redis connection pool
"""

import os
import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class RedisPool:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = aioredis.from_url(
                REDIS_URL, 
                decode_responses=True,
                max_connections=10
            )
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance:
            await cls._instance.close()
            cls._instance = None

async def get_redis_pool():
    return RedisPool.get_instance()


async def close_redis_pool():
    await RedisPool.close()
