"""
Pytest Configuration and Fixtures
Shared fixtures for all backend tests
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI


# ============================================
# HTTPX/STARLETTE COMPATIBILITY
# ============================================
# Handle incompatibility between Starlette 0.31.1 and httpx 0.28.1
# where TestClient constructor changed

def _create_test_client(app, **kwargs):
    """Create a test client with compatibility for different httpx versions."""
    try:
        # Try new httpx style with ASGITransport
        from httpx import ASGITransport as Transport
        return AsyncClient(
            transport=Transport(app=app),
            base_url=kwargs.get("base_url", "http://test"),
        )
    except TypeError:
        # Fallback for older versions
        from starlette.testclient import TestClient
        return TestClient(app, **kwargs)


# Set testing environment
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/tiktrend_test"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-12345"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["OPENAI_API_KEY"] = "test-api-key"

from api.main import app


# ============================================
# DEPENDENCY OVERRIDE CLEANUP (AUTOUSE)
# ============================================

@pytest.fixture(autouse=True)
def cleanup_dependency_overrides():
    """
    Automatically clean up dependency_overrides between tests.
    This prevents test pollution when fixtures modify app.dependency_overrides.
    """
    # Store original overrides (usually empty)
    original_overrides = app.dependency_overrides.copy()
    yield
    # Restore original overrides after each test
    app.dependency_overrides = original_overrides


@pytest.fixture(autouse=True)
def reset_rate_limiter_global():
    """
    Reset rate limiter state before each test to prevent 429 errors.
    """
    # Find and reset the rate limiter middleware
    for middleware in app.user_middleware:
        if hasattr(middleware, 'cls') and middleware.cls.__name__ == 'RateLimitMiddleware':
            # Clear any stored state
            if hasattr(middleware, 'kwargs') and 'app' in middleware.kwargs:
                if hasattr(middleware.kwargs['app'], 'request_counts'):
                    middleware.kwargs['app'].request_counts.clear()
    
    # Also clear via app middleware stack
    try:
        from api.middleware.ratelimit import RateLimitMiddleware
        for attr_name in dir(app):
            attr = getattr(app, attr_name, None)
            if isinstance(attr, RateLimitMiddleware):
                if hasattr(attr, 'request_counts'):
                    attr.request_counts.clear()
    except Exception:
        pass
    
    yield


# ============================================
# EVENT LOOP FIXTURE
# ============================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================
# APP FIXTURES
# ============================================

@pytest.fixture
def test_app() -> FastAPI:
    """Get the FastAPI test application."""
    return app


@pytest_asyncio.fixture
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def authenticated_client(
    async_client: AsyncClient,
    mock_auth_service: MagicMock
) -> AsyncClient:
    """Create authenticated async client with JWT token."""
    token = "test-jwt-token"
    async_client.headers["Authorization"] = f"Bearer {token}"
    return async_client


# ============================================
# MOCK FIXTURES
# ============================================

@pytest.fixture
def mock_db():
    """Mock database connection."""
    mock = AsyncMock()
    mock.fetch_one = AsyncMock(return_value=None)
    mock.fetch_all = AsyncMock(return_value=[])
    mock.execute = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def mock_auth_service():
    """Mock authentication service."""
    with patch("api.services.auth.AuthService") as mock:
        service = mock.return_value
        service.authenticate = AsyncMock(return_value={
            "id": "user-123",
            "email": "test@example.com",
            "name": "Test User",
            "plan": "lifetime",
            "credits": 100
        })
        service.validate_hwid = AsyncMock(return_value=True)
        service.create_user = AsyncMock(return_value={
            "id": "user-456",
            "email": "new@example.com",
            "name": "New User",
            "plan": "lifetime",
            "credits": 0
        })
        service.create_token = MagicMock(return_value="test-jwt-token")
        service.verify_token = MagicMock(return_value={
            "sub": "user-123",
            "hwid": "test-hwid"
        })
        yield service


@pytest.fixture
def mock_openai_service():
    """Mock OpenAI service."""
    with patch("api.services.openai.OpenAIService") as mock:
        service = mock.return_value
        service.generate_copy = AsyncMock(return_value={
            "id": str(uuid.uuid4()),
            "copy_text": "This is a mock generated copy for testing purposes.",
            "copy_type": "product_description",
            "tone": "professional",
            "platform": "instagram",
            "word_count": 10,
            "character_count": 56,
            "created_at": datetime.utcnow()
        })
        yield service


@pytest.fixture
def mock_cache_service():
    """Mock cache service."""
    with patch("api.services.cache.CacheService") as mock:
        service = mock.return_value
        service.get = AsyncMock(return_value=None)
        service.set = AsyncMock(return_value=True)
        service.delete = AsyncMock(return_value=True)
        yield service


@pytest.fixture
def mock_credits_service():
    """Mock credits service."""
    with patch("api.services.cache.CreditsService") as mock:
        service = mock.return_value
        service.get_cached_credits = AsyncMock(return_value=100)
        service.set_cached_credits = AsyncMock(return_value=True)
        service.invalidate_credits = AsyncMock(return_value=True)
        yield service


# Keep for backwards compatibility
@pytest.fixture
def mock_quota_service():
    """Mock quota service (deprecated - use mock_credits_service)."""
    with patch("api.services.cache.QuotaService") as mock:
        service = mock.return_value
        service.get_quota = AsyncMock(return_value={"used": 0, "limit": -1})
        yield service


# ============================================
# DATA FIXTURES
# ============================================

@pytest.fixture
def mock_user_data() -> dict:
    """Mock user data."""
    return {
        "id": "user-123",
        "email": "test@example.com",
        "name": "Test User",
        "password_hash": "$2b$12$test-hash",
        "plan": "premium",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_license_data() -> dict:
    """Mock license data."""
    return {
        "id": "license-123",
        "user_id": "user-123",
        "key": "VALID-LICENSE-KEY",
        "plan": "premium",
        "status": "active",
        "max_devices": 3,
        "activated_at": datetime.utcnow() - timedelta(days=30),
        "expires_at": datetime.utcnow() + timedelta(days=335),
        "is_active": True
    }


@pytest.fixture
def mock_product_data() -> dict:
    """Mock product data."""
    return {
        "id": "prod-123",
        "tiktok_id": "tiktok-123",
        "title": "Test Product",
        "description": "A test product description",
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
        "image_url": "https://example.com/image.jpg",
        "images": ["https://example.com/image1.jpg"],
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


@pytest.fixture
def mock_products_list(mock_product_data) -> list:
    """Mock list of products."""
    products = []
    for i in range(5):
        product = mock_product_data.copy()
        product["id"] = f"prod-{i}"
        product["title"] = f"Test Product {i}"
        products.append(product)
    return products


# ============================================
# HELPER FUNCTIONS
# ============================================

def create_test_token(user_id: str = "user-123", hwid: str = "test-hwid") -> str:
    """Create a test JWT token."""
    from jose import jwt
    
    payload = {
        "sub": user_id,
        "hwid": hwid,
        "exp": datetime.utcnow() + timedelta(hours=12),
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, "test-secret-key-for-testing-only-12345", algorithm="HS256")


async def create_test_user(db_mock, user_data: dict) -> dict:
    """Helper to create a test user."""
    db_mock.fetch_one.return_value = user_data
    return user_data


# ============================================
# MARKERS
# ============================================

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (require database)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (require full stack)")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "auth: Authentication related tests")
    config.addinivalue_line("markers", "products: Products related tests")
    config.addinivalue_line("markers", "copy: Copy generation related tests")
    config.addinivalue_line("markers", "license: License management related tests")
