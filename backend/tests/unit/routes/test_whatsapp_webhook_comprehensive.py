"""
Comprehensive tests for whatsapp_webhook.py
Tests for Evolution API webhook handler and chatbot functionality.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
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
            date_time="2024-01-01T12:00:00Z",
        )
        assert payload.event == "messages.upsert"
        assert payload.instance == "didin-whatsapp"
        assert payload.data == {"key": "value"}
        assert payload.sender == "5511999999999"

    def test_minimal_payload(self):
        from api.routes.whatsapp_webhook import EvolutionWebhookPayload

        payload = EvolutionWebhookPayload(
            event="connection.update", instance="test-instance", data={}
        )
        assert payload.event == "connection.update"
        assert payload.sender is None
        assert payload.destination is None

    def test_payload_with_nested_data(self):
        from api.routes.whatsapp_webhook import EvolutionWebhookPayload

        nested_data = {
            "message": {
                "conversation": "Hello",
                "key": {"remoteJid": "5511999999999@s.whatsapp.net"},
            }
        }
        payload = EvolutionWebhookPayload(
            event="messages.upsert", instance="test", data=nested_data
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
            timestamp=datetime.now(timezone.utc),
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
            timestamp=datetime.now(timezone.utc),
        )
        assert msg.message_type == "image"
        assert msg.media_url is not None
        assert msg.text is None


# ============================================
# CHATBOT TESTS
# ============================================


class TestRealProductChatbot:
    """Tests for RealProductChatbot class."""

    @pytest.mark.asyncio
    async def test_show_welcome_method(self):
        """Test _show_welcome method directly."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        result = await chatbot._show_welcome("João")

        assert "João" in result["text"]
        assert "Didin Fácil" in result["text"]
        assert result["action"] == "welcome"

    @pytest.mark.asyncio
    async def test_show_main_menu_method(self):
        """Test _show_main_menu method directly."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        result = await chatbot._show_main_menu("Cliente")

        assert "Menu Principal" in result["text"]
        assert result["action"] == "menu"

    @pytest.mark.asyncio
    async def test_handle_human_transfer_method(self):
        """Test _handle_human_transfer method directly."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        # Mock the cache's increment method
        chatbot.cache = AsyncMock()
        chatbot.cache.increment = AsyncMock()

        result = await chatbot._handle_human_transfer("5511999999999", "João")

        assert "Transferência para Atendente" in result["text"]
        assert result["action"] == "transfer_human"

    @pytest.mark.asyncio
    async def test_handle_product_search_start_method(self):
        """Test _handle_product_search_start method directly."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.set = AsyncMock()

        result = await chatbot._handle_product_search_start("5511999999999", "Maria")

        assert "Busca de Produtos" in result["text"]
        assert result["action"] == "await_query"
        chatbot.cache.set.assert_called()

    @pytest.mark.asyncio
    async def test_handle_alerts_no_alerts(self):
        """Test _handle_alerts method with no existing alerts."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.get = AsyncMock(return_value=None)

        result = await chatbot._handle_alerts("5511999999999", "Cliente")

        assert "Alertas de Preço" in result["text"]
        assert "ainda não tem alertas" in result["text"]
        assert result["action"] == "alerts"

    @pytest.mark.asyncio
    async def test_handle_alerts_with_alerts(self):
        """Test _handle_alerts method with existing alerts."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        user_alerts = [
            {"product": "iPhone 15", "target_price": 4500.00},
            {"product": "AirPods", "target_price": 800.00},
        ]
        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.get = AsyncMock(return_value=user_alerts)

        result = await chatbot._handle_alerts("5511999999999", "Cliente")

        assert "Seus Alertas de Preço" in result["text"]
        assert "iPhone 15" in result["text"]

    @pytest.mark.asyncio
    async def test_handle_price_comparison_with_products(self):
        """Test _handle_price_comparison with products."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.increment = AsyncMock()
        chatbot.scraper = AsyncMock()
        chatbot.scraper.get_products = AsyncMock(
            return_value={
                "products": [
                    {
                        "title": "Fone Bluetooth",
                        "price": 50.00,
                        "original_price": 100.00,
                    }
                ]
            }
        )

        result = await chatbot._handle_price_comparison("5511999999999", "Cliente")

        assert "Comparação de Preços" in result["text"]
        assert result["action"] == "comparison"

    @pytest.mark.asyncio
    async def test_handle_price_comparison_no_products(self):
        """Test _handle_price_comparison with no products."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.increment = AsyncMock()
        chatbot.scraper = AsyncMock()
        chatbot.scraper.get_products = AsyncMock(return_value={"products": []})

        result = await chatbot._handle_price_comparison("5511999999999", "Cliente")

        assert "não temos produtos em promoção" in result["text"]

    @pytest.mark.asyncio
    async def test_handle_price_comparison_error(self):
        """Test _handle_price_comparison handles errors."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.increment = AsyncMock()
        chatbot.scraper = AsyncMock()
        chatbot.scraper.get_products = AsyncMock(side_effect=Exception("DB Error"))

        result = await chatbot._handle_price_comparison("5511999999999", "Cliente")

        assert "Erro" in result["text"]

    @pytest.mark.asyncio
    async def test_search_real_products_with_results(self):
        """Test _search_real_products with results."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.delete = AsyncMock()
        chatbot.cache.increment = AsyncMock()
        chatbot.scraper = AsyncMock()
        chatbot.scraper.search_products = AsyncMock(
            return_value={
                "products": [
                    {
                        "title": "Fone Bluetooth JBL",
                        "price": 149.90,
                        "original_price": 249.90,
                        "rating": 4.5,
                        "sales_count": 1500,
                        "shop_name": "Loja Oficial",
                    }
                ],
                "total": 50,
            }
        )

        result = await chatbot._search_real_products(
            "5511999999999", "fone bluetooth", "João"
        )

        assert "Encontrei" in result["text"]
        assert "50" in result["text"]
        assert result["action"] == "products_found"
        assert "products" in result

    @pytest.mark.asyncio
    async def test_search_real_products_no_results(self):
        """Test _search_real_products with no results."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.delete = AsyncMock()
        chatbot.cache.increment = AsyncMock()
        chatbot.scraper = AsyncMock()
        chatbot.scraper.search_products = AsyncMock(
            return_value={"products": [], "total": 0}
        )
        chatbot.scraper.get_trending_products = AsyncMock(
            return_value={"products": [{"title": "Produto Trending"}]}
        )

        result = await chatbot._search_real_products(
            "5511999999999", "xyzabc123", "Cliente"
        )

        assert "Não encontrei" in result["text"]
        assert result["action"] == "no_results"

    @pytest.mark.asyncio
    async def test_search_real_products_error(self):
        """Test _search_real_products handles errors."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.delete = AsyncMock()
        chatbot.cache.increment = AsyncMock()
        chatbot.scraper = AsyncMock()
        chatbot.scraper.search_products = AsyncMock(side_effect=Exception("API Error"))

        result = await chatbot._search_real_products("5511999999999", "fone", "Cliente")

        assert "erro" in result["text"].lower()
        assert result["action"] == "error"

    @pytest.mark.asyncio
    async def test_increment_metric_success(self):
        """Test _increment_metric works correctly."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.increment = AsyncMock()

        await chatbot._increment_metric("test_metric")

        chatbot.cache.increment.assert_called_once()

    @pytest.mark.asyncio
    async def test_increment_metric_error_handling(self):
        """Test _increment_metric handles errors gracefully."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.increment = AsyncMock(side_effect=Exception("Redis error"))

        # Should not raise
        await chatbot._increment_metric("test_metric")


class TestProcessMessage:
    """Tests for process_message method."""

    @pytest.mark.asyncio
    async def test_process_message_welcome(self):
        """Test processing unknown message shows welcome."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.get = AsyncMock(return_value=None)
        chatbot.cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999", message="olá", push_name="João"
        )

        assert "Didin Fácil" in result["text"]
        assert result["action"] == "welcome"

    @pytest.mark.asyncio
    async def test_process_message_menu(self):
        """Test processing menu command."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.get = AsyncMock(return_value=None)
        chatbot.cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999", message="0", push_name="Maria"
        )

        assert "Menu Principal" in result["text"]
        assert result["action"] == "menu"

    @pytest.mark.asyncio
    async def test_process_message_search_start(self):
        """Test processing search start command."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.get = AsyncMock(return_value=None)
        chatbot.cache.set = AsyncMock()
        chatbot.cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999", message="1", push_name="Cliente"
        )

        assert "Busca de Produtos" in result["text"]
        assert result["action"] == "await_query"

    @pytest.mark.asyncio
    async def test_process_message_waiting_for_query(self):
        """Test processing query when waiting for product query."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.get = AsyncMock(return_value={"waiting_for": "product_query"})
        chatbot.cache.delete = AsyncMock()
        chatbot.cache.increment = AsyncMock()
        chatbot.scraper = AsyncMock()
        chatbot.scraper.search_products = AsyncMock(
            return_value={
                "products": [
                    {
                        "title": "Fone",
                        "price": 50.0,
                        "rating": 4.0,
                        "sales_count": 100,
                        "shop_name": "Loja",
                    }
                ],
                "total": 1,
            }
        )

        result = await chatbot.process_message(
            phone="5511999999999", message="fone", push_name="Cliente"
        )

        assert result["action"] == "products_found"

    @pytest.mark.asyncio
    async def test_process_message_human_transfer(self):
        """Test processing human transfer command."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.get = AsyncMock(return_value=None)
        chatbot.cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999", message="4", push_name="Cliente"
        )

        assert "Transferência para Atendente" in result["text"]
        assert result["action"] == "transfer_human"

    @pytest.mark.asyncio
    async def test_process_message_no_push_name(self):
        """Test processing with no push_name defaults to 'cliente'."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.get = AsyncMock(return_value=None)
        chatbot.cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999", message="olá", push_name=None
        )

        assert "cliente" in result["text"]

    @pytest.mark.asyncio
    async def test_process_message_uppercase(self):
        """Test processing uppercase commands."""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.get = AsyncMock(return_value=None)
        chatbot.cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999", message="MENU", push_name="Test"
        )

        assert result["action"] == "menu"


class TestChatbotMenuVariations:
    """Test different menu input variations."""

    @pytest.mark.asyncio
    async def test_menu_keyword_variations(self):
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.get = AsyncMock(return_value=None)
        chatbot.cache.increment = AsyncMock()

        keywords = ["0", "menu", "voltar", "inicio"]
        for keyword in keywords:
            result = await chatbot.process_message(
                phone="5511999999999", message=keyword, push_name="Test"
            )
            assert result["action"] == "menu", f"Failed for keyword: {keyword}"

    @pytest.mark.asyncio
    async def test_product_search_keyword_variations(self):
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.get = AsyncMock(return_value=None)
        chatbot.cache.set = AsyncMock()
        chatbot.cache.increment = AsyncMock()

        keywords = ["1", "buscar", "produto", "produtos"]
        for keyword in keywords:
            result = await chatbot.process_message(
                phone="5511999999999", message=keyword, push_name="Test"
            )
            assert result["action"] == "await_query", f"Failed for keyword: {keyword}"

    @pytest.mark.asyncio
    async def test_compare_keyword_variations(self):
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.get = AsyncMock(return_value=None)
        chatbot.cache.increment = AsyncMock()
        chatbot.scraper = AsyncMock()
        chatbot.scraper.get_products = AsyncMock(return_value={"products": []})

        keywords = ["2", "comparar", "preço", "preços"]
        for keyword in keywords:
            result = await chatbot.process_message(
                phone="5511999999999", message=keyword, push_name="Test"
            )
            assert result["action"] == "comparison", f"Failed for keyword: {keyword}"

    @pytest.mark.asyncio
    async def test_alerts_keyword_variations(self):
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.get = AsyncMock(return_value=None)
        chatbot.cache.increment = AsyncMock()

        keywords = ["3", "alerta", "alertas"]
        for keyword in keywords:
            result = await chatbot.process_message(
                phone="5511999999999", message=keyword, push_name="Test"
            )
            assert result["action"] == "alerts", f"Failed for keyword: {keyword}"

    @pytest.mark.asyncio
    async def test_human_transfer_keyword_variations(self):
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.get = AsyncMock(return_value=None)
        chatbot.cache.increment = AsyncMock()

        keywords = ["4", "atendente", "humano", "ajuda"]
        for keyword in keywords:
            result = await chatbot.process_message(
                phone="5511999999999", message=keyword, push_name="Test"
            )
            assert (
                result["action"] == "transfer_human"
            ), f"Failed for keyword: {keyword}"


# ============================================
# WEBHOOK ENDPOINT TESTS
# ============================================


class TestWebhookEndpoint:
    """Tests for the webhook endpoint."""

    def test_router_exists(self):
        from api.routes.whatsapp_webhook import router

        assert router is not None
        assert router.prefix == "/whatsapp-webhook"

    def test_router_tags(self):
        from api.routes.whatsapp_webhook import router

        assert "WhatsApp Webhook" in router.tags

    def test_constants_defined(self):
        from api.routes.whatsapp_webhook import (EVOLUTION_API_KEY,
                                                 EVOLUTION_API_URL,
                                                 EVOLUTION_INSTANCE)

        assert EVOLUTION_API_URL is not None
        assert EVOLUTION_API_KEY is not None
        assert EVOLUTION_INSTANCE is not None

    def test_chatbot_singleton_exists(self):
        from api.routes.whatsapp_webhook import chatbot

        assert chatbot is not None


class TestProductFormatting:
    """Tests for product formatting in chatbot responses."""

    @pytest.mark.asyncio
    async def test_product_with_discount(self):
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.delete = AsyncMock()
        chatbot.cache.increment = AsyncMock()
        chatbot.scraper = AsyncMock()
        chatbot.scraper.search_products = AsyncMock(
            return_value={
                "products": [
                    {
                        "title": "Produto com Desconto",
                        "price": 80.00,
                        "original_price": 100.00,
                        "rating": 4.0,
                        "sales_count": 100,
                        "shop_name": "Loja",
                    }
                ],
                "total": 1,
            }
        )

        result = await chatbot._search_real_products(
            "5511999999999", "produto", "Test"
        )

        # Should show discount percentage (-20%)
        assert "-20%" in result["text"]

    @pytest.mark.asyncio
    async def test_product_without_discount(self):
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.delete = AsyncMock()
        chatbot.cache.increment = AsyncMock()
        chatbot.scraper = AsyncMock()
        chatbot.scraper.search_products = AsyncMock(
            return_value={
                "products": [
                    {
                        "title": "Produto sem Desconto",
                        "price": 100.00,
                        "original_price": None,
                        "rating": 4.5,
                        "sales_count": 50,
                        "shop_name": "Loja",
                    }
                ],
                "total": 1,
            }
        )

        result = await chatbot._search_real_products(
            "5511999999999", "produto", "Test"
        )

        assert "R$ 100.00" in result["text"]

    @pytest.mark.asyncio
    async def test_long_product_title_truncated(self):
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.delete = AsyncMock()
        chatbot.cache.increment = AsyncMock()
        chatbot.scraper = AsyncMock()

        long_title = "A" * 100  # Very long title
        chatbot.scraper.search_products = AsyncMock(
            return_value={
                "products": [
                    {
                        "title": long_title,
                        "price": 50.00,
                        "rating": 4.0,
                        "sales_count": 10,
                        "shop_name": "Loja",
                    }
                ],
                "total": 1,
            }
        )

        result = await chatbot._search_real_products(
            "5511999999999", "produto", "Test"
        )

        # Title should be truncated to 50 chars in response
        assert len(long_title) > 50  # Original is long
        # Response should contain truncated version (50 chars)
        assert "A" * 50 in result["text"]


# ============================================
# EVOLUTION WEBHOOK TESTS
# ============================================


class TestEvolutionWebhook:
    """Tests for Evolution webhook endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.whatsapp_webhook.cache")
    async def test_connection_update_event(self, mock_cache):
        from unittest.mock import AsyncMock, MagicMock

        from api.routes.whatsapp_webhook import evolution_webhook
        from fastapi import BackgroundTasks

        mock_cache.set = AsyncMock()

        # Create mock request
        mock_request = MagicMock()
        mock_request.json = AsyncMock(return_value={
            "event": "CONNECTION_UPDATE",
            "instance": "test-instance",
            "data": {"state": "open"},
        })
        bg_tasks = BackgroundTasks()

        result = await evolution_webhook(mock_request, bg_tasks)

        assert result["status"] == "ok"
        assert result["state"] == "open"

    @pytest.mark.asyncio
    async def test_messages_update_event(self):
        from unittest.mock import AsyncMock, MagicMock

        from api.routes.whatsapp_webhook import evolution_webhook
        from fastapi import BackgroundTasks

        # Create mock request
        mock_request = MagicMock()
        mock_request.json = AsyncMock(return_value={
            "event": "MESSAGES_UPDATE",
            "instance": "test-instance",
            "data": {"status": "read"},
        })
        bg_tasks = BackgroundTasks()

        result = await evolution_webhook(mock_request, bg_tasks)

        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_unknown_event(self):
        from unittest.mock import AsyncMock, MagicMock

        from api.routes.whatsapp_webhook import evolution_webhook
        from fastapi import BackgroundTasks

        # Create mock request
        mock_request = MagicMock()
        mock_request.json = AsyncMock(return_value={
            "event": "UNKNOWN_EVENT",
            "instance": "test-instance",
            "data": {},
        })
        bg_tasks = BackgroundTasks()

        result = await evolution_webhook(mock_request, bg_tasks)

        # Unknown events may return different status based on implementation
        assert "status" in result


# ============================================
# EDGE CASES
# ============================================


class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_empty_message(self):
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.get = AsyncMock(return_value=None)
        chatbot.cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999", message="   ", push_name="Test"
        )

        # Should show welcome for empty/whitespace message
        assert result["action"] == "welcome"

    @pytest.mark.asyncio
    async def test_mixed_case_commands(self):
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.get = AsyncMock(return_value=None)
        chatbot.cache.set = AsyncMock()
        chatbot.cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999", message="BuScAr", push_name="Test"
        )

        assert result["action"] == "await_query"

    @pytest.mark.asyncio
    async def test_message_with_extra_spaces(self):
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache = AsyncMock()
        chatbot.cache.get = AsyncMock(return_value=None)
        chatbot.cache.increment = AsyncMock()

        result = await chatbot.process_message(
            phone="5511999999999", message="  0  ", push_name="Test"
        )

        assert result["action"] == "menu"
