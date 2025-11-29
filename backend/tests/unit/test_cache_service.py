"""
Cache Service Unit Tests
Tests for CacheService, RateLimitService, and CreditsService
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from api.services.cache import (
    CacheService,
    RateLimitService,
    CreditsService
)


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.exists = AsyncMock(return_value=1)
    redis.ttl = AsyncMock(return_value=3600)
    redis.incrby = AsyncMock(return_value=1)
    redis.incr = AsyncMock(return_value=1)
    redis.close = AsyncMock()
    redis.scan = AsyncMock(return_value=(0, []))
    return redis


@pytest.fixture
def cache_service():
    return CacheService()


@pytest.fixture
def rate_limit_service():
    return RateLimitService()


@pytest.fixture
def credits_service():
    return CreditsService()


# ============== CacheService Tests ==============

class TestCacheService:
    
    @pytest.mark.asyncio
    async def test_cache_prefix(self, cache_service):
        assert cache_service.prefix == "tiktrend:"
    
    @pytest.mark.asyncio
    async def test_get_returns_none_when_not_found(
        self, cache_service, mock_redis
    ):
        mock_redis.get.return_value = None
        
        with patch(
            "api.services.cache.get_redis",
            return_value=mock_redis
        ):
            result = await cache_service.get("test_key")
            
            assert result is None
            mock_redis.get.assert_called_once_with("tiktrend:test_key")
    
    @pytest.mark.asyncio
    async def test_get_returns_parsed_json(self, cache_service, mock_redis):
        mock_redis.get.return_value = '{"name": "test", "value": 123}'
        
        with patch(
            "api.services.cache.get_redis",
            return_value=mock_redis
        ):
            result = await cache_service.get("test_key")
            
            assert result == {"name": "test", "value": 123}
    
    @pytest.mark.asyncio
    async def test_set_stores_json(self, cache_service, mock_redis):
        with patch(
            "api.services.cache.get_redis",
            return_value=mock_redis
        ):
            result = await cache_service.set(
                "test_key",
                {"data": "value"},
                ttl=3600
            )
            
            assert result is True
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args[0]
            assert call_args[0] == "tiktrend:test_key"
            assert call_args[1] == 3600
    
    @pytest.mark.asyncio
    async def test_delete_key(self, cache_service, mock_redis):
        with patch(
            "api.services.cache.get_redis",
            return_value=mock_redis
        ):
            result = await cache_service.delete("test_key")
            
            assert result is True
            mock_redis.delete.assert_called_once_with("tiktrend:test_key")
    
    @pytest.mark.asyncio
    async def test_exists_true(self, cache_service, mock_redis):
        mock_redis.exists.return_value = 1
        
        with patch(
            "api.services.cache.get_redis",
            return_value=mock_redis
        ):
            result = await cache_service.exists("test_key")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_exists_false(self, cache_service, mock_redis):
        mock_redis.exists.return_value = 0
        
        with patch(
            "api.services.cache.get_redis",
            return_value=mock_redis
        ):
            result = await cache_service.exists("test_key")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_ttl(self, cache_service, mock_redis):
        mock_redis.ttl.return_value = 1800
        
        with patch(
            "api.services.cache.get_redis",
            return_value=mock_redis
        ):
            result = await cache_service.ttl("test_key")
            
            assert result == 1800
    
    @pytest.mark.asyncio
    async def test_incr(self, cache_service, mock_redis):
        mock_redis.incrby.return_value = 5
        
        with patch(
            "api.services.cache.get_redis",
            return_value=mock_redis
        ):
            result = await cache_service.incr("counter", 2)
            
            assert result == 5
            mock_redis.incrby.assert_called_once_with(
                "tiktrend:counter", 2
            )
    
    @pytest.mark.asyncio
    async def test_delete_pattern(self, cache_service, mock_redis):
        mock_redis.scan.return_value = (0, ["key1", "key2"])
        
        with patch(
            "api.services.cache.get_redis",
            return_value=mock_redis
        ):
            result = await cache_service.delete_pattern("products:*")
            
            assert result == 2
    
    @pytest.mark.asyncio
    async def test_get_or_set_cache_hit(self, cache_service, mock_redis):
        mock_redis.get.return_value = '{"cached": true}'
        
        with patch(
            "api.services.cache.get_redis",
            return_value=mock_redis
        ):
            factory = MagicMock(return_value={"new": True})
            result = await cache_service.get_or_set(
                "test_key", factory, ttl=3600
            )
            
            assert result == {"cached": True}
            factory.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_or_set_cache_miss(self, cache_service, mock_redis):
        mock_redis.get.return_value = None
        
        with patch(
            "api.services.cache.get_redis",
            return_value=mock_redis
        ):
            factory = MagicMock(return_value={"new": True})
            result = await cache_service.get_or_set(
                "test_key", factory, ttl=3600
            )
            
            assert result == {"new": True}
            factory.assert_called_once()


class TestCacheServiceKeyBuilders:
    
    def test_build_products_cache_key(self):
        service = CacheService()
        
        key1 = service.build_products_cache_key(
            category="electronics",
            min_price=10.0,
            max_price=100.0,
            min_sales=50,
            sort_by="price",
            page=1,
            per_page=20
        )
        
        assert key1.startswith("products:")
        assert len(key1) > len("products:")
    
    def test_build_products_cache_key_consistency(self):
        service = CacheService()
        
        key1 = service.build_products_cache_key(category="test", page=1)
        key2 = service.build_products_cache_key(category="test", page=1)
        
        assert key1 == key2
    
    def test_build_products_cache_key_uniqueness(self):
        service = CacheService()
        
        key1 = service.build_products_cache_key(category="electronics")
        key2 = service.build_products_cache_key(category="clothing")
        
        assert key1 != key2
    
    def test_build_copy_cache_key(self):
        service = CacheService()
        
        key = service.build_copy_cache_key(
            product_id="123",
            copy_type="description",
            tone="professional",
            platform="instagram"
        )
        
        assert key.startswith("copy:")
        assert len(key) > len("copy:")
    
    def test_build_copy_cache_key_consistency(self):
        service = CacheService()
        
        key1 = service.build_copy_cache_key(
            product_id="123",
            copy_type="title",
            tone="casual",
            platform="tiktok"
        )
        key2 = service.build_copy_cache_key(
            product_id="123",
            copy_type="title",
            tone="casual",
            platform="tiktok"
        )
        
        assert key1 == key2


# ============== RateLimitService Tests ==============

class TestRateLimitService:
    
    @pytest.mark.asyncio
    async def test_rate_limit_first_request(
        self, rate_limit_service, mock_redis
    ):
        mock_redis.get.return_value = None
        
        with patch(
            "api.services.cache.get_redis",
            return_value=mock_redis
        ):
            allowed, remaining = await rate_limit_service.check_rate_limit(
                "user:123", limit=10, window=60
            )
            
            assert allowed is True
            assert remaining == 9
            mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rate_limit_within_limit(
        self, rate_limit_service, mock_redis
    ):
        mock_redis.get.return_value = "5"
        
        with patch(
            "api.services.cache.get_redis",
            return_value=mock_redis
        ):
            allowed, remaining = await rate_limit_service.check_rate_limit(
                "user:123", limit=10, window=60
            )
            
            assert allowed is True
            assert remaining == 4
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(
        self, rate_limit_service, mock_redis
    ):
        mock_redis.get.return_value = "10"
        
        with patch(
            "api.services.cache.get_redis",
            return_value=mock_redis
        ):
            allowed, remaining = await rate_limit_service.check_rate_limit(
                "user:123", limit=10, window=60
            )
            
            assert allowed is False
            assert remaining == 0
    
    @pytest.mark.asyncio
    async def test_get_remaining_no_requests(
        self, rate_limit_service, mock_redis
    ):
        mock_redis.get.return_value = None
        
        with patch(
            "api.services.cache.get_redis",
            return_value=mock_redis
        ):
            remaining = await rate_limit_service.get_remaining(
                "user:123", limit=10
            )
            
            assert remaining == 10
    
    @pytest.mark.asyncio
    async def test_get_remaining_with_usage(
        self, rate_limit_service, mock_redis
    ):
        mock_redis.get.return_value = "7"
        
        with patch(
            "api.services.cache.get_redis",
            return_value=mock_redis
        ):
            remaining = await rate_limit_service.get_remaining(
                "user:123", limit=10
            )
            
            assert remaining == 3


# ============== CreditsService Tests ==============

class TestCreditsService:
    
    @pytest.mark.asyncio
    async def test_get_cached_credits_not_found(
        self, credits_service, mock_redis
    ):
        mock_redis.get.return_value = None
        
        with patch(
            "api.services.cache.get_redis",
            return_value=mock_redis
        ):
            result = await credits_service.get_cached_credits("user123")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_cached_credits_found(
        self, credits_service, mock_redis
    ):
        mock_redis.get.return_value = "100"
        
        with patch(
            "api.services.cache.get_redis",
            return_value=mock_redis
        ):
            result = await credits_service.get_cached_credits("user123")
            
            assert result == 100
