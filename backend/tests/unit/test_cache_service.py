"""
Cache Service Tests - 100% Coverage
Tests for Redis caching layer
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

# Import the service
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from backend.api.services.cache import CacheService


class TestCacheService:
    """Test suite for CacheService"""

    @pytest.fixture
    def cache_service(self):
        """Create a cache service instance"""
        return CacheService()

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client"""
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=None)
        redis_mock.setex = AsyncMock()
        redis_mock.delete = AsyncMock()
        redis_mock.scan = AsyncMock(return_value=(0, []))
        redis_mock.exists = AsyncMock(return_value=0)
        redis_mock.ttl = AsyncMock(return_value=-1)
        redis_mock.incrby = AsyncMock(return_value=1)
        return redis_mock

    # ==================== GET Tests ====================

    @pytest.mark.asyncio
    async def test_get_returns_none_when_key_not_found(self, cache_service, mock_redis):
        """Test get returns None when key doesn't exist"""
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.get('nonexistent')
            assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_parsed_json(self, cache_service, mock_redis):
        """Test get returns parsed JSON when key exists"""
        mock_redis.get = AsyncMock(return_value='{"key": "value"}')
        
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.get('test_key')
            assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_uses_correct_prefix(self, cache_service, mock_redis):
        """Test get uses tiktrend: prefix"""
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            await cache_service.get('mykey')
            mock_redis.get.assert_called_with('tiktrend:mykey')

    # ==================== SET Tests ====================

    @pytest.mark.asyncio
    async def test_set_stores_value_with_default_ttl(self, cache_service, mock_redis):
        """Test set stores value with default TTL of 3600"""
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.set('key', {'data': 'value'})
            
            assert result is True
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args
            assert call_args[0][0] == 'tiktrend:key'
            assert call_args[0][1] == 3600

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, cache_service, mock_redis):
        """Test set with custom TTL"""
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            await cache_service.set('key', 'value', ttl=7200)
            
            call_args = mock_redis.setex.call_args
            assert call_args[0][1] == 7200

    @pytest.mark.asyncio
    async def test_set_serializes_complex_objects(self, cache_service, mock_redis):
        """Test set properly serializes complex objects"""
        complex_data = {
            'list': [1, 2, 3],
            'nested': {'a': 'b'},
            'datetime': datetime.now()
        }
        
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            await cache_service.set('key', complex_data)
            
            # Should not raise an error
            assert mock_redis.setex.called

    # ==================== DELETE Tests ====================

    @pytest.mark.asyncio
    async def test_delete_removes_key(self, cache_service, mock_redis):
        """Test delete removes the specified key"""
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.delete('key')
            
            assert result is True
            mock_redis.delete.assert_called_with('tiktrend:key')

    # ==================== DELETE PATTERN Tests ====================

    @pytest.mark.asyncio
    async def test_delete_pattern_deletes_matching_keys(self, cache_service, mock_redis):
        """Test delete_pattern deletes all matching keys"""
        mock_redis.scan = AsyncMock(return_value=(0, ['tiktrend:products:1', 'tiktrend:products:2']))
        
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.delete_pattern('products:*')
            
            assert result == 2

    @pytest.mark.asyncio
    async def test_delete_pattern_handles_pagination(self, cache_service, mock_redis):
        """Test delete_pattern handles multiple scan iterations"""
        # First call returns cursor 1 with some keys
        # Second call returns cursor 0 (done) with more keys
        mock_redis.scan = AsyncMock(side_effect=[
            (1, ['tiktrend:key1', 'tiktrend:key2']),
            (0, ['tiktrend:key3'])
        ])
        
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.delete_pattern('key*')
            
            assert result == 3

    @pytest.mark.asyncio
    async def test_delete_pattern_with_no_matches(self, cache_service, mock_redis):
        """Test delete_pattern returns 0 when no keys match"""
        mock_redis.scan = AsyncMock(return_value=(0, []))
        
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.delete_pattern('nonexistent:*')
            
            assert result == 0

    # ==================== EXISTS Tests ====================

    @pytest.mark.asyncio
    async def test_exists_returns_true_when_key_exists(self, cache_service, mock_redis):
        """Test exists returns True when key exists"""
        mock_redis.exists = AsyncMock(return_value=1)
        
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.exists('key')
            
            assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_when_key_not_found(self, cache_service, mock_redis):
        """Test exists returns False when key doesn't exist"""
        mock_redis.exists = AsyncMock(return_value=0)
        
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.exists('key')
            
            assert result is False

    # ==================== TTL Tests ====================

    @pytest.mark.asyncio
    async def test_ttl_returns_remaining_time(self, cache_service, mock_redis):
        """Test ttl returns remaining time for key"""
        mock_redis.ttl = AsyncMock(return_value=3000)
        
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.ttl('key')
            
            assert result == 3000

    @pytest.mark.asyncio
    async def test_ttl_returns_negative_when_no_ttl(self, cache_service, mock_redis):
        """Test ttl returns -1 when key has no TTL"""
        mock_redis.ttl = AsyncMock(return_value=-1)
        
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.ttl('key')
            
            assert result == -1

    # ==================== INCR Tests ====================

    @pytest.mark.asyncio
    async def test_incr_increments_by_one_default(self, cache_service, mock_redis):
        """Test incr increments by 1 by default"""
        mock_redis.incrby = AsyncMock(return_value=1)
        
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.incr('counter')
            
            assert result == 1
            mock_redis.incrby.assert_called_with('tiktrend:counter', 1)

    @pytest.mark.asyncio
    async def test_incr_with_custom_amount(self, cache_service, mock_redis):
        """Test incr with custom amount"""
        mock_redis.incrby = AsyncMock(return_value=10)
        
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.incr('counter', 10)
            
            assert result == 10
            mock_redis.incrby.assert_called_with('tiktrend:counter', 10)

    # ==================== GET OR SET Tests ====================

    @pytest.mark.asyncio
    async def test_get_or_set_returns_cached_value(self, cache_service, mock_redis):
        """Test get_or_set returns cached value when exists"""
        mock_redis.get = AsyncMock(return_value='{"cached": true}')
        factory = AsyncMock()
        
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.get_or_set('key', factory)
            
            assert result == {"cached": True}
            factory.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_set_calls_factory_when_not_cached(self, cache_service, mock_redis):
        """Test get_or_set calls factory when key doesn't exist"""
        mock_redis.get = AsyncMock(return_value=None)
        factory = AsyncMock(return_value={"computed": True})
        
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.get_or_set('key', factory)
            
            assert result == {"computed": True}
            factory.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_set_caches_computed_value(self, cache_service, mock_redis):
        """Test get_or_set caches the computed value"""
        mock_redis.get = AsyncMock(return_value=None)
        factory = AsyncMock(return_value={"new": "value"})
        
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            await cache_service.get_or_set('key', factory)
            
            mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_set_with_sync_factory(self, cache_service, mock_redis):
        """Test get_or_set works with synchronous factory"""
        mock_redis.get = AsyncMock(return_value=None)
        def factory():
            return {"sync": True}
        
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.get_or_set('key', factory)
            
            assert result == {"sync": True}

    @pytest.mark.asyncio
    async def test_get_or_set_with_non_callable_factory(self, cache_service, mock_redis):
        """Test get_or_set with non-callable value"""
        mock_redis.get = AsyncMock(return_value=None)
        value = {"static": "value"}
        
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.get_or_set('key', value)
            
            assert result == {"static": "value"}

    # ==================== BUILD PRODUCTS CACHE KEY Tests ====================

    def test_build_products_cache_key_default(self, cache_service):
        """Test build_products_cache_key with defaults"""
        key = cache_service.build_products_cache_key()
        
        assert 'all' in key or 'c:all' in key.lower() or 'c=all' in key.lower()
        assert 'p=1' in key or 'p:1' in key or ':1:' in key

    def test_build_products_cache_key_with_category(self, cache_service):
        """Test build_products_cache_key with category"""
        key = cache_service.build_products_cache_key(category='electronics')
        
        assert 'electronics' in key

    def test_build_products_cache_key_with_price_range(self, cache_service):
        """Test build_products_cache_key with price range"""
        key = cache_service.build_products_cache_key(min_price=10, max_price=100)
        
        # Key should contain price parameters
        assert '10' in key
        assert '100' in key

    def test_build_products_cache_key_with_pagination(self, cache_service):
        """Test build_products_cache_key with pagination"""
        key = cache_service.build_products_cache_key(page=5, per_page=50)
        
        assert '5' in key
        assert '50' in key

    def test_build_products_cache_key_uniqueness(self, cache_service):
        """Test different parameters generate different keys"""
        key1 = cache_service.build_products_cache_key(category='a')
        key2 = cache_service.build_products_cache_key(category='b')
        
        assert key1 != key2

    def test_build_products_cache_key_consistency(self, cache_service):
        """Test same parameters generate same key"""
        key1 = cache_service.build_products_cache_key(
            category='test', min_price=10, page=1
        )
        key2 = cache_service.build_products_cache_key(
            category='test', min_price=10, page=1
        )
        
        assert key1 == key2


class TestCacheServiceEdgeCases:
    """Edge case tests for CacheService"""

    @pytest.fixture
    def cache_service(self):
        return CacheService()

    @pytest.fixture
    def mock_redis(self):
        redis_mock = AsyncMock()
        return redis_mock

    @pytest.mark.asyncio
    async def test_get_with_empty_key(self, cache_service, mock_redis):
        """Test get with empty key"""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.get('')
            assert result is None

    @pytest.mark.asyncio
    async def test_set_with_none_value(self, cache_service, mock_redis):
        """Test set with None value"""
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.set('key', None)
            assert result is True

    @pytest.mark.asyncio
    async def test_set_with_large_value(self, cache_service, mock_redis):
        """Test set with large value"""
        large_data = {'data': 'x' * 1000000}  # 1MB string
        
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            result = await cache_service.set('key', large_data)
            assert result is True

    @pytest.mark.asyncio
    async def test_get_with_special_characters_in_key(self, cache_service, mock_redis):
        """Test get with special characters in key"""
        mock_redis.get = AsyncMock(return_value='{"test": true}')
        
        with patch('backend.api.services.cache.get_redis', return_value=mock_redis):
            await cache_service.get('key:with:colons')
            mock_redis.get.assert_called_with('tiktrend:key:with:colons')
