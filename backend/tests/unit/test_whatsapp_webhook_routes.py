"""
Tests for WhatsApp Webhook Routes
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestWebhookModels:
    """Tests for webhook models"""

    def test_evolution_webhook_payload(self):
        """Test webhook payload model"""
        from api.routes.whatsapp_webhook import EvolutionWebhookPayload

        payload = EvolutionWebhookPayload(
            event="MESSAGES_UPSERT",
            instance="test",
            data={"key": "value"}
        )
        assert payload.event == "MESSAGES_UPSERT"

    def test_whatsapp_message_model(self):
        """Test WhatsApp message model"""
        from api.routes.whatsapp_webhook import WhatsAppMessage

        msg = WhatsAppMessage(
            remote_jid="5511999999999@s.whatsapp.net",
            message_id="msg-123",
            from_me=False,
            message_type="text",
            text="Hello",
            timestamp=datetime.now(timezone.utc)
        )
        assert msg.message_type == "text"


class TestChatbotMenuOptions:
    """Tests for chatbot menu handling"""

    @pytest.fixture
    def chatbot(self):
        from api.routes.whatsapp_webhook import RealProductChatbot
        return RealProductChatbot()

    @pytest.mark.asyncio
    async def test_menu_option_1(self, chatbot):
        """Test menu option 1"""
        with patch.object(chatbot.cache, 'set', new_callable=AsyncMock), \
             patch.object(chatbot.cache, 'get', return_value=None), \
             patch.object(chatbot.cache, 'increment', new_callable=AsyncMock):
            result = await chatbot.process_message("5511999999999", "1", "Test")
            assert result["action"] == "await_query"

    @pytest.mark.asyncio
    async def test_menu_option_0(self, chatbot):
        """Test menu option 0"""
        with patch.object(chatbot.cache, 'get', return_value=None), \
             patch.object(chatbot.cache, 'increment', new_callable=AsyncMock):
            result = await chatbot.process_message("5511999999999", "0", "Test")
            assert result["action"] == "menu"

    @pytest.mark.asyncio
    async def test_welcome_message(self, chatbot):
        """Test welcome message"""
        with patch.object(chatbot.cache, 'get', return_value=None), \
             patch.object(chatbot.cache, 'increment', new_callable=AsyncMock):
            result = await chatbot.process_message("5511999", "hello", "Test")
            assert result["action"] == "welcome"


class TestEvolutionWebhook:
    """Tests for evolution webhook endpoint"""

    @pytest.mark.asyncio
    async def test_messages_upsert(self):
        """Test MESSAGES_UPSERT event"""
        from api.routes.whatsapp_webhook import evolution_webhook

        mock_req = MagicMock()
        mock_req.json = AsyncMock(return_value={
            "event": "MESSAGES_UPSERT",
            "instance": "test",
            "data": {"key": {"remoteJid": "5511@s.whatsapp.net"}}
        })
        mock_bg = MagicMock()

        result = await evolution_webhook(mock_req, mock_bg)
        assert result["status"] == "processing"

    @pytest.mark.asyncio
    async def test_connection_update(self):
        """Test CONNECTION_UPDATE event"""
        from api.routes.whatsapp_webhook import cache, evolution_webhook

        mock_req = MagicMock()
        mock_req.json = AsyncMock(return_value={
            "event": "CONNECTION_UPDATE",
            "instance": "test",
            "data": {"state": "open"}
        })
        mock_bg = MagicMock()

        with patch.object(cache, 'set', new_callable=AsyncMock):
            result = await evolution_webhook(mock_req, mock_bg)
        assert result["state"] == "open"

    @pytest.mark.asyncio
    async def test_unknown_event(self):
        """Test unknown event"""
        from api.routes.whatsapp_webhook import evolution_webhook

        mock_req = MagicMock()
        mock_req.json = AsyncMock(return_value={
            "event": "UNKNOWN",
            "instance": "test",
            "data": {}
        })
        mock_bg = MagicMock()

        result = await evolution_webhook(mock_req, mock_bg)
        assert result["status"] == "ignored"

    @pytest.mark.asyncio
    async def test_webhook_error(self):
        """Test webhook error handling"""
        from api.routes.whatsapp_webhook import evolution_webhook

        mock_req = MagicMock()
        mock_req.json = AsyncMock(side_effect=Exception("Parse error"))
        mock_bg = MagicMock()

        result = await evolution_webhook(mock_req, mock_bg)
        assert result["status"] == "error"


class TestProcessMessage:
    """Tests for process_incoming_message"""

    @pytest.mark.asyncio
    async def test_ignore_from_me(self):
        """Test ignoring own messages"""
        from api.routes.whatsapp_webhook import process_incoming_message

        data = {"key": {"remoteJid": "5511@s.whatsapp.net", "fromMe": True}}
        await process_incoming_message(data, "test")  # Should not raise

    @pytest.mark.asyncio
    async def test_ignore_group(self):
        """Test ignoring group messages"""
        from api.routes.whatsapp_webhook import process_incoming_message

        data = {"key": {"remoteJid": "123@g.us", "fromMe": False}}
        await process_incoming_message(data, "test")  # Should not raise


class TestWebhookStatus:
    """Tests for webhook status endpoint"""

    @pytest.mark.asyncio
    async def test_status_healthy(self):
        """Test healthy status"""
        from api.routes.whatsapp_webhook import cache, webhook_status

        with patch.object(cache, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [{"state": "open"}, 100, 50]
            result = await webhook_status()
            assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_status_error(self):
        """Test status with error"""
        from api.routes.whatsapp_webhook import cache, webhook_status

        with patch.object(cache, 'get', side_effect=Exception("Redis error")):
            result = await webhook_status()
            assert result["status"] == "error"


class TestTestChatbot:
    """Tests for test_chatbot endpoint"""

    @pytest.mark.asyncio
    async def test_chatbot_test_endpoint(self):
        """Test chatbot test endpoint"""
        from api.routes.whatsapp_webhook import chatbot, test_chatbot

        with patch.object(
            chatbot, 'process_message', new_callable=AsyncMock
        ) as mock_p:
            mock_p.return_value = {"text": "Hi", "action": "welcome"}
            result = await test_chatbot("5511999999999", "hi", "Test")
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_chatbot_test_endpoint_error(self):
        """Test chatbot test endpoint with error"""
        from api.routes.whatsapp_webhook import chatbot, test_chatbot
        from fastapi import HTTPException

        with patch.object(
            chatbot, 'process_message', new_callable=AsyncMock
        ) as mock_p:
            mock_p.side_effect = Exception("Chatbot error")
            with pytest.raises(HTTPException) as exc:
                await test_chatbot("5511999999999", "hi", "Test")
            assert exc.value.status_code == 500


class TestChatbotProductSearch:
    """Tests for chatbot product search functionality"""

    @pytest.fixture
    def chatbot(self):
        from api.routes.whatsapp_webhook import RealProductChatbot
        return RealProductChatbot()

    @pytest.mark.asyncio
    async def test_search_real_products_success(self, chatbot):
        """Test successful product search"""
        mock_products = {
            "products": [
                {
                    "title": "Fone Bluetooth",
                    "price": 59.90,
                    "original_price": 99.90,
                    "rating": 4.5,
                    "sales_count": 1000,
                    "shop_name": "Loja Test"
                }
            ],
            "total": 1
        }
        
        with patch.object(chatbot.cache, 'delete', new_callable=AsyncMock), \
             patch.object(chatbot.cache, 'increment', new_callable=AsyncMock), \
             patch.object(chatbot.scraper, 'search_products', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_products
            
            result = await chatbot._search_real_products(
                "5511999999999", "fone bluetooth", "Test"
            )
            
            assert result["action"] == "products_found"
            assert len(result["products"]) == 1

    @pytest.mark.asyncio
    async def test_search_real_products_no_results(self, chatbot):
        """Test product search with no results"""
        with patch.object(chatbot.cache, 'delete', new_callable=AsyncMock), \
             patch.object(chatbot.cache, 'increment', new_callable=AsyncMock), \
             patch.object(chatbot.scraper, 'search_products', new_callable=AsyncMock) as mock_search, \
             patch.object(chatbot.scraper, 'get_trending_products', new_callable=AsyncMock) as mock_trend:
            mock_search.return_value = {"products": [], "total": 0}
            mock_trend.return_value = {"products": []}
            
            result = await chatbot._search_real_products(
                "5511999999999", "produto inexistente", "Test"
            )
            
            assert result["action"] == "no_results"

    @pytest.mark.asyncio
    async def test_search_real_products_with_trending(self, chatbot):
        """Test product search showing trending when no results"""
        trending = [{"title": "Produto Trending"}]
        
        with patch.object(chatbot.cache, 'delete', new_callable=AsyncMock), \
             patch.object(chatbot.cache, 'increment', new_callable=AsyncMock), \
             patch.object(chatbot.scraper, 'search_products', new_callable=AsyncMock) as mock_search, \
             patch.object(chatbot.scraper, 'get_trending_products', new_callable=AsyncMock) as mock_trend:
            mock_search.return_value = {"products": [], "total": 0}
            mock_trend.return_value = {"products": trending}
            
            result = await chatbot._search_real_products(
                "5511999999999", "xyz", "Test"
            )
            
            assert "Produtos em Alta" in result["text"]

    @pytest.mark.asyncio
    async def test_search_real_products_error(self, chatbot):
        """Test product search with error"""
        with patch.object(chatbot.cache, 'delete', new_callable=AsyncMock), \
             patch.object(chatbot.cache, 'increment', new_callable=AsyncMock), \
             patch.object(chatbot.scraper, 'search_products', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = Exception("DB error")
            
            result = await chatbot._search_real_products(
                "5511999999999", "fone", "Test"
            )
            
            assert result["action"] == "error"


class TestChatbotPriceComparison:
    """Tests for chatbot price comparison"""

    @pytest.fixture
    def chatbot(self):
        from api.routes.whatsapp_webhook import RealProductChatbot
        return RealProductChatbot()

    @pytest.mark.asyncio
    async def test_price_comparison_success(self, chatbot):
        """Test successful price comparison"""
        mock_products = {
            "products": [
                {
                    "title": "Produto 1",
                    "price": 50.00,
                    "original_price": 100.00
                }
            ]
        }
        
        with patch.object(chatbot.scraper, 'get_products', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_products
            
            result = await chatbot._handle_price_comparison("5511999999999", "Test")
            
            assert result["action"] == "comparison"
            assert "Economia" in result["text"]

    @pytest.mark.asyncio
    async def test_price_comparison_no_products(self, chatbot):
        """Test price comparison with no products"""
        with patch.object(chatbot.scraper, 'get_products', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"products": []}
            
            result = await chatbot._handle_price_comparison("5511999999999", "Test")
            
            assert result["action"] == "comparison"
            assert "não temos produtos" in result["text"]

    @pytest.mark.asyncio
    async def test_price_comparison_error(self, chatbot):
        """Test price comparison with error"""
        with patch.object(chatbot.scraper, 'get_products', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Error")
            
            result = await chatbot._handle_price_comparison("5511999999999", "Test")
            
            assert "Erro" in result["text"]


class TestChatbotAlerts:
    """Tests for chatbot alerts functionality"""

    @pytest.fixture
    def chatbot(self):
        from api.routes.whatsapp_webhook import RealProductChatbot
        return RealProductChatbot()

    @pytest.mark.asyncio
    async def test_alerts_with_existing(self, chatbot):
        """Test alerts with existing alerts"""
        existing_alerts = [
            {"product": "Fone", "target_price": 50.00}
        ]
        
        with patch.object(chatbot.cache, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = existing_alerts
            
            result = await chatbot._handle_alerts("5511999999999", "Test")
            
            assert "1 alertas ativos" in result["text"]

    @pytest.mark.asyncio
    async def test_alerts_empty(self, chatbot):
        """Test alerts when no alerts exist"""
        with patch.object(chatbot.cache, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            result = await chatbot._handle_alerts("5511999999999", "Test")
            
            assert "ainda não tem alertas" in result["text"]


class TestChatbotHumanTransfer:
    """Tests for human transfer functionality"""

    @pytest.fixture
    def chatbot(self):
        from api.routes.whatsapp_webhook import RealProductChatbot
        return RealProductChatbot()

    @pytest.mark.asyncio
    async def test_human_transfer(self, chatbot):
        """Test human transfer request"""
        with patch.object(chatbot.cache, 'increment', new_callable=AsyncMock):
            result = await chatbot._handle_human_transfer("5511999999999", "Test")
            
            assert result["action"] == "transfer_human"
            assert result["metadata"]["department"] == "support"


class TestChatbotMetrics:
    """Tests for chatbot metrics functionality"""

    @pytest.fixture
    def chatbot(self):
        from api.routes.whatsapp_webhook import RealProductChatbot
        return RealProductChatbot()

    @pytest.mark.asyncio
    async def test_increment_metric_success(self, chatbot):
        """Test successful metric increment"""
        with patch.object(chatbot.cache, 'increment', new_callable=AsyncMock) as mock_inc:
            await chatbot._increment_metric("test_metric")
            mock_inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_increment_metric_error(self, chatbot):
        """Test metric increment with error (should not raise)"""
        with patch.object(chatbot.cache, 'increment', new_callable=AsyncMock) as mock_inc:
            mock_inc.side_effect = Exception("Redis error")
            # Should not raise, just log warning
            await chatbot._increment_metric("test_metric")


class TestSendWhatsAppMessage:
    """Tests for send_whatsapp_message function"""

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Test successful message sending"""
        from api.routes.whatsapp_webhook import cache, send_whatsapp_message
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_instance
            
            with patch.object(cache, 'increment', new_callable=AsyncMock):
                await send_whatsapp_message("test-instance", "5511999", "Hello")

    @pytest.mark.asyncio
    async def test_send_message_failure(self):
        """Test message sending failure"""
        from api.routes.whatsapp_webhook import send_whatsapp_message
        
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Error"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_instance
            
            # Should not raise, just log error
            await send_whatsapp_message("test-instance", "5511999", "Hello")

    @pytest.mark.asyncio
    async def test_send_message_exception(self):
        """Test message sending with exception"""
        from api.routes.whatsapp_webhook import send_whatsapp_message
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.side_effect = Exception("Network error")
            
            # Should not raise, just log error
            await send_whatsapp_message("test-instance", "5511999", "Hello")


class TestSaveInteraction:
    """Tests for save_interaction function"""

    @pytest.mark.asyncio
    async def test_save_interaction_success(self):
        """Test successful interaction saving"""
        from api.routes.whatsapp_webhook import cache, save_interaction
        
        with patch.object(cache, 'increment', new_callable=AsyncMock), \
             patch.object(cache, 'get', new_callable=AsyncMock) as mock_get, \
             patch.object(cache, 'set', new_callable=AsyncMock), \
             patch.object(cache, 'sadd', new_callable=AsyncMock):
            mock_get.return_value = []
            
            await save_interaction(
                "5511999999999",
                "Hello",
                {"action": "welcome", "text": "Hi"}
            )

    @pytest.mark.asyncio
    async def test_save_interaction_with_existing(self):
        """Test save interaction with existing conversation"""
        from api.routes.whatsapp_webhook import cache, save_interaction
        
        existing_conversation = [
            {"timestamp": "2024-01-01T00:00:00", "user_message": "Hi", "bot_action": "welcome"}
        ]
        
        with patch.object(cache, 'increment', new_callable=AsyncMock), \
             patch.object(cache, 'get', new_callable=AsyncMock) as mock_get, \
             patch.object(cache, 'set', new_callable=AsyncMock) as mock_set, \
             patch.object(cache, 'sadd', new_callable=AsyncMock):
            mock_get.return_value = existing_conversation
            
            await save_interaction(
                "5511999999999",
                "Hello again",
                {"action": "menu"}
            )
            
            # Check conversation was extended
            call_args = mock_set.call_args
            assert len(call_args[0][1]) == 2

    @pytest.mark.asyncio
    async def test_save_interaction_error(self):
        """Test save interaction with error (should not raise)"""
        from api.routes.whatsapp_webhook import cache, save_interaction
        
        with patch.object(cache, 'increment', new_callable=AsyncMock) as mock_inc:
            mock_inc.side_effect = Exception("Redis error")
            
            # Should not raise, just log warning
            await save_interaction("5511999", "Hi", {"action": "test"})


class TestProcessIncomingMessage:
    """Tests for process_incoming_message function"""

    @pytest.mark.asyncio
    async def test_process_text_conversation(self):
        """Test processing text conversation message"""
        from api.routes.whatsapp_webhook import (cache, chatbot,
                                                 process_incoming_message)
        
        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "msg-123"
            },
            "message": {
                "conversation": "Hello"
            },
            "pushName": "Test User"
        }
        
        with patch.object(chatbot, 'process_message', new_callable=AsyncMock) as mock_proc, \
             patch('api.routes.whatsapp_webhook.send_whatsapp_message', new_callable=AsyncMock), \
             patch('api.routes.whatsapp_webhook.save_interaction', new_callable=AsyncMock):
            mock_proc.return_value = {"text": "Hi!", "action": "welcome"}
            
            await process_incoming_message(data, "test-instance")
            
            mock_proc.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_extended_text_message(self):
        """Test processing extended text message"""
        from api.routes.whatsapp_webhook import (chatbot,
                                                 process_incoming_message)
        
        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "msg-123"
            },
            "message": {
                "extendedTextMessage": {"text": "Extended message"}
            },
            "pushName": "Test"
        }
        
        with patch.object(chatbot, 'process_message', new_callable=AsyncMock) as mock_proc, \
             patch('api.routes.whatsapp_webhook.send_whatsapp_message', new_callable=AsyncMock), \
             patch('api.routes.whatsapp_webhook.save_interaction', new_callable=AsyncMock):
            mock_proc.return_value = {"text": "Response", "action": "menu"}
            
            await process_incoming_message(data, "test-instance")
            
            # Should extract text from extendedTextMessage
            call_args = mock_proc.call_args
            assert call_args[1]["message"] == "Extended message"

    @pytest.mark.asyncio
    async def test_process_image_message(self):
        """Test processing image message"""
        from api.routes.whatsapp_webhook import (chatbot,
                                                 process_incoming_message)
        
        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "msg-123"
            },
            "message": {
                "imageMessage": {"caption": "Check this image"}
            },
            "pushName": "Test"
        }
        
        with patch.object(chatbot, 'process_message', new_callable=AsyncMock) as mock_proc, \
             patch('api.routes.whatsapp_webhook.send_whatsapp_message', new_callable=AsyncMock), \
             patch('api.routes.whatsapp_webhook.save_interaction', new_callable=AsyncMock):
            mock_proc.return_value = {"text": "Response", "action": "welcome"}
            
            await process_incoming_message(data, "test-instance")
            
            call_args = mock_proc.call_args
            assert call_args[1]["message"] == "Check this image"

    @pytest.mark.asyncio
    async def test_process_audio_message(self):
        """Test processing audio message"""
        from api.routes.whatsapp_webhook import (chatbot,
                                                 process_incoming_message)
        
        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "msg-123"
            },
            "message": {
                "audioMessage": {}
            },
            "pushName": "Test"
        }
        
        with patch.object(chatbot, 'process_message', new_callable=AsyncMock) as mock_proc, \
             patch('api.routes.whatsapp_webhook.send_whatsapp_message', new_callable=AsyncMock), \
             patch('api.routes.whatsapp_webhook.save_interaction', new_callable=AsyncMock):
            mock_proc.return_value = {"text": "Response", "action": "welcome"}
            
            await process_incoming_message(data, "test-instance")
            
            call_args = mock_proc.call_args
            assert call_args[1]["message"] == "audio"

    @pytest.mark.asyncio
    async def test_process_document_message(self):
        """Test processing document message"""
        from api.routes.whatsapp_webhook import (chatbot,
                                                 process_incoming_message)
        
        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "msg-123"
            },
            "message": {
                "documentMessage": {}
            },
            "pushName": "Test"
        }
        
        with patch.object(chatbot, 'process_message', new_callable=AsyncMock) as mock_proc, \
             patch('api.routes.whatsapp_webhook.send_whatsapp_message', new_callable=AsyncMock), \
             patch('api.routes.whatsapp_webhook.save_interaction', new_callable=AsyncMock):
            mock_proc.return_value = {"text": "Response", "action": "welcome"}
            
            await process_incoming_message(data, "test-instance")
            
            call_args = mock_proc.call_args
            assert call_args[1]["message"] == "documento"

    @pytest.mark.asyncio
    async def test_process_no_text_content(self):
        """Test processing message with no text content"""
        from api.routes.whatsapp_webhook import process_incoming_message
        
        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "msg-123"
            },
            "message": {}  # Empty message
        }
        
        # Should return early without error
        await process_incoming_message(data, "test-instance")

    @pytest.mark.asyncio
    async def test_process_message_error(self):
        """Test process message with error (should not raise)"""
        from api.routes.whatsapp_webhook import (chatbot,
                                                 process_incoming_message)
        
        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "msg-123"
            },
            "message": {"conversation": "Hello"}
        }
        
        with patch.object(chatbot, 'process_message', new_callable=AsyncMock) as mock_proc:
            mock_proc.side_effect = Exception("Error")
            
            # Should not raise, just log error
            await process_incoming_message(data, "test-instance")


class TestChatbotStateHandling:
    """Tests for chatbot state handling"""

    @pytest.fixture
    def chatbot(self):
        from api.routes.whatsapp_webhook import RealProductChatbot
        return RealProductChatbot()

    @pytest.mark.asyncio
    async def test_waiting_for_product_query(self, chatbot):
        """Test handling when waiting for product query"""
        user_state = {"waiting_for": "product_query"}
        
        with patch.object(chatbot.cache, 'get', new_callable=AsyncMock) as mock_get, \
             patch.object(chatbot.cache, 'delete', new_callable=AsyncMock), \
             patch.object(chatbot.cache, 'increment', new_callable=AsyncMock), \
             patch.object(chatbot.scraper, 'search_products', new_callable=AsyncMock) as mock_search:
            mock_get.return_value = user_state
            mock_search.return_value = {"products": [], "total": 0}
            
            with patch.object(chatbot.scraper, 'get_trending_products', new_callable=AsyncMock) as mock_trend:
                mock_trend.return_value = {"products": []}
                
                result = await chatbot.process_message(
                    "5511999", "fone bluetooth", "Test"
                )
                
                assert result["action"] == "no_results"

    @pytest.mark.asyncio
    async def test_menu_option_buscar(self, chatbot):
        """Test 'buscar' keyword"""
        with patch.object(chatbot.cache, 'set', new_callable=AsyncMock), \
             patch.object(chatbot.cache, 'get', return_value=None), \
             patch.object(chatbot.cache, 'increment', new_callable=AsyncMock):
            result = await chatbot.process_message("5511999", "buscar", "Test")
            assert result["action"] == "await_query"

    @pytest.mark.asyncio
    async def test_menu_option_comparar(self, chatbot):
        """Test 'comparar' keyword"""
        with patch.object(chatbot.cache, 'get', return_value=None), \
             patch.object(chatbot.cache, 'increment', new_callable=AsyncMock), \
             patch.object(chatbot.scraper, 'get_products', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"products": []}
            
            result = await chatbot.process_message("5511999", "comparar", "Test")
            assert result["action"] == "comparison"

    @pytest.mark.asyncio
    async def test_menu_option_alerta(self, chatbot):
        """Test 'alerta' keyword"""
        with patch.object(chatbot.cache, 'get', new_callable=AsyncMock) as mock_get, \
             patch.object(chatbot.cache, 'increment', new_callable=AsyncMock):
            mock_get.side_effect = [None, None]  # First for state, second for alerts
            
            result = await chatbot.process_message("5511999", "alerta", "Test")
            assert result["action"] == "alerts"

    @pytest.mark.asyncio
    async def test_menu_option_atendente(self, chatbot):
        """Test 'atendente' keyword"""
        with patch.object(chatbot.cache, 'get', return_value=None), \
             patch.object(chatbot.cache, 'increment', new_callable=AsyncMock):
            result = await chatbot.process_message("5511999", "atendente", "Test")
            assert result["action"] == "transfer_human"


class TestEvolutionWebhookMessagesUpdate:
    """Tests for MESSAGES_UPDATE event"""

    @pytest.mark.asyncio
    async def test_messages_update_event(self):
        """Test MESSAGES_UPDATE event handling"""
        from api.routes.whatsapp_webhook import evolution_webhook

        mock_req = MagicMock()
        mock_req.json = AsyncMock(return_value={
            "event": "MESSAGES_UPDATE",
            "instance": "test",
            "data": {"status": "read"}
        })
        mock_bg = MagicMock()

        result = await evolution_webhook(mock_req, mock_bg)
        assert result["status"] == "ok"
        assert result["event"] == "MESSAGES_UPDATE"
