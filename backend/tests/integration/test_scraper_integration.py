"""
Scraper Service Integration Tests
Tests for save_products (upsert) and get_products (complex filters)
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import uuid

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from api.services.scraper import ScraperOrchestrator, format_product


class TestFormatProduct:
    """Test format_product function edge cases"""
    
    def test_format_product_with_string_images(self):
        """Test formatting product with JSON string images"""
        row = MagicMock()
        row_dict = {
            "id": uuid.uuid4(),
            "title": "Test Product",
            "images": '["img1.jpg", "img2.jpg"]',
            "metadata": '{"key": "value"}'
        }
        row.__iter__ = lambda s: iter(row_dict.items())
        row.keys = lambda: row_dict.keys()
        row.__getitem__ = lambda s, k: row_dict[k]
        
        result = format_product(row_dict)
        
        assert isinstance(result["images"], list)
        assert result["images"] == ["img1.jpg", "img2.jpg"]
        assert isinstance(result["metadata"], dict)
        assert result["metadata"] == {"key": "value"}
    
    def test_format_product_with_invalid_images_json(self):
        """Test formatting product with invalid JSON in images"""
        row_dict = {
            "id": uuid.uuid4(),
            "title": "Test Product",
            "images": "not valid json",
            "metadata": "also not valid"
        }
        
        result = format_product(row_dict)
        
        assert result["images"] == []
        assert result["metadata"] == {}
    
    def test_format_product_with_none_images(self):
        """Test formatting product with None images"""
        row_dict = {
            "id": uuid.uuid4(),
            "title": "Test Product",
            "images": None,
            "metadata": None
        }
        
        result = format_product(row_dict)
        
        assert result["images"] == []
        assert result["metadata"] == {}
    
    def test_format_product_with_already_parsed_data(self):
        """Test formatting product with already parsed lists/dicts"""
        row_dict = {
            "id": uuid.uuid4(),
            "title": "Test Product",
            "images": ["already", "parsed"],
            "metadata": {"already": "parsed"}
        }
        
        result = format_product(row_dict)
        
        assert result["images"] == ["already", "parsed"]
        assert result["metadata"] == {"already": "parsed"}


class TestScraperOrchestratorIntegration:
    """Integration tests for ScraperOrchestrator"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a comprehensive mock database"""
        db = AsyncMock()
        db.fetch_one = AsyncMock()
        db.fetch_all = AsyncMock()
        db.execute = AsyncMock()
        db.execute_many = AsyncMock()
        return db
    
    @pytest.fixture
    def scraper(self, mock_db):
        """Create a scraper with mocked db"""
        with patch('api.services.scraper.database', mock_db):
            s = ScraperOrchestrator()
            s.db = mock_db
            return s
    
    @pytest.fixture
    def sample_product_row(self):
        """Create a sample product row as returned from DB"""
        return {
            "id": str(uuid.uuid4()),
            "tiktok_id": "tiktok_123",
            "title": "Test Product",
            "description": "A great product",
            "price": 99.90,
            "original_price": 149.90,
            "currency": "BRL",
            "category": "electronics",
            "subcategory": "audio",
            "seller_name": "Test Seller",
            "seller_rating": 4.5,
            "product_rating": 4.8,
            "reviews_count": 150,
            "sales_count": 2500,
            "sales_7d": 350,
            "sales_30d": 1200,
            "commission_rate": 10.0,
            "image_url": "https://example.com/img.jpg",
            "images": [],
            "video_url": None,
            "product_url": "https://tiktok.com/product/123",
            "affiliate_url": None,
            "has_free_shipping": True,
            "is_trending": True,
            "is_on_sale": True,
            "in_stock": True,
            "collected_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    # ==================== SAVE_PRODUCTS (UPSERT) Tests ====================
    
    @pytest.mark.asyncio
    async def test_save_products_empty_list(self, scraper, mock_db):
        """Test saving empty product list returns 0"""
        result = await scraper.save_products([])
        
        assert result == 0
        mock_db.execute_many.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_save_products_single_product(self, scraper, mock_db, sample_product_row):
        """Test saving a single product"""
        products = [sample_product_row]
        
        result = await scraper.save_products(products)
        
        assert result == 1
        mock_db.execute_many.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_products_batch_processing(self, scraper, mock_db, sample_product_row):
        """Test saving products in batches of 100"""
        # Create 250 products to test batching (should be 3 batches: 100, 100, 50)
        products = []
        for i in range(250):
            p = sample_product_row.copy()
            p["id"] = str(uuid.uuid4())
            p["tiktok_id"] = f"tiktok_{i}"
            products.append(p)
        
        result = await scraper.save_products(products)
        
        assert result == 250
        # Should have been called 3 times (100, 100, 50)
        assert mock_db.execute_many.call_count == 3
    
    @pytest.mark.asyncio
    async def test_save_products_upsert_on_conflict(self, scraper, mock_db, sample_product_row):
        """Test that ON CONFLICT DO UPDATE is in the query"""
        products = [sample_product_row]
        
        await scraper.save_products(products)
        
        # Verify the query contains ON CONFLICT for upsert behavior
        call_args = mock_db.execute_many.call_args
        query = call_args[0][0]  # First positional argument is the query
        
        assert "ON CONFLICT (tiktok_id) DO UPDATE" in query
        assert "title = EXCLUDED.title" in query
        assert "sales_count = EXCLUDED.sales_count" in query
    
    # ==================== GET_PRODUCTS (Complex Filters) Tests ====================
    
    @pytest.mark.asyncio
    async def test_get_products_all_filters_combined(self, scraper, mock_db, sample_product_row):
        """Test get_products with all filters combined"""
        mock_db.fetch_one = AsyncMock(return_value={"total": 5})
        mock_db.fetch_all = AsyncMock(return_value=[sample_product_row])
        
        result = await scraper.get_products(
            page=2,
            per_page=10,
            category="electronics",
            min_price=50.0,
            max_price=200.0,
            min_sales=100,
            sort_by="price",
            sort_order="asc"
        )
        
        assert result["page"] == 2
        assert result["per_page"] == 10
        assert result["total"] == 5
        assert len(result["products"]) == 1
        
        # Verify filter parameters were passed correctly
        query_params = mock_db.fetch_all.call_args[0][1]
        assert query_params["category"] == "electronics"
        assert query_params["min_price"] == 50.0
        assert query_params["max_price"] == 200.0
        assert query_params["min_sales"] == 100
    
    @pytest.mark.asyncio
    async def test_get_products_invalid_sort_column_fallback(self, scraper, mock_db):
        """Test that invalid sort column falls back to sales_30d"""
        mock_db.fetch_one = AsyncMock(return_value={"total": 0})
        mock_db.fetch_all = AsyncMock(return_value=[])
        
        await scraper.get_products(sort_by="invalid_column")
        
        # Verify the query uses sales_30d as fallback
        query = mock_db.fetch_all.call_args[0][0]
        assert "ORDER BY sales_30d" in query
    
    @pytest.mark.asyncio
    async def test_get_products_sort_order_asc(self, scraper, mock_db):
        """Test ascending sort order"""
        mock_db.fetch_one = AsyncMock(return_value={"total": 0})
        mock_db.fetch_all = AsyncMock(return_value=[])
        
        await scraper.get_products(sort_order="asc")
        
        query = mock_db.fetch_all.call_args[0][0]
        assert "ASC" in query
    
    @pytest.mark.asyncio
    async def test_get_products_has_more_pagination(self, scraper, mock_db, sample_product_row):
        """Test has_more flag for pagination"""
        # 25 total, page 1, per_page 10 -> has_more should be True
        mock_db.fetch_one = AsyncMock(return_value={"total": 25})
        mock_db.fetch_all = AsyncMock(return_value=[sample_product_row] * 10)
        
        result = await scraper.get_products(page=1, per_page=10)
        assert result["has_more"] is True
        
        # Page 3 with 25 total and per_page 10 -> has_more should be False
        result = await scraper.get_products(page=3, per_page=10)
        assert result["has_more"] is False
    
    @pytest.mark.asyncio
    async def test_get_products_no_filters(self, scraper, mock_db):
        """Test get_products with no filters (defaults only)"""
        mock_db.fetch_one = AsyncMock(return_value={"total": 0})
        mock_db.fetch_all = AsyncMock(return_value=[])
        
        result = await scraper.get_products()
        
        assert result["page"] == 1
        assert result["per_page"] == 20
        
        # Verify WHERE clause only has deleted_at IS NULL
        count_query = mock_db.fetch_one.call_args[0][0]
        assert "deleted_at IS NULL" in count_query
    
    # ==================== SEARCH_PRODUCTS Tests ====================
    
    @pytest.mark.asyncio
    async def test_search_products_basic(self, scraper, mock_db, sample_product_row):
        """Test basic product search"""
        mock_db.fetch_one = AsyncMock(return_value={"total": 1})
        mock_db.fetch_all = AsyncMock(return_value=[sample_product_row])
        
        result = await scraper.search_products("Test", page=1, per_page=10)
        
        assert result["total"] == 1
        assert len(result["products"]) == 1
        
        # Verify ILIKE is used for search
        query = mock_db.fetch_all.call_args[0][0]
        assert "ILIKE" in query
        assert "title" in query.lower() or "description" in query.lower()
    
    @pytest.mark.asyncio
    async def test_search_products_pagination(self, scraper, mock_db):
        """Test search with pagination"""
        mock_db.fetch_one = AsyncMock(return_value={"total": 50})
        mock_db.fetch_all = AsyncMock(return_value=[])
        
        result = await scraper.search_products("product", page=3, per_page=15)
        
        assert result["page"] == 3
        assert result["per_page"] == 15
        
        # Verify offset is calculated correctly
        query_params = mock_db.fetch_all.call_args[0][1]
        assert query_params["offset"] == 30  # (3-1) * 15
    
    # ==================== GET_TRENDING_PRODUCTS Tests ====================
    
    @pytest.mark.asyncio
    async def test_get_trending_products(self, scraper, mock_db, sample_product_row):
        """Test getting trending products"""
        mock_db.fetch_one = AsyncMock(return_value={"total": 10})
        mock_db.fetch_all = AsyncMock(return_value=[sample_product_row])
        
        result = await scraper.get_trending_products(page=1, per_page=20, category="electronics")
        
        assert result["total"] == 10
        
        # Verify ORDER BY trending_score
        query = mock_db.fetch_all.call_args[0][0]
        assert "trending_score DESC" in query
    
    @pytest.mark.asyncio
    async def test_get_trending_products_no_category(self, scraper, mock_db):
        """Test trending products without category filter"""
        mock_db.fetch_one = AsyncMock(return_value={"total": 0})
        mock_db.fetch_all = AsyncMock(return_value=[])
        
        await scraper.get_trending_products()
        
        # Verify category filter is not in query
        count_params = mock_db.fetch_one.call_args[0][1]
        assert count_params is None or "category" not in count_params
    
    # ==================== GET_CATEGORIES Tests ====================
    
    @pytest.mark.asyncio
    async def test_get_categories(self, scraper, mock_db):
        """Test getting category list with counts"""
        mock_db.fetch_all = AsyncMock(return_value=[
            {"category": "electronics", "count": 150},
            {"category": "fashion", "count": 120},
            {"category": "home", "count": 80}
        ])
        
        result = await scraper.get_categories()
        
        assert len(result) == 3
        assert result[0]["name"] == "electronics"
        assert result[0]["count"] == 150
    
    # ==================== GET_PRODUCT_BY_ID Tests ====================
    
    @pytest.mark.asyncio
    async def test_get_product_by_id_found(self, scraper, mock_db, sample_product_row):
        """Test getting product by ID when found"""
        mock_db.fetch_one = AsyncMock(return_value=sample_product_row)
        
        result = await scraper.get_product_by_id("product-123")
        
        assert result is not None
        assert result["title"] == "Test Product"
    
    @pytest.mark.asyncio
    async def test_get_product_by_id_not_found(self, scraper, mock_db):
        """Test getting product by ID when not found"""
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        result = await scraper.get_product_by_id("nonexistent-id")
        
        assert result is None
    
    # ==================== JOB QUEUE Tests ====================
    
    @pytest.mark.asyncio
    async def test_enqueue_refresh_job(self, scraper):
        """Test enqueueing a refresh job"""
        mock_redis = AsyncMock()
        mock_redis.lpush = AsyncMock()
        mock_redis.hset = AsyncMock()
        mock_redis.close = AsyncMock()
        
        with patch('api.services.scraper.get_redis_client', return_value=mock_redis):
            job_id = await scraper.enqueue_refresh_job(
                category="electronics",
                user_id="user-123"
            )
        
        assert job_id is not None
        mock_redis.lpush.assert_called_once()
        mock_redis.hset.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_job_status_found(self, scraper):
        """Test getting job status when job exists"""
        mock_redis = AsyncMock()
        mock_redis.hgetall = AsyncMock(return_value={
            "status": "completed",
            "created_at": "2024-01-01T00:00:00"
        })
        mock_redis.close = AsyncMock()
        
        with patch('api.services.scraper.get_redis_client', return_value=mock_redis):
            result = await scraper.get_job_status("job-123")
        
        assert result is not None
        assert result["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self, scraper):
        """Test getting job status when job doesn't exist"""
        mock_redis = AsyncMock()
        mock_redis.hgetall = AsyncMock(return_value={})
        mock_redis.close = AsyncMock()
        
        with patch('api.services.scraper.get_redis_client', return_value=mock_redis):
            result = await scraper.get_job_status("nonexistent-job")
        
        assert result is None
