"""
OpenAI Service Unit Tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from api.services.openai import OpenAIService


class TestOpenAIService:
    """Tests for OpenAIService class"""

    @pytest.fixture
    def openai_service(self):
        """Create OpenAIService instance for testing."""
        with patch("api.services.openai.OPENAI_API_KEY", "test-api-key"), \
             patch("api.services.openai.OPENAI_MODEL", "gpt-4-turbo-preview"), \
             patch("api.services.openai.AsyncOpenAI") as mock_client:
            
            service = OpenAIService()
            service.client = mock_client.return_value
            return service

    @pytest.fixture
    def mock_openai_response(self):
        """Create mock OpenAI API response."""
        mock = MagicMock()
        mock.choices = [
            MagicMock(
                message=MagicMock(
                    content="Este é um produto incrível que vai transformar sua vida! 🔥 #trending #produto"
                )
            )
        ]
        mock.usage = MagicMock(
            prompt_tokens=50,
            completion_tokens=100,
            total_tokens=150
        )
        return mock

    # ============================================
    # COPY GENERATION TESTS
    # ============================================

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_copy_success(self, openai_service, mock_openai_response):
        """Should generate copy successfully."""
        openai_service.client.chat.completions.create = AsyncMock(
            return_value=mock_openai_response
        )

        result = await openai_service.generate_copy(
            product_title="Fone Bluetooth",
            product_description="Fone sem fio de alta qualidade",
            product_price=199.90,
            product_benefits=["Cancelamento de ruído", "40h de bateria"],
            copy_type="product_description",
            tone="professional",
            platform="instagram",
            language="pt-BR"
        )

        assert result is not None
        assert "copy_text" in result
        assert result["copy_type"] == "product_description"
        assert result["platform"] == "instagram"
        assert "id" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_copy_with_all_options(self, openai_service, mock_openai_response):
        """Should handle all optional parameters."""
        openai_service.client.chat.completions.create = AsyncMock(
            return_value=mock_openai_response
        )

        result = await openai_service.generate_copy(
            product_title="Test Product",
            product_description="Description",
            product_price=100.0,
            product_benefits=["Benefit 1", "Benefit 2"],
            copy_type="facebook_ad",
            tone="casual",
            platform="facebook",
            language="pt-BR",
            max_length=300,
            include_emoji=True,
            include_hashtags=True,
            custom_instructions="Be extra creative"
        )

        assert result is not None
        assert result["copy_type"] == "facebook_ad"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_copy_strips_whitespace(self, openai_service):
        """Should strip whitespace from generated copy."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="  Content with whitespace  \n"))
        ]
        openai_service.client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        result = await openai_service.generate_copy(
            product_title="Test",
            product_description=None,
            product_price=50.0,
            product_benefits=None,
            copy_type="tiktok_hook",
            tone="fun",
            platform="tiktok"
        )

        assert result["copy_text"] == "Content with whitespace"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_copy_includes_metadata(self, openai_service, mock_openai_response):
        """Should include word and character counts."""
        openai_service.client.chat.completions.create = AsyncMock(
            return_value=mock_openai_response
        )

        result = await openai_service.generate_copy(
            product_title="Test",
            product_description=None,
            product_price=50.0,
            product_benefits=None,
            copy_type="product_description",
            tone="professional",
            platform="general"
        )

        assert "word_count" in result
        assert "character_count" in result
        assert isinstance(result["word_count"], int)
        assert isinstance(result["character_count"], int)

    # ============================================
    # SYSTEM PROMPT TESTS
    # ============================================

    @pytest.mark.unit
    def test_get_system_prompt_instagram(self, openai_service):
        """Should return Instagram-specific prompt."""
        prompt = openai_service._get_system_prompt("instagram", "pt-BR")

        assert "Instagram" in prompt
        assert "emoji" in prompt.lower()
        assert "hashtags" in prompt.lower()

    @pytest.mark.unit
    def test_get_system_prompt_tiktok(self, openai_service):
        """Should return TikTok-specific prompt."""
        prompt = openai_service._get_system_prompt("tiktok", "pt-BR")

        assert "TikTok" in prompt
        assert "conciso" in prompt.lower() or "short" in prompt.lower()

    @pytest.mark.unit
    def test_get_system_prompt_facebook(self, openai_service):
        """Should return Facebook-specific prompt."""
        prompt = openai_service._get_system_prompt("facebook", "pt-BR")

        assert "Facebook" in prompt
        assert "storytelling" in prompt.lower() or "detalhad" in prompt.lower()

    @pytest.mark.unit
    def test_get_system_prompt_whatsapp(self, openai_service):
        """Should return WhatsApp-specific prompt."""
        prompt = openai_service._get_system_prompt("whatsapp", "pt-BR")

        assert "WhatsApp" in prompt
        assert "pessoal" in prompt.lower() or "conversacional" in prompt.lower()

    @pytest.mark.unit
    def test_get_system_prompt_general(self, openai_service):
        """Should return general prompt for unknown platforms."""
        prompt = openai_service._get_system_prompt("unknown_platform", "pt-BR")

        assert "copywriter" in prompt.lower()
        assert "vendas" in prompt.lower()

    @pytest.mark.unit
    def test_get_system_prompt_includes_language(self, openai_service):
        """Should include language in prompt."""
        prompt = openai_service._get_system_prompt("instagram", "en-US")

        assert "en-US" in prompt

    # ============================================
    # PROMPT BUILDING TESTS
    # ============================================

    @pytest.mark.unit
    def test_build_prompt_basic(self, openai_service):
        """Should build basic prompt."""
        prompt = openai_service._build_prompt(
            product_title="Test Product",
            product_description="A test description",
            product_price=100.0,
            product_benefits=None,
            copy_type="product_description",
            tone="professional",
            platform="instagram",
            language="pt-BR",
            max_length=None,
            include_emoji=True,
            include_hashtags=True,
            custom_instructions=None
        )

        assert "Test Product" in prompt
        assert "100" in str(prompt) or "R$" in prompt

    @pytest.mark.unit
    def test_build_prompt_with_benefits(self, openai_service):
        """Should include product benefits in prompt."""
        prompt = openai_service._build_prompt(
            product_title="Test",
            product_description=None,
            product_price=50.0,
            product_benefits=["Fast shipping", "30-day warranty"],
            copy_type="facebook_ad",
            tone="persuasive",
            platform="facebook",
            language="pt-BR",
            max_length=None,
            include_emoji=False,
            include_hashtags=False,
            custom_instructions=None
        )

        assert "Fast shipping" in prompt or "warranty" in prompt

    @pytest.mark.unit
    def test_build_prompt_with_custom_instructions(self, openai_service):
        """Should include custom instructions in prompt."""
        custom = "Focus on the eco-friendly aspects"
        prompt = openai_service._build_prompt(
            product_title="Eco Product",
            product_description=None,
            product_price=75.0,
            product_benefits=None,
            copy_type="product_description",
            tone="professional",
            platform="general",
            language="pt-BR",
            max_length=None,
            include_emoji=True,
            include_hashtags=True,
            custom_instructions=custom
        )

        assert custom in prompt

    # ============================================
    # ERROR HANDLING TESTS
    # ============================================

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_copy_api_error(self, openai_service):
        """Should handle API errors gracefully."""
        openai_service.client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )

        with pytest.raises(Exception) as exc_info:
            await openai_service.generate_copy(
                product_title="Test",
                product_description=None,
                product_price=50.0,
                product_benefits=None,
                copy_type="product_description",
                tone="professional",
                platform="instagram"
            )

        assert "API Error" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_copy_empty_response(self, openai_service):
        """Should handle empty API response."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=""))
        ]
        openai_service.client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        result = await openai_service.generate_copy(
            product_title="Test",
            product_description=None,
            product_price=50.0,
            product_benefits=None,
            copy_type="product_description",
            tone="professional",
            platform="instagram"
        )

        assert result["copy_text"] == ""
        assert result["word_count"] == 0

    # ============================================
    # TONE TESTS
    # ============================================

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_copy_different_tones(self, openai_service, mock_openai_response):
        """Should accept different tone options."""
        openai_service.client.chat.completions.create = AsyncMock(
            return_value=mock_openai_response
        )

        tones = ["professional", "casual", "fun", "urgent", "persuasive"]

        for tone in tones:
            result = await openai_service.generate_copy(
                product_title="Test",
                product_description=None,
                product_price=50.0,
                product_benefits=None,
                copy_type="product_description",
                tone=tone,
                platform="instagram"
            )

            assert result["tone"] == tone

    # ============================================
    # COPY TYPE TESTS
    # ============================================

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_copy_different_types(self, openai_service, mock_openai_response):
        """Should accept different copy types."""
        openai_service.client.chat.completions.create = AsyncMock(
            return_value=mock_openai_response
        )

        copy_types = [
            "product_description",
            "facebook_ad",
            "tiktok_hook",
            "instagram_caption",
            "whatsapp_message"
        ]

        for copy_type in copy_types:
            result = await openai_service.generate_copy(
                product_title="Test",
                product_description=None,
                product_price=50.0,
                product_benefits=None,
                copy_type=copy_type,
                tone="professional",
                platform="instagram"
            )

            assert result["copy_type"] == copy_type

    # ============================================
    # EDGE CASES
    # ============================================

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_copy_with_unicode(self, openai_service, mock_openai_response):
        """Should handle unicode characters."""
        openai_service.client.chat.completions.create = AsyncMock(
            return_value=mock_openai_response
        )

        result = await openai_service.generate_copy(
            product_title="Produto com acentos: é ã ç",
            product_description="Descrição com 中文 e emojis 🔥",
            product_price=50.0,
            product_benefits=None,
            copy_type="product_description",
            tone="professional",
            platform="instagram"
        )

        assert result is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_copy_with_zero_price(self, openai_service, mock_openai_response):
        """Should handle zero price (free product)."""
        openai_service.client.chat.completions.create = AsyncMock(
            return_value=mock_openai_response
        )

        result = await openai_service.generate_copy(
            product_title="Free Product",
            product_description=None,
            product_price=0.0,
            product_benefits=None,
            copy_type="product_description",
            tone="professional",
            platform="instagram"
        )

        assert result is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_copy_with_very_long_title(self, openai_service, mock_openai_response):
        """Should handle very long product titles."""
        openai_service.client.chat.completions.create = AsyncMock(
            return_value=mock_openai_response
        )

        long_title = "A" * 500

        result = await openai_service.generate_copy(
            product_title=long_title,
            product_description=None,
            product_price=50.0,
            product_benefits=None,
            copy_type="product_description",
            tone="professional",
            platform="instagram"
        )

        assert result is not None
