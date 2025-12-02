"""
Tests for TikTok Routes (Extended Coverage)
Tests for TikTok API, session management, and product scraping.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class TestModels:
    """Tests for TikTok Pydantic models"""

    def test_session_setup(self):
        """Test TikTokSessionSetup model"""
        from api.routes.tiktok import TikTokSessionSetup

        data = TikTokSessionSetup(
            account_name="test_account",
            cookies=[{"name": "session", "value": "abc123"}]
        )

        assert data.account_name == "test_account"
        assert len(data.cookies) == 1

    def test_upload_request(self):
        """Test TikTokUploadRequest model"""
        from api.routes.tiktok import TikTokUploadRequest

        data = TikTokUploadRequest(
            account_name="test_account",
            caption="Test video",
            hashtags=["test", "video"],
            privacy="public"
        )

        assert data.account_name == "test_account"
        assert data.caption == "Test video"
        assert len(data.hashtags) == 2

    def test_upload_request_defaults(self):
        """Test TikTokUploadRequest default values"""
        from api.routes.tiktok import TikTokUploadRequest

        data = TikTokUploadRequest(
            account_name="test",
            caption="Caption"
        )

        assert data.hashtags is None
        assert data.privacy == "public"
        assert data.schedule_time is None


class TestTikTokAPIHealth:
    """Tests for tiktok_api_health endpoint"""

    @pytest.mark.asyncio
    async def test_health_healthy(self):
        """Test healthy API status"""
        from api.routes.tiktok import tiktok_api_health

        mock_user = {"id": "user-123"}

        with patch('api.routes.tiktok.TikTokAPIScraper') as MockScraper:
            mock_scraper = MockScraper.return_value
            mock_scraper.health_check = AsyncMock(return_value={
                "healthy": True,
                "api_accessible": True,
                "cookies_valid": True,
                "endpoints_tested": ["/api/search"]
            })

            result = await tiktok_api_health(mock_user)

        assert result.status == "healthy"
        assert result.api_accessible is True
        assert result.cookies_valid is True

    @pytest.mark.asyncio
    async def test_health_degraded(self):
        """Test degraded API status"""
        from api.routes.tiktok import tiktok_api_health

        mock_user = {"id": "user-123"}

        with patch('api.routes.tiktok.TikTokAPIScraper') as MockScraper:
            mock_scraper = MockScraper.return_value
            mock_scraper.health_check = AsyncMock(return_value={
                "healthy": False,
                "api_accessible": True,
                "cookies_valid": False
            })

            result = await tiktok_api_health(mock_user)

        assert result.status == "degraded"
        assert result.cookies_valid is False

    @pytest.mark.asyncio
    async def test_health_error(self):
        """Test error in health check"""
        from api.routes.tiktok import tiktok_api_health

        mock_user = {"id": "user-123"}

        with patch('api.routes.tiktok.TikTokAPIScraper') as MockScraper:
            mock_scraper = MockScraper.return_value
            mock_scraper.health_check = AsyncMock(side_effect=Exception("API error"))

            result = await tiktok_api_health(mock_user)

        assert result.status == "error"
        assert result.api_accessible is False
        assert "API error" in result.error


class TestGetTrendingProducts:
    """Tests for get_trending_tiktok_products endpoint"""

    @pytest.mark.asyncio
    async def test_trending_from_cache(self):
        """Test getting trending products from cache"""
        from api.routes.tiktok import get_trending_tiktok_products

        mock_user = {"id": "user-123"}
        mock_cached_products = [
            {
                "id": "prod1",
                "title": "Product 1",
                "price": 29.99,
                "currency": "USD",
                "url": "https://tiktok.com/product/1",
                "image_url": "https://tiktok.com/img/1.jpg",
                "shop_name": "Shop 1",
                "rating": 4.5,
                "sales_count": 100,
                "source": "tiktok"
            }
        ]

        with patch('api.routes.tiktok.ProductCacheManager') as MockCache:
            mock_cache = MockCache.return_value
            mock_cache.get_trending = AsyncMock(return_value=mock_cached_products)
            mock_cache.get_ttl = AsyncMock(return_value=1800)

            result = await get_trending_tiktok_products(
                category=None,
                max_results=20,
                use_cache=True,
                current_user=mock_user
            )

        assert result.cached is True
        assert len(result.products) == 1

    @pytest.mark.asyncio
    async def test_trending_from_api(self):
        """Test getting trending products from API"""
        from api.routes.tiktok import get_trending_tiktok_products

        mock_user = {"id": "user-123"}
        mock_products = [
            {
                "id": "prod1",
                "title": "Trending Product",
                "price": 19.99,
                "currency": "USD",
                "url": "https://tiktok.com/product/1",
                "image_url": "https://tiktok.com/img/1.jpg",
                "shop_name": "Shop",
                "rating": 4.0,
                "sales_count": 500,
                "source": "tiktok"
            }
        ]

        with patch('api.routes.tiktok.ProductCacheManager') as MockCache:
            mock_cache = MockCache.return_value
            mock_cache.get_trending = AsyncMock(return_value=None)
            mock_cache.cache_trending = AsyncMock()

            with patch('api.routes.tiktok.TikTokAPIScraper') as MockScraper:
                mock_scraper = MockScraper.return_value
                mock_scraper.get_trending_products = AsyncMock(return_value=mock_products)

                result = await get_trending_tiktok_products(
                    category=None,
                    max_results=20,
                    use_cache=True,
                    current_user=mock_user
                )

        assert result.cached is False
        assert len(result.products) == 1
        mock_cache.cache_trending.assert_called_once()

    @pytest.mark.asyncio
    async def test_trending_skip_cache(self):
        """Test getting trending products with cache disabled"""
        from api.routes.tiktok import get_trending_tiktok_products

        mock_user = {"id": "user-123"}
        mock_products = [
            {
                "id": "prod1",
                "title": "Fresh Product",
                "price": 9.99,
                "currency": "USD",
                "url": "https://tiktok.com/product/1",
                "image_url": "https://tiktok.com/img/1.jpg",
                "shop_name": "Shop",
                "rating": 5.0,
                "sales_count": 1000,
                "source": "tiktok"
            }
        ]

        with patch('api.routes.tiktok.ProductCacheManager') as MockCache:
            mock_cache = MockCache.return_value
            mock_cache.cache_trending = AsyncMock()

            with patch('api.routes.tiktok.TikTokAPIScraper') as MockScraper:
                mock_scraper = MockScraper.return_value
                mock_scraper.get_trending_products = AsyncMock(return_value=mock_products)

                result = await get_trending_tiktok_products(
                    category=None,
                    max_results=20,
                    use_cache=False,
                    current_user=mock_user
                )

        assert result.cached is False

    @pytest.mark.asyncio
    async def test_trending_with_category(self):
        """Test getting trending products with category filter"""
        from api.routes.tiktok import get_trending_tiktok_products

        mock_user = {"id": "user-123"}
        mock_products = []

        with patch('api.routes.tiktok.ProductCacheManager') as MockCache:
            mock_cache = MockCache.return_value
            mock_cache.get_trending = AsyncMock(return_value=None)
            mock_cache.cache_trending = AsyncMock()

            with patch('api.routes.tiktok.TikTokAPIScraper') as MockScraper:
                mock_scraper = MockScraper.return_value
                mock_scraper.get_trending_products = AsyncMock(return_value=mock_products)

                result = await get_trending_tiktok_products(
                    category="electronics",
                    max_results=10,
                    use_cache=True,
                    current_user=mock_user
                )

        assert result.total == 0

    @pytest.mark.asyncio
    async def test_trending_error(self):
        """Test error handling in trending products"""
        from api.routes.tiktok import get_trending_tiktok_products

        mock_user = {"id": "user-123"}

        with patch('api.routes.tiktok.ProductCacheManager') as MockCache:
            mock_cache = MockCache.return_value
            mock_cache.get_trending = AsyncMock(return_value=None)

            with patch('api.routes.tiktok.TikTokAPIScraper') as MockScraper:
                mock_scraper = MockScraper.return_value
                mock_scraper.get_trending_products = AsyncMock(
                    side_effect=Exception("API failed")
                )

                with pytest.raises(HTTPException) as exc_info:
                    await get_trending_tiktok_products(
                        category=None,
                        max_results=20,
                        use_cache=True,
                        current_user=mock_user
                    )

                assert exc_info.value.status_code == 500


class TestGetCacheStats:
    """Tests for get_cache_stats endpoint"""

    @pytest.mark.asyncio
    async def test_cache_stats_success(self):
        """Test successful cache stats retrieval"""
        from api.routes.tiktok import get_cache_stats

        mock_user = {"id": "user-123"}

        with patch('api.routes.tiktok.ProductCacheManager') as MockCache:
            mock_cache = MockCache.return_value
            mock_cache.get_stats = AsyncMock(return_value={
                "total_keys": 100,
                "hits": 80,
                "misses": 20,
                "hit_rate": 0.8,
                "trending_cached": True,
                "search_queries_cached": 50,
                "memory_used_mb": 10.5
            })

            result = await get_cache_stats(mock_user)

        assert result.total_keys == 100
        assert result.hit_rate == 0.8
        assert result.trending_cached is True

    @pytest.mark.asyncio
    async def test_cache_stats_error(self):
        """Test error handling in cache stats"""
        from api.routes.tiktok import get_cache_stats

        mock_user = {"id": "user-123"}

        with patch('api.routes.tiktok.ProductCacheManager') as MockCache:
            mock_cache = MockCache.return_value
            mock_cache.get_stats = AsyncMock(side_effect=Exception("Redis error"))

            with pytest.raises(HTTPException) as exc_info:
                await get_cache_stats(mock_user)

            assert exc_info.value.status_code == 500


class TestRouterConfiguration:
    """Tests for router configuration"""

    def test_router_exists(self):
        """Test router exists"""
        from api.routes.tiktok import router

        assert router is not None

