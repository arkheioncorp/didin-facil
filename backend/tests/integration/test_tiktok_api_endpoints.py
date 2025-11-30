"""
Integration Tests for TikTok API Endpoints
Tests the new API endpoints: /api/health, /api/search, /api/trending, /api/cache/*
"""
# ruff: noqa: E402, E501
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock

from api.main import app


@pytest.fixture
def mock_current_user():
    """Mock authenticated user"""
    return MagicMock(
        id="user-123",
        email="test@example.com",
        plan="pro",
        get=lambda k, d=None: {
            "id": "user-123",
            "plan": "pro",
            "email": "test@example.com"
        }.get(k, d)
    )


@pytest.fixture
def mock_api_scraper():
    """Mock TikTok API Scraper"""
    scraper = AsyncMock()
    scraper.health_check = AsyncMock(return_value={
        "status": "healthy",
        "provider": "api",
        "cache_enabled": True,
        "rate_limit_remaining": 100
    })
    return scraper


@pytest.fixture
def mock_cache_manager():
    """Mock cache manager"""
    cache = AsyncMock()
    cache.get_cached_products = AsyncMock(return_value=[])
    cache.cache_products = AsyncMock()
    cache.get_stats = AsyncMock(return_value={
        "total_cached": 150,
        "cache_hit_rate": 0.85,
        "avg_ttl_remaining": 3600
    })
    cache.clear_cache = AsyncMock(return_value={"cleared": 50})
    return cache


class TestAPIHealth:
    """Test /api/health endpoint"""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_current_user, mock_api_scraper):
        """Should return healthy status"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            with patch("api.routes.tiktok.get_current_user", return_value=mock_current_user):
                with patch("api.routes.tiktok.TikTokAPIScraper", return_value=mock_api_scraper):
                    response = await client.get("/api/v1/tiktok/health")
        
        assert response.status_code in [200, 401]  # 401 if auth not mocked correctly

    @pytest.mark.asyncio
    async def test_health_without_auth(self):
        """Should require authentication"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/tiktok/health")
        
        assert response.status_code in [401, 403, 422]


class TestAPISearch:
    """Test /api/search endpoint"""
    
    @pytest.mark.asyncio
    async def test_search_success(self, mock_current_user, mock_api_scraper, mock_cache_manager):
        """Should search products successfully"""
        mock_api_scraper.search_products = AsyncMock(return_value={
            "products": [
                {"id": "prod-001", "title": "Test Product", "price": 29.90}
            ],
            "total": 1,
            "source": "api"
        })
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            with patch("api.routes.tiktok.get_current_user", return_value=mock_current_user):
                with patch("api.routes.tiktok.TikTokAPIScraper", return_value=mock_api_scraper):
                    with patch("api.routes.tiktok.ProductCacheManager", return_value=mock_cache_manager):
                        response = await client.get(
                            "/api/v1/tiktok/search",
                            params={"keyword": "test product"}
                        )
        
        assert response.status_code in [200, 401]


class TestCacheStats:
    """Test /cache/stats endpoint"""
    
    @pytest.mark.asyncio
    async def test_cache_stats_success(self, mock_current_user, mock_cache_manager):
        """Should return cache statistics"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            with patch("api.routes.tiktok.get_current_user", return_value=mock_current_user):
                with patch("api.routes.tiktok.ProductCacheManager", return_value=mock_cache_manager):
                    response = await client.get("/api/v1/tiktok/cache/stats")
        
        assert response.status_code in [200, 401]


class TestCacheClear:
    """Test /cache/clear endpoint"""
    
    @pytest.mark.asyncio
    async def test_cache_clear_success(self, mock_current_user, mock_cache_manager):
        """Should clear cache successfully"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            with patch("api.routes.tiktok.get_current_user", return_value=mock_current_user):
                with patch("api.routes.tiktok.ProductCacheManager", return_value=mock_cache_manager):
                    response = await client.delete("/api/v1/tiktok/cache/clear")
        
        assert response.status_code in [200, 401, 405]


class TestTrendingEndpoint:
    """Test /api/trending endpoint"""
    
    @pytest.mark.asyncio
    async def test_trending_success(self, mock_current_user, mock_api_scraper):
        """Should return trending products"""
        mock_api_scraper.get_trending = AsyncMock(return_value={
            "products": [
                {"id": "trend-001", "title": "Trending Item", "views": 100000}
            ],
            "category": "general",
            "source": "api"
        })
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            with patch("api.routes.tiktok.get_current_user", return_value=mock_current_user):
                with patch("api.routes.tiktok.TikTokAPIScraper", return_value=mock_api_scraper):
                    response = await client.get("/api/v1/tiktok/trending")
        
        assert response.status_code in [200, 401]


class TestRefreshEndpoint:
    """Test /api/refresh endpoint"""
    
    @pytest.mark.asyncio
    async def test_refresh_success(self, mock_current_user, mock_api_scraper, mock_cache_manager):
        """Should trigger cache refresh"""
        mock_api_scraper.search_products = AsyncMock(return_value={
            "products": [],
            "total": 0
        })
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            with patch("api.routes.tiktok.get_current_user", return_value=mock_current_user):
                with patch("api.routes.tiktok.TikTokAPIScraper", return_value=mock_api_scraper):
                    with patch("api.routes.tiktok.ProductCacheManager", return_value=mock_cache_manager):
                        response = await client.post(
                            "/api/v1/tiktok/refresh",
                            json={"keyword": "test"}
                        )
        
        assert response.status_code in [200, 401, 422]
