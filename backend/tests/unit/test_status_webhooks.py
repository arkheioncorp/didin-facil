"""
Tests for Status Webhooks
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime


class TestWebhookConfig:
    """Tests for WebhookConfig model"""

    def test_webhook_config_creation(self):
        """Should create a valid webhook config"""
        from api.routes.status_webhooks import WebhookConfig
        
        config = WebhookConfig(
            id="test123",
            url="https://example.com/webhook",
            events=["post.completed", "post.failed"]
        )
        
        assert config.id == "test123"
        assert str(config.url) == "https://example.com/webhook"
        assert len(config.events) == 2
        assert config.active is True
        assert config.failure_count == 0

    def test_webhook_config_with_secret(self):
        """Should accept optional secret"""
        from api.routes.status_webhooks import WebhookConfig
        
        config = WebhookConfig(
            id="test123",
            url="https://example.com/webhook",
            events=["post.completed"],
            secret="my-secret-key"
        )
        
        assert config.secret == "my-secret-key"


class TestWebhookEvent:
    """Tests for WebhookEvent model"""

    def test_webhook_event_creation(self):
        """Should create a valid webhook event"""
        from api.routes.status_webhooks import WebhookEvent
        
        event = WebhookEvent(
            event_type="post.completed",
            timestamp=datetime.utcnow(),
            data={"post_id": "123", "platform": "youtube"}
        )
        
        assert event.event_type == "post.completed"
        assert "post_id" in event.data

    def test_webhook_event_serialization(self):
        """Should serialize to JSON correctly"""
        from api.routes.status_webhooks import WebhookEvent
        
        event = WebhookEvent(
            event_type="post.failed",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            data={"error": "Rate limit exceeded"}
        )
        
        payload = event.model_dump(mode="json")
        
        assert payload["event_type"] == "post.failed"
        assert "error" in payload["data"]


class TestMetricsCollector:
    """Tests for MetricsCollector used in webhook delivery"""

    def test_hmac_signature_generation(self):
        """Should generate correct HMAC signature"""
        import hmac
        import hashlib
        
        secret = "my-secret"
        payload = b'{"event_type": "test"}'
        
        signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        assert len(signature) == 64  # SHA256 hex digest length
        
        # Verify signature is reproducible
        signature2 = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        assert signature == signature2


class TestWebhookDelivery:
    """Tests for webhook delivery functionality"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        with patch("api.routes.status_webhooks.redis_client") as mock:
            mock.keys = AsyncMock(return_value=[])
            mock.hgetall = AsyncMock(return_value={})
            mock.hset = AsyncMock(return_value=True)
            mock.lpush = AsyncMock(return_value=1)
            mock.ltrim = AsyncMock(return_value=True)
            mock.hincrby = AsyncMock(return_value=1)
            yield mock

    @pytest.mark.asyncio
    async def test_send_webhook_success(self, mock_redis):
        """Should send webhook and record success"""
        from api.routes.status_webhooks import send_webhook, WebhookConfig, WebhookEvent
        
        webhook = WebhookConfig(
            id="test123",
            url="https://example.com/webhook",
            events=["post.completed"]
        )
        
        event = WebhookEvent(
            event_type="post.completed",
            timestamp=datetime.utcnow(),
            data={"post_id": "123"}
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            await send_webhook(webhook, event)
            
            # Verify Redis history was updated
            mock_redis.lpush.assert_called()
            mock_redis.hset.assert_called()

    @pytest.mark.asyncio
    async def test_send_webhook_failure(self, mock_redis):
        """Should record failure and increment counter"""
        from api.routes.status_webhooks import send_webhook, WebhookConfig, WebhookEvent
        
        webhook = WebhookConfig(
            id="test123",
            url="https://example.com/webhook",
            events=["post.completed"]
        )
        
        event = WebhookEvent(
            event_type="post.completed",
            timestamp=datetime.utcnow(),
            data={"post_id": "123"}
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            await send_webhook(webhook, event)
            
            # Verify failure was recorded
            mock_redis.hincrby.assert_called()

    @pytest.mark.asyncio
    async def test_send_webhook_timeout(self, mock_redis):
        """Should handle timeout gracefully"""
        from api.routes.status_webhooks import send_webhook, WebhookConfig, WebhookEvent
        import httpx
        
        webhook = WebhookConfig(
            id="test123",
            url="https://example.com/webhook",
            events=["post.completed"]
        )
        
        event = WebhookEvent(
            event_type="post.completed",
            timestamp=datetime.utcnow(),
            data={"post_id": "123"}
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )
            
            # Should not raise exception
            await send_webhook(webhook, event)
            
            # Verify failure was recorded
            mock_redis.hincrby.assert_called()


class TestTriggerEvent:
    """Tests for event triggering"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        with patch("api.routes.status_webhooks.redis_client") as mock:
            mock.keys = AsyncMock(return_value=[])
            mock.hgetall = AsyncMock(return_value={})
            yield mock

    @pytest.mark.asyncio
    async def test_trigger_event_no_webhooks(self, mock_redis):
        """Should handle case with no webhooks configured"""
        from api.routes.status_webhooks import trigger_event
        
        # Should not raise any errors
        await trigger_event("post.completed", {"post_id": "123"})

    @pytest.mark.asyncio
    async def test_trigger_event_inactive_webhook(self, mock_redis):
        """Should skip inactive webhooks"""
        from api.routes.status_webhooks import trigger_event
        
        mock_redis.keys.return_value = ["webhook:config:abc123"]
        mock_redis.hgetall.return_value = {
            "id": "abc123",
            "url": "https://example.com/webhook",
            "events": '["post.completed"]',
            "active": "false",  # Inactive
            "created_at": "2024-01-01T00:00:00",
            "failure_count": "0"
        }
        
        with patch("api.routes.status_webhooks.send_webhook") as mock_send:
            await trigger_event("post.completed", {"post_id": "123"})
            
            # Should not be called for inactive webhooks
            mock_send.assert_not_called()


class TestListWebhooks:
    """Tests for list webhooks function"""

    @pytest.mark.asyncio
    async def test_list_webhooks_empty(self):
        """Should return empty list when no webhooks"""
        from api.routes.status_webhooks import list_webhooks
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=[])
            
            webhooks = await list_webhooks()
            
            assert webhooks == []

    @pytest.mark.asyncio
    async def test_list_webhooks_with_data(self):
        """Should return parsed webhooks"""
        from api.routes.status_webhooks import list_webhooks
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=["webhook:config:abc123"])
            mock_redis.hgetall = AsyncMock(return_value={
                "id": "abc123",
                "url": "https://example.com/webhook",
                "events": '["post.completed"]',
                "active": "true",
                "created_at": "2024-01-01T00:00:00",
                "failure_count": "0"
            })
            
            webhooks = await list_webhooks()
            
            assert len(webhooks) == 1
            assert webhooks[0].id == "abc123"


class TestCreateWebhook:
    """Tests for create webhook function"""

    @pytest.mark.asyncio
    async def test_create_webhook(self):
        """Should create webhook in Redis"""
        from api.routes.status_webhooks import create_webhook, WebhookCreateRequest
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.hset = AsyncMock(return_value=True)
            
            request = WebhookCreateRequest(
                url="https://example.com/webhook",
                events=["post.completed"]
            )
            
            webhook = await create_webhook(request)
            
            # HttpUrl normaliza a URL (remove trailing slash)
            assert str(webhook.url) == "https://example.com/webhook"
            assert webhook.active is True
            mock_redis.hset.assert_called_once()


class TestGetWebhook:
    """Tests for get webhook function"""

    @pytest.mark.asyncio
    async def test_get_webhook_found(self):
        """Should return webhook when found"""
        from api.routes.status_webhooks import get_webhook
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.hgetall = AsyncMock(return_value={
                "id": "abc123",
                "url": "https://example.com/webhook",
                "events": '["post.completed"]',
                "active": "true",
                "created_at": "2024-01-01T00:00:00",
                "failure_count": "0"
            })
            
            webhook = await get_webhook("abc123")
            
            assert webhook.id == "abc123"

    @pytest.mark.asyncio
    async def test_get_webhook_not_found(self):
        """Should raise 404 when not found"""
        from api.routes.status_webhooks import get_webhook
        from fastapi import HTTPException
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.hgetall = AsyncMock(return_value={})
            
            with pytest.raises(HTTPException) as exc:
                await get_webhook("nonexistent")
            
            assert exc.value.status_code == 404

