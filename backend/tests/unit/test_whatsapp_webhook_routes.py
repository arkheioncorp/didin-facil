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
