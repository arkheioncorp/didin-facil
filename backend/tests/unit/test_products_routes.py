"""
Unit tests for Products Routes
Tests for product search and retrieval endpoints
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestProductSchemas:
    """Tests for product request/response schemas"""

    def test_product_filters_schema(self):
        """Test ProductFilters schema"""
        from api.routes.products import ProductFilters
        
        filters = ProductFilters(
            query="test",
            category="electronics",
            min_price=10.0,
            max_price=100.0,
            min_sales=50
        )
        
        assert filters.query == "test"
        assert filters.min_price == 10.0
        assert filters.max_price == 100.0

    def test_products_response_schema(self):
        """Test ProductsResponse schema"""
        from api.routes.products import ProductsResponse
        
        response = ProductsResponse(
            products=[],
            total=0,
            page=1,
            per_page=20,
            has_more=False,
            cached=False
        )
        
        assert response.total == 0
        assert response.page == 1

    def test_export_request_schema(self):
        """Test ExportRequest schema"""
        from api.routes.products import ExportRequest
        
        request = ExportRequest(
            product_ids=["1", "2", "3"],
            format="csv"
        )
        
        assert len(request.product_ids) == 3
        assert request.format == "csv"


class TestGetProducts:
    """Tests for get_products endpoint"""

    @pytest.fixture
    def mock_user(self):
        return {"id": str(uuid4()), "email": "test@example.com"}

    @pytest.fixture
    def mock_cache(self):
        with patch('api.routes.products.CacheService') as mock:
            cache_instance = MagicMock()
            cache_instance.get = AsyncMock(return_value=None)
            cache_instance.set = AsyncMock()
            cache_instance.build_products_cache_key = MagicMock(
                return_value="test_key"
            )
            mock.return_value = cache_instance
            yield cache_instance

    @pytest.fixture
    def mock_orchestrator(self):
        with patch('api.routes.products.ScraperOrchestrator') as mock:
            orchestrator = MagicMock()
            orchestrator.get_products = AsyncMock()
            mock.return_value = orchestrator
            yield orchestrator

    @pytest.mark.asyncio
    async def test_get_products_success(
        self, mock_user, mock_cache, mock_orchestrator
    ):
        """Test successful products retrieval"""
        from api.routes.products import get_products
        
        mock_orchestrator.get_products.return_value = {
            "products": [
                {"id": "1", "title": "Test", "price": 10.0}
            ],
            "total": 1,
            "page": 1,
            "per_page": 20,
            "has_more": False
        }
        
        result = await get_products(
            page=1,
            per_page=20,
            user=mock_user
        )
        
        assert result.total == 1
        mock_orchestrator.get_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_products_from_cache(
        self, mock_user, mock_cache, mock_orchestrator
    ):
        """Test products from cache"""
        from api.routes.products import get_products
        
        mock_cache.get.return_value = {
            "products": [],
            "total": 0,
            "page": 1,
            "per_page": 20,
            "has_more": False
        }
        
        result = await get_products(
            page=1,
            per_page=20,
            user=mock_user
        )
        
        assert result.cached is True
        mock_orchestrator.get_products.assert_not_called()


class TestSearchProducts:
    """Tests for search_products endpoint"""

    @pytest.fixture
    def mock_user(self):
        return {"id": str(uuid4()), "email": "test@example.com"}

    @pytest.fixture
    def mock_cache(self):
        with patch('api.routes.products.CacheService') as mock:
            cache_instance = MagicMock()
            cache_instance.get = AsyncMock(return_value=None)
            cache_instance.set = AsyncMock()
            mock.return_value = cache_instance
            yield cache_instance

    @pytest.fixture
    def mock_orchestrator(self):
        with patch('api.routes.products.ScraperOrchestrator') as mock:
            orchestrator = MagicMock()
            orchestrator.search_products = AsyncMock()
            mock.return_value = orchestrator
            yield orchestrator

    @pytest.mark.asyncio
    async def test_search_products_success(
        self, mock_user, mock_cache, mock_orchestrator
    ):
        """Test successful product search"""
        from api.routes.products import search_products
        
        mock_orchestrator.search_products.return_value = {
            "products": [
                {"id": "1", "title": "Phone", "price": 999.0}
            ],
            "total": 1,
            "page": 1,
            "per_page": 20,
            "has_more": False
        }
        
        result = await search_products(
            q="phone",
            page=1,
            per_page=20,
            user=mock_user
        )
        
        assert result.total == 1
        mock_orchestrator.search_products.assert_called_once()


class TestTrendingProducts:
    """Tests for trending products endpoint"""

    @pytest.fixture
    def mock_user(self):
        return {"id": str(uuid4()), "email": "test@example.com"}

    @pytest.fixture
    def mock_cache(self):
        with patch('api.routes.products.CacheService') as mock:
            cache_instance = MagicMock()
            cache_instance.get = AsyncMock(return_value=None)
            cache_instance.set = AsyncMock()
            mock.return_value = cache_instance
            yield cache_instance

    @pytest.fixture
    def mock_orchestrator(self):
        with patch('api.routes.products.ScraperOrchestrator') as mock:
            orchestrator = MagicMock()
            orchestrator.get_trending_products = AsyncMock()
            mock.return_value = orchestrator
            yield orchestrator

    @pytest.mark.asyncio
    async def test_get_trending_success(
        self, mock_user, mock_cache, mock_orchestrator
    ):
        """Test trending products retrieval"""
        from api.routes.products import get_trending_products
        
        mock_orchestrator.get_trending_products.return_value = {
            "products": [
                {"id": "1", "title": "Trending 1", "trending_score": 95.0}
            ],
            "total": 1,
            "page": 1,
            "per_page": 20,
            "has_more": False
        }
        
        result = await get_trending_products(
            page=1,
            per_page=20,
            user=mock_user
        )
        
        assert result.total == 1
        mock_orchestrator.get_trending_products.assert_called_once()


class TestGetCategories:
    """Tests for get_categories endpoint"""

    @pytest.fixture
    def mock_user(self):
        return {"id": str(uuid4()), "email": "test@example.com"}

    @pytest.fixture
    def mock_cache(self):
        with patch('api.routes.products.CacheService') as mock:
            cache_instance = MagicMock()
            cache_instance.get = AsyncMock(return_value=None)
            cache_instance.set = AsyncMock()
            mock.return_value = cache_instance
            yield cache_instance

    @pytest.fixture
    def mock_orchestrator(self):
        with patch('api.routes.products.ScraperOrchestrator') as mock:
            orchestrator = MagicMock()
            orchestrator.get_categories = AsyncMock(return_value=[
                {"id": "1", "name": "Electronics"},
                {"id": "2", "name": "Fashion"}
            ])
            mock.return_value = orchestrator
            yield orchestrator

    @pytest.mark.asyncio
    async def test_get_categories_success(
        self, mock_user, mock_cache, mock_orchestrator
    ):
        """Test categories retrieval"""
        from api.routes.products import get_categories
        
        result = await get_categories(user=mock_user)
        
        assert len(result) == 2
        mock_orchestrator.get_categories.assert_called_once()


class TestExportProducts:
    """Tests for export_products endpoint"""

    @pytest.fixture
    def mock_user(self):
        return {"id": str(uuid4()), "email": "test@example.com"}

    @pytest.mark.asyncio
    async def test_export_csv(self, mock_user):
        """Test CSV export"""
        from api.routes.products import export_products, ExportRequest
        
        request = ExportRequest(
            product_ids=["1", "2"],
            format="csv"
        )
        
        result = await export_products(request, mock_user)
        
        # Should return a Response object
        assert result.media_type == "text/csv"

    @pytest.mark.asyncio
    async def test_export_returns_response(self, mock_user):
        """Test export returns valid response"""
        from api.routes.products import export_products, ExportRequest
        from fastapi import Response
        
        request = ExportRequest(
            product_ids=["1"],
            format="csv"
        )
        
        result = await export_products(request, mock_user)
        
        assert isinstance(result, Response)


class TestProductStats:
    """Tests for product stats endpoint"""

    @pytest.fixture
    def mock_user(self):
        return {"id": str(uuid4()), "email": "test@example.com"}

    @pytest.mark.asyncio
    async def test_get_product_stats(self, mock_user):
        """Test product stats retrieval"""
        from api.routes.products import get_product_stats
        
        result = await get_product_stats(user=mock_user)
        
        assert "total" in result
        assert "trending" in result
        assert "categories" in result
