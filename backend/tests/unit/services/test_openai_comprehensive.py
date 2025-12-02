"""
Comprehensive tests for OpenAI Service
Tests for copy generation, token tracking, prompts, and error handling
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestOpenAIServiceGeneration:
    """Tests for OpenAI copy generation"""

    @pytest.fixture
    def mock_openai_response(self):
        """Create mock OpenAI response"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "🔥 Confira este produto incrível! Apenas R$99,90. #oferta #promoção"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        return mock_response

    @pytest.mark.asyncio
    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    async def test_generate_copy_success(self, mock_cache, mock_openai_class, mock_accounting_class, mock_openai_response):
        """Test successful copy generation"""
        # Setup mocks
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        mock_openai_class.return_value = mock_client
        
        mock_accounting = AsyncMock()
        mock_accounting.track_openai_usage = AsyncMock()
        mock_accounting_class.return_value = mock_accounting
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        result = await service.generate_copy(
            product_title="Smartphone Galaxy S23",
            product_description="Celular top de linha",
            product_price=4999.90,
            product_benefits=["Câmera 200MP", "Bateria 5000mAh"],
            copy_type="promotional",
            tone="enthusiastic",
            platform="instagram",
            language="pt-BR"
        )
        
        assert "copy_text" in result
        assert result["platform"] == "instagram"
        assert result["tokens_used"] == 150

    @pytest.mark.asyncio
    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    async def test_generate_copy_with_emoji_option(self, mock_cache, mock_openai_class, mock_accounting_class, mock_openai_response):
        """Test copy generation with emoji option"""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        mock_openai_class.return_value = mock_client
        mock_accounting_class.return_value = AsyncMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        result = await service.generate_copy(
            product_title="Tênis Nike",
            product_description="Tênis esportivo",
            product_price=599.90,
            product_benefits=["Confortável", "Durável"],
            copy_type="promotional",
            tone="casual",
            platform="facebook",
            include_emoji=True,
            include_hashtags=True
        )
        
        assert result is not None
        assert "copy_text" in result

    @pytest.mark.asyncio
    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    async def test_generate_copy_without_emoji(self, mock_cache, mock_openai_class, mock_accounting_class, mock_openai_response):
        """Test copy generation without emoji"""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        mock_openai_class.return_value = mock_client
        mock_accounting_class.return_value = AsyncMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        result = await service.generate_copy(
            product_title="Carro Usado",
            product_description="Sedã 2020",
            product_price=45000.00,
            product_benefits=None,
            copy_type="informative",
            tone="professional",
            platform="general",
            include_emoji=False,
            include_hashtags=False
        )
        
        assert result is not None

    @pytest.mark.asyncio
    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    async def test_generate_copy_with_max_length(self, mock_cache, mock_openai_class, mock_accounting_class, mock_openai_response):
        """Test copy generation with max length"""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        mock_openai_class.return_value = mock_client
        mock_accounting_class.return_value = AsyncMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        result = await service.generate_copy(
            product_title="Produto",
            product_description=None,
            product_price=99.90,
            product_benefits=None,
            copy_type="short",
            tone="casual",
            platform="tiktok",
            max_length=150
        )
        
        assert result is not None

    @pytest.mark.asyncio
    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    async def test_generate_copy_with_custom_instructions(self, mock_cache, mock_openai_class, mock_accounting_class, mock_openai_response):
        """Test copy generation with custom instructions"""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        mock_openai_class.return_value = mock_client
        mock_accounting_class.return_value = AsyncMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        result = await service.generate_copy(
            product_title="Curso Online",
            product_description="Curso de Python",
            product_price=197.00,
            product_benefits=["Certificado", "Suporte"],
            copy_type="educational",
            tone="professional",
            platform="general",
            custom_instructions="Foque na urgência e escassez"
        )
        
        assert result is not None

    @pytest.mark.asyncio
    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    async def test_generate_copy_no_usage(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test copy generation without usage data"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Copy text"
        mock_response.usage = None
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client
        mock_accounting_class.return_value = AsyncMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        result = await service.generate_copy(
            product_title="Test",
            product_description=None,
            product_price=10.00,
            product_benefits=None,
            copy_type="test",
            tone="test",
            platform="general"
        )
        
        assert result["tokens_used"] == 0


class TestOpenAIServicePrompts:
    """Tests for prompt building"""

    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    def test_get_system_prompt_instagram(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test system prompt for Instagram"""
        mock_accounting_class.return_value = MagicMock()
        mock_openai_class.return_value = MagicMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        prompt = service._get_system_prompt("instagram", "pt-BR")
        
        assert "Instagram" in prompt
        assert "emoji" in prompt.lower() or "Emojis" in prompt

    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    def test_get_system_prompt_facebook(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test system prompt for Facebook"""
        mock_accounting_class.return_value = MagicMock()
        mock_openai_class.return_value = MagicMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        prompt = service._get_system_prompt("facebook", "pt-BR")
        
        assert "Facebook" in prompt

    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    def test_get_system_prompt_tiktok(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test system prompt for TikTok"""
        mock_accounting_class.return_value = MagicMock()
        mock_openai_class.return_value = MagicMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        prompt = service._get_system_prompt("tiktok", "pt-BR")
        
        assert "TikTok" in prompt

    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    def test_get_system_prompt_whatsapp(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test system prompt for WhatsApp"""
        mock_accounting_class.return_value = MagicMock()
        mock_openai_class.return_value = MagicMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        prompt = service._get_system_prompt("whatsapp", "pt-BR")
        
        assert "WhatsApp" in prompt

    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    def test_get_system_prompt_general(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test system prompt for general platform"""
        mock_accounting_class.return_value = MagicMock()
        mock_openai_class.return_value = MagicMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        prompt = service._get_system_prompt("general", "pt-BR")
        
        assert "copywriting" in prompt.lower()

    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    def test_get_system_prompt_unknown_platform(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test system prompt for unknown platform (should use general)"""
        mock_accounting_class.return_value = MagicMock()
        mock_openai_class.return_value = MagicMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        prompt = service._get_system_prompt("unknown", "pt-BR")
        
        # Should return None or use default
        assert prompt is None or "copywriting" in prompt.lower()

    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    def test_build_prompt_basic(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test building basic prompt"""
        mock_accounting_class.return_value = MagicMock()
        mock_openai_class.return_value = MagicMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        prompt = service._build_prompt(
            product_title="iPhone 15",
            product_description="Smartphone Apple",
            product_price=7999.00,
            product_benefits=["A17 Pro", "Titânio"],
            copy_type="promotional",
            tone="enthusiastic",
            platform="instagram",
            language="pt-BR",
            max_length=None,
            include_emoji=True,
            include_hashtags=True,
            custom_instructions=None
        )
        
        assert "iPhone 15" in prompt
        assert "7999" in prompt or "7.999" in prompt

    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    def test_build_prompt_with_benefits(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test building prompt with benefits"""
        mock_accounting_class.return_value = MagicMock()
        mock_openai_class.return_value = MagicMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        prompt = service._build_prompt(
            product_title="Produto",
            product_description=None,
            product_price=100.00,
            product_benefits=["Benefício 1", "Benefício 2", "Benefício 3"],
            copy_type="promotional",
            tone="casual",
            platform="general",
            language="pt-BR",
            max_length=500,
            include_emoji=True,
            include_hashtags=False,
            custom_instructions=None
        )
        
        assert "Benefício 1" in prompt or "benefício" in prompt.lower()

    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    def test_build_prompt_without_description(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test building prompt without description"""
        mock_accounting_class.return_value = MagicMock()
        mock_openai_class.return_value = MagicMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        prompt = service._build_prompt(
            product_title="Produto Simples",
            product_description=None,
            product_price=50.00,
            product_benefits=None,
            copy_type="short",
            tone="direct",
            platform="tiktok",
            language="pt-BR",
            max_length=150,
            include_emoji=True,
            include_hashtags=True,
            custom_instructions=None
        )
        
        assert "Produto Simples" in prompt


class TestOpenAIServiceAccountingIntegration:
    """Tests for accounting integration"""

    @pytest.mark.asyncio
    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    async def test_tracks_usage_on_generation(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test that token usage is tracked"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated copy"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client
        
        mock_accounting = AsyncMock()
        mock_accounting.track_openai_usage = AsyncMock()
        mock_accounting_class.return_value = mock_accounting
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        await service.generate_copy(
            product_title="Test",
            product_description=None,
            product_price=10.00,
            product_benefits=None,
            copy_type="test",
            tone="test",
            platform="general"
        )
        
        mock_accounting.track_openai_usage.assert_called_once()

    @pytest.mark.asyncio
    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    async def test_does_not_track_when_no_usage(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test that tracking is skipped when no usage data"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated copy"
        mock_response.usage = None
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client
        
        mock_accounting = AsyncMock()
        mock_accounting.track_openai_usage = AsyncMock()
        mock_accounting_class.return_value = mock_accounting
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        await service.generate_copy(
            product_title="Test",
            product_description=None,
            product_price=10.00,
            product_benefits=None,
            copy_type="test",
            tone="test",
            platform="general"
        )
        
        mock_accounting.track_openai_usage.assert_not_called()


class TestOpenAIServiceErrors:
    """Tests for error handling"""

    @pytest.mark.asyncio
    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    async def test_handles_api_error(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test handling OpenAI API errors"""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        mock_openai_class.return_value = mock_client
        mock_accounting_class.return_value = AsyncMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        with pytest.raises(Exception) as exc_info:
            await service.generate_copy(
                product_title="Test",
                product_description=None,
                product_price=10.00,
                product_benefits=None,
                copy_type="test",
                tone="test",
                platform="general"
            )
        
        assert "API Error" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    async def test_handles_empty_response(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test handling empty API response"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ""
        mock_response.usage = None
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client
        mock_accounting_class.return_value = AsyncMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        result = await service.generate_copy(
            product_title="Test",
            product_description=None,
            product_price=10.00,
            product_benefits=None,
            copy_type="test",
            tone="test",
            platform="general"
        )
        
        assert result["copy_text"] == ""


class TestOpenAIServicePlatforms:
    """Tests for different platform support"""

    @pytest.mark.asyncio
    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    async def test_instagram_platform(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test Instagram platform generation"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Instagram copy 📸"
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client
        mock_accounting_class.return_value = AsyncMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        result = await service.generate_copy(
            product_title="Test",
            product_description=None,
            product_price=10.00,
            product_benefits=None,
            copy_type="promotional",
            tone="casual",
            platform="instagram"
        )
        
        assert result["platform"] == "instagram"

    @pytest.mark.asyncio
    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    async def test_tiktok_platform(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test TikTok platform generation"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "TikTok copy"
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client
        mock_accounting_class.return_value = AsyncMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        result = await service.generate_copy(
            product_title="Test",
            product_description=None,
            product_price=10.00,
            product_benefits=None,
            copy_type="promotional",
            tone="casual",
            platform="tiktok"
        )
        
        assert result["platform"] == "tiktok"

    @pytest.mark.asyncio
    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    async def test_whatsapp_platform(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test WhatsApp platform generation"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "WhatsApp message"
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client
        mock_accounting_class.return_value = AsyncMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        result = await service.generate_copy(
            product_title="Test",
            product_description=None,
            product_price=10.00,
            product_benefits=None,
            copy_type="message",
            tone="friendly",
            platform="whatsapp"
        )
        
        assert result["platform"] == "whatsapp"

    @pytest.mark.asyncio
    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    async def test_facebook_platform(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test Facebook platform generation"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Facebook post"
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client
        mock_accounting_class.return_value = AsyncMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        result = await service.generate_copy(
            product_title="Test",
            product_description=None,
            product_price=10.00,
            product_benefits=None,
            copy_type="post",
            tone="professional",
            platform="facebook"
        )
        
        assert result["platform"] == "facebook"


class TestOpenAIServiceTones:
    """Tests for different tone support"""

    @pytest.mark.asyncio
    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    async def test_enthusiastic_tone(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test enthusiastic tone"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "AMAZING!"
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client
        mock_accounting_class.return_value = AsyncMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        result = await service.generate_copy(
            product_title="Test",
            product_description=None,
            product_price=10.00,
            product_benefits=None,
            copy_type="promotional",
            tone="enthusiastic",
            platform="general"
        )
        
        assert result["tone"] == "enthusiastic"

    @pytest.mark.asyncio
    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    async def test_professional_tone(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test professional tone"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Professional description"
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client
        mock_accounting_class.return_value = AsyncMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        result = await service.generate_copy(
            product_title="Test",
            product_description=None,
            product_price=10.00,
            product_benefits=None,
            copy_type="description",
            tone="professional",
            platform="general"
        )
        
        assert result["tone"] == "professional"

    @pytest.mark.asyncio
    @patch('api.services.openai.AccountingService')
    @patch('api.services.openai.AsyncOpenAI')
    @patch('api.services.openai.CacheService')
    async def test_casual_tone(self, mock_cache, mock_openai_class, mock_accounting_class):
        """Test casual tone"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hey check this out"
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client
        mock_accounting_class.return_value = AsyncMock()
        
        from api.services.openai import OpenAIService
        service = OpenAIService()
        
        result = await service.generate_copy(
            product_title="Test",
            product_description=None,
            product_price=10.00,
            product_benefits=None,
            copy_type="social",
            tone="casual",
            platform="instagram"
        )
        
        assert result["tone"] == "casual"
        assert result["tone"] == "casual"
