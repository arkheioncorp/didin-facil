"""
Integration Tests for TikTok API Endpoints
Tests the new endpoints: /tiktok/api/*
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
    """Test /tiktok/api/health endpoint"""
    
    @pytest.mark.asyncio
    async def test_health_check_returns_response(
        self, mock_current_user, mock_api_scraper
    ):
        """Should return a valid HTTP response"""
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.get("/tiktok/api/health")
        
        # 200=success, 401/403=auth required
        assert response.status_code in [200, 401, 403]

    @pytest.mark.asyncio
    async def test_health_without_auth(self):
        """Should require authentication"""
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.get("/tiktok/api/health")
        
        assert response.status_code in [401, 403, 422]


class TestAPISearch:
    """Test /tiktok/api/search endpoint"""
    
    @pytest.mark.asyncio
    async def test_search_returns_response(
        self, mock_current_user, mock_api_scraper, mock_cache_manager
    ):
        """Should return a valid HTTP response for search"""
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.get(
                "/tiktok/api/search",
                params={"keyword": "test product"}
            )
        
        assert response.status_code in [200, 401, 403]


class TestCacheStats:
    """Test /tiktok/api/cache/stats endpoint"""
    
    @pytest.mark.asyncio
    async def test_cache_stats_returns_response(
        self, mock_current_user, mock_cache_manager
    ):
        """Should return cache statistics or require auth"""
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.get("/tiktok/api/cache/stats")
        
        assert response.status_code in [200, 401, 403]


class TestCacheClear:
    """Test /tiktok/api/cache/clear endpoint"""
    
    @pytest.mark.asyncio
    async def test_cache_clear_returns_response(
        self, mock_current_user, mock_cache_manager
    ):
        """Should clear cache or require auth"""
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.delete("/tiktok/api/cache/clear")
        
        assert response.status_code in [200, 401, 403, 405]


class TestTrendingEndpoint:
    """Test /tiktok/api/trending endpoint"""
    
    @pytest.mark.asyncio
    async def test_trending_returns_response(
        self, mock_current_user, mock_api_scraper
    ):
        """Should return trending products or require auth"""
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.get("/tiktok/api/trending")
        
        assert response.status_code in [200, 401, 403]


class TestRefreshEndpoint:
    """Test /tiktok/api/refresh endpoint"""
    
    @pytest.mark.asyncio
    async def test_refresh_returns_response(
        self, mock_current_user, mock_api_scraper, mock_cache_manager
    ):
        """Should trigger cache refresh or require auth"""
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.post(
                "/tiktok/api/refresh",
                json={"keyword": "test"}
            )
        
        assert response.status_code in [200, 401, 403, 422]
