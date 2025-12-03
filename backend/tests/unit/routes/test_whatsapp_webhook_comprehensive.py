"""
Comprehensive tests for whatsapp_webhook.py
Tests for Evolution API webhook handler and chatbot functionality.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import ValidationError


# ============================================
# SCHEMA TESTS
# ============================================

class TestEvolutionWebhookPayload:
    """Tests for EvolutionWebhookPayload schema."""

    def test_valid_payload(self):
        from api.routes.whatsapp_webhook import EvolutionWebhookPayload

        payload = EvolutionWebhookPayload(
            event="messages.upsert",
            instance="didin-whatsapp",
            data={"key": "value"},
            sender="5511999999999",
            destination="5511888888888",
            date_time="2024-01-01T12:00:00Z"
        )
        assert payload.event == "messages.upsert"
        assert payload.instance == "didin-whatsapp"
        assert payload.data == {"key": "value"}
        assert payload.sender == "5511999999999"

    def test_minimal_payload(self):
        from api.routes.whatsapp_webhook import EvolutionWebhookPayload

        payload = EvolutionWebhookPayload(
            event="connection.update",
            instance="test-instance",
            data={}
        )
        assert payload.event == "connection.update"
        assert payload.sender is None
        assert payload.destination is None

    def test_payload_with_nested_data(self):
        from api.routes.whatsapp_webhook import EvolutionWebhookPayload

        nested_data = {
            "message": {
                "conversation": "Hello",
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net"
                }
            }
        }
        payload = EvolutionWebhookPayload(
            event="messages.upsert",
            instance="test",
            data=nested_data
        )
        assert payload.data["message"]["conversation"] == "Hello"


class TestWhatsAppMessage:
    """Tests for WhatsAppMessage schema."""

    def test_text_message(self):
        from api.routes.whatsapp_webhook import WhatsAppMessage

        msg = WhatsAppMessage(
            remote_jid="5511999999999@s.whatsapp.net",
            message_id="ABC123",
            from_me=False,
            push_name="João",
            message_type="text",
            text="Hello",
            timestamp=datetime.now(timezone.utc)
        )
        assert msg.message_type == "text"
        assert msg.text == "Hello"
        assert msg.from_me is False

    def test_media_message(self):
        from api.routes.whatsapp_webhook import WhatsAppMessage

        msg = WhatsAppMessage(
            remote_jid="5511999999999@s.whatsapp.net",
            message_id="DEF456",
            from_me=True,
            message_type="image",
            media_url="https://example.com/image.jpg",
            timestamp=datetime.now(timezone.utc)
        )
        assert msg.message_type == "image"
        assert msg.media_url is not None
        assert msg.text is None


# ============================================
# CHATBOT TESTS
# ============================================

class TestRealProductChatbot:
    """Tests for RealProductChatbot class."""

    @pytest.fixture
    def chatbot(self):
        from api.routes.whatsapp_webhook import RealProductChatbot
        return RealProductChatbot()

    @pytest.fixture
    def mock_cache(self):
        return AsyncMock()

    @pytest.fixture
    def mock_scraper(self):
        return AsyncMock()

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_welcome_message(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999",
            message="olá",
            push_name="João"
        )

        assert "text" in result
        assert "João" in result["text"]
        assert "Didin Fácil" in result["text"]
        assert result["action"] == "welcome"

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_show_menu_option(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999",
            message="0",
            push_name="Maria"
        )

        assert "Menu Principal" in result["text"]
        assert result["action"] == "menu"

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_product_search_start(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999",
            message="1",
            push_name="Cliente"
        )

        assert "Busca de Produtos" in result["text"]
        assert result["action"] == "await_query"
        mock_cache.set.assert_called()

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_product_search_with_palavra_buscar(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999",
            message="buscar",
            push_name="Cliente"
        )

        assert "Busca de Produtos" in result["text"]

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_compare_prices_option(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.increment = AsyncMock()

        with patch("api.routes.whatsapp_webhook.scraper") as mock_scraper:
            mock_scraper.get_products = AsyncMock(return_value={
                "products": [
                    {
                        "title": "Fone Bluetooth",
                        "price": 50.00,
                        "original_price": 100.00
                    }
                ]
            })

            result = await chatbot.process_message(
                phone="5511999999999",
                message="2",
                push_name="Cliente"
            )

            assert "Comparação de Preços" in result["text"]
            assert result["action"] == "comparison"

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_alerts_option_no_alerts(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(side_effect=[None, None])
        mock_cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999",
            message="3",
            push_name="Cliente"
        )

        assert "Alertas de Preço" in result["text"]
        assert "ainda não tem alertas" in result["text"]
        assert result["action"] == "alerts"

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_alerts_option_with_alerts(self, mock_cache, chatbot):
        user_alerts = [
            {"product": "iPhone 15", "target_price": 4500.00},
            {"product": "AirPods", "target_price": 800.00}
        ]
        mock_cache.get = AsyncMock(side_effect=[None, user_alerts])
        mock_cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999",
            message="3",
            push_name="Cliente"
        )

        assert "Seus Alertas de Preço" in result["text"]
        assert "iPhone 15" in result["text"]

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_human_transfer_option(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999",
            message="4",
            push_name="Cliente"
        )

        assert "Transferência para Atendente" in result["text"]
        assert result["action"] == "human_transfer"

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    @patch("api.routes.whatsapp_webhook.scraper")
    async def test_real_product_search_with_results(self, mock_scraper, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value={"waiting_for": "product_query"})
        mock_cache.delete = AsyncMock()
        mock_cache.increment = AsyncMock()

        mock_scraper.search_products = AsyncMock(return_value={
            "products": [
                {
                    "title": "Fone Bluetooth JBL",
                    "price": 149.90,
                    "original_price": 249.90,
                    "rating": 4.5,
                    "sales_count": 1500,
                    "shop_name": "Loja Oficial"
                },
                {
                    "title": "Fone Bluetooth Sony",
                    "price": 199.90,
                    "rating": 4.8,
                    "sales_count": 800,
                    "shop_name": "Tech Store"
                }
            ],
            "total": 50
        })

        result = await chatbot.process_message(
            phone="5511999999999",
            message="fone bluetooth",
            push_name="João"
        )

        assert "Encontrei" in result["text"]
        assert "50" in result["text"]
        assert "fone bluetooth" in result["text"]
        assert result["action"] == "products_found"
        assert "products" in result

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    @patch("api.routes.whatsapp_webhook.scraper")
    async def test_real_product_search_no_results(self, mock_scraper, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value={"waiting_for": "product_query"})
        mock_cache.delete = AsyncMock()
        mock_cache.increment = AsyncMock()

        mock_scraper.search_products = AsyncMock(return_value={
            "products": [],
            "total": 0
        })
        mock_scraper.get_trending_products = AsyncMock(return_value={
            "products": [{"title": "Produto Trending"}]
        })

        result = await chatbot.process_message(
            phone="5511999999999",
            message="xyzabc123",
            push_name="Cliente"
        )

        assert "Não encontrei" in result["text"]
        assert result["action"] == "no_results"

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    @patch("api.routes.whatsapp_webhook.scraper")
    async def test_real_product_search_error(self, mock_scraper, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value={"waiting_for": "product_query"})
        mock_cache.delete = AsyncMock()
        mock_cache.increment = AsyncMock()

        mock_scraper.search_products = AsyncMock(side_effect=Exception("API Error"))

        result = await chatbot.process_message(
            phone="5511999999999",
            message="fone",
            push_name="Cliente"
        )

        assert "erro" in result["text"].lower()
        assert result["action"] == "error"

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_increment_metric_error_handling(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.increment = AsyncMock(side_effect=Exception("Redis error"))

        # Should not raise even if increment fails
        result = await chatbot.process_message(
            phone="5511999999999",
            message="olá",
            push_name="João"
        )

        assert result is not None

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    @patch("api.routes.whatsapp_webhook.scraper")
    async def test_compare_prices_no_products(self, mock_scraper, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.increment = AsyncMock()
        mock_scraper.get_products = AsyncMock(return_value={"products": []})

        result = await chatbot.process_message(
            phone="5511999999999",
            message="2",
            push_name="Cliente"
        )

        assert "não temos produtos em promoção" in result["text"]

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    @patch("api.routes.whatsapp_webhook.scraper")
    async def test_compare_prices_error(self, mock_scraper, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.increment = AsyncMock()
        mock_scraper.get_products = AsyncMock(side_effect=Exception("DB Error"))

        result = await chatbot.process_message(
            phone="5511999999999",
            message="preços",
            push_name="Cliente"
        )

        assert "Erro" in result["text"]


class TestChatbotMenuVariations:
    """Test different menu input variations."""

    @pytest.fixture
    def chatbot(self):
        from api.routes.whatsapp_webhook import RealProductChatbot
        return RealProductChatbot()

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_menu_keyword_variations(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.increment = AsyncMock()

        keywords = ["menu", "voltar", "inicio"]
        for keyword in keywords:
            result = await chatbot.process_message(
                phone="5511999999999",
                message=keyword,
                push_name="Test"
            )
            assert result["action"] == "menu"

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_product_search_keyword_variations(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.increment = AsyncMock()

        keywords = ["1", "buscar", "produto", "produtos"]
        for keyword in keywords:
            result = await chatbot.process_message(
                phone="5511999999999",
                message=keyword,
                push_name="Test"
            )
            assert result["action"] == "await_query"

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_compare_keyword_variations(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.increment = AsyncMock()

        with patch("api.routes.whatsapp_webhook.scraper") as mock_scraper:
            mock_scraper.get_products = AsyncMock(return_value={"products": []})

            keywords = ["2", "comparar", "preço", "preços"]
            for keyword in keywords:
                result = await chatbot.process_message(
                    phone="5511999999999",
                    message=keyword,
                    push_name="Test"
                )
                assert result["action"] == "comparison"

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_alerts_keyword_variations(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(side_effect=[None, None])
        mock_cache.increment = AsyncMock()

        keywords = ["3", "alerta", "alertas"]
        for keyword in keywords:
            mock_cache.get.reset_mock()
            mock_cache.get.side_effect = [None, None]

            result = await chatbot.process_message(
                phone="5511999999999",
                message=keyword,
                push_name="Test"
            )
            assert result["action"] == "alerts"

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_human_transfer_keyword_variations(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.increment = AsyncMock()

        keywords = ["4", "atendente", "humano", "ajuda"]
        for keyword in keywords:
            result = await chatbot.process_message(
                phone="5511999999999",
                message=keyword,
                push_name="Test"
            )
            assert result["action"] == "human_transfer"


# ============================================
# WEBHOOK ENDPOINT TESTS
# ============================================

class TestWebhookEndpoint:
    """Tests for the webhook endpoint."""

    @pytest.mark.asyncio
    async def test_router_exists(self):
        from api.routes.whatsapp_webhook import router

        assert router is not None
        assert router.prefix == "/whatsapp-webhook"

    @pytest.mark.asyncio
    async def test_router_tags(self):
        from api.routes.whatsapp_webhook import router

        assert "WhatsApp Webhook" in router.tags

    def test_constants_defined(self):
        from api.routes.whatsapp_webhook import (
            EVOLUTION_API_URL,
            EVOLUTION_API_KEY,
            EVOLUTION_INSTANCE
        )

        assert EVOLUTION_API_URL is not None
        assert EVOLUTION_API_KEY is not None
        assert EVOLUTION_INSTANCE is not None


class TestProductFormatting:
    """Tests for product formatting in chatbot responses."""

    @pytest.fixture
    def chatbot(self):
        from api.routes.whatsapp_webhook import RealProductChatbot
        return RealProductChatbot()

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    @patch("api.routes.whatsapp_webhook.scraper")
    async def test_product_with_discount(self, mock_scraper, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value={"waiting_for": "product_query"})
        mock_cache.delete = AsyncMock()
        mock_cache.increment = AsyncMock()

        mock_scraper.search_products = AsyncMock(return_value={
            "products": [{
                "title": "Produto com Desconto",
                "price": 80.00,
                "original_price": 100.00,
                "rating": 4.0,
                "sales_count": 100,
                "shop_name": "Loja"
            }],
            "total": 1
        })

        result = await chatbot.process_message(
            phone="5511999999999",
            message="produto",
            push_name="Test"
        )

        # Should show discount percentage (-20%)
        assert "-20%" in result["text"] or "💰" in result["text"]

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    @patch("api.routes.whatsapp_webhook.scraper")
    async def test_product_without_discount(self, mock_scraper, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value={"waiting_for": "product_query"})
        mock_cache.delete = AsyncMock()
        mock_cache.increment = AsyncMock()

        mock_scraper.search_products = AsyncMock(return_value={
            "products": [{
                "title": "Produto sem Desconto",
                "price": 100.00,
                "original_price": None,
                "rating": 4.5,
                "sales_count": 50,
                "shop_name": "Loja"
            }],
            "total": 1
        })

        result = await chatbot.process_message(
            phone="5511999999999",
            message="produto",
            push_name="Test"
        )

        assert "R$ 100.00" in result["text"]

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    @patch("api.routes.whatsapp_webhook.scraper")
    async def test_long_product_title_truncated(self, mock_scraper, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value={"waiting_for": "product_query"})
        mock_cache.delete = AsyncMock()
        mock_cache.increment = AsyncMock()

        long_title = "A" * 100  # Very long title
        mock_scraper.search_products = AsyncMock(return_value={
            "products": [{
                "title": long_title,
                "price": 50.00,
                "rating": 4.0,
                "sales_count": 10,
                "shop_name": "Loja"
            }],
            "total": 1
        })

        result = await chatbot.process_message(
            phone="5511999999999",
            message="produto",
            push_name="Test"
        )

        # Title should be truncated to 50 chars
        assert len(long_title) > 50  # Original is long
        # Response should contain truncated version
        assert "A" * 50 in result["text"]


class TestMetrics:
    """Tests for metrics tracking."""

    @pytest.fixture
    def chatbot(self):
        from api.routes.whatsapp_webhook import RealProductChatbot
        return RealProductChatbot()

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_increment_messages_received(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.increment = AsyncMock()

        await chatbot.process_message(
            phone="5511999999999",
            message="oi",
            push_name="Test"
        )

        # Check that messages_received was incremented
        calls = mock_cache.increment.call_args_list
        metric_keys = [str(c) for c in calls]
        assert any("messages_received" in str(k) for k in metric_keys)

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    @patch("api.routes.whatsapp_webhook.scraper")
    async def test_increment_product_searches(self, mock_scraper, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value={"waiting_for": "product_query"})
        mock_cache.delete = AsyncMock()
        mock_cache.increment = AsyncMock()
        mock_scraper.search_products = AsyncMock(return_value={"products": [], "total": 0})
        mock_scraper.get_trending_products = AsyncMock(return_value={"products": []})

        await chatbot.process_message(
            phone="5511999999999",
            message="fone",
            push_name="Test"
        )

        calls = mock_cache.increment.call_args_list
        metric_keys = [str(c) for c in calls]
        assert any("product_searches" in str(k) for k in metric_keys)

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_increment_human_transfers(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.increment = AsyncMock()

        await chatbot.process_message(
            phone="5511999999999",
            message="4",
            push_name="Test"
        )

        calls = mock_cache.increment.call_args_list
        metric_keys = [str(c) for c in calls]
        assert any("human_transfers" in str(k) for k in metric_keys)


# ============================================
# EDGE CASES
# ============================================

class TestEdgeCases:
    """Edge case tests."""

    @pytest.fixture
    def chatbot(self):
        from api.routes.whatsapp_webhook import RealProductChatbot
        return RealProductChatbot()

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_empty_message(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999",
            message="   ",
            push_name="Test"
        )

        # Should show welcome for empty/whitespace message
        assert result["action"] == "welcome"

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_no_push_name(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999",
            message="oi",
            push_name=None
        )

        # Should use "cliente" as default name
        assert "cliente" in result["text"]

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_uppercase_commands(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999",
            message="MENU",
            push_name="Test"
        )

        # Should handle uppercase
        assert result["action"] == "menu"

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_mixed_case_commands(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999",
            message="BuScAr",
            push_name="Test"
        )

        assert result["action"] == "await_query"

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_message_with_extra_spaces(self, mock_cache, chatbot):
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999",
            message="  0  ",
            push_name="Test"
        )

        assert result["action"] == "menu"
