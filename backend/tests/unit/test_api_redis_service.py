import pytest
from unittest.mock import AsyncMock, patch
from api.services.redis import RedisPool, get_redis_pool, close_redis_pool

@pytest.fixture
async def redis_pool_cleanup():
    # Setup
    RedisPool._instance = None
    yield
    # Teardown
    if RedisPool._instance:
        await RedisPool.close()
    RedisPool._instance = None

@pytest.mark.asyncio
async def test_redis_pool_singleton(redis_pool_cleanup):
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_redis = AsyncMock()
        mock_from_url.return_value = mock_redis
        
        # First call should create instance
        instance1 = RedisPool.get_instance()
        assert instance1 is mock_redis
        mock_from_url.assert_called_once()
        
        # Second call should return same instance
        instance2 = RedisPool.get_instance()
        assert instance2 is instance1
        mock_from_url.assert_called_once() # Should still be called only once

@pytest.mark.asyncio
async def test_redis_pool_close(redis_pool_cleanup):
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_redis = AsyncMock()
        mock_from_url.return_value = mock_redis
        
        # Initialize
        RedisPool.get_instance()
        assert RedisPool._instance is not None
        
        # Close
        await RedisPool.close()
        mock_redis.close.assert_called_once()
        assert RedisPool._instance is None

@pytest.mark.asyncio
async def test_redis_pool_close_not_initialized():
    RedisPool._instance = None
    # Should not raise error
    await RedisPool.close()

@pytest.mark.asyncio
async def test_get_redis_pool_wrapper(redis_pool_cleanup):
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_redis = AsyncMock()
        mock_from_url.return_value = mock_redis
        
        pool = await get_redis_pool()
        assert pool is mock_redis

@pytest.mark.asyncio
async def test_close_redis_pool_wrapper(redis_pool_cleanup):
    with patch("api.services.redis.RedisPool") as mock_pool_cls:
        mock_pool_cls.close = AsyncMock()
        
        await close_redis_pool()
        mock_pool_cls.close.assert_called_once()
