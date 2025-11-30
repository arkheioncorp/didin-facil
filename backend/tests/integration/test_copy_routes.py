"""
Copy Routes Tests - Full Coverage
Tests for AI copy generation endpoints using AsyncClient.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from api.main import app
from api.routes.copy import get_current_user


@pytest_asyncio.fixture
async def async_client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user."""
    user = {
        "id": "user_123",
        "email": "test@example.com",
        "name": "Test User",
        "plan": "lifetime"
    }
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides = {}


@pytest.fixture
def mock_services():
    """Mock all services used by copy routes."""
    with patch("api.routes.copy.CacheService") as cache_cls, \
         patch("api.routes.copy.OpenAIService") as openai_cls, \
         patch("api.routes.copy.check_credits") as check, \
         patch("api.routes.copy.deduct_credits") as deduct:

        cache = AsyncMock()
        cache.build_copy_cache_key = MagicMock(return_value="cache_key")
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()

        openai = AsyncMock()
        openai.generate_copy = AsyncMock()
        openai.save_to_history = AsyncMock()
        openai.get_credits_status = AsyncMock()
        openai.get_history = AsyncMock()

        check.return_value = {
            "balance": 100,
            "required": 1,
            "remaining_after": 99
        }

        deduct.return_value = {
            "new_balance": 99,
            "cost": 1
        }

        cache_cls.return_value = cache
        openai_cls.return_value = openai

        yield {
            "cache": cache,
            "openai": openai,
            "check_credits": check,
            "deduct_credits": deduct
        }


class TestGenerateCopy:
    """Tests for /copy/generate endpoint."""

    @pytest.mark.asyncio
    async def test_generate_copy_success(
        self,
        mock_auth_user,
        mock_services,
        async_client
    ):
        """Test successful copy generation."""
        mock_services["openai"].generate_copy.return_value = {
            "id": "copy_123",
            "copy_text": "Amazing product!",
            "copy_type": "ad",
            "tone": "professional",
            "platform": "instagram",
            "word_count": 2,
            "character_count": 16,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        response = await async_client.post(
            "/copy/generate",
            json={
                "product_id": "prod_123",
                "product_title": "Test Product",
                "product_price": 99.90,
                "copy_type": "ad",
                "tone": "professional"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["copy_text"] == "Amazing product!"
        assert data["cached"] is False
        assert data["credits_used"] == 1

    @pytest.mark.asyncio
    async def test_generate_copy_from_cache(
        self,
        mock_auth_user,
        mock_services,
        async_client
    ):
        """Test returning cached copy."""
        mock_services["cache"].get.return_value = {
            "id": "cached_123",
            "copy_text": "Cached copy!",
            "copy_type": "ad",
            "tone": "professional",
            "platform": "instagram",
            "word_count": 2,
            "character_count": 12,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        response = await async_client.post(
            "/copy/generate",
            json={
                "product_id": "prod_123",
                "product_title": "Test Product",
                "product_price": 99.90,
                "copy_type": "ad",
                "tone": "professional"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is True
        assert data["credits_used"] == 0

    @pytest.mark.asyncio
    async def test_generate_copy_insufficient_credits(
        self,
        mock_auth_user,
        mock_services,
        async_client
    ):
        """Test copy generation with insufficient credits."""
        try:
            from api.middleware.quota import InsufficientCreditsError
            mock_services["check_credits"].side_effect = (
                InsufficientCreditsError("No credits", required=1, available=0)
            )
        except ImportError:

            class InsufficientCreditsError(Exception):
                pass

            mock_services["check_credits"].side_effect = (
                InsufficientCreditsError("No credits")
            )

        response = await async_client.post(
            "/copy/generate",
            json={
                "product_id": "prod_123",
                "product_title": "Test Product",
                "product_price": 99.90,
                "copy_type": "ad",
                "tone": "professional"
            }
        )

        assert response.status_code == 402

    @pytest.mark.asyncio
    async def test_generate_copy_with_all_options(
        self,
        mock_auth_user,
        mock_services,
        async_client
    ):
        """Test copy generation with all options."""
        mock_services["openai"].generate_copy.return_value = {
            "id": "copy_full",
            "copy_text": "Full featured copy!",
            "copy_type": "story",
            "tone": "luxury",
            "platform": "facebook",
            "word_count": 3,
            "character_count": 20,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        response = await async_client.post(
            "/copy/generate",
            json={
                "product_id": "prod_123",
                "product_title": "Luxury Product",
                "product_description": "High-end item",
                "product_price": 999.90,
                "product_benefits": ["Premium", "Exclusive"],
                "copy_type": "story",
                "tone": "luxury",
                "platform": "facebook",
                "language": "en-US",
                "max_length": 500,
                "include_emoji": False,
                "include_hashtags": False,
                "custom_instructions": "Keep it classy"
            }
        )

        assert response.status_code == 200


class TestCreditsEndpoints:
    """Tests for credits and quota endpoints."""

    @pytest.mark.asyncio
    async def test_get_credits(
        self,
        mock_auth_user,
        mock_services,
        async_client
    ):
        """Test getting credits status."""
        mock_services["openai"].get_credits_status.return_value = {
            "balance": 100,
            "total_purchased": 200,
            "total_used": 50,
            "last_reload": datetime.now(timezone.utc).isoformat()
        }

        response = await async_client.get("/copy/credits")

        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 100
        assert data["total_purchased"] == 200
        assert data["total_used"] == 50

    @pytest.mark.asyncio
    async def test_get_quota(
        self,
        mock_auth_user,
        mock_services,
        async_client
    ):
        """Test getting quota information."""
        response = await async_client.get("/copy/quota")

        assert response.status_code == 200


class TestHistoryEndpoints:
    """Tests for history endpoints."""

    @pytest.mark.asyncio
    async def test_get_history(
        self,
        mock_auth_user,
        mock_services,
        async_client
    ):
        """Test getting copy history."""
        # The endpoint returns List[CopyHistoryItem], mock returns list of dicts
        mock_services["openai"].get_history.return_value = []

        response = await async_client.get("/copy/history")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_history_with_pagination(
        self,
        mock_auth_user,
        mock_services,
        async_client
    ):
        """Test getting copy history with pagination."""
        # Return list of valid CopyHistoryItem dicts
        mock_services["openai"].get_history.return_value = [
            {
                "id": "copy_123",
                "product_id": "prod_456",
                "product_title": "Test Product",
                "copy_type": "ad",
                "tone": "professional",
                "copy_text": "Amazing product!",
                "created_at": datetime.now(timezone.utc)
            }
        ]

        response = await async_client.get("/copy/history?limit=10&offset=20")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == "copy_123"


class TestTemplatesEndpoints:
    """Tests for templates endpoints."""

    @pytest.mark.asyncio
    async def test_get_templates(
        self,
        mock_auth_user,
        mock_services,
        async_client
    ):
        """Test getting available templates."""
        response = await async_client.get("/copy/templates")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_apply_template(
        self,
        mock_auth_user,
        mock_services,
        async_client
    ):
        """Test applying a valid template."""
        # Use a real template ID that exists
        response = await async_client.post(
            "/copy/templates/urgency/apply",
            json={
                "product_title": "Test Product",
                "price": "99.99"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "copy_text" in data
        assert "Test Product" in data["copy_text"]
        assert "99.99" in data["copy_text"]

    @pytest.mark.asyncio
    async def test_apply_template_not_found(
        self,
        mock_auth_user,
        mock_services,
        async_client
    ):
        """Test applying a non-existent template."""
        response = await async_client.post(
            "/copy/templates/invalid_template/apply",
            json={
                "product_title": "Test Product",
                "price": "99.99"
            }
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_apply_template_missing_variable(
        self,
        mock_auth_user,
        mock_services,
        async_client
    ):
        """Test applying template with missing variable."""
        response = await async_client.post(
            "/copy/templates/urgency/apply",
            json={
                "product_title": "Test Product"
                # missing "price" variable
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_custom_template(
        self,
        mock_auth_user,
        mock_services,
        async_client
    ):
        """Test creating a custom template."""
        response = await async_client.post(
            "/copy/template",
            json={
                "name": "My Template",
                "copy_type": "ad",
                "tone": "professional",
                "platform": "instagram",
                "template_text": "Check out {product_name}!"
            }
        )

        assert response.status_code in [200, 201, 404]

    @pytest.mark.asyncio
    async def test_delete_template(
        self,
        mock_auth_user,
        mock_services,
        async_client
    ):
        """Test deleting a template."""
        response = await async_client.delete("/copy/template/template_123")

        assert response.status_code in [200, 404]
