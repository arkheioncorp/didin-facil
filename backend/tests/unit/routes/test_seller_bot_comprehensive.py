"""
Comprehensive tests for Seller Bot routes
Target: api/routes/seller_bot.py (currently 71.8% coverage)
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestSellerBotSchemas:
    """Test request/response schemas"""
    
    def test_webhook_payload_defaults(self):
        """Test WebhookPayload with defaults"""
        from api.routes.seller_bot import WebhookPayload
        
        payload = WebhookPayload()
        
        assert payload.event is None
        assert payload.data == {}
        assert payload.message is None
    
    def test_webhook_payload_with_data(self):
        """Test WebhookPayload with data"""
        from api.routes.seller_bot import WebhookPayload
        
        payload = WebhookPayload(
            event="message_created",
            data={"key": "value"},
            message={"text": "Hello"},
            conversation={"id": "123"},
            sender={"name": "Test"}
        )
        
        assert payload.event == "message_created"
        assert payload.data["key"] == "value"
        assert payload.message["text"] == "Hello"
    
    def test_webhook_payload_evolution_fields(self):
        """Test WebhookPayload with Evolution API fields"""
        from api.routes.seller_bot import WebhookPayload
        
        payload = WebhookPayload(
            event="messages.upsert",
            key={"id": "msg123"},
            pushName="User Name",
            instance="bot-instance"
        )
        
        assert payload.key["id"] == "msg123"
        assert payload.pushName == "User Name"
        assert payload.instance == "bot-instance"
    
    def test_direct_message_request_defaults(self):
        """Test DirectMessageRequest with defaults"""
        from api.routes.seller_bot import DirectMessageRequest
        
        request = DirectMessageRequest(
            sender_id="user123",
            content="Hello"
        )
        
        assert request.channel == "webchat"
        assert request.sender_name is None
        assert request.media_url is None
    
    def test_direct_message_request_full(self):
        """Test DirectMessageRequest with all fields"""
        from api.routes.seller_bot import DirectMessageRequest
        
        request = DirectMessageRequest(
            channel="whatsapp",
            sender_id="user123",
            sender_name="John Doe",
            content="Check this image",
            media_url="https://example.com/image.jpg"
        )
        
        assert request.channel == "whatsapp"
        assert request.sender_name == "John Doe"
        assert request.media_url == "https://example.com/image.jpg"
    
    def test_conversation_response(self):
        """Test ConversationResponse schema"""
        from api.routes.seller_bot import ConversationResponse
        
        response = ConversationResponse(
            conversation_id="conv123",
            user_id="user123",
            channel="whatsapp",
            stage="greeting",
            lead_temperature="warm",
            lead_score=50,
            message_count=10,
            is_active=True,
            last_interaction=datetime.now(),
            interested_products=["prod1", "prod2"],
            search_history=["query1"]
        )
        
        assert response.conversation_id == "conv123"
        assert response.lead_score == 50
        assert len(response.interested_products) == 2
    
    def test_bot_stats_response(self):
        """Test BotStatsResponse schema"""
        from api.routes.seller_bot import BotStatsResponse
        
        response = BotStatsResponse(
            total_conversations=100,
            active_conversations=25,
            messages_today=500,
            handoffs_today=10,
            avg_response_time_ms=250.5,
            top_intents=[{"intent": "buy", "count": 50}],
            lead_distribution={"hot": 20, "warm": 50, "cold": 30}
        )
        
        assert response.total_conversations == 100
        assert response.avg_response_time_ms == 250.5
        assert response.lead_distribution["hot"] == 20
    
    def test_bot_config_request_defaults(self):
        """Test BotConfigRequest with defaults"""
        from api.routes.seller_bot import BotConfigRequest
        
        config = BotConfigRequest()
        
        assert config.greeting_message is None
        assert config.fallback_message is None
        assert config.handoff_threshold is None
        assert config.enable_ai_responses is None
        assert config.typing_delay_ms is None
    
    def test_bot_config_request_full(self):
        """Test BotConfigRequest with all fields"""
        from api.routes.seller_bot import BotConfigRequest
        
        config = BotConfigRequest(
            greeting_message="Hello! How can I help?",
            fallback_message="Sorry, I didn't understand",
            handoff_threshold=5,
            enable_ai_responses=True,
            typing_delay_ms=1000
        )
        
        assert config.greeting_message == "Hello! How can I help?"
        assert config.handoff_threshold == 5
        assert config.typing_delay_ms == 1000


class TestGetBot:
    """Test bot singleton getter"""
    
    def test_get_bot_creates_instance(self):
        """Test get_bot creates new instance"""
        from api.routes import seller_bot

        # Reset singleton
        seller_bot._bot_instance = None
        
        with patch('api.routes.seller_bot.create_seller_bot') as mock_create:
            mock_bot = MagicMock()
            mock_create.return_value = mock_bot
            
            with patch('api.routes.seller_bot.settings') as mock_settings:
                mock_settings.N8N_API_KEY = None
                
                result = seller_bot.get_bot()
                
                mock_create.assert_called_once()
        
        # Reset after test
        seller_bot._bot_instance = None
    
    def test_get_bot_returns_existing(self):
        """Test get_bot returns existing instance"""
        from api.routes import seller_bot
        
        mock_bot = MagicMock()
        seller_bot._bot_instance = mock_bot
        
        result = seller_bot.get_bot()
        
        assert result is mock_bot
        
        # Reset after test
        seller_bot._bot_instance = None


class TestGetChannelRouter:
    """Test channel router getter"""
    
    def test_get_channel_router_creates_instance(self):
        """Test get_channel_router creates new instance"""
        from api.routes import seller_bot

        # Reset singleton
        seller_bot._channel_router = None
        
        with patch('api.routes.seller_bot.ChannelRouter') as mock_router_class:
            mock_router = MagicMock()
            mock_router_class.return_value = mock_router
            
            with patch('api.routes.seller_bot.settings') as mock_settings:
                mock_settings.CHATWOOT_ACCESS_TOKEN = None
                mock_settings.EVOLUTION_API_KEY = None
                
                result = seller_bot.get_channel_router()
                
                assert result is mock_router
        
        # Reset after test
        seller_bot._channel_router = None
    
    def test_get_channel_router_with_chatwoot(self):
        """Test get_channel_router configures Chatwoot"""
        from api.routes import seller_bot
        
        seller_bot._channel_router = None
        
        with patch('api.routes.seller_bot.ChannelRouter') as mock_router_class:
            mock_router = MagicMock()
            mock_router_class.return_value = mock_router
            
            with patch('api.routes.seller_bot.create_chatwoot_adapter') as mock_create:
                mock_adapter = MagicMock()
                mock_create.return_value = mock_adapter
                
                with patch('api.routes.seller_bot.settings') as mock_settings:
                    mock_settings.CHATWOOT_ACCESS_TOKEN = "test_token"
                    mock_settings.CHATWOOT_API_URL = "https://chatwoot.test"
                    mock_settings.CHATWOOT_ACCOUNT_ID = "123"
                    mock_settings.EVOLUTION_API_KEY = None
                    
                    result = seller_bot.get_channel_router()
                    
                    mock_create.assert_called_once()
                    assert mock_router.register_adapter.called
        
        seller_bot._channel_router = None
    
    def test_get_channel_router_with_evolution(self):
        """Test get_channel_router configures Evolution"""
        from api.routes import seller_bot
        
        seller_bot._channel_router = None
        
        with patch('api.routes.seller_bot.ChannelRouter') as mock_router_class:
            mock_router = MagicMock()
            mock_router_class.return_value = mock_router
            
            with patch('api.routes.seller_bot.create_evolution_adapter') as mock_create:
                mock_adapter = MagicMock()
                mock_create.return_value = mock_adapter
                
                with patch('api.routes.seller_bot.settings') as mock_settings:
                    mock_settings.CHATWOOT_ACCESS_TOKEN = None
                    mock_settings.EVOLUTION_API_KEY = "test_key"
                    mock_settings.EVOLUTION_API_URL = "https://evolution.test"
                    
                    result = seller_bot.get_channel_router()
                    
                    mock_create.assert_called_once()
        
        seller_bot._channel_router = None


class TestChatwootWebhook:
    """Test Chatwoot webhook endpoint"""
    
    @pytest.mark.asyncio
    async def test_chatwoot_webhook_ignored_event(self):
        """Test Chatwoot webhook ignores non-message events"""
        from api.routes.seller_bot import WebhookPayload, chatwoot_webhook
        
        payload = WebhookPayload(event="conversation_status_changed")
        mock_bot = MagicMock()
        mock_router = MagicMock()
        mock_tasks = MagicMock()
        
        result = await chatwoot_webhook(
            payload=payload,
            background_tasks=mock_tasks,
            bot=mock_bot,
            router=mock_router
        )
        
        assert result["status"] == "ignored"
        assert result["event"] == "conversation_status_changed"
    
    @pytest.mark.asyncio
    async def test_chatwoot_webhook_no_adapter(self):
        """Test Chatwoot webhook fails without adapter"""
        from api.routes.seller_bot import WebhookPayload, chatwoot_webhook
        from fastapi import HTTPException
        
        payload = WebhookPayload(event="message_created")
        mock_bot = MagicMock()
        mock_router = MagicMock()
        mock_router.get_adapter.return_value = None
        mock_tasks = MagicMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await chatwoot_webhook(
                payload=payload,
                background_tasks=mock_tasks,
                bot=mock_bot,
                router=mock_router
            )
        
        assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_chatwoot_webhook_message_not_incoming(self):
        """Test Chatwoot webhook ignores outgoing messages"""
        from api.routes.seller_bot import WebhookPayload, chatwoot_webhook
        
        payload = WebhookPayload(event="message_created")
        mock_bot = MagicMock()
        mock_router = MagicMock()
        mock_adapter = AsyncMock()
        mock_adapter.parse_incoming = AsyncMock(return_value=None)
        mock_router.get_adapter.return_value = mock_adapter
        mock_tasks = MagicMock()
        
        result = await chatwoot_webhook(
            payload=payload,
            background_tasks=mock_tasks,
            bot=mock_bot,
            router=mock_router
        )
        
        assert result["status"] == "ignored"
        assert result["reason"] == "not_incoming_message"
    
    @pytest.mark.asyncio
    async def test_chatwoot_webhook_success(self):
        """Test Chatwoot webhook processes message"""
        from api.routes.seller_bot import WebhookPayload, chatwoot_webhook
        
        payload = WebhookPayload(event="message_created")
        mock_bot = MagicMock()
        mock_router = MagicMock()
        mock_adapter = AsyncMock()
        mock_message = MagicMock()
        mock_message.id = "msg123"
        mock_adapter.parse_incoming = AsyncMock(return_value=mock_message)
        mock_router.get_adapter.return_value = mock_adapter
        mock_tasks = MagicMock()
        
        result = await chatwoot_webhook(
            payload=payload,
            background_tasks=mock_tasks,
            bot=mock_bot,
            router=mock_router
        )
        
        assert result["status"] == "processing"
        assert result["message_id"] == "msg123"
        mock_tasks.add_task.assert_called_once()


class TestEvolutionWebhook:
    """Test Evolution webhook endpoint"""
    
    @pytest.mark.asyncio
    async def test_evolution_webhook_ignored_event(self):
        """Test Evolution webhook ignores non-message events"""
        from api.routes.seller_bot import WebhookPayload, evolution_webhook
        
        payload = WebhookPayload(event="connection.update")
        mock_bot = MagicMock()
        mock_router = MagicMock()
        mock_tasks = MagicMock()
        
        result = await evolution_webhook(
            payload=payload,
            background_tasks=mock_tasks,
            bot=mock_bot,
            router=mock_router
        )
        
        assert result["status"] == "ignored"
    
    @pytest.mark.asyncio
    async def test_evolution_webhook_no_adapter(self):
        """Test Evolution webhook fails without adapter"""
        from api.routes.seller_bot import WebhookPayload, evolution_webhook
        from fastapi import HTTPException
        
        payload = WebhookPayload(event="messages.upsert")
        mock_bot = MagicMock()
        mock_router = MagicMock()
        mock_router.get_adapter.return_value = None
        mock_tasks = MagicMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await evolution_webhook(
                payload=payload,
                background_tasks=mock_tasks,
                bot=mock_bot,
                router=mock_router
            )
        
        assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_evolution_webhook_success(self):
        """Test Evolution webhook processes message"""
        from api.routes.seller_bot import WebhookPayload, evolution_webhook
        
        payload = WebhookPayload(event="messages.upsert")
        mock_bot = MagicMock()
        mock_router = MagicMock()
        mock_adapter = AsyncMock()
        mock_message = MagicMock()
        mock_message.id = "msg456"
        mock_adapter.parse_incoming = AsyncMock(return_value=mock_message)
        mock_router.get_adapter.return_value = mock_adapter
        mock_tasks = MagicMock()
        
        result = await evolution_webhook(
            payload=payload,
            background_tasks=mock_tasks,
            bot=mock_bot,
            router=mock_router
        )
        
        assert result["status"] == "processing"
        assert result["message_id"] == "msg456"


class TestInstagramWebhook:
    """Test Instagram webhook endpoint"""
    
    @pytest.mark.asyncio
    async def test_instagram_webhook_hub_verification(self):
        """Test Instagram webhook hub verification"""
        from api.routes.seller_bot import instagram_webhook
        
        mock_request = MagicMock()
        mock_request.query_params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "default_token",
            "hub.challenge": "12345"
        }
        
        with patch('api.routes.seller_bot.settings') as mock_settings:
            mock_settings.INSTAGRAM_VERIFY_TOKEN = "default_token"
            
            result = await instagram_webhook(mock_request)
            
            assert result == 12345
    
    @pytest.mark.asyncio
    async def test_instagram_webhook_invalid_token(self):
        """Test Instagram webhook with invalid verify token"""
        from api.routes.seller_bot import instagram_webhook
        from fastapi import HTTPException
        
        mock_request = MagicMock()
        mock_request.query_params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "12345"
        }
        
        with patch('api.routes.seller_bot.settings') as mock_settings:
            mock_settings.INSTAGRAM_VERIFY_TOKEN = "correct_token"
            
            with pytest.raises(HTTPException) as exc_info:
                await instagram_webhook(mock_request)
            
            assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    async def test_instagram_webhook_not_instagram(self):
        """Test Instagram webhook ignores non-Instagram payloads"""
        from api.routes.seller_bot import instagram_webhook
        
        mock_request = MagicMock()
        mock_request.query_params = {}
        mock_request.json = AsyncMock(return_value={"object": "facebook"})
        
        result = await instagram_webhook(mock_request)
        
        assert result["status"] == "ignored"
        assert result["reason"] == "not_instagram"
    
    @pytest.mark.asyncio
    async def test_instagram_webhook_no_entries(self):
        """Test Instagram webhook with no entries"""
        from api.routes.seller_bot import instagram_webhook
        
        mock_request = MagicMock()
        mock_request.query_params = {}
        mock_request.json = AsyncMock(return_value={
            "object": "instagram",
            "entry": []
        })
        
        result = await instagram_webhook(mock_request)
        
        assert result["status"] == "ignored"
        assert result["reason"] == "no_entries"
    
    @pytest.mark.asyncio
    async def test_instagram_webhook_processes_message(self):
        """Test Instagram webhook processes message"""
        from api.routes.seller_bot import instagram_webhook
        
        mock_request = MagicMock()
        mock_request.query_params = {}
        mock_request.json = AsyncMock(return_value={
            "object": "instagram",
            "entry": [{
                "messaging": [{
                    "sender": {"id": "sender123"},
                    "message": {"text": "Hello bot"}
                }]
            }]
        })
        
        with patch('api.routes.seller_bot.get_bot') as mock_get_bot:
            mock_bot = MagicMock()
            mock_bot.process_message = AsyncMock(return_value=[])
            mock_get_bot.return_value = mock_bot
            
            result = await instagram_webhook(mock_request)
            
            mock_bot.process_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_instagram_webhook_ignores_echo(self):
        """Test Instagram webhook ignores echo messages"""
        from api.routes.seller_bot import instagram_webhook
        
        mock_request = MagicMock()
        mock_request.query_params = {}
        mock_request.json = AsyncMock(return_value={
            "object": "instagram",
            "entry": [{
                "messaging": [{
                    "sender": {"id": "sender123"},
                    "message": {"text": "Echo", "is_echo": True}
                }]
            }]
        })
        
        with patch('api.routes.seller_bot.get_bot') as mock_get_bot:
            mock_bot = MagicMock()
            mock_bot.process_message = AsyncMock(return_value=[])
            mock_get_bot.return_value = mock_bot
            
            result = await instagram_webhook(mock_request)
            
            # Process should not be called for echo messages
            mock_bot.process_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_instagram_webhook_processes_postback(self):
        """Test Instagram webhook processes postback"""
        from api.routes.seller_bot import instagram_webhook
        
        mock_request = MagicMock()
        mock_request.query_params = {}
        mock_request.json = AsyncMock(return_value={
            "object": "instagram",
            "entry": [{
                "messaging": [{
                    "sender": {"id": "sender123"},
                    "postback": {"payload": "BUTTON_CLICKED"}
                }]
            }]
        })
        
        with patch('api.routes.seller_bot.get_bot') as mock_get_bot:
            mock_bot = MagicMock()
            mock_bot.process_message = AsyncMock(return_value=[])
            mock_get_bot.return_value = mock_bot
            
            result = await instagram_webhook(mock_request)
            
            mock_bot.process_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_instagram_webhook_handles_attachment(self):
        """Test Instagram webhook handles attachments"""
        from api.routes.seller_bot import instagram_webhook
        
        mock_request = MagicMock()
        mock_request.query_params = {}
        mock_request.json = AsyncMock(return_value={
            "object": "instagram",
            "entry": [{
                "messaging": [{
                    "sender": {"id": "sender123"},
                    "message": {
                        "text": "",
                        "attachments": [{
                            "type": "image",
                            "payload": {"url": "https://example.com/image.jpg"}
                        }]
                    }
                }]
            }]
        })
        
        with patch('api.routes.seller_bot.get_bot') as mock_get_bot:
            mock_bot = MagicMock()
            mock_bot.process_message = AsyncMock(return_value=[])
            mock_get_bot.return_value = mock_bot
            
            result = await instagram_webhook(mock_request)
            
            # Should process with media_url extracted
            mock_bot.process_message.assert_called_once()
            call_args = mock_bot.process_message.call_args[0][0]
            assert call_args.media_url == "https://example.com/image.jpg"
            assert call_args.media_url == "https://example.com/image.jpg"
