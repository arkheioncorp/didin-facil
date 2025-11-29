import pytest
from unittest.mock import AsyncMock, patch
from api.services.redis import RedisPool, get_redis_pool, close_redis_pool


@pytest.fixture(autouse=True)
def reset_redis_pool():
    # Reset singleton before each test
    RedisPool._instance = None
    yield
    # Cleanup after test
    RedisPool._instance = None


@pytest.mark.asyncio
async def test_redis_pool_singleton():
    with patch("api.services.redis.aioredis.from_url") as mock_from_url:
        mock_client = AsyncMock()
        mock_from_url.return_value = mock_client
        
        instance1 = RedisPool.get_instance()
        instance2 = RedisPool.get_instance()
        
        assert instance1 is instance2
        # Should only call from_url once
        mock_from_url.assert_called_once()


@pytest.mark.asyncio
async def test_redis_pool_get_instance():
    with patch("api.services.redis.aioredis.from_url") as mock_from_url:
        mock_client = AsyncMock()
        mock_from_url.return_value = mock_client
        
        instance = RedisPool.get_instance()
        
        assert instance is mock_client
        # Just verify it was called with decode_responses and max_connections
        assert mock_from_url.call_count == 1
        call_kwargs = mock_from_url.call_args[1]
        assert call_kwargs["decode_responses"] is True
        assert call_kwargs["max_connections"] == 10


@pytest.mark.asyncio
async def test_redis_pool_custom_url():
    with patch("api.services.redis.aioredis.from_url") as mock_from_url, \
         patch.dict("os.environ", {"REDIS_URL": "redis://custom:6380/1"}):
        
        mock_client = AsyncMock()
        mock_from_url.return_value = mock_client
        
        # Force re-import to pick up new env var
        from importlib import reload
        import api.services.redis as redis_module
        reload(redis_module)
        
        instance = redis_module.RedisPool.get_instance()
        
        assert instance is mock_client


@pytest.mark.asyncio
async def test_redis_pool_close():
    with patch("api.services.redis.aioredis.from_url") as mock_from_url:
        mock_client = AsyncMock()
        mock_from_url.return_value = mock_client
        
        RedisPool.get_instance()
        await RedisPool.close()
        
        mock_client.close.assert_called_once()
        assert RedisPool._instance is None


@pytest.mark.asyncio
async def test_redis_pool_close_when_not_initialized():
    # Should not raise error when closing without initialization
    await RedisPool.close()
    assert RedisPool._instance is None


@pytest.mark.asyncio
async def test_get_redis_pool():
    # The autouse fixture already resets the singleton
    with patch("api.services.redis.aioredis.from_url") as mock_from_url:
        mock_client = AsyncMock()
        mock_from_url.return_value = mock_client
        
        pool = await get_redis_pool()
        
        # Just verify we got something back
        assert pool is not None


@pytest.mark.asyncio
async def test_close_redis_pool():
    # The autouse fixture already resets the singleton
    with patch("api.services.redis.aioredis.from_url") as mock_from_url:
        mock_client = AsyncMock()
        mock_from_url.return_value = mock_client
        
        # Get instance
        await get_redis_pool()
        
        # Close
        await close_redis_pool()
        
        assert RedisPool._instance is None


@pytest.mark.asyncio
async def test_redis_pool_reconnect_after_close():
    with patch("api.services.redis.aioredis.from_url") as mock_from_url:
        mock_client1 = AsyncMock()
        mock_client2 = AsyncMock()
        mock_from_url.side_effect = [mock_client1, mock_client2]
        
        # First connection
        pool1 = RedisPool.get_instance()
        assert pool1 is mock_client1
        
        # Close
        await RedisPool.close()
        
        # Reconnect
        pool2 = RedisPool.get_instance()
        assert pool2 is mock_client2
        assert pool2 is not pool1
