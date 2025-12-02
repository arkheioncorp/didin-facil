"""
Testes para OpenAI Service
===========================
Cobertura para api/services/openai.py
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

# ==================== FIXTURES ====================

@pytest.fixture
def mock_openai_client():
    """Mock do cliente OpenAI."""
    client = MagicMock()
    
    # Mock da resposta
    mock_choice = MagicMock()
    mock_choice.message.content = "Incrível produto! 🔥 Compre agora!"
    
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 100
    mock_usage.completion_tokens = 50
    mock_usage.total_tokens = 150
    
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage
    
    client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    return client


@pytest.fixture
def mock_accounting_service():
    """Mock do AccountingService."""
    service = MagicMock()
    service.track_openai_usage = AsyncMock(return_value=None)
    return service


@pytest.fixture
def mock_cache_service():
    """Mock do CacheService."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    return cache


# ==================== BUILD PROMPT TESTS ====================

class TestBuildPrompt:
    """Testes do _build_prompt."""

    def test_build_prompt_basic(self):
        """Testa construção básica do prompt."""
        with patch("api.services.openai.AsyncOpenAI"), \
             patch("api.services.openai.CacheService"), \
             patch("api.services.openai.AccountingService"):
            from api.services.openai import OpenAIService

            service = OpenAIService()
            prompt = service._build_prompt(
                product_title="Test Product",
                product_description="A great product",
                product_price=99.90,
                product_benefits=["Benefit 1", "Benefit 2"],
                copy_type="ad",
                tone="professional",
                platform="instagram",
                language="pt-BR",
                max_length=None,
                include_emoji=True,
                include_hashtags=True,
                custom_instructions=None,
            )

            assert "Test Product" in prompt
            assert "R$ 99.90" in prompt
            assert "Benefit 1" in prompt
            assert "instagram" in prompt

    def test_build_prompt_without_description(self):
        """Testa prompt sem descrição."""
        with patch("api.services.openai.AsyncOpenAI"), \
             patch("api.services.openai.CacheService"), \
             patch("api.services.openai.AccountingService"):
            from api.services.openai import OpenAIService

            service = OpenAIService()
            prompt = service._build_prompt(
                product_title="Simple Product",
                product_description=None,
                product_price=50.00,
                product_benefits=None,
                copy_type="headline",
                tone="casual",
                platform="facebook",
                language="pt-BR",
                max_length=100,
                include_emoji=False,
                include_hashtags=False,
                custom_instructions=None,
            )

            assert "Simple Product" in prompt
            assert "R$ 50.00" in prompt
            assert "Descrição" not in prompt

    def test_build_prompt_with_custom_instructions(self):
        """Testa prompt com instruções customizadas."""
        with patch("api.services.openai.AsyncOpenAI"), \
             patch("api.services.openai.CacheService"), \
             patch("api.services.openai.AccountingService"):
            from api.services.openai import OpenAIService

            service = OpenAIService()
            prompt = service._build_prompt(
                product_title="Custom Product",
                product_description=None,
                product_price=150.00,
                product_benefits=None,
                copy_type="story",
                tone="emotional",
                platform="whatsapp",
                language="pt-BR",
                max_length=None,
                include_emoji=True,
                include_hashtags=False,
                custom_instructions="Mencionar frete grátis",
            )

            assert "Mencionar frete grátis" in prompt

    def test_build_prompt_with_max_length(self):
        """Testa prompt com limite de caracteres."""
        with patch("api.services.openai.AsyncOpenAI"), \
             patch("api.services.openai.CacheService"), \
             patch("api.services.openai.AccountingService"):
            from api.services.openai import OpenAIService

            service = OpenAIService()
            prompt = service._build_prompt(
                product_title="Product",
                product_description=None,
                product_price=100.00,
                product_benefits=None,
                copy_type="ad",
                tone="urgent",
                platform="tiktok",
                language="pt-BR",
                max_length=280,
                include_emoji=True,
                include_hashtags=True,
                custom_instructions=None,
            )

            assert "280" in prompt or "Limite" in prompt

    def test_build_prompt_all_copy_types(self):
        """Testa todos os tipos de copy."""
        copy_types = [
            "ad", "description", "headline", "cta", "story",
            "facebook_ad", "tiktok_hook", "product_description",
            "story_reels", "email", "whatsapp"
        ]

        with patch("api.services.openai.AsyncOpenAI"), \
             patch("api.services.openai.CacheService"), \
             patch("api.services.openai.AccountingService"):
            from api.services.openai import OpenAIService

            service = OpenAIService()

            for copy_type in copy_types:
                prompt = service._build_prompt(
                    product_title="Test",
                    product_description=None,
                    product_price=10.00,
                    product_benefits=None,
                    copy_type=copy_type,
                    tone="professional",
                    platform="instagram",
                    language="pt-BR",
                    max_length=None,
                    include_emoji=False,
                    include_hashtags=False,
                    custom_instructions=None,
                )
                assert len(prompt) > 0

    def test_build_prompt_all_tones(self):
        """Testa todos os tons."""
        tones = [
            "professional", "casual", "urgent", "friendly",
            "luxury", "educational", "emotional", "authority"
        ]

        with patch("api.services.openai.AsyncOpenAI"), \
             patch("api.services.openai.CacheService"), \
             patch("api.services.openai.AccountingService"):
            from api.services.openai import OpenAIService

            service = OpenAIService()

            for tone in tones:
                prompt = service._build_prompt(
                    product_title="Test",
                    product_description=None,
                    product_price=10.00,
                    product_benefits=None,
                    copy_type="ad",
                    tone=tone,
                    platform="instagram",
                    language="pt-BR",
                    max_length=None,
                    include_emoji=False,
                    include_hashtags=False,
                    custom_instructions=None,
                )
                assert len(prompt) > 0


# ==================== SYSTEM PROMPT TESTS ====================

class TestSystemPrompt:
    """Testes do _get_system_prompt."""

    def test_get_system_prompt_instagram(self):
        """Testa prompt de sistema para Instagram."""
        with patch("api.services.openai.AsyncOpenAI"), \
             patch("api.services.openai.CacheService"), \
             patch("api.services.openai.AccountingService"):
            from api.services.openai import OpenAIService

            service = OpenAIService()
            prompt = service._get_system_prompt("instagram", "pt-BR")

            assert "Instagram" in prompt
            assert "emoji" in prompt.lower()

    def test_get_system_prompt_facebook(self):
        """Testa prompt de sistema para Facebook."""
        with patch("api.services.openai.AsyncOpenAI"), \
             patch("api.services.openai.CacheService"), \
             patch("api.services.openai.AccountingService"):
            from api.services.openai import OpenAIService

            service = OpenAIService()
            prompt = service._get_system_prompt("facebook", "pt-BR")

            assert "Facebook" in prompt

    def test_get_system_prompt_tiktok(self):
        """Testa prompt de sistema para TikTok."""
        with patch("api.services.openai.AsyncOpenAI"), \
             patch("api.services.openai.CacheService"), \
             patch("api.services.openai.AccountingService"):
            from api.services.openai import OpenAIService

            service = OpenAIService()
            prompt = service._get_system_prompt("tiktok", "pt-BR")

            assert "TikTok" in prompt

    def test_get_system_prompt_whatsapp(self):
        """Testa prompt de sistema para WhatsApp."""
        with patch("api.services.openai.AsyncOpenAI"), \
             patch("api.services.openai.CacheService"), \
             patch("api.services.openai.AccountingService"):
            from api.services.openai import OpenAIService

            service = OpenAIService()
            prompt = service._get_system_prompt("whatsapp", "pt-BR")

            assert "WhatsApp" in prompt

    def test_get_system_prompt_general(self):
        """Testa prompt de sistema genérico."""
        with patch("api.services.openai.AsyncOpenAI"), \
             patch("api.services.openai.CacheService"), \
             patch("api.services.openai.AccountingService"):
            from api.services.openai import OpenAIService

            service = OpenAIService()
            prompt = service._get_system_prompt("general", "pt-BR")

            assert "copywriter" in prompt.lower()

    def test_get_system_prompt_unknown_platform(self):
        """Testa prompt para plataforma desconhecida."""
        with patch("api.services.openai.AsyncOpenAI"), \
             patch("api.services.openai.CacheService"), \
             patch("api.services.openai.AccountingService"):
            from api.services.openai import OpenAIService

            service = OpenAIService()
            prompt = service._get_system_prompt("unknown_platform", "en-US")

            # Deve usar general como fallback
            assert len(prompt) > 0


# ==================== GENERATE COPY TESTS ====================

class TestGenerateCopy:
    """Testes do generate_copy."""

    @pytest.mark.asyncio
    async def test_generate_copy_success(
        self, mock_openai_client, mock_accounting_service
    ):
        """Testa geração de copy com sucesso."""
        with patch("api.services.openai.AsyncOpenAI",
                   return_value=mock_openai_client), \
             patch("api.services.openai.CacheService"), \
             patch("api.services.openai.AccountingService",
                   return_value=mock_accounting_service):
            from api.services.openai import OpenAIService

            service = OpenAIService()
            service.client = mock_openai_client
            service.accounting = mock_accounting_service

            result = await service.generate_copy(
                product_title="Amazing Product",
                product_description="Best product ever",
                product_price=199.90,
                product_benefits=["Fast shipping", "High quality"],
                copy_type="ad",
                tone="professional",
                platform="instagram",
            )

            assert "id" in result
            assert "copy_text" in result
            assert result["copy_type"] == "ad"
            assert result["platform"] == "instagram"
            assert "word_count" in result

    @pytest.mark.asyncio
    async def test_generate_copy_tracks_usage(
        self, mock_openai_client, mock_accounting_service
    ):
        """Testa que uso é rastreado."""
        with patch("api.services.openai.AsyncOpenAI",
                   return_value=mock_openai_client), \
             patch("api.services.openai.CacheService"), \
             patch("api.services.openai.AccountingService",
                   return_value=mock_accounting_service):
            from api.services.openai import OpenAIService

            service = OpenAIService()
            service.client = mock_openai_client
            service.accounting = mock_accounting_service

            await service.generate_copy(
                product_title="Product",
                product_description=None,
                product_price=50.00,
                product_benefits=None,
                copy_type="headline",
                tone="casual",
                platform="facebook",
            )

            mock_accounting_service.track_openai_usage.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_copy_with_max_length(
        self, mock_openai_client, mock_accounting_service
    ):
        """Testa geração com limite de caracteres."""
        with patch("api.services.openai.AsyncOpenAI",
                   return_value=mock_openai_client), \
             patch("api.services.openai.CacheService"), \
             patch("api.services.openai.AccountingService",
                   return_value=mock_accounting_service):
            from api.services.openai import OpenAIService

            service = OpenAIService()
            service.client = mock_openai_client
            service.accounting = mock_accounting_service

            result = await service.generate_copy(
                product_title="Product",
                product_description=None,
                product_price=100.00,
                product_benefits=None,
                copy_type="ad",
                tone="urgent",
                platform="tiktok",
                max_length=150,
            )

            assert result is not None
            # Verificar que max_tokens foi passado
            call_args = mock_openai_client.chat.completions.create.call_args
            assert call_args.kwargs["max_tokens"] == 150


# ==================== CREDITS TESTS ====================

class TestCreditsOperations:
    """Testes de operações de créditos."""

    @pytest.mark.asyncio
    async def test_get_credits_status_method_exists(self):
        """Testa que método get_credits_status existe."""
        with patch("api.services.openai.AsyncOpenAI"), \
             patch("api.services.openai.CacheService"), \
             patch("api.services.openai.AccountingService"):
            from api.services.openai import OpenAIService

            service = OpenAIService()
            assert hasattr(service, "get_credits_status")

    @pytest.mark.asyncio
    async def test_deduct_credits_method_exists(self):
        """Testa que método deduct_credits existe."""
        with patch("api.services.openai.AsyncOpenAI"), \
             patch("api.services.openai.CacheService"), \
             patch("api.services.openai.AccountingService"):
            from api.services.openai import OpenAIService

            service = OpenAIService()
            assert hasattr(service, "deduct_credits")


# ==================== SAVE TO HISTORY TESTS ====================

class TestSaveToHistory:
    """Testes do save_to_history."""

    @pytest.mark.asyncio
    async def test_save_to_history_method_exists(self):
        """Testa que método save_to_history existe."""
        with patch("api.services.openai.AsyncOpenAI"), \
             patch("api.services.openai.CacheService"), \
             patch("api.services.openai.AccountingService"):
            from api.services.openai import OpenAIService

            service = OpenAIService()
            assert hasattr(service, "save_to_history")


# ==================== SERVICE INITIALIZATION TESTS ====================

class TestServiceInitialization:
    """Testes de inicialização do serviço."""

    def test_service_initialization(self):
        """Testa inicialização do serviço."""
        with patch("api.services.openai.AsyncOpenAI") as mock_openai, \
             patch("api.services.openai.CacheService") as mock_cache, \
             patch("api.services.openai.AccountingService") as mock_acc:
            from api.services.openai import OpenAIService

            service = OpenAIService()

            assert service.client is not None
            mock_openai.assert_called_once()
            mock_cache.assert_called_once()
            mock_acc.assert_called_once()

    def test_service_uses_configured_model(self):
        """Testa que serviço usa modelo configurado."""
        with patch("api.services.openai.AsyncOpenAI"), \
             patch("api.services.openai.CacheService"), \
             patch("api.services.openai.AccountingService"), \
             patch("api.services.openai.OPENAI_MODEL", "gpt-4o"):
            from api.services.openai import OpenAIService

            service = OpenAIService()

            assert service.model == "gpt-4o"
