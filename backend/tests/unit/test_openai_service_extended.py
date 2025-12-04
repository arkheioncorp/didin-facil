"""
OpenAI Service Extended Tests
============================
Testes para cobrir funções adicionais do serviço OpenAI.
"""

from unittest.mock import AsyncMock, patch

import pytest
from api.services.openai import OpenAIService

# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def service():
    """Create OpenAI service instance."""
    with patch("api.services.openai.AsyncOpenAI"), \
         patch("api.services.openai.AccountingService"):
        return OpenAIService()


# ============================================
# PRIVATE METHOD TESTS
# ============================================


class TestPrivateMethods:
    """Tests for private helper methods."""

    def test_get_system_prompt_instagram(self, service):
        """Test system prompt generation for Instagram."""
        prompt = service._get_system_prompt("instagram", "pt-BR")
        assert len(prompt) > 0

    def test_get_system_prompt_tiktok(self, service):
        """Test system prompt generation for TikTok."""
        prompt = service._get_system_prompt("tiktok", "en-US")
        assert len(prompt) > 0

    def test_get_system_prompt_youtube(self, service):
        """Test system prompt generation for YouTube."""
        prompt = service._get_system_prompt("youtube", "pt-BR")
        assert len(prompt) > 0

    def test_get_system_prompt_facebook(self, service):
        """Test system prompt generation for Facebook."""
        prompt = service._get_system_prompt("facebook", "pt-BR")
        assert len(prompt) > 0

    def test_build_prompt_complete(self, service):
        """Test prompt building with all parameters."""
        prompt = service._build_prompt(
            product_title="Amazing Widget",
            product_description="The best widget ever",
            product_price=99.99,
            product_benefits=["Fast", "Reliable", "Affordable"],
            copy_type="product_description",
            tone="persuasive",
            platform="instagram",
            language="pt-BR",
            max_length=200,
            include_emoji=True,
            include_hashtags=True,
            custom_instructions="Focus on durability"
        )
        assert "Amazing Widget" in prompt
        assert "durability" in prompt

    def test_build_prompt_minimal(self, service):
        """Test prompt building with minimal parameters."""
        prompt = service._build_prompt(
            product_title="Widget",
            product_description=None,
            product_price=10.0,
            product_benefits=None,
            copy_type="headline",
            tone="casual",
            platform="tiktok",
            language="pt-BR",
            max_length=None,
            include_emoji=False,
            include_hashtags=False,
            custom_instructions=None
        )
        assert "Widget" in prompt
        assert len(prompt) > 0

    def test_build_prompt_with_benefits(self, service):
        """Test prompt with multiple benefits."""
        prompt = service._build_prompt(
            product_title="Super Product",
            product_description="Amazing product",
            product_price=49.99,
            product_benefits=["Benefit 1", "Benefit 2", "Benefit 3"],
            copy_type="social_post",
            tone="excited",
            platform="instagram",
            language="pt-BR",
            max_length=300,
            include_emoji=True,
            include_hashtags=True,
            custom_instructions=None
        )
        assert "Super Product" in prompt

    def test_build_prompt_various_tones(self, service):
        """Test prompt building with various tones."""
        tones = ["persuasive", "casual", "professional", "urgent", "friendly"]
        for tone in tones:
            prompt = service._build_prompt(
                product_title="Product",
                product_description="Description",
                product_price=29.99,
                product_benefits=None,
                copy_type="headline",
                tone=tone,
                platform="instagram",
                language="pt-BR",
                max_length=None,
                include_emoji=False,
                include_hashtags=False,
                custom_instructions=None
            )
            assert len(prompt) > 0
            assert "Product" in prompt

    def test_build_prompt_various_copy_types(self, service):
        """Test prompt building with various copy types."""
        copy_types = ["headline", "product_description", "social_post"]
        for copy_type in copy_types:
            prompt = service._build_prompt(
                product_title="Test Product",
                product_description="Test description",
                product_price=19.99,
                product_benefits=["Fast shipping"],
                copy_type=copy_type,
                tone="casual",
                platform="instagram",
                language="pt-BR",
                max_length=150,
                include_emoji=True,
                include_hashtags=True,
                custom_instructions=None
            )
            assert len(prompt) > 0

    def test_build_prompt_english(self, service):
        """Test prompt building in English."""
        prompt = service._build_prompt(
            product_title="Widget",
            product_description="Great widget",
            product_price=25.00,
            product_benefits=["Durable", "Easy to use"],
            copy_type="product_description",
            tone="professional",
            platform="linkedin",
            language="en-US",
            max_length=200,
            include_emoji=False,
            include_hashtags=False,
            custom_instructions=None
        )
        assert "Widget" in prompt
        assert len(prompt) > 0


# ============================================
# INITIALIZATION TESTS
# ============================================


class TestOpenAIServiceInit:
    """Tests for OpenAIService initialization."""

    def test_service_init(self, service):
        """Test service initialization."""
        assert service.model is not None
        assert service.cache_service is not None


# ============================================
# PROMPT VARIATIONS TESTS
# ============================================


class TestPromptVariations:
    """Tests for different prompt variations."""

    def test_prompt_without_description(self, service):
        """Test prompt when description is None."""
        prompt = service._build_prompt(
            product_title="Simple Widget",
            product_description=None,
            product_price=15.00,
            product_benefits=None,
            copy_type="headline",
            tone="casual",
            platform="twitter",
            language="pt-BR",
            max_length=None,
            include_emoji=False,
            include_hashtags=False,
            custom_instructions=None
        )
        assert "Simple Widget" in prompt

    def test_prompt_with_zero_price(self, service):
        """Test prompt with zero price (free product)."""
        prompt = service._build_prompt(
            product_title="Free Widget",
            product_description="Free download",
            product_price=0.0,
            product_benefits=["Free", "Easy"],
            copy_type="social_post",
            tone="excited",
            platform="instagram",
            language="pt-BR",
            max_length=200,
            include_emoji=True,
            include_hashtags=True,
            custom_instructions=None
        )
        assert "Free Widget" in prompt

    def test_prompt_with_high_price(self, service):
        """Test prompt with high price."""
        prompt = service._build_prompt(
            product_title="Luxury Widget",
            product_description="Premium luxury item",
            product_price=9999.99,
            product_benefits=["Exclusive", "Premium"],
            copy_type="ad_copy",
            tone="professional",
            platform="linkedin",
            language="pt-BR",
            max_length=300,
            include_emoji=False,
            include_hashtags=False,
            custom_instructions="Target high-end customers"
        )
        assert "Luxury Widget" in prompt

    def test_system_prompt_returns_string(self, service):
        """Test that system prompt returns a non-empty string."""
        platforms = ["instagram", "tiktok", "youtube", "facebook"]
        for platform in platforms:
            prompt = service._get_system_prompt(platform, "pt-BR")
            assert isinstance(prompt, str)
            assert len(prompt) > 10
