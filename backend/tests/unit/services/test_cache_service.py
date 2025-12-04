"""
Comprehensive tests for CacheService
Tests for Redis caching functionality
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCacheService:
    """Test suite for CacheService"""
    
    @pytest.fixture
    def cache_service(self):
        """Create CacheService instance"""
        from api.services.cache import CacheService
        return CacheService()
    
    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client"""
        mock = AsyncMock()
        mock.get = AsyncMock(return_value=None)
        mock.setex = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=1)
        mock.exists = AsyncMock(return_value=0)
        mock.ttl = AsyncMock(return_value=3600)
        mock.incrby = AsyncMock(return_value=1)
        mock.sadd = AsyncMock(return_value=1)
        mock.smembers = AsyncMock(return_value=set())
        mock.scard = AsyncMock(return_value=0)
        mock.scan = AsyncMock(return_value=(0, []))
        return mock

    @pytest.mark.asyncio
    async def test_init_sets_prefix(self, cache_service):
        """Test that CacheService initializes with correct prefix"""
        assert cache_service.prefix == "tiktrend:"
    
    @pytest.mark.asyncio
    async def test_get_returns_none_when_key_not_found(self, cache_service, mock_redis):
        """Test get returns None for missing keys"""
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await cache_service.get("nonexistent_key")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_returns_parsed_json(self, cache_service, mock_redis):
        """Test get returns parsed JSON data"""
        cached_data = {"name": "test", "price": 99.99}
        mock_redis.get = AsyncMock(return_value=json.dumps(cached_data))
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await cache_service.get("product:123")
            
            assert result == cached_data
            mock_redis.get.assert_called_once_with("tiktrend:product:123")
    
    @pytest.mark.asyncio
    async def test_get_handles_redis_error_gracefully(self, cache_service, mock_redis):
        """Test get returns None on Redis error"""
        mock_redis.get = AsyncMock(side_effect=Exception("Redis connection error"))
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await cache_service.get("key")
            assert result is None  # Graceful degradation
    
    @pytest.mark.asyncio
    async def test_set_stores_json_with_ttl(self, cache_service, mock_redis):
        """Test set stores serialized JSON with TTL"""
        data = {"id": 1, "name": "Product"}
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await cache_service.set("product:1", data, ttl=1800)
            
            assert result is True
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args
            assert call_args[0][0] == "tiktrend:product:1"
            assert call_args[0][1] == 1800
            assert json.loads(call_args[0][2]) == data
    
    @pytest.mark.asyncio
    async def test_set_uses_default_ttl(self, cache_service, mock_redis):
        """Test set uses default TTL of 3600"""
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            await cache_service.set("key", {"data": "value"})
            
            call_args = mock_redis.setex.call_args
            assert call_args[0][1] == 3600  # Default TTL
    
    @pytest.mark.asyncio
    async def test_set_handles_redis_error_gracefully(self, cache_service, mock_redis):
        """Test set returns False on Redis error"""
        mock_redis.setex = AsyncMock(side_effect=Exception("Redis error"))
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await cache_service.set("key", {"data": "value"})
            assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_removes_key(self, cache_service, mock_redis):
        """Test delete removes key from cache"""
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await cache_service.delete("product:1")
            
            assert result is True
            mock_redis.delete.assert_called_once_with("tiktrend:product:1")
    
    @pytest.mark.asyncio
    async def test_delete_handles_redis_error_gracefully(self, cache_service, mock_redis):
        """Test delete returns False on Redis error"""
        mock_redis.delete = AsyncMock(side_effect=Exception("Redis error"))
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await cache_service.delete("key")
            assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_pattern_removes_matching_keys(self, cache_service, mock_redis):
        """Test delete_pattern removes all matching keys"""
        # Simulate scan returning keys then finishing
        mock_redis.scan = AsyncMock(
            side_effect=[
                (1, [b"tiktrend:products:1", b"tiktrend:products:2"]),
                (0, [b"tiktrend:products:3"])
            ]
        )
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            deleted = await cache_service.delete_pattern("products:*")
            
            assert deleted == 3
            assert mock_redis.delete.call_count == 2
    
    @pytest.mark.asyncio
    async def test_exists_returns_true_for_existing_key(self, cache_service, mock_redis):
        """Test exists returns True for existing keys"""
        mock_redis.exists = AsyncMock(return_value=1)
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await cache_service.exists("product:1")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_exists_returns_false_for_missing_key(self, cache_service, mock_redis):
        """Test exists returns False for missing keys"""
        mock_redis.exists = AsyncMock(return_value=0)
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await cache_service.exists("nonexistent")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_ttl_returns_remaining_time(self, cache_service, mock_redis):
        """Test ttl returns remaining TTL"""
        mock_redis.ttl = AsyncMock(return_value=1234)
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await cache_service.ttl("key")
            
            assert result == 1234
    
    @pytest.mark.asyncio
    async def test_incr_increments_counter(self, cache_service, mock_redis):
        """Test incr increments counter by amount"""
        mock_redis.incrby = AsyncMock(return_value=5)
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await cache_service.incr("counter", 3)
            
            assert result == 5
            mock_redis.incrby.assert_called_once_with("tiktrend:counter", 3)
    
    @pytest.mark.asyncio
    async def test_increment_is_alias_for_incr(self, cache_service, mock_redis):
        """Test increment is an alias for incr"""
        mock_redis.incrby = AsyncMock(return_value=10)
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await cache_service.increment("counter", 5)
            
            assert result == 10
    
    @pytest.mark.asyncio
    async def test_sadd_adds_to_set(self, cache_service, mock_redis):
        """Test sadd adds values to a set"""
        mock_redis.sadd = AsyncMock(return_value=2)
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await cache_service.sadd("myset", "value1", "value2")
            
            assert result == 2
    
    @pytest.mark.asyncio
    async def test_smembers_returns_set(self, cache_service, mock_redis):
        """Test smembers returns set members"""
        mock_redis.smembers = AsyncMock(return_value={b"v1", b"v2"})
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await cache_service.smembers("myset")
            
            assert result == {b"v1", b"v2"}
    
    @pytest.mark.asyncio
    async def test_scard_returns_count(self, cache_service, mock_redis):
        """Test scard returns set cardinality"""
        mock_redis.scard = AsyncMock(return_value=5)
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await cache_service.scard("myset")
            
            assert result == 5
    
    @pytest.mark.asyncio
    async def test_get_or_set_returns_cached_value(self, cache_service, mock_redis):
        """Test get_or_set returns cached value if exists"""
        cached = {"cached": True}
        mock_redis.get = AsyncMock(return_value=json.dumps(cached))
        factory = AsyncMock(return_value={"fresh": True})
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await cache_service.get_or_set("key", factory)
            
            assert result == cached
            factory.assert_not_called()  # Should not compute
    
    @pytest.mark.asyncio
    async def test_get_or_set_computes_and_caches_on_miss(self, cache_service, mock_redis):
        """Test get_or_set computes and caches value on cache miss"""
        mock_redis.get = AsyncMock(return_value=None)
        fresh_value = {"fresh": True}
        
        # Test with a sync factory function (the actual code path)
        def sync_factory():
            return fresh_value
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await cache_service.get_or_set("key", sync_factory, ttl=1800)
            
            assert result == fresh_value
            mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_or_set_handles_sync_factory(self, cache_service, mock_redis):
        """Test get_or_set handles synchronous factory function"""
        mock_redis.get = AsyncMock(return_value=None)
        
        def sync_factory():
            return {"sync": True}
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await cache_service.get_or_set("key", sync_factory)
            
            assert result == {"sync": True}
    
    @pytest.mark.asyncio
    async def test_get_or_set_handles_literal_value(self, cache_service, mock_redis):
        """Test get_or_set handles literal value instead of factory"""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await cache_service.get_or_set("key", {"literal": True})
            
            assert result == {"literal": True}


class TestCacheServiceCacheKeys:
    """Test cache key building methods"""
    
    @pytest.fixture
    def cache_service(self):
        from api.services.cache import CacheService
        return CacheService()
    
    def test_build_products_cache_key_basic(self, cache_service):
        """Test basic products cache key generation"""
        key = cache_service.build_products_cache_key()
        
        assert key.startswith("products:")
        assert len(key) > len("products:")
    
    def test_build_products_cache_key_with_params(self, cache_service):
        """Test products cache key with parameters"""
        key1 = cache_service.build_products_cache_key(
            category="electronics",
            min_price=100,
            max_price=500,
            page=1
        )
        key2 = cache_service.build_products_cache_key(
            category="electronics",
            min_price=100,
            max_price=500,
            page=2
        )
        
        # Different pages should produce different keys
        assert key1 != key2
        assert key1.startswith("products:")
        assert key2.startswith("products:")
    
    def test_build_products_cache_key_consistent(self, cache_service):
        """Test that same params produce same key"""
        key1 = cache_service.build_products_cache_key(
            category="fashion",
            sort_by="price",
            page=1
        )
        key2 = cache_service.build_products_cache_key(
            category="fashion",
            sort_by="price",
            page=1
        )
        
        assert key1 == key2
    
    def test_build_copy_cache_key(self, cache_service):
        """Test copy cache key generation"""
        key = cache_service.build_copy_cache_key(
            product_id="prod_123",
            copy_type="description",
            tone="professional",
            platform="tiktok"
        )
        
        assert key.startswith("copy:")
        assert len(key) > len("copy:")
    
    def test_build_copy_cache_key_different_params(self, cache_service):
        """Test copy cache key differs with different params"""
        key1 = cache_service.build_copy_cache_key(
            product_id="prod_123",
            copy_type="description",
            tone="casual",
            platform="tiktok"
        )
        key2 = cache_service.build_copy_cache_key(
            product_id="prod_123",
            copy_type="description",
            tone="professional",  # Different tone
            platform="tiktok"
        )
        
        assert key1 != key2


class TestRateLimitService:
    """Test suite for RateLimitService"""
    
    @pytest.fixture
    def rate_limit_service(self):
        from api.services.cache import RateLimitService
        return RateLimitService()
    
    @pytest.fixture
    def mock_redis(self):
        mock = AsyncMock()
        mock.get = AsyncMock(return_value=None)
        mock.setex = AsyncMock(return_value=True)
        mock.incr = AsyncMock(return_value=1)
        return mock
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_first_request(self, rate_limit_service, mock_redis):
        """Test first request in window is allowed"""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            allowed, remaining = await rate_limit_service.check_rate_limit(
                "user:123", limit=10, window=60
            )
            
            assert allowed is True
            assert remaining == 9
            mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_within_limit(self, rate_limit_service, mock_redis):
        """Test request within limit is allowed"""
        mock_redis.get = AsyncMock(return_value="5")  # 5 requests made
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            allowed, remaining = await rate_limit_service.check_rate_limit(
                "user:123", limit=10, window=60
            )
            
            assert allowed is True
            assert remaining == 4
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self, rate_limit_service, mock_redis):
        """Test request exceeding limit is blocked"""
        mock_redis.get = AsyncMock(return_value="10")  # Limit reached
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            allowed, remaining = await rate_limit_service.check_rate_limit(
                "user:123", limit=10, window=60
            )
            
            assert allowed is False
            assert remaining == 0
    
    @pytest.mark.asyncio
    async def test_get_remaining_no_requests(self, rate_limit_service, mock_redis):
        """Test get_remaining when no requests made"""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            remaining = await rate_limit_service.get_remaining("user:123", 10)
            
            assert remaining == 10
    
    @pytest.mark.asyncio
    async def test_get_remaining_some_requests(self, rate_limit_service, mock_redis):
        """Test get_remaining with some requests made"""
        mock_redis.get = AsyncMock(return_value="7")
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            remaining = await rate_limit_service.get_remaining("user:123", 10)
            
            assert remaining == 3
    
    @pytest.mark.asyncio
    async def test_get_remaining_limit_exceeded(self, rate_limit_service, mock_redis):
        """Test get_remaining when limit exceeded"""
        mock_redis.get = AsyncMock(return_value="15")  # Over limit
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            remaining = await rate_limit_service.get_remaining("user:123", 10)
            
            assert remaining == 0  # Should not be negative


class TestCreditsService:
    """Test suite for CreditsService"""
    
    @pytest.fixture
    def credits_service(self):
        from api.services.cache import CreditsService
        return CreditsService()
    
    @pytest.fixture
    def mock_redis(self):
        mock = AsyncMock()
        mock.get = AsyncMock(return_value=None)
        mock.setex = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=1)
        return mock
    
    @pytest.mark.asyncio
    async def test_get_cached_credits_returns_none_on_miss(
        self, credits_service, mock_redis
    ):
        """Test get_cached_credits returns None on cache miss"""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await credits_service.get_cached_credits("user_123")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_cached_credits_returns_integer(
        self, credits_service, mock_redis
    ):
        """Test get_cached_credits returns integer credits"""
        mock_redis.get = AsyncMock(return_value="500")
        
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await credits_service.get_cached_credits("user_123")
            
            assert result == 500
            assert isinstance(result, int)
    
    @pytest.mark.asyncio
    async def test_set_cached_credits_stores_value(
        self, credits_service, mock_redis
    ):
        """Test set_cached_credits stores credits with TTL"""
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await credits_service.set_cached_credits("user_123", 1000)
            
            assert result is True
            mock_redis.setex.assert_called_once_with(
                "credits:user_123", 300, 1000  # Default TTL 5 min
            )
    
    @pytest.mark.asyncio
    async def test_set_cached_credits_custom_ttl(
        self, credits_service, mock_redis
    ):
        """Test set_cached_credits with custom TTL"""
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            await credits_service.set_cached_credits("user_123", 500, ttl=600)
            
            mock_redis.setex.assert_called_once_with(
                "credits:user_123", 600, 500
            )
    
    @pytest.mark.asyncio
    async def test_invalidate_credits_deletes_cache(
        self, credits_service, mock_redis
    ):
        """Test invalidate_credits removes cached value"""
        with patch('api.services.cache.get_redis_pool', return_value=mock_redis):
            result = await credits_service.invalidate_credits("user_123")
            
            assert result is True
            mock_redis.delete.assert_called_once_with("credits:user_123")


class TestQuotaServiceDeprecated:
    """Test suite for deprecated QuotaService"""
    
    @pytest.fixture
    def quota_service(self):
        from api.services.cache import QuotaService
        return QuotaService()
    
    @pytest.mark.asyncio
    async def test_get_quota_returns_unlimited(self, quota_service):
        """Test deprecated get_quota returns unlimited quota"""
        result = await quota_service.get_quota("user_123", "copies")
        
        assert result == {"used": 0, "limit": -1, "reset_date": None}
    
    @pytest.mark.asyncio
    async def test_increment_quota_is_noop(self, quota_service):
        """Test deprecated increment_quota is a no-op"""
        result = await quota_service.increment_quota("user_123", "copies", 5)
        
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_reset_quota_is_noop(self, quota_service):
        """Test deprecated reset_quota is a no-op"""
        # Should not raise any errors
        await quota_service.reset_quota("user_123", "copies", 100, "2025-01-01")
