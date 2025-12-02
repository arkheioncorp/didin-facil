"""
Tests for api/routes/seller_bot.py
Professional Seller Bot API routes testing
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.seller_bot import (BotConfigRequest, BotStatsResponse,
                                   ConversationResponse, DirectMessageRequest,
                                   WebhookPayload, chatwoot_webhook,
                                   close_conversation, evolution_webhook,
                                   get_bot, get_bot_stats, get_channel_router,
                                   get_conversation, handoff_conversation,
                                   instagram_webhook, list_conversations,
                                   router, send_direct_message)
from fastapi import HTTPException

# ==================== FIXTURES ====================

@pytest.fixture
def mock_bot():
    """Mock ProfessionalSellerBot."""
    bot = MagicMock()
    bot._contexts = {}
    bot.process_message = AsyncMock(return_value=[])
    return bot


@pytest.fixture
def mock_channel_router():
    """Mock ChannelRouter."""
    router = MagicMock()
    return router


@pytest.fixture
def mock_background_tasks():
    """Mock FastAPI BackgroundTasks."""
    tasks = MagicMock()
    return tasks


@pytest.fixture
def chatwoot_payload():
    """Sample Chatwoot webhook payload."""
    return WebhookPayload(
        event="message_created",
        data={"event": "message_created"},
        message={"id": 123, "content": "Hello"},
        conversation={"id": 456},
        sender={"id": 789, "name": "John"}
    )


@pytest.fixture
def evolution_payload():
    """Sample Evolution API webhook payload."""
    return WebhookPayload(
        event="messages.upsert",
        data={},
        key={"remoteJid": "5511999999999@s.whatsapp.net"},
        pushName="Maria",
        instance="didin-bot"
    )


@pytest.fixture
def direct_message_request():
    """Sample direct message request."""
    return DirectMessageRequest(
        channel="webchat",
        sender_id="user-123",
        sender_name="Test User",
        content="Olá, preciso de ajuda!",
        media_url=None
    )


@pytest.fixture
def mock_conversation_context():
    """Mock ConversationContext."""
    ctx = MagicMock()
    ctx.conversation_id = "conv-123"
    ctx.user_id = "user-456"
    ctx.channel.value = "whatsapp"
    ctx.stage.value = "greeting"
    ctx.lead_temperature.value = "warm"
    ctx.lead_score = 50
    ctx.message_count = 5
    ctx.is_active = True
    ctx.last_interaction = datetime.now(timezone.utc)
    ctx.interested_products = ["product-1"]
    ctx.search_history = ["search-1"]
    ctx.user_name = "Test User"
    ctx.intents_detected = ["greeting", "product_inquiry"]
    ctx.metadata = {}
    return ctx


# ==================== BOT SINGLETON TESTS ====================

class TestGetBot:
    """Tests for bot singleton."""

    @patch("api.routes.seller_bot._bot_instance", None)
    @patch("api.routes.seller_bot.create_seller_bot")
    @patch("api.routes.seller_bot.settings")
    def test_get_bot_creates_instance(self, mock_settings, mock_create):
        """Test get_bot creates new instance when None."""
        mock_settings.N8N_API_KEY = None
        mock_bot = MagicMock()
        mock_create.return_value = mock_bot

        result = get_bot()

        mock_create.assert_called_once()
        assert result == mock_bot

    @patch("api.routes.seller_bot._bot_instance")
    def test_get_bot_returns_existing(self, mock_instance):
        """Test get_bot returns existing instance."""
        mock_instance.return_value = MagicMock()
        # When _bot_instance is set, it should be returned


class TestGetChannelRouter:
    """Tests for channel router singleton."""

    @patch("api.routes.seller_bot._channel_router", None)
    @patch("api.routes.seller_bot.ChannelRouter")
    @patch("api.routes.seller_bot.settings")
    def test_get_channel_router_creates_instance(self, mock_settings, mock_router_class):
        """Test get_channel_router creates new instance."""
        mock_settings.CHATWOOT_API_TOKEN = None
        mock_settings.EVOLUTION_API_KEY = None
        mock_router = MagicMock()
        mock_router_class.return_value = mock_router

        result = get_channel_router()

        mock_router_class.assert_called_once()


# ==================== CHATWOOT WEBHOOK TESTS ====================

class TestChatwootWebhook:
    """Tests for Chatwoot webhook endpoint."""

    @pytest.mark.asyncio
    async def test_chatwoot_ignores_non_message_events(
        self, mock_bot, mock_channel_router, mock_background_tasks
    ):
        """Test that non-message events are ignored."""
        payload = WebhookPayload(
            event="conversation_status_changed",
            data={}
        )

        response = await chatwoot_webhook(
            payload=payload,
            background_tasks=mock_background_tasks,
            bot=mock_bot,
            router=mock_channel_router
        )

        assert response["status"] == "ignored"
        assert response["event"] == "conversation_status_changed"

    @pytest.mark.asyncio
    async def test_chatwoot_adapter_not_configured(
        self, mock_bot, mock_channel_router, mock_background_tasks, chatwoot_payload
    ):
        """Test error when Chatwoot adapter not configured."""
        mock_channel_router.get_adapter = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await chatwoot_webhook(
                payload=chatwoot_payload,
                background_tasks=mock_background_tasks,
                bot=mock_bot,
                router=mock_channel_router
            )

        assert exc_info.value.status_code == 500
        assert "não configurado" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_chatwoot_processes_message(
        self, mock_bot, mock_channel_router, mock_background_tasks, chatwoot_payload
    ):
        """Test message processing."""
        mock_adapter = MagicMock()
        mock_message = MagicMock()
        mock_message.id = "msg-123"
        mock_adapter.parse_incoming = AsyncMock(return_value=mock_message)
        mock_channel_router.get_adapter = MagicMock(return_value=mock_adapter)

        response = await chatwoot_webhook(
            payload=chatwoot_payload,
            background_tasks=mock_background_tasks,
            bot=mock_bot,
            router=mock_channel_router
        )

        assert response["status"] == "processing"
        assert response["message_id"] == "msg-123"
        mock_background_tasks.add_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_chatwoot_ignores_non_incoming(
        self, mock_bot, mock_channel_router, mock_background_tasks, chatwoot_payload
    ):
        """Test that outgoing messages are ignored."""
        mock_adapter = MagicMock()
        mock_adapter.parse_incoming = AsyncMock(return_value=None)
        mock_channel_router.get_adapter = MagicMock(return_value=mock_adapter)

        response = await chatwoot_webhook(
            payload=chatwoot_payload,
            background_tasks=mock_background_tasks,
            bot=mock_bot,
            router=mock_channel_router
        )

        assert response["status"] == "ignored"


# ==================== EVOLUTION WEBHOOK TESTS ====================

class TestEvolutionWebhook:
    """Tests for Evolution API webhook endpoint."""

    @pytest.mark.asyncio
    async def test_evolution_ignores_non_message_events(
        self, mock_bot, mock_channel_router, mock_background_tasks
    ):
        """Test that non-message events are ignored."""
        payload = WebhookPayload(event="connection.update", data={})

        response = await evolution_webhook(
            payload=payload,
            background_tasks=mock_background_tasks,
            bot=mock_bot,
            router=mock_channel_router
        )

        assert response["status"] == "ignored"

    @pytest.mark.asyncio
    async def test_evolution_adapter_not_configured(
        self, mock_bot, mock_channel_router, mock_background_tasks, evolution_payload
    ):
        """Test error when Evolution adapter not configured."""
        mock_channel_router.get_adapter = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await evolution_webhook(
                payload=evolution_payload,
                background_tasks=mock_background_tasks,
                bot=mock_bot,
                router=mock_channel_router
            )

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_evolution_processes_message(
        self, mock_bot, mock_channel_router, mock_background_tasks, evolution_payload
    ):
        """Test message processing from Evolution."""
        mock_adapter = MagicMock()
        mock_message = MagicMock()
        mock_message.id = "evo-msg-123"
        mock_adapter.parse_incoming = AsyncMock(return_value=mock_message)
        mock_channel_router.get_adapter = MagicMock(return_value=mock_adapter)

        response = await evolution_webhook(
            payload=evolution_payload,
            background_tasks=mock_background_tasks,
            bot=mock_bot,
            router=mock_channel_router
        )

        assert response["status"] == "processing"
        assert response["message_id"] == "evo-msg-123"


# ==================== INSTAGRAM WEBHOOK TESTS ====================

class TestInstagramWebhook:
    """Tests for Instagram webhook endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.seller_bot.settings")
    async def test_instagram_hub_verification(self, mock_settings):
        """Test Instagram hub challenge verification."""
        mock_settings.INSTAGRAM_VERIFY_TOKEN = "my-verify-token"

        mock_request = MagicMock()
        mock_request.query_params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "my-verify-token",
            "hub.challenge": "12345"
        }

        response = await instagram_webhook(request=mock_request)

        assert response == 12345

    @pytest.mark.asyncio
    @patch("api.routes.seller_bot.settings")
    async def test_instagram_hub_invalid_token(self, mock_settings):
        """Test Instagram hub verification with invalid token."""
        mock_settings.INSTAGRAM_VERIFY_TOKEN = "correct-token"

        mock_request = MagicMock()
        mock_request.query_params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token"
        }

        with pytest.raises(HTTPException) as exc_info:
            await instagram_webhook(request=mock_request)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_instagram_message_received(self):
        """Test Instagram message webhook with valid Instagram payload."""
        mock_request = MagicMock()
        mock_request.query_params = {}
        # Valid Instagram webhook payload structure
        mock_request.json = AsyncMock(return_value={
            "object": "instagram",
            "entry": [
                {
                    "id": "123456789",
                    "time": 1234567890,
                    "messaging": [
                        {
                            "sender": {"id": "987654321"},
                            "recipient": {"id": "123456789"},
                            "timestamp": 1234567890,
                            "message": {
                                "mid": "msg_123",
                                "text": "Hello"
                            }
                        }
                    ]
                }
            ]
        })

        with patch('api.routes.seller_bot.get_bot') as mock_get_bot:
            mock_bot_instance = MagicMock()
            mock_bot_instance.process_message = AsyncMock(return_value=[])
            mock_get_bot.return_value = mock_bot_instance

            response = await instagram_webhook(request=mock_request)

            assert response["status"] == "processed"

    @pytest.mark.asyncio
    async def test_instagram_invalid_payload(self):
        """Test Instagram webhook with invalid payload."""
        mock_request = MagicMock()
        mock_request.query_params = {}
        mock_request.json = AsyncMock(return_value={"entry": []})

        response = await instagram_webhook(request=mock_request)

        # Should be ignored because no "object": "instagram"
        assert response["status"] == "ignored"


# ==================== DIRECT MESSAGE TESTS ====================

class TestSendDirectMessage:
    """Tests for direct message endpoint."""

    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_bot, direct_message_request):
        """Test sending direct message successfully."""
        mock_response = MagicMock()
        mock_response.content = "Olá! Como posso ajudar?"
        mock_response.quick_replies = ["Ver produtos", "Falar com vendedor"]
        mock_response.intent_detected.value = "greeting"
        mock_response.should_handoff = False
        mock_bot.process_message = AsyncMock(return_value=[mock_response])

        response = await send_direct_message(
            request=direct_message_request,
            bot=mock_bot
        )

        assert response["status"] == "success"
        assert len(response["responses"]) == 1
        assert response["responses"][0]["content"] == "Olá! Como posso ajudar?"

    @pytest.mark.asyncio
    async def test_send_message_different_channels(self, mock_bot):
        """Test sending messages to different channels."""
        channels = ["whatsapp", "instagram", "webchat", "tiktok", "telegram"]
        mock_bot.process_message = AsyncMock(return_value=[])

        for channel in channels:
            request = DirectMessageRequest(
                channel=channel,
                sender_id="user-123",
                content="Test"
            )
            response = await send_direct_message(request=request, bot=mock_bot)
            assert response["status"] == "success"

    @pytest.mark.asyncio
    async def test_send_message_with_media(self, mock_bot):
        """Test sending message with media."""
        mock_bot.process_message = AsyncMock(return_value=[])

        request = DirectMessageRequest(
            channel="whatsapp",
            sender_id="user-123",
            content="Check this image",
            media_url="https://example.com/image.jpg"
        )

        response = await send_direct_message(request=request, bot=mock_bot)

        assert response["status"] == "success"
        # Verify message was created with media_url
        call_args = mock_bot.process_message.call_args[0][0]
        assert call_args.media_url == "https://example.com/image.jpg"

    @pytest.mark.asyncio
    async def test_send_message_error(self, mock_bot, direct_message_request):
        """Test error handling in send_direct_message."""
        mock_bot.process_message = AsyncMock(side_effect=Exception("Bot error"))

        with pytest.raises(HTTPException) as exc_info:
            await send_direct_message(
                request=direct_message_request,
                bot=mock_bot
            )

        assert exc_info.value.status_code == 500


# ==================== CONVERSATION MANAGEMENT TESTS ====================

class TestListConversations:
    """Tests for list conversations endpoint."""

    @pytest.mark.asyncio
    async def test_list_active_conversations(self, mock_bot, mock_conversation_context):
        """Test listing active conversations."""
        mock_bot._contexts = {"key1": mock_conversation_context}

        response = await list_conversations(
            active_only=True,
            bot=mock_bot
        )

        assert response["total"] == 1
        assert len(response["items"]) == 1
        assert response["items"][0]["conversation_id"] == "conv-123"

    @pytest.mark.asyncio
    async def test_list_conversations_with_filters(self, mock_bot, mock_conversation_context):
        """Test listing conversations with filters."""
        mock_bot._contexts = {"key1": mock_conversation_context}

        response = await list_conversations(
            active_only=True,
            channel="whatsapp",
            stage="greeting",
            lead_temperature="warm",
            bot=mock_bot
        )

        assert response["total"] == 1

    @pytest.mark.asyncio
    async def test_list_conversations_filter_excludes(self, mock_bot, mock_conversation_context):
        """Test filter excludes non-matching conversations."""
        mock_bot._contexts = {"key1": mock_conversation_context}

        response = await list_conversations(
            active_only=True,
            channel="instagram",  # Different channel
            bot=mock_bot
        )

        assert response["total"] == 0

    @pytest.mark.asyncio
    async def test_list_conversations_pagination(self, mock_bot):
        """Test conversation pagination."""
        # Create multiple contexts
        contexts = {}
        for i in range(10):
            ctx = MagicMock()
            ctx.conversation_id = f"conv-{i}"
            ctx.user_id = f"user-{i}"
            ctx.channel.value = "whatsapp"
            ctx.stage.value = "greeting"
            ctx.lead_temperature.value = "warm"
            ctx.lead_score = 50
            ctx.message_count = 5
            ctx.is_active = True
            ctx.last_interaction = datetime.now(timezone.utc)
            ctx.user_name = f"User {i}"
            contexts[f"key{i}"] = ctx

        mock_bot._contexts = contexts

        response = await list_conversations(
            limit=5,
            offset=0,
            bot=mock_bot
        )

        assert len(response["items"]) == 5
        assert response["total"] == 10


class TestGetConversation:
    """Tests for get single conversation endpoint."""

    @pytest.mark.asyncio
    async def test_get_conversation_success(self, mock_bot, mock_conversation_context):
        """Test getting conversation details."""
        mock_bot._contexts = {"key1": mock_conversation_context}

        response = await get_conversation(
            conversation_id="conv-123",
            bot=mock_bot
        )

        assert response.conversation_id == "conv-123"
        assert response.user_id == "user-456"
        assert response.channel == "whatsapp"

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, mock_bot):
        """Test getting non-existent conversation."""
        mock_bot._contexts = {}

        with pytest.raises(HTTPException) as exc_info:
            await get_conversation(
                conversation_id="non-existent",
                bot=mock_bot
            )

        assert exc_info.value.status_code == 404


class TestHandoffConversation:
    """Tests for conversation handoff endpoint."""

    @pytest.mark.asyncio
    async def test_handoff_success(self, mock_bot, mock_channel_router, mock_conversation_context):
        """Test successful handoff to human."""
        mock_bot._contexts = {"key1": mock_conversation_context}
        mock_channel_router.get_adapter = MagicMock(return_value=None)

        response = await handoff_conversation(
            conversation_id="conv-123",
            reason="complex_issue",
            bot=mock_bot,
            router=mock_channel_router
        )

        assert response["status"] == "success"
        assert response["reason"] == "complex_issue"

    @pytest.mark.asyncio
    async def test_handoff_with_chatwoot(self, mock_bot, mock_channel_router, mock_conversation_context):
        """Test handoff with Chatwoot integration."""
        mock_conversation_context.metadata = {"conversation_id": "chatwoot-123"}
        mock_bot._contexts = {"key1": mock_conversation_context}

        mock_adapter = MagicMock()
        mock_adapter.handoff_to_human = AsyncMock()
        mock_channel_router.get_adapter = MagicMock(return_value=mock_adapter)

        response = await handoff_conversation(
            conversation_id="conv-123",
            reason="complex",
            bot=mock_bot,
            router=mock_channel_router
        )

        assert response["status"] == "success"

    @pytest.mark.asyncio
    async def test_handoff_not_found(self, mock_bot, mock_channel_router):
        """Test handoff for non-existent conversation."""
        mock_bot._contexts = {}

        with pytest.raises(HTTPException) as exc_info:
            await handoff_conversation(
                conversation_id="non-existent",
                bot=mock_bot,
                router=mock_channel_router
            )

        assert exc_info.value.status_code == 404


class TestCloseConversation:
    """Tests for close conversation endpoint."""

    @pytest.mark.asyncio
    async def test_close_conversation_success(self, mock_bot, mock_conversation_context):
        """Test closing conversation."""
        mock_bot._contexts = {"key1": mock_conversation_context}

        response = await close_conversation(
            conversation_id="conv-123",
            bot=mock_bot
        )

        assert response["status"] == "closed"
        assert mock_conversation_context.is_active is False

    @pytest.mark.asyncio
    async def test_close_conversation_not_found(self, mock_bot):
        """Test closing non-existent conversation."""
        mock_bot._contexts = {}

        with pytest.raises(HTTPException) as exc_info:
            await close_conversation(
                conversation_id="non-existent",
                bot=mock_bot
            )

        assert exc_info.value.status_code == 404


# ==================== ANALYTICS TESTS ====================

class TestGetBotStats:
    """Tests for bot statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_stats_empty(self, mock_bot):
        """Test stats with no conversations."""
        mock_bot._contexts = {}

        response = await get_bot_stats(bot=mock_bot)

        assert response.total_conversations == 0
        assert response.active_conversations == 0

    @pytest.mark.asyncio
    async def test_get_stats_with_conversations(self, mock_bot, mock_conversation_context):
        """Test stats with conversations."""
        mock_bot._contexts = {"key1": mock_conversation_context}

        response = await get_bot_stats(bot=mock_bot)

        assert response.total_conversations == 1
        assert response.active_conversations == 1
        assert "warm" in response.lead_distribution

    @pytest.mark.asyncio
    async def test_get_stats_top_intents(self, mock_bot, mock_conversation_context):
        """Test stats includes top intents."""
        mock_bot._contexts = {"key1": mock_conversation_context}

        response = await get_bot_stats(bot=mock_bot)

        assert len(response.top_intents) > 0


# ==================== MODEL TESTS ====================

class TestModels:
    """Tests for Pydantic models."""

    def test_webhook_payload(self):
        """Test WebhookPayload model."""
        payload = WebhookPayload(
            event="message_created",
            data={"key": "value"},
            message={"content": "Hello"}
        )
        assert payload.event == "message_created"
        assert payload.message["content"] == "Hello"

    def test_direct_message_request(self):
        """Test DirectMessageRequest model."""
        request = DirectMessageRequest(
            channel="whatsapp",
            sender_id="user-123",
            content="Hello"
        )
        assert request.channel == "whatsapp"
        assert request.sender_name is None

    def test_bot_config_request(self):
        """Test BotConfigRequest model."""
        config = BotConfigRequest(
            greeting_message="Olá! Bem-vindo!",
            handoff_threshold=10,
            enable_ai_responses=True
        )
        assert config.greeting_message == "Olá! Bem-vindo!"
        assert config.handoff_threshold == 10


# ==================== ROUTER TESTS ====================

class TestRouter:
    """Tests for router configuration."""

    def test_router_has_webhook_endpoints(self):
        """Verify router has webhook endpoints."""
        routes = [r.path for r in router.routes]
        
        assert "/seller-bot/webhook/chatwoot" in routes
        assert "/seller-bot/webhook/evolution" in routes
        assert "/seller-bot/webhook/instagram" in routes

    def test_router_has_conversation_endpoints(self):
        """Verify router has conversation endpoints."""
        routes = [r.path for r in router.routes]
        
        assert "/seller-bot/conversations" in routes
        assert "/seller-bot/conversations/{conversation_id}" in routes
        assert "/seller-bot/conversations/{conversation_id}/handoff" in routes

    def test_router_has_stats_endpoint(self):
        """Verify router has stats endpoint."""
        routes = [r.path for r in router.routes]
        
        assert "/seller-bot/stats" in routes

    def test_router_prefix(self):
        """Verify router has correct prefix."""
        assert router.prefix == "/seller-bot"
