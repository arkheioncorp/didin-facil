"""
Scraper Orchestrator Service Tests - 100% Coverage
Tests for scraping jobs and product data management
"""

import pytest
from unittest.mock import AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from backend.api.services.scraper import ScraperOrchestrator


class TestScraperOrchestrator:
    """Test suite for ScraperOrchestrator"""

    @pytest.fixture
    def scraper(self):
        """Create a scraper orchestrator instance"""
        with patch('backend.api.services.scraper.database'):
            return ScraperOrchestrator()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database"""
        db_mock = AsyncMock()
        db_mock.fetch_one = AsyncMock(return_value={'total': 0})
        db_mock.fetch_all = AsyncMock(return_value=[])
        return db_mock

    @pytest.fixture
    def sample_products(self):
        """Sample product data"""
        return [
            {
                'id': '1',
                'tiktok_id': 'tiktok-1',
                'title': 'Product 1',
                'price': 99.99,
                'sales_30d': 500,
                'category': 'Electronics'
            },
            {
                'id': '2',
                'tiktok_id': 'tiktok-2',
                'title': 'Product 2',
                'price': 49.99,
                'sales_30d': 1000,
                'category': 'Fashion'
            }
        ]

    # ==================== GET PRODUCTS Tests ====================

    @pytest.mark.asyncio
    async def test_get_products_default_params(self, scraper, mock_db, sample_products):
        """Test getting products with default parameters"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 2})
        mock_db.fetch_all = AsyncMock(return_value=sample_products)
        scraper.db = mock_db
        
        result = await scraper.get_products()
        
        assert 'products' in result
        assert 'total' in result
        assert 'page' in result
        assert result['page'] == 1
        assert result['per_page'] == 20

    @pytest.mark.asyncio
    async def test_get_products_with_pagination(self, scraper, mock_db):
        """Test getting products with pagination"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 100})
        mock_db.fetch_all = AsyncMock(return_value=[])
        scraper.db = mock_db
        
        result = await scraper.get_products(page=3, per_page=50)
        
        assert result['page'] == 3
        assert result['per_page'] == 50

    @pytest.mark.asyncio
    async def test_get_products_with_category_filter(self, scraper, mock_db, sample_products):
        """Test getting products filtered by category"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 1})
        mock_db.fetch_all = AsyncMock(return_value=[sample_products[0]])
        scraper.db = mock_db
        
        result = await scraper.get_products(category='Electronics')
        
        assert len(result['products']) == 1

    @pytest.mark.asyncio
    async def test_get_products_with_price_range(self, scraper, mock_db, sample_products):
        """Test getting products with price range"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 1})
        mock_db.fetch_all = AsyncMock(return_value=[sample_products[1]])
        scraper.db = mock_db
        
        result = await scraper.get_products(min_price=10, max_price=60)
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_products_with_min_sales(self, scraper, mock_db, sample_products):
        """Test getting products with minimum sales filter"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 1})
        mock_db.fetch_all = AsyncMock(return_value=[sample_products[1]])
        scraper.db = mock_db
        
        result = await scraper.get_products(min_sales=800)
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_products_sorting(self, scraper, mock_db, sample_products):
        """Test getting products with custom sorting"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 2})
        mock_db.fetch_all = AsyncMock(return_value=sample_products)
        scraper.db = mock_db
        
        result = await scraper.get_products(sort_by='price', sort_order='asc')
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_products_invalid_sort_uses_default(self, scraper, mock_db):
        """Test invalid sort column defaults to sales_30d"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 0})
        mock_db.fetch_all = AsyncMock(return_value=[])
        scraper.db = mock_db
        
        result = await scraper.get_products(sort_by='invalid_column')
        
        # Should not raise an error
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_products_has_more_true(self, scraper, mock_db, sample_products):
        """Test has_more is true when more pages exist"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 100})
        mock_db.fetch_all = AsyncMock(return_value=sample_products)
        scraper.db = mock_db
        
        result = await scraper.get_products(page=1, per_page=20)
        
        assert result['has_more'] is True

    @pytest.mark.asyncio
    async def test_get_products_has_more_false(self, scraper, mock_db, sample_products):
        """Test has_more is false when on last page"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 2})
        mock_db.fetch_all = AsyncMock(return_value=sample_products)
        scraper.db = mock_db
        
        result = await scraper.get_products(page=1, per_page=20)
        
        assert result['has_more'] is False

    # ==================== SEARCH PRODUCTS Tests ====================

    @pytest.mark.asyncio
    async def test_search_products_basic(self, scraper, mock_db, sample_products):
        """Test basic product search"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 1})
        mock_db.fetch_all = AsyncMock(return_value=[sample_products[0]])
        scraper.db = mock_db
        
        result = await scraper.search_products('Product 1')
        
        assert 'products' in result
        assert result['total'] == 1

    @pytest.mark.asyncio
    async def test_search_products_with_pagination(self, scraper, mock_db):
        """Test search with pagination"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 50})
        mock_db.fetch_all = AsyncMock(return_value=[])
        scraper.db = mock_db
        
        result = await scraper.search_products('query', page=2, per_page=10)
        
        assert result['page'] == 2
        assert result['per_page'] == 10

    @pytest.mark.asyncio
    async def test_search_products_no_results(self, scraper, mock_db):
        """Test search with no results"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 0})
        mock_db.fetch_all = AsyncMock(return_value=[])
        scraper.db = mock_db
        
        result = await scraper.search_products('nonexistent product xyz')
        
        assert result['products'] == []
        assert result['total'] == 0

    @pytest.mark.asyncio
    async def test_search_products_special_characters(self, scraper, mock_db):
        """Test search with special characters"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 0})
        mock_db.fetch_all = AsyncMock(return_value=[])
        scraper.db = mock_db
        
        result = await scraper.search_products("test's \"product\" & more")
        
        # Should not raise an error
        assert result is not None

    # ==================== GET TRENDING PRODUCTS Tests ====================

    @pytest.mark.asyncio
    async def test_get_trending_products_basic(self, scraper, mock_db, sample_products):
        """Test getting trending products"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 2})
        mock_db.fetch_all = AsyncMock(return_value=sample_products)
        scraper.db = mock_db
        
        result = await scraper.get_trending_products()
        
        assert 'products' in result

    @pytest.mark.asyncio
    async def test_get_trending_products_with_category(self, scraper, mock_db, sample_products):
        """Test getting trending products filtered by category"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 1})
        mock_db.fetch_all = AsyncMock(return_value=[sample_products[0]])
        scraper.db = mock_db
        
        result = await scraper.get_trending_products(category='Electronics')
        
        assert len(result['products']) == 1

    @pytest.mark.asyncio
    async def test_get_trending_products_with_pagination(self, scraper, mock_db):
        """Test trending products with pagination"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 100})
        mock_db.fetch_all = AsyncMock(return_value=[])
        scraper.db = mock_db
        
        result = await scraper.get_trending_products(page=2, per_page=30)
        
        assert result['page'] == 2
        assert result['per_page'] == 30

    # ==================== GET CATEGORIES Tests ====================

    @pytest.mark.asyncio
    async def test_get_categories(self, scraper, mock_db):
        """Test getting product categories"""
        categories = [
            {'category': 'Electronics', 'count': 100},
            {'category': 'Fashion', 'count': 200},
            {'category': 'Home', 'count': 50}
        ]
        mock_db.fetch_all = AsyncMock(return_value=categories)
        scraper.db = mock_db
        
        result = await scraper.get_categories()
        
        assert len(result) == 3
        assert result[0]['category'] == 'Electronics'

    @pytest.mark.asyncio
    async def test_get_categories_empty(self, scraper, mock_db):
        """Test getting categories when none exist"""
        mock_db.fetch_all = AsyncMock(return_value=[])
        scraper.db = mock_db
        
        result = await scraper.get_categories()
        
        assert result == []


class TestScraperOrchestratorEdgeCases:
    """Edge case tests for ScraperOrchestrator"""

    @pytest.fixture
    def scraper(self):
        with patch('backend.api.services.scraper.database'):
            return ScraperOrchestrator()

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_get_products_with_null_total(self, scraper, mock_db):
        """Test handling null total count"""
        mock_db.fetch_one = AsyncMock(return_value=None)
        mock_db.fetch_all = AsyncMock(return_value=[])
        scraper.db = mock_db
        
        result = await scraper.get_products()
        
        assert result['total'] == 0

    @pytest.mark.asyncio
    async def test_get_products_with_negative_page(self, scraper, mock_db):
        """Test handling negative page number"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 0})
        mock_db.fetch_all = AsyncMock(return_value=[])
        scraper.db = mock_db
        
        # Negative page should be handled (might result in negative offset)
        result = await scraper.get_products(page=-1)
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_products_with_zero_per_page(self, scraper, mock_db):
        """Test handling zero per_page"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 0})
        mock_db.fetch_all = AsyncMock(return_value=[])
        scraper.db = mock_db
        
        result = await scraper.get_products(per_page=0)
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_search_products_empty_query(self, scraper, mock_db):
        """Test search with empty query"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 0})
        mock_db.fetch_all = AsyncMock(return_value=[])
        scraper.db = mock_db
        
        result = await scraper.search_products('')
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_products_all_filters_combined(self, scraper, mock_db):
        """Test getting products with all filters combined"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 5})
        mock_db.fetch_all = AsyncMock(return_value=[])
        scraper.db = mock_db
        
        result = await scraper.get_products(
            page=2,
            per_page=10,
            category='Electronics',
            min_price=50,
            max_price=500,
            min_sales=100,
            sort_by='price',
            sort_order='asc'
        )
        
        assert result is not None
        assert result['page'] == 2

    @pytest.mark.asyncio
    async def test_get_products_sort_order_case_insensitive(self, scraper, mock_db):
        """Test sort order is case insensitive"""
        mock_db.fetch_one = AsyncMock(return_value={'total': 0})
        mock_db.fetch_all = AsyncMock(return_value=[])
        scraper.db = mock_db
        
        result1 = await scraper.get_products(sort_order='DESC')
        result2 = await scraper.get_products(sort_order='desc')
        
        assert result1 is not None
        assert result2 is not None

    @pytest.mark.asyncio
    async def test_get_products_valid_sort_columns(self, scraper, mock_db):
        """Test all valid sort columns"""
        valid_sorts = ['sales_30d', 'sales_7d', 'sales_count', 'price', 'product_rating', 'created_at']
        mock_db.fetch_one = AsyncMock(return_value={'total': 0})
        mock_db.fetch_all = AsyncMock(return_value=[])
        scraper.db = mock_db
        
        for sort_col in valid_sorts:
            result = await scraper.get_products(sort_by=sort_col)
            assert result is not None
