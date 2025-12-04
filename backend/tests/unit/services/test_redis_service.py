"""
Comprehensive tests for Redis service
Tests for Redis connection pool and management
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestRedisPool:
    """Test suite for RedisPool singleton"""
    
    @pytest.fixture(autouse=True)
    def reset_pool(self):
        """Reset pool instance before each test"""
        with patch('api.services.redis.RedisPool._instance', None):
            yield
    
    def test_get_instance_creates_singleton(self):
        """Test that get_instance creates a singleton"""
        with patch('api.services.redis.aioredis') as mock_aioredis:
            mock_client = MagicMock()
            mock_aioredis.from_url.return_value = mock_client
            
            from api.services.redis import RedisPool
            RedisPool._instance = None  # Reset
            
            instance1 = RedisPool.get_instance()
            instance2 = RedisPool.get_instance()
            
            assert instance1 is instance2
            # from_url should only be called once
            mock_aioredis.from_url.assert_called_once()
    
    def test_get_instance_uses_redis_url(self):
        """Test that get_instance uses REDIS_URL environment variable"""
        with patch('api.services.redis.aioredis') as mock_aioredis:
            with patch('api.services.redis.REDIS_URL', 'redis://custom:6380/1'):
                mock_client = MagicMock()
                mock_aioredis.from_url.return_value = mock_client
                
                from api.services.redis import RedisPool
                RedisPool._instance = None
                
                RedisPool.get_instance()
                
                mock_aioredis.from_url.assert_called_with(
                    'redis://custom:6380/1',
                    decode_responses=True,
                    max_connections=10
                )
    
    @pytest.mark.asyncio
    async def test_close_closes_connection(self):
        """Test that close properly closes the Redis connection"""
        mock_client = AsyncMock()
        
        with patch('api.services.redis.RedisPool._instance', mock_client):
            from api.services.redis import RedisPool
            
            await RedisPool.close()
            
            mock_client.close.assert_called_once()
            assert RedisPool._instance is None
    
    @pytest.mark.asyncio
    async def test_close_handles_no_instance(self):
        """Test that close handles case when no instance exists"""
        from api.services.redis import RedisPool
        RedisPool._instance = None
        
        # Should not raise
        await RedisPool.close()


class TestRedisPoolHelpers:
    """Test helper functions"""
    
    @pytest.fixture(autouse=True)
    def reset_pool(self):
        """Reset pool before each test"""
        with patch('api.services.redis.RedisPool._instance', None):
            yield
    
    @pytest.mark.asyncio
    async def test_get_redis_pool_returns_instance(self):
        """Test get_redis_pool returns pool instance"""
        mock_client = MagicMock()
        
        with patch('api.services.redis.RedisPool.get_instance', return_value=mock_client):
            from api.services.redis import get_redis_pool
            
            result = await get_redis_pool()
            
            assert result is mock_client
    
    @pytest.mark.asyncio
    async def test_close_redis_pool_closes(self):
        """Test close_redis_pool calls close"""
        with patch('api.services.redis.RedisPool.close', new_callable=AsyncMock) as mock_close:
            from api.services.redis import close_redis_pool
            
            await close_redis_pool()
            
            mock_close.assert_called_once()


class TestRedisPoolConfiguration:
    """Test Redis pool configuration"""
    
    def test_default_redis_url(self):
        """Test default REDIS_URL value"""
        import os

        # Save current value
        original = os.environ.get('REDIS_URL')
        
        try:
            # Remove env var to test default
            if 'REDIS_URL' in os.environ:
                del os.environ['REDIS_URL']
            
            # Re-import to get default
            import importlib

            import api.services.redis as redis_module
            importlib.reload(redis_module)
            
            assert redis_module.REDIS_URL == "redis://localhost:6379/0"
        finally:
            # Restore
            if original:
                os.environ['REDIS_URL'] = original
    
    def test_custom_redis_url_from_env(self):
        """Test REDIS_URL from environment variable"""
        import os
        
        original = os.environ.get('REDIS_URL')
        
        try:
            os.environ['REDIS_URL'] = 'redis://production:6379/2'
            
            import importlib

            import api.services.redis as redis_module
            importlib.reload(redis_module)
            
            assert redis_module.REDIS_URL == 'redis://production:6379/2'
        finally:
            if original:
                os.environ['REDIS_URL'] = original
            elif 'REDIS_URL' in os.environ:
                del os.environ['REDIS_URL']


class TestRedisOperations:
    """Integration-style tests for Redis operations via pool"""
    
    @pytest.fixture
    def mock_redis(self):
        """Create fully mocked Redis client"""
        mock = AsyncMock()
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        mock.setex = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=1)
        mock.exists = AsyncMock(return_value=0)
        mock.expire = AsyncMock(return_value=True)
        mock.ttl = AsyncMock(return_value=3600)
        mock.incr = AsyncMock(return_value=1)
        mock.incrby = AsyncMock(return_value=1)
        mock.decr = AsyncMock(return_value=0)
        mock.lpush = AsyncMock(return_value=1)
        mock.rpush = AsyncMock(return_value=1)
        mock.lpop = AsyncMock(return_value=None)
        mock.rpop = AsyncMock(return_value=None)
        mock.lrange = AsyncMock(return_value=[])
        mock.sadd = AsyncMock(return_value=1)
        mock.srem = AsyncMock(return_value=1)
        mock.smembers = AsyncMock(return_value=set())
        mock.sismember = AsyncMock(return_value=False)
        mock.hset = AsyncMock(return_value=1)
        mock.hget = AsyncMock(return_value=None)
        mock.hgetall = AsyncMock(return_value={})
        mock.hdel = AsyncMock(return_value=1)
        mock.ping = AsyncMock(return_value=True)
        mock.close = AsyncMock()
        return mock
    
    @pytest.mark.asyncio
    async def test_redis_string_operations(self, mock_redis):
        """Test Redis string operations through the pool"""
        with patch('api.services.redis.RedisPool.get_instance', return_value=mock_redis):
            from api.services.redis import get_redis_pool
            
            redis = await get_redis_pool()
            
            # Set
            await redis.set("key", "value")
            mock_redis.set.assert_called_with("key", "value")
            
            # Get
            await redis.get("key")
            mock_redis.get.assert_called_with("key")
            
            # Setex
            await redis.setex("key", 3600, "value")
            mock_redis.setex.assert_called_with("key", 3600, "value")
    
    @pytest.mark.asyncio
    async def test_redis_counter_operations(self, mock_redis):
        """Test Redis counter operations"""
        with patch('api.services.redis.RedisPool.get_instance', return_value=mock_redis):
            from api.services.redis import get_redis_pool
            
            redis = await get_redis_pool()
            
            # Incr
            await redis.incr("counter")
            mock_redis.incr.assert_called_with("counter")
            
            # Incrby
            await redis.incrby("counter", 5)
            mock_redis.incrby.assert_called_with("counter", 5)
    
    @pytest.mark.asyncio
    async def test_redis_set_operations(self, mock_redis):
        """Test Redis set operations"""
        with patch('api.services.redis.RedisPool.get_instance', return_value=mock_redis):
            from api.services.redis import get_redis_pool
            
            redis = await get_redis_pool()
            
            # Sadd
            await redis.sadd("myset", "value1", "value2")
            mock_redis.sadd.assert_called_with("myset", "value1", "value2")
            
            # Smembers
            await redis.smembers("myset")
            mock_redis.smembers.assert_called_with("myset")
    
    @pytest.mark.asyncio
    async def test_redis_hash_operations(self, mock_redis):
        """Test Redis hash operations"""
        with patch('api.services.redis.RedisPool.get_instance', return_value=mock_redis):
            from api.services.redis import get_redis_pool
            
            redis = await get_redis_pool()
            
            # Hset
            await redis.hset("myhash", "field", "value")
            mock_redis.hset.assert_called_with("myhash", "field", "value")
            
            # Hget
            await redis.hget("myhash", "field")
            mock_redis.hget.assert_called_with("myhash", "field")
            
            # Hgetall
            await redis.hgetall("myhash")
            mock_redis.hgetall.assert_called_with("myhash")
    
    @pytest.mark.asyncio
    async def test_redis_list_operations(self, mock_redis):
        """Test Redis list operations"""
        with patch('api.services.redis.RedisPool.get_instance', return_value=mock_redis):
            from api.services.redis import get_redis_pool
            
            redis = await get_redis_pool()
            
            # Lpush
            await redis.lpush("mylist", "value")
            mock_redis.lpush.assert_called_with("mylist", "value")
            
            # Rpush
            await redis.rpush("mylist", "value")
            mock_redis.rpush.assert_called_with("mylist", "value")
            
            # Lrange
            await redis.lrange("mylist", 0, -1)
            mock_redis.lrange.assert_called_with("mylist", 0, -1)
    
    @pytest.mark.asyncio
    async def test_redis_key_operations(self, mock_redis):
        """Test Redis key operations"""
        with patch('api.services.redis.RedisPool.get_instance', return_value=mock_redis):
            from api.services.redis import get_redis_pool
            
            redis = await get_redis_pool()
            
            # Delete
            await redis.delete("key")
            mock_redis.delete.assert_called_with("key")
            
            # Exists
            await redis.exists("key")
            mock_redis.exists.assert_called_with("key")
            
            # Expire
            await redis.expire("key", 3600)
            mock_redis.expire.assert_called_with("key", 3600)
            
            # TTL
            await redis.ttl("key")
            mock_redis.ttl.assert_called_with("key")
    
    @pytest.mark.asyncio
    async def test_redis_connection_check(self, mock_redis):
        """Test Redis connection check with ping"""
        with patch('api.services.redis.RedisPool.get_instance', return_value=mock_redis):
            from api.services.redis import get_redis_pool
            
            redis = await get_redis_pool()
            
            result = await redis.ping()
            
            assert result is True
            mock_redis.ping.assert_called_once()
