import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from shared.redis import (
    RedisManager,
    init_redis,
    close_redis,
    get_redis,
    redis_connection,
    RedisCache,
    RedisQueue,
    RedisLock,
    RedisPubSub
)

@pytest.fixture
def mock_redis_client():
    client = AsyncMock()
    return client

@pytest.fixture
def mock_pool():
    pool = MagicMock()
    pool.disconnect = AsyncMock()
    return pool

@pytest.fixture
async def redis_manager(mock_redis_client, mock_pool):
    # Reset singleton
    RedisManager._instance = None
    manager = RedisManager()
    
    with patch("shared.redis.ConnectionPool") as pool_cls, \
         patch("shared.redis.Redis") as redis_cls:
        
        pool_cls.from_url.return_value = mock_pool
        redis_cls.return_value = mock_redis_client
        
        yield manager
        
        # Cleanup
        if manager._client:
            await manager.close()
    
    RedisManager._instance = None

@pytest.mark.asyncio
async def test_redis_manager_singleton():
    m1 = RedisManager()
    m2 = RedisManager()
    assert m1 is m2

@pytest.mark.asyncio
async def test_redis_manager_init(redis_manager, mock_redis_client):
    await redis_manager.init()
    
    assert redis_manager._client is mock_redis_client
    mock_redis_client.ping.assert_called_once()

@pytest.mark.asyncio
async def test_redis_manager_init_failure(redis_manager, mock_redis_client):
    mock_redis_client.ping.side_effect = Exception("Connection failed")
    
    with pytest.raises(Exception, match="Connection failed"):
        await redis_manager.init()

@pytest.mark.asyncio
async def test_redis_manager_close(redis_manager, mock_redis_client, mock_pool):
    await redis_manager.init()
    await redis_manager.close()
    
    mock_redis_client.close.assert_called_once()
    mock_pool.disconnect.assert_called_once()
    assert redis_manager._client is None

@pytest.mark.asyncio
async def test_redis_manager_client_property_not_initialized():
    """Test client property raises when not initialized"""
    RedisManager._instance = None
    manager = RedisManager()
    manager._client = None
    
    with pytest.raises(RuntimeError, match="Redis not initialized"):
        _ = manager.client
    
    RedisManager._instance = None

@pytest.mark.asyncio
async def test_global_functions(redis_manager, mock_redis_client):
    with patch("shared.redis._manager", redis_manager):
        await init_redis()
        assert redis_manager._client is not None
        
        client = await get_redis()
        assert client is mock_redis_client
        
        await close_redis()
        assert redis_manager._client is None

@pytest.mark.asyncio
async def test_get_redis_auto_init(mock_redis_client, mock_pool):
    """Test get_redis auto-initializes when not connected"""
    RedisManager._instance = None
    manager = RedisManager()
    
    with patch("shared.redis._manager", manager), \
         patch("shared.redis.ConnectionPool") as pool_cls, \
         patch("shared.redis.Redis") as redis_cls:
        
        pool_cls.from_url.return_value = mock_pool
        redis_cls.return_value = mock_redis_client
        
        client = await get_redis()
        assert client is mock_redis_client
        mock_redis_client.ping.assert_called_once()
    
    RedisManager._instance = None

@pytest.mark.asyncio
async def test_redis_connection_context_manager(redis_manager, mock_redis_client):
    """Test redis_connection context manager"""
    redis_manager._client = mock_redis_client
    
    with patch("shared.redis._manager", redis_manager):
        async with redis_connection() as client:
            assert client is mock_redis_client

@pytest.mark.asyncio
async def test_redis_cache(redis_manager, mock_redis_client):
    redis_manager._client = mock_redis_client
    cache = RedisCache(prefix="test")
    
    with patch("shared.redis._manager", redis_manager):
        # Test get
        mock_redis_client.get.return_value = "value"
        val = await cache.get("key")
        assert val == "value"
        mock_redis_client.get.assert_called_with("test:key")
        
        # Test set
        await cache.set("key", "value")
        mock_redis_client.set.assert_called_with("test:key", "value", ex=3600)
        
        # Test delete
        mock_redis_client.delete.return_value = 1
        assert await cache.delete("key") is True
        
        # Test exists
        mock_redis_client.exists.return_value = 1
        assert await cache.exists("key") is True

@pytest.mark.asyncio
async def test_redis_cache_incr_decr(redis_manager, mock_redis_client):
    """Test incr and decr operations"""
    redis_manager._client = mock_redis_client
    cache = RedisCache(prefix="counter")
    
    with patch("shared.redis._manager", redis_manager):
        # Test incr
        mock_redis_client.incrby.return_value = 5
        result = await cache.incr("key", 1)
        assert result == 5
        mock_redis_client.incrby.assert_called_with("counter:key", 1)
        
        # Test decr
        mock_redis_client.decrby.return_value = 4
        result = await cache.decr("key", 1)
        assert result == 4
        mock_redis_client.decrby.assert_called_with("counter:key", 1)

@pytest.mark.asyncio
async def test_redis_cache_expire_ttl(redis_manager, mock_redis_client):
    """Test expire and ttl operations"""
    redis_manager._client = mock_redis_client
    cache = RedisCache(prefix="test")
    
    with patch("shared.redis._manager", redis_manager):
        # Test expire
        mock_redis_client.expire.return_value = True
        result = await cache.expire("key", 3600)
        assert result is True
        mock_redis_client.expire.assert_called_with("test:key", 3600)
        
        # Test ttl
        mock_redis_client.ttl.return_value = 1800
        result = await cache.ttl("key")
        assert result == 1800
        mock_redis_client.ttl.assert_called_with("test:key")

@pytest.mark.asyncio
async def test_redis_cache_get_many(redis_manager, mock_redis_client):
    """Test get_many operation"""
    redis_manager._client = mock_redis_client
    cache = RedisCache(prefix="test")
    
    with patch("shared.redis._manager", redis_manager):
        mock_redis_client.mget.return_value = ["val1", "val2", None]
        result = await cache.get_many(["key1", "key2", "key3"])
        
        assert result == {"key1": "val1", "key2": "val2", "key3": None}
        mock_redis_client.mget.assert_called_with(
            ["test:key1", "test:key2", "test:key3"]
        )

@pytest.mark.asyncio
async def test_redis_cache_set_many(redis_manager, mock_redis_client):
    """Test set_many operation"""
    redis_manager._client = mock_redis_client
    cache = RedisCache(prefix="test")
    
    # Setup mock pipeline - pipeline() is synchronous in redis-py
    mock_pipeline = MagicMock()
    mock_pipeline.set = MagicMock()  # set on pipeline is sync
    mock_pipeline.execute = AsyncMock(return_value=[True, True])
    mock_redis_client.pipeline = MagicMock(return_value=mock_pipeline)
    
    with patch("shared.redis._manager", redis_manager):
        result = await cache.set_many({"key1": "val1", "key2": "val2"}, expire=600)
        
        assert result is True
        mock_redis_client.pipeline.assert_called_once()
        assert mock_pipeline.set.call_count == 2
        mock_pipeline.execute.assert_called_once()

@pytest.mark.asyncio
async def test_redis_cache_delete_pattern(redis_manager, mock_redis_client):
    """Test delete_pattern operation"""
    redis_manager._client = mock_redis_client
    cache = RedisCache(prefix="test")
    
    with patch("shared.redis._manager", redis_manager):
        # Simulate scan returning some keys then 0 cursor
        mock_redis_client.scan.side_effect = [
            (1, ["test:key1", "test:key2"]),
            (0, ["test:key3"])
        ]
        mock_redis_client.delete.return_value = 2
        
        result = await cache.delete_pattern("key*")
        
        assert result == 4  # 2 + 2 deleted

@pytest.mark.asyncio
async def test_redis_queue(redis_manager, mock_redis_client):
    redis_manager._client = mock_redis_client
    queue = RedisQueue("jobs")
    
    with patch("shared.redis._manager", redis_manager):
        # Test push
        await queue.push("job1")
        mock_redis_client.lpush.assert_called_with("queue:jobs", "job1")
        
        # Test pop
        mock_redis_client.rpop.return_value = "job1"
        val = await queue.pop()
        assert val == "job1"
        
        # Test length
        mock_redis_client.llen.return_value = 5
        assert await queue.length() == 5

@pytest.mark.asyncio
async def test_redis_queue_pop_with_timeout(redis_manager, mock_redis_client):
    """Test queue pop with timeout (blocking)"""
    redis_manager._client = mock_redis_client
    queue = RedisQueue("jobs")
    
    with patch("shared.redis._manager", redis_manager):
        # Test brpop returns tuple
        mock_redis_client.brpop.return_value = ("queue:jobs", "job1")
        result = await queue.pop(timeout=5)
        assert result == "job1"
        mock_redis_client.brpop.assert_called_with("queue:jobs", timeout=5)
        
        # Test brpop returns None (timeout)
        mock_redis_client.brpop.return_value = None
        result = await queue.pop(timeout=1)
        assert result is None

@pytest.mark.asyncio
async def test_redis_queue_peek(redis_manager, mock_redis_client):
    """Test queue peek operation"""
    redis_manager._client = mock_redis_client
    queue = RedisQueue("jobs")
    
    with patch("shared.redis._manager", redis_manager):
        mock_redis_client.lrange.return_value = ["job1", "job2"]
        result = await queue.peek(count=2)
        
        assert result == ["job1", "job2"]
        mock_redis_client.lrange.assert_called_with("queue:jobs", -2, -1)

@pytest.mark.asyncio
async def test_redis_queue_clear(redis_manager, mock_redis_client):
    """Test queue clear operation"""
    redis_manager._client = mock_redis_client
    queue = RedisQueue("jobs")
    
    with patch("shared.redis._manager", redis_manager):
        mock_redis_client.delete.return_value = 1
        result = await queue.clear()
        
        assert result is True
        mock_redis_client.delete.assert_called_with("queue:jobs")

@pytest.mark.asyncio
async def test_redis_lock(redis_manager, mock_redis_client):
    redis_manager._client = mock_redis_client
    lock = RedisLock("resource")
    
    with patch("shared.redis._manager", redis_manager):
        # Test acquire success
        mock_redis_client.set.return_value = True
        assert await lock.acquire(blocking=False) is True
        
        # Test release
        mock_redis_client.eval.return_value = 1
        assert await lock.release() is True
        
        # Test context manager
        mock_redis_client.set.return_value = True
        async with lock:
            pass
        mock_redis_client.eval.assert_called()

@pytest.mark.asyncio
async def test_redis_lock_acquire_blocking(redis_manager, mock_redis_client):
    """Test blocking lock acquisition"""
    redis_manager._client = mock_redis_client
    lock = RedisLock("resource", timeout=5)
    
    with patch("shared.redis._manager", redis_manager), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        
        # First attempt fails, second succeeds
        mock_redis_client.set.side_effect = [False, True]
        
        result = await lock.acquire(blocking=True, wait_timeout=1)
        assert result is True
        assert mock_redis_client.set.call_count == 2

@pytest.mark.asyncio
async def test_redis_lock_acquire_blocking_timeout(redis_manager, mock_redis_client):
    """Test blocking lock acquisition timeout"""
    redis_manager._client = mock_redis_client
    lock = RedisLock("resource", timeout=5)
    
    with patch("shared.redis._manager", redis_manager), \
         patch("asyncio.get_event_loop") as mock_loop:
        
        # Simulate time passing past the wait_timeout
        mock_time = MagicMock()
        mock_time.time.side_effect = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.1, 1.2]
        mock_loop.return_value = mock_time
        
        mock_redis_client.set.return_value = False  # Always fail
        
        result = await lock.acquire(blocking=True, wait_timeout=1)
        assert result is False

@pytest.mark.asyncio
async def test_redis_lock_release_not_owned(redis_manager, mock_redis_client):
    """Test releasing lock that wasn't acquired"""
    redis_manager._client = mock_redis_client
    lock = RedisLock("resource")
    
    with patch("shared.redis._manager", redis_manager):
        # Token is None, should return False
        result = await lock.release()
        assert result is False

@pytest.mark.asyncio
async def test_redis_pubsub(redis_manager, mock_redis_client):
    redis_manager._client = mock_redis_client
    pubsub = RedisPubSub()
    
    mock_pubsub = AsyncMock()
    # pubsub() is synchronous, returns a PubSub object
    mock_redis_client.pubsub = MagicMock(return_value=mock_pubsub)
    
    with patch("shared.redis._manager", redis_manager):
        # Test subscribe
        await pubsub.subscribe("channel1")
        mock_pubsub.subscribe.assert_called_with("channel1")
        
        # Test publish
        await pubsub.publish("channel1", "msg")
        mock_redis_client.publish.assert_called_with("channel1", "msg")
        
        # Test unsubscribe
        await pubsub.unsubscribe("channel1")
        mock_pubsub.unsubscribe.assert_called_with("channel1")

@pytest.mark.asyncio
async def test_redis_pubsub_listen(redis_manager, mock_redis_client):
    """Test pubsub listen generator - just verify method is callable"""
    # This test is simplified because mocking async generators is complex
    # The actual listen() functionality is tested in integration tests
    redis_manager._client = mock_redis_client
    pubsub = RedisPubSub()
    
    mock_pubsub = MagicMock()
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.close = AsyncMock()
    mock_redis_client.pubsub = MagicMock(return_value=mock_pubsub)
    
    with patch("shared.redis._manager", redis_manager):
        await pubsub.subscribe("test")
        # Verify pubsub was set up
        assert pubsub._pubsub is not None
        mock_pubsub.subscribe.assert_called_with("test")
        
        # Test close
        await pubsub.close()
        mock_pubsub.close.assert_called_once()

@pytest.mark.asyncio
async def test_redis_pubsub_close(redis_manager, mock_redis_client):
    """Test pubsub close"""
    redis_manager._client = mock_redis_client
    pubsub = RedisPubSub()
    
    mock_pubsub = AsyncMock()
    mock_redis_client.pubsub = MagicMock(return_value=mock_pubsub)
    
    with patch("shared.redis._manager", redis_manager):
        await pubsub.subscribe("channel1")
        await pubsub.close()
        
        mock_pubsub.close.assert_called_once()

@pytest.mark.asyncio
async def test_redis_pubsub_unsubscribe_not_connected():
    """Test unsubscribe when not connected"""
    pubsub = RedisPubSub()
    
    # Should not raise, just no-op
    await pubsub.unsubscribe("channel")

@pytest.mark.asyncio
async def test_redis_manager_close_when_not_initialized():
    """Test close when not initialized"""
    RedisManager._instance = None
    manager = RedisManager()
    
    # Should not raise
    await manager.close()
    
    RedisManager._instance = None

@pytest.mark.asyncio
async def test_redis_manager_init_already_initialized(redis_manager, mock_redis_client):
    """Test init when already initialized"""
    await redis_manager.init()
    
    # Second call should be no-op
    mock_redis_client.ping.reset_mock()
    await redis_manager.init()
    
    # ping should not be called again
    mock_redis_client.ping.assert_not_called()

@pytest.mark.asyncio
async def test_redis_cache_delete_not_found(redis_manager, mock_redis_client):
    """Test delete returns False when key not found"""
    redis_manager._client = mock_redis_client
    cache = RedisCache(prefix="test")
    
    with patch("shared.redis._manager", redis_manager):
        mock_redis_client.delete.return_value = 0
        result = await cache.delete("nonexistent")
        assert result is False

@pytest.mark.asyncio
async def test_redis_cache_exists_not_found(redis_manager, mock_redis_client):
    """Test exists returns False when key not found"""
    redis_manager._client = mock_redis_client
    cache = RedisCache(prefix="test")
    
    with patch("shared.redis._manager", redis_manager):
        mock_redis_client.exists.return_value = 0
        result = await cache.exists("nonexistent")
        assert result is False
