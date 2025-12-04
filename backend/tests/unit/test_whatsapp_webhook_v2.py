"""
Tests for WhatsApp Webhook Handler (Extended Coverage)
Tests for Evolution API webhook processing and chatbot logic.
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestEvolutionWebhookPayload:
    """Tests for EvolutionWebhookPayload model"""

    def test_payload_full(self):
        """Test payload with all fields"""
        from api.routes.whatsapp_webhook import EvolutionWebhookPayload

        payload = EvolutionWebhookPayload(
            event="MESSAGES_UPSERT",
            instance="test-instance",
            data={"key": {"remoteJid": "5511999999999@s.whatsapp.net"}},
            sender="5511999999999",
            destination="5511888888888",
            date_time="2024-01-01T00:00:00"
        )

        assert payload.event == "MESSAGES_UPSERT"
        assert payload.instance == "test-instance"
        assert "key" in payload.data
        assert payload.sender == "5511999999999"

    def test_payload_minimal(self):
        """Test payload with minimal fields"""
        from api.routes.whatsapp_webhook import EvolutionWebhookPayload

        payload = EvolutionWebhookPayload(
            event="CONNECTION_UPDATE",
            instance="tiktrend-whatsapp",
            data={"state": "open"}
        )

        assert payload.event == "CONNECTION_UPDATE"
        assert payload.sender is None
        assert payload.destination is None


class TestWhatsAppMessage:
    """Tests for WhatsAppMessage model"""

    def test_message_full(self):
        """Test message with all fields"""
        from api.routes.whatsapp_webhook import WhatsAppMessage

        msg = WhatsAppMessage(
            remote_jid="5511999999999@s.whatsapp.net",
            message_id="MSG123",
            from_me=False,
            push_name="João",
            message_type="text",
            text="Olá!",
            media_url=None,
            timestamp=datetime.now(timezone.utc)
        )

        assert msg.remote_jid == "5511999999999@s.whatsapp.net"
        assert msg.from_me is False
        assert msg.push_name == "João"
        assert msg.message_type == "text"

    def test_message_media(self):
        """Test message with media"""
        from api.routes.whatsapp_webhook import WhatsAppMessage

        msg = WhatsAppMessage(
            remote_jid="5511999999999@s.whatsapp.net",
            message_id="MSG456",
            from_me=False,
            message_type="image",
            media_url="https://example.com/image.jpg",
            timestamp=datetime.now(timezone.utc)
        )

        assert msg.message_type == "image"
        assert msg.media_url == "https://example.com/image.jpg"
        assert msg.text is None


class TestRealProductChatbot:
    """Tests for RealProductChatbot class"""

    @pytest.mark.asyncio
    async def test_process_welcome_message(self):
        """Test welcome message processing"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        
        with patch.object(chatbot.cache, 'get', new_callable=AsyncMock) as mock_get, \
             patch.object(chatbot.cache, 'increment', new_callable=AsyncMock):
            mock_get.return_value = None
            
            result = await chatbot.process_message(
                phone="5511999999999",
                message="oi",
                push_name="João"
            )

            assert result["action"] == "welcome"

    @pytest.mark.asyncio
    async def test_process_menu_option_1(self):
        """Test menu option 1 - product search"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        with patch.object(RealProductChatbot, '_increment_metric', new_callable=AsyncMock):
            with patch.object(RealProductChatbot, '_handle_product_search_start', new_callable=AsyncMock) as mock_search:
                mock_search.return_value = {"text": "Busca", "action": "await_query"}
                
                chatbot = RealProductChatbot()
                
                # Mock cache.get to return None (no state)
                chatbot.cache.get = AsyncMock(return_value=None)
                
                result = await chatbot.process_message(
                    phone="5511999999999",
                    message="1",
                    push_name="João"
                )

                assert result["action"] == "await_query"

    @pytest.mark.asyncio
    async def test_process_menu_option_2(self):
        """Test menu option 2 - price comparison"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        with patch.object(RealProductChatbot, '_increment_metric', new_callable=AsyncMock):
            with patch.object(RealProductChatbot, '_handle_price_comparison', new_callable=AsyncMock) as mock_comparison:
                mock_comparison.return_value = {"text": "Comparação", "action": "comparison"}
                
                chatbot = RealProductChatbot()
                chatbot.cache.get = AsyncMock(return_value=None)
                
                result = await chatbot.process_message(
                    phone="5511999999999",
                    message="comparar",
                    push_name="Maria"
                )

                assert result["action"] == "comparison"

    @pytest.mark.asyncio
    async def test_process_menu_option_3(self):
        """Test menu option 3 - alerts"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        with patch.object(RealProductChatbot, '_increment_metric', new_callable=AsyncMock):
            with patch.object(RealProductChatbot, '_handle_alerts', new_callable=AsyncMock) as mock_alerts:
                mock_alerts.return_value = {"text": "Alertas", "action": "alerts"}
                
                chatbot = RealProductChatbot()
                chatbot.cache.get = AsyncMock(return_value=None)
                
                result = await chatbot.process_message(
                    phone="5511999999999",
                    message="alerta"
                )

                assert result["action"] == "alerts"

    @pytest.mark.asyncio
    async def test_process_menu_option_4(self):
        """Test menu option 4 - human transfer"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        with patch.object(RealProductChatbot, '_increment_metric', new_callable=AsyncMock):
            with patch.object(RealProductChatbot, '_handle_human_transfer', new_callable=AsyncMock) as mock_transfer:
                mock_transfer.return_value = {"text": "Transferindo", "action": "transfer_human"}
                
                chatbot = RealProductChatbot()
                chatbot.cache.get = AsyncMock(return_value=None)
                
                result = await chatbot.process_message(
                    phone="5511999999999",
                    message="atendente"
                )

                assert result["action"] == "transfer_human"

    @pytest.mark.asyncio
    async def test_process_menu_back(self):
        """Test menu back option"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        with patch.object(RealProductChatbot, '_increment_metric', new_callable=AsyncMock):
            with patch.object(RealProductChatbot, '_show_main_menu', new_callable=AsyncMock) as mock_menu:
                mock_menu.return_value = {"text": "Menu", "action": "menu"}
                
                chatbot = RealProductChatbot()
                chatbot.cache.get = AsyncMock(return_value=None)
                
                result = await chatbot.process_message(
                    phone="5511999999999",
                    message="0"
                )

                assert result["action"] == "menu"

    @pytest.mark.asyncio
    async def test_process_product_query_state(self):
        """Test processing when waiting for product query"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        with patch.object(RealProductChatbot, '_increment_metric', new_callable=AsyncMock):
            with patch.object(RealProductChatbot, '_search_real_products', new_callable=AsyncMock) as mock_search:
                mock_search.return_value = {"text": "Produtos", "action": "products_found"}
                
                chatbot = RealProductChatbot()
                chatbot.cache.get = AsyncMock(return_value={"waiting_for": "product_query"})
                
                result = await chatbot.process_message(
                    phone="5511999999999",
                    message="fone bluetooth"
                )

                mock_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_increment_metric(self):
        """Test metric increment"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache.increment = AsyncMock()

        await chatbot._increment_metric("test_metric")

        chatbot.cache.increment.assert_called_once()

    @pytest.mark.asyncio
    async def test_increment_metric_error(self):
        """Test metric increment handles errors"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache.increment = AsyncMock(side_effect=Exception("Redis error"))

        # Should not raise
        await chatbot._increment_metric("test_metric")

    @pytest.mark.asyncio
    async def test_show_welcome(self):
        """Test welcome message"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        result = await chatbot._show_welcome("João")

        assert result["action"] == "welcome"
        assert "João" in result["text"]
        assert "TikTrend Finder" in result["text"]

    @pytest.mark.asyncio
    async def test_show_main_menu(self):
        """Test main menu message"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        result = await chatbot._show_main_menu("Maria")

        assert result["action"] == "menu"
        assert "Menu Principal" in result["text"]

    @pytest.mark.asyncio
    async def test_handle_product_search_start(self):
        """Test product search start"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache.set = AsyncMock()

        result = await chatbot._handle_product_search_start("5511999999999", "João")

        assert result["action"] == "await_query"
        assert "Busca de Produtos" in result["text"]
        chatbot.cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_real_products_found(self):
        """Test real product search with results"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache.delete = AsyncMock()
        chatbot._increment_metric = AsyncMock()
        chatbot.scraper.search_products = AsyncMock(return_value={
            "products": [
                {
                    "title": "Fone Bluetooth XYZ",
                    "price": 99.90,
                    "original_price": 149.90,
                    "rating": 4.5,
                    "sales_count": 1000,
                    "shop_name": "Loja Teste"
                }
            ],
            "total": 10
        })

        result = await chatbot._search_real_products("5511999999999", "fone", "João")

        assert result["action"] == "products_found"
        assert "products" in result
        assert len(result["products"]) == 1

    @pytest.mark.asyncio
    async def test_search_real_products_no_results(self):
        """Test real product search without results"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache.delete = AsyncMock()
        chatbot._increment_metric = AsyncMock()
        chatbot.scraper.search_products = AsyncMock(return_value={"products": [], "total": 0})
        chatbot.scraper.get_trending_products = AsyncMock(return_value={"products": []})

        result = await chatbot._search_real_products("5511999999999", "xyzabc123", "João")

        assert result["action"] == "no_results"
        assert "Não encontrei" in result["text"]

    @pytest.mark.asyncio
    async def test_search_real_products_with_trending(self):
        """Test search shows trending when no results"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache.delete = AsyncMock()
        chatbot._increment_metric = AsyncMock()
        chatbot.scraper.search_products = AsyncMock(return_value={"products": [], "total": 0})
        chatbot.scraper.get_trending_products = AsyncMock(return_value={
            "products": [{"title": "Trending Product"}]
        })

        result = await chatbot._search_real_products("5511999999999", "notfound", "João")

        assert result["action"] == "no_results"
        assert "Produtos em Alta" in result["text"]

    @pytest.mark.asyncio
    async def test_search_real_products_error(self):
        """Test search handles errors"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache.delete = AsyncMock()
        chatbot._increment_metric = AsyncMock()
        chatbot.scraper.search_products = AsyncMock(side_effect=Exception("DB error"))

        result = await chatbot._search_real_products("5511999999999", "fone", "João")

        assert result["action"] == "error"
        assert "erro" in result["text"].lower()

    @pytest.mark.asyncio
    async def test_handle_price_comparison_success(self):
        """Test price comparison with results"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.scraper.get_products = AsyncMock(return_value={
            "products": [
                {
                    "title": "Product A",
                    "price": 79.90,
                    "original_price": 99.90
                }
            ]
        })

        result = await chatbot._handle_price_comparison("5511999999999", "João")

        assert result["action"] == "comparison"
        assert "Comparação de Preços" in result["text"]

    @pytest.mark.asyncio
    async def test_handle_price_comparison_no_results(self):
        """Test price comparison without results"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.scraper.get_products = AsyncMock(return_value={"products": []})

        result = await chatbot._handle_price_comparison("5511999999999", "João")

        assert result["action"] == "comparison"
        assert "não temos produtos" in result["text"]

    @pytest.mark.asyncio
    async def test_handle_price_comparison_error(self):
        """Test price comparison handles errors"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.scraper.get_products = AsyncMock(side_effect=Exception("Error"))

        result = await chatbot._handle_price_comparison("5511999999999", "João")

        assert result["action"] == "comparison"
        assert "Erro" in result["text"]

    @pytest.mark.asyncio
    async def test_handle_alerts_with_existing(self):
        """Test alerts with existing user alerts"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache.get = AsyncMock(return_value=[
            {"product": "Fone", "target_price": 50.00}
        ])

        result = await chatbot._handle_alerts("5511999999999", "João")

        assert result["action"] == "alerts"
        assert "Seus Alertas" in result["text"]
        assert "1 alertas" in result["text"]

    @pytest.mark.asyncio
    async def test_handle_alerts_empty(self):
        """Test alerts without existing alerts"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot.cache.get = AsyncMock(return_value=None)

        result = await chatbot._handle_alerts("5511999999999", "João")

        assert result["action"] == "alerts"
        assert "ainda não tem alertas" in result["text"]

    @pytest.mark.asyncio
    async def test_handle_human_transfer(self):
        """Test human transfer"""
        from api.routes.whatsapp_webhook import RealProductChatbot

        chatbot = RealProductChatbot()
        chatbot._increment_metric = AsyncMock()

        result = await chatbot._handle_human_transfer("5511999999999", "João")

        assert result["action"] == "transfer_human"
        assert "metadata" in result
        assert result["metadata"]["department"] == "support"


class TestEvolutionWebhookEndpoint:
    """Tests for evolution_webhook endpoint"""

    @pytest.mark.asyncio
    async def test_messages_upsert_event(self):
        """Test MESSAGES_UPSERT event"""
        from unittest.mock import AsyncMock, MagicMock

        from api.routes.whatsapp_webhook import evolution_webhook
        from fastapi import BackgroundTasks

        request = MagicMock()
        request.json = AsyncMock(return_value={
            "event": "MESSAGES_UPSERT",
            "instance": "test",
            "data": {
                "key": {"remoteJid": "5511999999999@s.whatsapp.net"}
            }
        })
        
        background_tasks = MagicMock(spec=BackgroundTasks)
        background_tasks.add_task = MagicMock()

        result = await evolution_webhook(request, background_tasks)

        assert result["status"] == "processing"
        assert result["event"] == "MESSAGES_UPSERT"
        background_tasks.add_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_update_event(self):
        """Test CONNECTION_UPDATE event"""
        from api.routes.whatsapp_webhook import evolution_webhook
        from fastapi import BackgroundTasks

        request = MagicMock()
        request.json = AsyncMock(return_value={
            "event": "CONNECTION_UPDATE",
            "instance": "test",
            "data": {"state": "open"}
        })
        
        background_tasks = MagicMock(spec=BackgroundTasks)

        with patch('api.routes.whatsapp_webhook.cache.set', new_callable=AsyncMock):
            result = await evolution_webhook(request, background_tasks)

        assert result["status"] == "ok"
        assert result["state"] == "open"

    @pytest.mark.asyncio
    async def test_messages_update_event(self):
        """Test MESSAGES_UPDATE event"""
        from api.routes.whatsapp_webhook import evolution_webhook
        from fastapi import BackgroundTasks

        request = MagicMock()
        request.json = AsyncMock(return_value={
            "event": "MESSAGES_UPDATE",
            "instance": "test",
            "data": {"status": "read"}
        })
        
        background_tasks = MagicMock(spec=BackgroundTasks)

        result = await evolution_webhook(request, background_tasks)

        assert result["status"] == "ok"
        assert result["event"] == "MESSAGES_UPDATE"

    @pytest.mark.asyncio
    async def test_unknown_event(self):
        """Test unknown event"""
        from api.routes.whatsapp_webhook import evolution_webhook
        from fastapi import BackgroundTasks

        request = MagicMock()
        request.json = AsyncMock(return_value={
            "event": "UNKNOWN_EVENT",
            "instance": "test",
            "data": {}
        })
        
        background_tasks = MagicMock(spec=BackgroundTasks)

        result = await evolution_webhook(request, background_tasks)

        assert result["status"] == "ignored"

    @pytest.mark.asyncio
    async def test_webhook_error(self):
        """Test webhook error handling"""
        from api.routes.whatsapp_webhook import evolution_webhook
        from fastapi import BackgroundTasks

        request = MagicMock()
        request.json = AsyncMock(side_effect=Exception("Parse error"))
        
        background_tasks = MagicMock(spec=BackgroundTasks)

        result = await evolution_webhook(request, background_tasks)

        assert result["status"] == "error"


class TestProcessIncomingMessage:
    """Tests for process_incoming_message function"""

    @pytest.mark.asyncio
    async def test_ignore_own_message(self):
        """Test ignoring own messages"""
        from api.routes.whatsapp_webhook import process_incoming_message

        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": True,
                "id": "MSG123"
            }
        }

        # Should not raise
        await process_incoming_message(data, "test-instance")

    @pytest.mark.asyncio
    async def test_ignore_group_message(self):
        """Test ignoring group messages"""
        from api.routes.whatsapp_webhook import process_incoming_message

        data = {
            "key": {
                "remoteJid": "123456789@g.us",
                "fromMe": False,
                "id": "MSG123"
            }
        }

        # Should not raise
        await process_incoming_message(data, "test-instance")

    @pytest.mark.asyncio
    async def test_process_text_message(self):
        """Test processing text message"""
        from api.routes.whatsapp_webhook import process_incoming_message

        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "MSG123"
            },
            "message": {"conversation": "Olá"},
            "pushName": "João"
        }

        with patch('api.routes.whatsapp_webhook.chatbot.process_message', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {"text": "Resposta", "action": "welcome"}
            
            with patch('api.routes.whatsapp_webhook.send_whatsapp_message', new_callable=AsyncMock):
                with patch('api.routes.whatsapp_webhook.save_interaction', new_callable=AsyncMock):
                    await process_incoming_message(data, "test-instance")

        mock_process.assert_called_once_with(
            phone="5511999999999",
            message="Olá",
            push_name="João"
        )

    @pytest.mark.asyncio
    async def test_process_extended_text_message(self):
        """Test processing extended text message"""
        from api.routes.whatsapp_webhook import process_incoming_message

        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "MSG123"
            },
            "message": {"extendedTextMessage": {"text": "Mensagem longa"}},
            "pushName": "João"
        }

        with patch('api.routes.whatsapp_webhook.chatbot.process_message', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {"text": "Resposta", "action": "welcome"}
            
            with patch('api.routes.whatsapp_webhook.send_whatsapp_message', new_callable=AsyncMock):
                with patch('api.routes.whatsapp_webhook.save_interaction', new_callable=AsyncMock):
                    await process_incoming_message(data, "test-instance")

        mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_image_message(self):
        """Test processing image message"""
        from api.routes.whatsapp_webhook import process_incoming_message

        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "MSG123"
            },
            "message": {"imageMessage": {"caption": "Foto do produto"}},
            "pushName": "João"
        }

        with patch('api.routes.whatsapp_webhook.chatbot.process_message', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {"text": "Resposta", "action": "welcome"}
            
            with patch('api.routes.whatsapp_webhook.send_whatsapp_message', new_callable=AsyncMock):
                with patch('api.routes.whatsapp_webhook.save_interaction', new_callable=AsyncMock):
                    await process_incoming_message(data, "test-instance")

        mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_audio_message(self):
        """Test processing audio message"""
        from api.routes.whatsapp_webhook import process_incoming_message

        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "MSG123"
            },
            "message": {"audioMessage": {}},
            "pushName": "João"
        }

        with patch('api.routes.whatsapp_webhook.chatbot.process_message', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {"text": "Resposta", "action": "welcome"}
            
            with patch('api.routes.whatsapp_webhook.send_whatsapp_message', new_callable=AsyncMock):
                with patch('api.routes.whatsapp_webhook.save_interaction', new_callable=AsyncMock):
                    await process_incoming_message(data, "test-instance")

        mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_no_text_content(self):
        """Test ignoring message without text content"""
        from api.routes.whatsapp_webhook import process_incoming_message

        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "MSG123"
            },
            "message": {},
            "pushName": "João"
        }

        with patch('api.routes.whatsapp_webhook.chatbot.process_message', new_callable=AsyncMock) as mock_process:
            await process_incoming_message(data, "test-instance")

        mock_process.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_message_error(self):
        """Test message processing error handling"""
        from api.routes.whatsapp_webhook import process_incoming_message

        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "MSG123"
            },
            "message": {"conversation": "Olá"},
            "pushName": "João"
        }

        with patch('api.routes.whatsapp_webhook.chatbot.process_message', new_callable=AsyncMock) as mock_process:
            mock_process.side_effect = Exception("Error")
            
            # Should not raise
            await process_incoming_message(data, "test-instance")


class TestSendWhatsAppMessage:
    """Tests for send_whatsapp_message function"""

    @pytest.mark.asyncio
    async def test_send_success(self):
        """Test successful message sending"""
        import httpx
        from api.routes.whatsapp_webhook import send_whatsapp_message

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with patch('api.routes.whatsapp_webhook.cache.increment', new_callable=AsyncMock):
                await send_whatsapp_message("test-instance", "5511999999999", "Olá!")

            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_failure(self):
        """Test failed message sending"""
        from api.routes.whatsapp_webhook import send_whatsapp_message

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Should not raise
            await send_whatsapp_message("test-instance", "5511999999999", "Olá!")

    @pytest.mark.asyncio
    async def test_send_error(self):
        """Test message sending error handling"""
        from api.routes.whatsapp_webhook import send_whatsapp_message

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(side_effect=Exception("Network error"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Should not raise
            await send_whatsapp_message("test-instance", "5511999999999", "Olá!")


class TestSaveInteraction:
    """Tests for save_interaction function"""

    @pytest.mark.asyncio
    async def test_save_interaction_success(self):
        """Test saving interaction"""
        from api.routes.whatsapp_webhook import save_interaction

        with patch('api.routes.whatsapp_webhook.cache.increment', new_callable=AsyncMock):
            with patch('api.routes.whatsapp_webhook.cache.get', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = []
                with patch('api.routes.whatsapp_webhook.cache.set', new_callable=AsyncMock):
                    with patch('api.routes.whatsapp_webhook.cache.sadd', new_callable=AsyncMock):
                        await save_interaction(
                            "5511999999999",
                            "Olá",
                            {"action": "welcome"}
                        )

    @pytest.mark.asyncio
    async def test_save_interaction_with_existing(self):
        """Test saving interaction with existing conversation"""
        from api.routes.whatsapp_webhook import save_interaction

        with patch('api.routes.whatsapp_webhook.cache.increment', new_callable=AsyncMock):
            with patch('api.routes.whatsapp_webhook.cache.get', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = [{"user_message": "Oi", "bot_action": "welcome"}]
                with patch('api.routes.whatsapp_webhook.cache.set', new_callable=AsyncMock):
                    with patch('api.routes.whatsapp_webhook.cache.sadd', new_callable=AsyncMock):
                        await save_interaction(
                            "5511999999999",
                            "Buscar",
                            {"action": "await_query"}
                        )

    @pytest.mark.asyncio
    async def test_save_interaction_error(self):
        """Test interaction saving error handling"""
        from api.routes.whatsapp_webhook import save_interaction

        with patch('api.routes.whatsapp_webhook.cache.increment', new_callable=AsyncMock) as mock_increment:
            mock_increment.side_effect = Exception("Redis error")
            
            # Should not raise
            await save_interaction(
                "5511999999999",
                "Olá",
                {"action": "welcome"}
            )


class TestWebhookStatus:
    """Tests for webhook_status endpoint"""

    @pytest.mark.asyncio
    async def test_status_healthy(self):
        """Test healthy status"""
        from api.routes.whatsapp_webhook import webhook_status

        with patch('api.routes.whatsapp_webhook.cache.get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [
                {"state": "open"},  # connection
                100,  # received
                50    # sent
            ]

            result = await webhook_status()

        assert result["status"] == "healthy"
        assert "today_metrics" in result

    @pytest.mark.asyncio
    async def test_status_error(self):
        """Test status error handling"""
        from api.routes.whatsapp_webhook import webhook_status

        with patch('api.routes.whatsapp_webhook.cache.get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Redis error")

            result = await webhook_status()

        assert result["status"] == "error"


class TestTestChatbot:
    """Tests for test_chatbot endpoint"""

    @pytest.mark.asyncio
    async def test_chatbot_success(self):
        """Test chatbot test endpoint"""
        from api.routes.whatsapp_webhook import test_chatbot

        with patch('api.routes.whatsapp_webhook.chatbot.process_message', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {"text": "Bem-vindo!", "action": "welcome"}

            result = await test_chatbot(
                phone="5511999999999",
                message="oi",
                push_name="Teste"
            )

        assert result["success"] is True
        assert "response" in result

    @pytest.mark.asyncio
    async def test_chatbot_error(self):
        """Test chatbot test endpoint error"""
        from api.routes.whatsapp_webhook import test_chatbot
        from fastapi import HTTPException

        with patch('api.routes.whatsapp_webhook.chatbot.process_message', new_callable=AsyncMock) as mock_process:
            mock_process.side_effect = Exception("Chatbot error")

            with pytest.raises(HTTPException) as exc_info:
                await test_chatbot(
                    phone="5511999999999",
                    message="oi"
                )

            assert exc_info.value.status_code == 500


class TestRouterConfiguration:
    """Tests for router configuration"""

    def test_router_prefix(self):
        """Test router prefix"""
        from api.routes.whatsapp_webhook import router

        assert router.prefix == "/whatsapp-webhook"

    def test_router_tags(self):
        """Test router tags"""
        from api.routes.whatsapp_webhook import router

        assert "WhatsApp Webhook" in router.tags


class TestConstants:
    """Tests for constants configuration"""

    def test_evolution_api_url(self):
        """Test Evolution API URL constant"""
        from api.routes.whatsapp_webhook import EVOLUTION_API_URL

        assert EVOLUTION_API_URL is not None
        assert isinstance(EVOLUTION_API_URL, str)

    def test_evolution_instance(self):
        """Test Evolution instance constant"""
        from api.routes.whatsapp_webhook import EVOLUTION_INSTANCE

        assert EVOLUTION_INSTANCE is not None
        assert isinstance(EVOLUTION_INSTANCE, str)
