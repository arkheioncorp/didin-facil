"""
Products Routes Tests - Full Coverage
Tests for product endpoints using AsyncClient.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from api.main import app
from api.routes.products import get_current_user


@pytest_asyncio.fixture
async def async_client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def mock_services():
    """Mock CacheService and ScraperOrchestrator."""
    with patch("api.routes.products.CacheService") as cache_cls, \
         patch("api.routes.products.ScraperOrchestrator") as scraper_cls:

        cache = AsyncMock()
        cache.build_products_cache_key = MagicMock(return_value="cache_key")

        scraper = AsyncMock()

        cache_cls.return_value = cache
        scraper_cls.return_value = scraper

        yield cache, scraper


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user."""
    user = {
        "id": "user_123",
        "email": "test@example.com",
        "plan": "lifetime",
        "credits": 100
    }
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_products_cached(mock_services, mock_auth_user, async_client):
    """Test getting products from cache."""
    cache, _ = mock_services

    cached_data = {
        "products": [],
        "total": 0,
        "page": 1,
        "per_page": 20,
        "has_more": False
    }
    cache.get.return_value = cached_data

    response = await async_client.get("/products")

    assert response.status_code == 200
    data = response.json()
    assert data["cached"] is True
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_products_uncached(mock_services, mock_auth_user, async_client):
    """Test getting products when not cached."""
    cache, scraper = mock_services

    cache.get.return_value = None
    scraper.get_products.return_value = {
        "products": [
            {"id": "p1", "title": "Product 1", "sales_count": 10, "review_count": 5}
        ],
        "total": 1,
        "page": 1,
        "per_page": 20,
        "has_more": False
    }

    response = await async_client.get("/products")

    assert response.status_code == 200
    data = response.json()
    assert data["cached"] is False
    assert len(data["products"]) == 1
    assert data["products"][0]["title"] == "Product 1"

    cache.set.assert_called_once()


@pytest.mark.asyncio
async def test_search_products(mock_services, mock_auth_user, async_client):
    """Test searching products."""
    cache, scraper = mock_services

    cache.get.return_value = None
    scraper.search_products.return_value = {
        "products": [
            {"id": "p1", "title": "Search Result", "sales_count": 10, "review_count": 5}
        ],
        "total": 1,
        "page": 1,
        "per_page": 20,
        "has_more": False
    }

    response = await async_client.get("/products/search?q=test")

    assert response.status_code == 200
    data = response.json()
    assert data["products"][0]["title"] == "Search Result"
    scraper.search_products.assert_called_with(query="test", page=1, per_page=20)


@pytest.mark.asyncio
async def test_get_trending_products(mock_services, mock_auth_user, async_client):
    """Test getting trending products."""
    cache, scraper = mock_services

    cache.get.return_value = None
    scraper.get_trending_products.return_value = {
        "products": [
            {"id": "p1", "title": "Trending", "sales_count": 100, "review_count": 50}
        ],
        "total": 1,
        "page": 1,
        "per_page": 20,
        "has_more": False
    }

    response = await async_client.get("/products/trending")

    assert response.status_code == 200
    data = response.json()
    assert data["products"][0]["title"] == "Trending"


@pytest.mark.asyncio
async def test_get_categories(mock_services, mock_auth_user, async_client):
    """Test getting categories."""
    cache, scraper = mock_services

    cache.get.return_value = None
    scraper.get_categories.return_value = ["Electronics", "Fashion"]

    response = await async_client.get("/products/categories")

    assert response.status_code == 200
    assert response.json() == ["Electronics", "Fashion"]
    cache.set.assert_called_with(
        "categories",
        ["Electronics", "Fashion"],
        ttl=86400
    )


@pytest.mark.asyncio
async def test_get_product_by_id_found(mock_services, mock_auth_user, async_client):
    """Test getting product by ID when found."""
    cache, scraper = mock_services

    cache.get.return_value = None
    scraper.get_product_by_id.return_value = {
        "id": "p1",
        "title": "Product 1",
        "sales_count": 10,
        "review_count": 5
    }

    response = await async_client.get("/products/p1")

    assert response.status_code == 200
    assert response.json()["title"] == "Product 1"


@pytest.mark.asyncio
async def test_get_product_by_id_not_found(
    mock_services,
    mock_auth_user,
    async_client
):
    """Test getting product by ID when not found."""
    cache, scraper = mock_services

    cache.get.return_value = None
    scraper.get_product_by_id.return_value = None

    response = await async_client.get("/products/unknown")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_refresh_products_success(mock_services, async_client):
    """Test refreshing products."""
    _, scraper = mock_services

    pro_user = {
        "id": "user_123",
        "email": "test@example.com",
        "plan": "pro",
        "credits": 100
    }
    app.dependency_overrides[get_current_user] = lambda: pro_user

    scraper.enqueue_refresh_job.return_value = "job_123"

    response = await async_client.post("/products/refresh")

    assert response.status_code == 200
    assert response.json()["job_id"] == "job_123"

    app.dependency_overrides = {}
