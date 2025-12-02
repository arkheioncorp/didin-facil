"""
Tests for AI Copy Generation Routes
====================================
Comprehensive tests for copy.py endpoints.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from api.routes.copy import (CopyHistoryItem, CopyRequest, CopyResponse,
                             CreditsStatus, router)
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_user():
    """User mock as dict for route authentication."""
    return {
        "id": str(uuid4()),
        "email": "user@test.com"
    }


@pytest.fixture
def app(mock_user):
    """Create test FastAPI app with mocked auth."""
    app = FastAPI()
    app.include_router(router)
    
    from api.middleware.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    return app


@pytest.fixture
async def client(app):
    """Async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


# ============================================
# UNIT TESTS - Models
# ============================================

class TestCopyModels:
    """Tests for Pydantic models."""

    def test_copy_request_model(self):
        """Test CopyRequest model."""
        request = CopyRequest(
            product_id="prod-123",
            product_title="Test Product",
            product_description="A great product",
            product_price=99.90,
            product_benefits=["Fast delivery", "High quality"],
            copy_type="ad",
            tone="professional",
            platform="instagram",
            language="pt-BR",
            max_length=500,
            include_emoji=True,
            include_hashtags=True,
            custom_instructions="Make it catchy"
        )
        assert request.product_id == "prod-123"
        assert request.copy_type == "ad"
        assert request.tone == "professional"

    def test_copy_request_minimal(self):
        """Test CopyRequest with minimal data."""
        request = CopyRequest(
            product_id="prod-123",
            product_title="Test Product",
            product_price=99.90,
            copy_type="ad",
            tone="professional"
        )
        assert request.platform == "instagram"
        assert request.language == "pt-BR"
        assert request.include_emoji is True

    def test_copy_request_all_copy_types(self):
        """Test CopyRequest with all valid copy types."""
        copy_types = [
            "ad", "description", "headline", "cta", "story",
            "facebook_ad", "tiktok_hook", "product_description",
            "story_reels", "email", "whatsapp"
        ]
        for ct in copy_types:
            request = CopyRequest(
                product_id="prod-123",
                product_title="Test",
                product_price=10.0,
                copy_type=ct,
                tone="professional"
            )
            assert request.copy_type == ct

    def test_copy_request_all_tones(self):
        """Test CopyRequest with all valid tones."""
        tones = [
            "professional", "casual", "urgent", "friendly",
            "luxury", "educational", "emotional", "authority"
        ]
        for t in tones:
            request = CopyRequest(
                product_id="prod-123",
                product_title="Test",
                product_price=10.0,
                copy_type="ad",
                tone=t
            )
            assert request.tone == t

    def test_copy_request_all_platforms(self):
        """Test CopyRequest with all valid platforms."""
        platforms = [
            "instagram", "facebook", "tiktok",
            "whatsapp", "general", "youtube", "email"
        ]
        for p in platforms:
            request = CopyRequest(
                product_id="prod-123",
                product_title="Test",
                product_price=10.0,
                copy_type="ad",
                tone="professional",
                platform=p
            )
            assert request.platform == p

    def test_copy_response_model(self):
        """Test CopyResponse model."""
        response = CopyResponse(
            id="copy-123",
            copy_text="Amazing product!",
            copy_type="ad",
            tone="professional",
            platform="instagram",
            word_count=2,
            character_count=16,
            created_at=datetime.now(timezone.utc),
            cached=False,
            credits_used=10,
            credits_remaining=90
        )
        assert response.id == "copy-123"
        assert response.credits_used == 10

    def test_copy_history_item_model(self):
        """Test CopyHistoryItem model."""
        item = CopyHistoryItem(
            id="hist-123",
            product_id="prod-456",
            product_title="Test Product",
            copy_type="ad",
            tone="professional",
            copy_text="Great copy!",
            created_at=datetime.now(timezone.utc)
        )
        assert item.id == "hist-123"
        assert item.product_title == "Test Product"

    def test_credits_status_model(self):
        """Test CreditsStatus model."""
        status = CreditsStatus(
            balance=100,
            total_purchased=200,
            total_used=100,
            cost_per_copy=10
        )
        assert status.balance == 100
        assert status.cost_per_copy == 10


# ============================================
# INTEGRATION TESTS - Generate Copy
# ============================================

class TestGenerateCopyEndpoint:
    """Tests for /generate endpoint."""

    @pytest.mark.asyncio
    async def test_generate_copy_success(self, client, mock_user):
        """Test generating copy successfully."""
        with patch(
            "api.routes.copy.check_credits",
            new_callable=AsyncMock
        ) as mock_check:
            mock_check.return_value = {"balance": 100}
            
            with patch(
                "api.routes.copy.CacheService"
            ) as MockCache:
                mock_cache = MagicMock()
                mock_cache.get = AsyncMock(return_value=None)
                mock_cache.set = AsyncMock()
                mock_cache.build_copy_cache_key = MagicMock(
                    return_value="cache-key"
                )
                MockCache.return_value = mock_cache
                
                with patch(
                    "api.routes.copy.OpenAIService"
                ) as MockOpenAI:
                    mock_openai = MagicMock()
                    mock_openai.generate_copy = AsyncMock(return_value={
                        "id": "copy-123",
                        "copy_text": "Amazing product!",
                        "copy_type": "ad",
                        "tone": "professional",
                        "platform": "instagram",
                        "word_count": 2,
                        "character_count": 16,
                        "created_at": datetime.now(timezone.utc)
                    })
                    mock_openai.save_to_history = AsyncMock()
                    MockOpenAI.return_value = mock_openai
                    
                    with patch(
                        "api.routes.copy.deduct_credits",
                        new_callable=AsyncMock
                    ) as mock_deduct:
                        mock_deduct.return_value = {
                            "cost": 10,
                            "new_balance": 90
                        }
                        
                        response = await client.post(
                            "/generate",
                            json={
                                "product_id": "prod-123",
                                "product_title": "Test Product",
                                "product_price": 99.90,
                                "copy_type": "ad",
                                "tone": "professional"
                            }
                        )
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data["copy_text"] == "Amazing product!"
                        assert data["credits_used"] == 10

    @pytest.mark.asyncio
    async def test_generate_copy_cached(self, client, mock_user):
        """Test generating copy with cache hit."""
        with patch(
            "api.routes.copy.check_credits",
            new_callable=AsyncMock
        ) as mock_check:
            mock_check.return_value = {"balance": 100}
            
            with patch(
                "api.routes.copy.CacheService"
            ) as MockCache:
                mock_cache = MagicMock()
                mock_cache.get = AsyncMock(return_value={
                    "id": "cached-123",
                    "copy_text": "Cached copy!",
                    "copy_type": "ad",
                    "tone": "professional",
                    "platform": "instagram",
                    "word_count": 2,
                    "character_count": 12,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                mock_cache.build_copy_cache_key = MagicMock(
                    return_value="cache-key"
                )
                MockCache.return_value = mock_cache
                
                with patch(
                    "api.routes.copy.OpenAIService"
                ) as MockOpenAI:
                    mock_openai = MagicMock()
                    mock_openai.save_to_history = AsyncMock(return_value=None)
                    MockOpenAI.return_value = mock_openai
                
                    response = await client.post(
                        "/generate",
                        json={
                            "product_id": "prod-123",
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
    async def test_generate_copy_insufficient_credits(self, client, mock_user):
        """Test generating copy with insufficient credits."""
        from fastapi import HTTPException
        
        with patch(
            "api.routes.copy.check_credits",
            new_callable=AsyncMock
        ) as mock_check:
            # Create a proper HTTPException for 402
            mock_check.side_effect = HTTPException(
                status_code=402,
                detail={
                    "message": "Insufficient credits",
                    "required": 10,
                    "available": 5
                }
            )
            
            with patch(
                "api.routes.copy.CacheService"
            ) as MockCache:
                MockCache.return_value = MagicMock()
                
                with patch(
                    "api.routes.copy.OpenAIService"
                ) as MockOpenAI:
                    MockOpenAI.return_value = MagicMock()
                    
                    response = await client.post(
                        "/generate",
                        json={
                            "product_id": "prod-123",
                            "product_title": "Test Product",
                            "product_price": 99.90,
                            "copy_type": "ad",
                            "tone": "professional"
                        }
                    )
                    
                    assert response.status_code == 402


# ============================================
# INTEGRATION TESTS - Credits
# ============================================

class TestCreditsEndpoint:
    """Tests for /credits endpoint."""

    @pytest.mark.asyncio
    async def test_get_credits_status(self, client, mock_user):
        """Test getting credits status."""
        with patch(
            "api.routes.copy.OpenAIService"
        ) as MockOpenAI:
            mock_openai = MagicMock()
            mock_openai.get_credits_status = AsyncMock(return_value={
                "balance": 100,
                "total_purchased": 200,
                "total_used": 100
            })
            MockOpenAI.return_value = mock_openai
            
            with patch(
                "api.routes.copy.CREDIT_COSTS",
                {"copy": 10}
            ):
                response = await client.get("/credits")
                
                assert response.status_code == 200
                data = response.json()
                assert data["balance"] == 100
                assert data["cost_per_copy"] == 10


# ============================================
# INTEGRATION TESTS - Quota (Legacy)
# ============================================

class TestQuotaEndpoint:
    """Tests for /quota endpoint (legacy)."""

    @pytest.mark.asyncio
    async def test_get_quota_status(self, client, mock_user):
        """Test getting quota status (legacy)."""
        with patch(
            "api.routes.copy.OpenAIService"
        ) as MockOpenAI:
            mock_openai = MagicMock()
            mock_openai.get_credits_status = AsyncMock(return_value={
                "balance": 100,
                "total_purchased": 200,
                "total_used": 100
            })
            MockOpenAI.return_value = mock_openai
            
            response = await client.get("/quota")
            
            assert response.status_code == 200
            data = response.json()
            assert data["copies_remaining"] == 100
            assert data["plan"] == "lifetime"


# ============================================
# INTEGRATION TESTS - History
# ============================================

class TestHistoryEndpoint:
    """Tests for /history endpoint."""

    @pytest.mark.asyncio
    async def test_get_copy_history(self, client, mock_user):
        """Test getting copy history."""
        with patch(
            "api.routes.copy.OpenAIService"
        ) as MockOpenAI:
            mock_openai = MagicMock()
            mock_openai.get_history = AsyncMock(return_value=[
                {
                    "id": "hist-1",
                    "product_id": "prod-1",
                    "product_title": "Product 1",
                    "copy_type": "ad",
                    "tone": "professional",
                    "copy_text": "Copy 1",
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "id": "hist-2",
                    "product_id": "prod-2",
                    "product_title": "Product 2",
                    "copy_type": "description",
                    "tone": "casual",
                    "copy_text": "Copy 2",
                    "created_at": datetime.now(timezone.utc)
                }
            ])
            MockOpenAI.return_value = mock_openai
            
            response = await client.get("/history")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_copy_history_with_pagination(self, client, mock_user):
        """Test getting copy history with pagination."""
        with patch(
            "api.routes.copy.OpenAIService"
        ) as MockOpenAI:
            mock_openai = MagicMock()
            mock_openai.get_history = AsyncMock(return_value=[])
            MockOpenAI.return_value = mock_openai
            
            response = await client.get("/history?limit=10&offset=20")
            
            assert response.status_code == 200
            mock_openai.get_history.assert_called_once()


# ============================================
# INTEGRATION TESTS - Templates
# ============================================

class TestTemplatesEndpoint:
    """Tests for /templates endpoint."""

    @pytest.mark.asyncio
    async def test_get_copy_templates(self, client, mock_user):
        """Test getting copy templates."""
        response = await client.get("/templates")
        
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) > 0
        
        # Check template structure
        template = data["templates"][0]
        assert "id" in template
        assert "name" in template
        assert "template" in template
        assert "variables" in template


class TestApplyTemplateEndpoint:
    """Tests for /templates/{template_id}/apply endpoint."""

    @pytest.mark.asyncio
    async def test_apply_template_urgency(self, client, mock_user):
        """Test applying urgency template."""
        response = await client.post(
            "/templates/urgency/apply",
            json={
                "product_title": "Amazing Headphones",
                "price": "99.90"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Amazing Headphones" in data["copy_text"]
        assert "99.90" in data["copy_text"]
        assert data["template_id"] == "urgency"

    @pytest.mark.asyncio
    async def test_apply_template_benefits(self, client, mock_user):
        """Test applying benefits template."""
        response = await client.post(
            "/templates/benefits/apply",
            json={
                "product_title": "Smart Watch",
                "benefit_1": "Track fitness",
                "benefit_2": "Notifications",
                "benefit_3": "Long battery",
                "price": "199.90"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Smart Watch" in data["copy_text"]
        assert "Track fitness" in data["copy_text"]

    @pytest.mark.asyncio
    async def test_apply_template_story(self, client, mock_user):
        """Test applying story template."""
        response = await client.post(
            "/templates/story/apply",
            json={
                "desired_outcome": "better sleep",
                "product_title": "Sleep Mask",
                "price": "29.90"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "better sleep" in data["copy_text"]
        assert "Sleep Mask" in data["copy_text"]

    @pytest.mark.asyncio
    async def test_apply_template_social_proof(self, client, mock_user):
        """Test applying social proof template."""
        response = await client.post(
            "/templates/social_proof/apply",
            json={
                "reviews_count": "5000",
                "product_title": "Wireless Earbuds",
                "price": "149.90"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "5000" in data["copy_text"]
        assert "Wireless Earbuds" in data["copy_text"]

    @pytest.mark.asyncio
    async def test_apply_template_not_found(self, client, mock_user):
        """Test applying non-existent template."""
        response = await client.post(
            "/templates/nonexistent/apply",
            json={
                "product_title": "Test",
                "price": "10.00"
            }
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_apply_template_missing_variable(self, client, mock_user):
        """Test applying template with missing variable."""
        response = await client.post(
            "/templates/urgency/apply",
            json={
                "product_title": "Test"
                # Missing "price"
            }
        )
        
        assert response.status_code == 400
        assert "Missing variable" in response.json()["detail"]


# ============================================
# EDGE CASES
# ============================================

class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_generate_copy_with_all_options(self, client, mock_user):
        """Test generating copy with all options."""
        with patch(
            "api.routes.copy.check_credits",
            new_callable=AsyncMock
        ) as mock_check:
            mock_check.return_value = {"balance": 100}
            
            with patch(
                "api.routes.copy.CacheService"
            ) as MockCache:
                mock_cache = MagicMock()
                mock_cache.get = AsyncMock(return_value=None)
                mock_cache.set = AsyncMock()
                mock_cache.build_copy_cache_key = MagicMock(
                    return_value="cache-key"
                )
                MockCache.return_value = mock_cache
                
                with patch(
                    "api.routes.copy.OpenAIService"
                ) as MockOpenAI:
                    mock_openai = MagicMock()
                    mock_openai.generate_copy = AsyncMock(return_value={
                        "id": "copy-123",
                        "copy_text": "Full options copy!",
                        "copy_type": "facebook_ad",
                        "tone": "luxury",
                        "platform": "facebook",
                        "word_count": 3,
                        "character_count": 18,
                        "created_at": datetime.now(timezone.utc)
                    })
                    mock_openai.save_to_history = AsyncMock()
                    MockOpenAI.return_value = mock_openai
                    
                    with patch(
                        "api.routes.copy.deduct_credits",
                        new_callable=AsyncMock
                    ) as mock_deduct:
                        mock_deduct.return_value = {
                            "cost": 10,
                            "new_balance": 90
                        }
                        
                        response = await client.post(
                            "/generate",
                            json={
                                "product_id": "prod-123",
                                "product_title": "Luxury Watch",
                                "product_description": "A premium timepiece",
                                "product_price": 5999.90,
                                "product_benefits": [
                                    "Swiss movement",
                                    "Sapphire crystal",
                                    "Lifetime warranty"
                                ],
                                "copy_type": "facebook_ad",
                                "tone": "luxury",
                                "platform": "facebook",
                                "language": "pt-BR",
                                "max_length": 1000,
                                "include_emoji": False,
                                "include_hashtags": False,
                                "custom_instructions": "Focus on exclusivity"
                            }
                        )
                        
                        assert response.status_code == 200
