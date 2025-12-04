"""
Comprehensive tests for status_webhooks.py routes.
Target: status_webhooks.py 39% -> 95%+
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# ============================================
# SCHEMA TESTS
# ============================================

class TestWebhookSchemas:
    """Test Pydantic schemas for webhooks"""
    
    def test_webhook_config_schema(self):
        """Test WebhookConfig schema with all fields"""
        from api.routes.status_webhooks import WebhookConfig
        
        config = WebhookConfig(
            id="test123",
            url="https://example.com/webhook",
            events=["post.completed", "post.failed"],
            secret="secret123",
            active=True
        )
        
        assert config.id == "test123"
        assert str(config.url) == "https://example.com/webhook"
        assert "post.completed" in config.events
        assert config.secret == "secret123"
        assert config.active is True
        assert config.failure_count == 0
    
    def test_webhook_config_defaults(self):
        """Test WebhookConfig default values"""
        from api.routes.status_webhooks import WebhookConfig
        
        config = WebhookConfig(
            id="test",
            url="https://example.com/webhook"
        )
        
        assert config.active is True
        assert config.failure_count == 0
        assert config.last_triggered is None
        assert "post.completed" in config.events
        assert "post.failed" in config.events
    
    def test_webhook_event_schema(self):
        """Test WebhookEvent schema"""
        from api.routes.status_webhooks import WebhookEvent
        
        event = WebhookEvent(
            event_type="post.completed",
            timestamp=datetime.now(timezone.utc),
            data={"post_id": "123", "platform": "youtube"}
        )
        
        assert event.event_type == "post.completed"
        assert event.data["post_id"] == "123"
        assert event.data["platform"] == "youtube"
    
    def test_webhook_create_request_schema(self):
        """Test WebhookCreateRequest schema"""
        from api.routes.status_webhooks import WebhookCreateRequest
        
        request = WebhookCreateRequest(
            url="https://example.com/webhook",
            events=["post.scheduled"],
            secret="mysecret"
        )
        
        assert str(request.url) == "https://example.com/webhook"
        assert request.events == ["post.scheduled"]
        assert request.secret == "mysecret"
    
    def test_webhook_create_request_defaults(self):
        """Test WebhookCreateRequest default events"""
        from api.routes.status_webhooks import WebhookCreateRequest
        
        request = WebhookCreateRequest(
            url="https://example.com/webhook"
        )
        
        assert "post.completed" in request.events
        assert "post.failed" in request.events
        assert request.secret is None
    
    def test_webhook_update_request_schema(self):
        """Test WebhookUpdateRequest schema"""
        from api.routes.status_webhooks import WebhookUpdateRequest
        
        request = WebhookUpdateRequest(
            url="https://new.example.com/webhook",
            events=["post.processing"],
            secret="newsecret",
            active=False
        )
        
        assert str(request.url) == "https://new.example.com/webhook"
        assert request.events == ["post.processing"]
        assert request.secret == "newsecret"
        assert request.active is False
    
    def test_webhook_update_request_partial(self):
        """Test WebhookUpdateRequest with partial data"""
        from api.routes.status_webhooks import WebhookUpdateRequest
        
        request = WebhookUpdateRequest(active=False)
        
        assert request.url is None
        assert request.events is None
        assert request.secret is None
        assert request.active is False


# ============================================
# LIST WEBHOOKS TESTS
# ============================================

class TestListWebhooks:
    """Test list_webhooks endpoint"""
    
    @pytest.mark.asyncio
    async def test_list_webhooks_empty(self):
        """Test listing webhooks when none exist"""
        from api.routes.status_webhooks import list_webhooks
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=[])
            
            result = await list_webhooks()
            
            assert result == []
            mock_redis.keys.assert_called_once_with("webhook:config:*")
    
    @pytest.mark.asyncio
    async def test_list_webhooks_with_data(self):
        """Test listing webhooks with existing data"""
        from api.routes.status_webhooks import list_webhooks
        
        webhook_data = {
            "id": "abc123",
            "url": "https://example.com/webhook",
            "events": '["post.completed"]',
            "secret": "secret",
            "active": "true",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "failure_count": "0"
        }
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=["webhook:config:abc123"])
            mock_redis.hgetall = AsyncMock(return_value=webhook_data)
            
            result = await list_webhooks()
            
            assert len(result) == 1
            assert result[0].id == "abc123"
            assert str(result[0].url) == "https://example.com/webhook"
            assert result[0].active is True
    
    @pytest.mark.asyncio
    async def test_list_webhooks_with_last_triggered(self):
        """Test listing webhooks with last_triggered field"""
        from api.routes.status_webhooks import list_webhooks
        
        last_triggered = datetime.now(timezone.utc).isoformat()
        webhook_data = {
            "id": "abc123",
            "url": "https://example.com/webhook",
            "events": '["post.completed"]',
            "active": "true",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_triggered": last_triggered,
            "failure_count": "2"
        }
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=["webhook:config:abc123"])
            mock_redis.hgetall = AsyncMock(return_value=webhook_data)
            
            result = await list_webhooks()
            
            assert result[0].last_triggered is not None
            assert result[0].failure_count == 2
    
    @pytest.mark.asyncio
    async def test_list_webhooks_inactive(self):
        """Test listing inactive webhooks"""
        from api.routes.status_webhooks import list_webhooks
        
        webhook_data = {
            "id": "abc123",
            "url": "https://example.com/webhook",
            "events": '["post.completed"]',
            "active": "false",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "failure_count": "0"
        }
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=["webhook:config:abc123"])
            mock_redis.hgetall = AsyncMock(return_value=webhook_data)
            
            result = await list_webhooks()
            
            assert result[0].active is False


# ============================================
# CREATE WEBHOOK TESTS
# ============================================

class TestCreateWebhook:
    """Test create_webhook endpoint"""
    
    @pytest.mark.asyncio
    async def test_create_webhook_success(self):
        """Test creating a webhook successfully"""
        from api.routes.status_webhooks import (WebhookCreateRequest,
                                                create_webhook)
        
        request = WebhookCreateRequest(
            url="https://example.com/webhook",
            events=["post.completed", "post.failed"],
            secret="mysecret"
        )
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.hset = AsyncMock()
            
            result = await create_webhook(request)
            
            assert result.url is not None
            assert result.events == ["post.completed", "post.failed"]
            assert result.secret == "mysecret"
            assert result.active is True
            mock_redis.hset.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_webhook_without_secret(self):
        """Test creating a webhook without secret"""
        from api.routes.status_webhooks import (WebhookCreateRequest,
                                                create_webhook)
        
        request = WebhookCreateRequest(
            url="https://example.com/webhook"
        )
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.hset = AsyncMock()
            
            result = await create_webhook(request)
            
            assert result.secret is None
            assert "post.completed" in result.events
    
    @pytest.mark.asyncio
    async def test_create_webhook_custom_events(self):
        """Test creating a webhook with custom events"""
        from api.routes.status_webhooks import (WebhookCreateRequest,
                                                create_webhook)
        
        request = WebhookCreateRequest(
            url="https://example.com/webhook",
            events=["post.scheduled", "quota.warning", "session.expired"]
        )
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.hset = AsyncMock()
            
            result = await create_webhook(request)
            
            assert "post.scheduled" in result.events
            assert "quota.warning" in result.events
            assert "session.expired" in result.events


# ============================================
# GET WEBHOOK TESTS
# ============================================

class TestGetWebhook:
    """Test get_webhook endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_webhook_success(self):
        """Test getting a webhook successfully"""
        from api.routes.status_webhooks import get_webhook
        
        webhook_data = {
            "id": "abc123",
            "url": "https://example.com/webhook",
            "events": '["post.completed"]',
            "secret": "secret",
            "active": "true",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "failure_count": "0"
        }
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.hgetall = AsyncMock(return_value=webhook_data)
            
            result = await get_webhook("abc123")
            
            assert result.id == "abc123"
            assert str(result.url) == "https://example.com/webhook"
    
    @pytest.mark.asyncio
    async def test_get_webhook_not_found(self):
        """Test getting a non-existent webhook"""
        from api.routes.status_webhooks import get_webhook
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.hgetall = AsyncMock(return_value={})
            
            with pytest.raises(HTTPException) as exc:
                await get_webhook("nonexistent")
            
            assert exc.value.status_code == 404
            assert "not found" in exc.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_get_webhook_with_null_secret(self):
        """Test getting a webhook with null secret"""
        from api.routes.status_webhooks import get_webhook
        
        webhook_data = {
            "id": "abc123",
            "url": "https://example.com/webhook",
            "events": '["post.completed"]',
            "secret": "",
            "active": "true",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "failure_count": "0"
        }
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.hgetall = AsyncMock(return_value=webhook_data)
            
            result = await get_webhook("abc123")
            
            assert result.secret is None


# ============================================
# UPDATE WEBHOOK TESTS
# ============================================

class TestUpdateWebhook:
    """Test update_webhook endpoint"""
    
    @pytest.mark.asyncio
    async def test_update_webhook_url(self):
        """Test updating webhook URL"""
        from api.routes.status_webhooks import (WebhookUpdateRequest,
                                                update_webhook)
        
        request = WebhookUpdateRequest(url="https://new.example.com/webhook")
        
        existing_data = {
            "id": "abc123",
            "url": "https://old.example.com/webhook",
            "events": '["post.completed"]',
            "active": "true",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "failure_count": "0"
        }
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.exists = AsyncMock(return_value=True)
            mock_redis.hset = AsyncMock()
            mock_redis.hgetall = AsyncMock(return_value=existing_data)
            
            result = await update_webhook("abc123", request)
            
            mock_redis.hset.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_webhook_events(self):
        """Test updating webhook events"""
        from api.routes.status_webhooks import (WebhookUpdateRequest,
                                                update_webhook)
        
        request = WebhookUpdateRequest(events=["post.scheduled", "post.processing"])
        
        existing_data = {
            "id": "abc123",
            "url": "https://example.com/webhook",
            "events": '["post.completed"]',
            "active": "true",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "failure_count": "0"
        }
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.exists = AsyncMock(return_value=True)
            mock_redis.hset = AsyncMock()
            mock_redis.hgetall = AsyncMock(return_value=existing_data)
            
            await update_webhook("abc123", request)
            
            mock_redis.hset.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_webhook_active_status(self):
        """Test updating webhook active status"""
        from api.routes.status_webhooks import (WebhookUpdateRequest,
                                                update_webhook)
        
        request = WebhookUpdateRequest(active=False)
        
        existing_data = {
            "id": "abc123",
            "url": "https://example.com/webhook",
            "events": '["post.completed"]',
            "active": "true",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "failure_count": "0"
        }
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.exists = AsyncMock(return_value=True)
            mock_redis.hset = AsyncMock()
            mock_redis.hgetall = AsyncMock(return_value=existing_data)
            
            await update_webhook("abc123", request)
            
            mock_redis.hset.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_webhook_not_found(self):
        """Test updating a non-existent webhook"""
        from api.routes.status_webhooks import (WebhookUpdateRequest,
                                                update_webhook)
        
        request = WebhookUpdateRequest(active=False)
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.exists = AsyncMock(return_value=False)
            
            with pytest.raises(HTTPException) as exc:
                await update_webhook("nonexistent", request)
            
            assert exc.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_webhook_secret(self):
        """Test updating webhook secret"""
        from api.routes.status_webhooks import (WebhookUpdateRequest,
                                                update_webhook)
        
        request = WebhookUpdateRequest(secret="newsecret")
        
        existing_data = {
            "id": "abc123",
            "url": "https://example.com/webhook",
            "events": '["post.completed"]',
            "active": "true",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "failure_count": "0"
        }
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.exists = AsyncMock(return_value=True)
            mock_redis.hset = AsyncMock()
            mock_redis.hgetall = AsyncMock(return_value=existing_data)
            
            await update_webhook("abc123", request)
            
            # Verify secret was updated
            call_args = mock_redis.hset.call_args
            assert "secret" in call_args[1]["mapping"]


# ============================================
# DELETE WEBHOOK TESTS
# ============================================

class TestDeleteWebhook:
    """Test delete_webhook endpoint"""
    
    @pytest.mark.asyncio
    async def test_delete_webhook_success(self):
        """Test deleting a webhook successfully"""
        from api.routes.status_webhooks import delete_webhook
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.delete = AsyncMock(return_value=1)
            
            result = await delete_webhook("abc123")
            
            assert result["success"] is True
            assert result["deleted"] == "abc123"
    
    @pytest.mark.asyncio
    async def test_delete_webhook_not_found(self):
        """Test deleting a non-existent webhook"""
        from api.routes.status_webhooks import delete_webhook
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.delete = AsyncMock(return_value=0)
            
            with pytest.raises(HTTPException) as exc:
                await delete_webhook("nonexistent")
            
            assert exc.value.status_code == 404


# ============================================
# TEST WEBHOOK TESTS
# ============================================

class TestTestWebhook:
    """Test test_webhook endpoint"""
    
    @pytest.mark.asyncio
    async def test_test_webhook_success(self):
        """Test sending a test webhook"""
        from api.routes.status_webhooks import WebhookConfig, test_webhook
        from fastapi import BackgroundTasks
        
        webhook_data = {
            "id": "abc123",
            "url": "https://example.com/webhook",
            "events": '["post.completed"]',
            "active": "true",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "failure_count": "0"
        }
        
        background_tasks = BackgroundTasks()
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.hgetall = AsyncMock(return_value=webhook_data)
            
            result = await test_webhook("abc123", background_tasks)
            
            assert result["success"] is True
            assert "queued" in result["message"].lower()


# ============================================
# WEBHOOK HISTORY TESTS
# ============================================

class TestWebhookHistory:
    """Test get_webhook_history endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_webhook_history_success(self):
        """Test getting webhook history"""
        from api.routes.status_webhooks import get_webhook_history
        
        history_entries = [
            json.dumps({"timestamp": "2024-01-01T00:00:00", "success": True, "status_code": 200}),
            json.dumps({"timestamp": "2024-01-01T00:01:00", "success": False, "status_code": 500})
        ]
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.lrange = AsyncMock(return_value=history_entries)
            
            result = await get_webhook_history("abc123")
            
            assert len(result) == 2
            assert result[0]["success"] is True
            assert result[1]["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_webhook_history_empty(self):
        """Test getting empty webhook history"""
        from api.routes.status_webhooks import get_webhook_history
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.lrange = AsyncMock(return_value=[])
            
            result = await get_webhook_history("abc123")
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_webhook_history_with_limit(self):
        """Test getting webhook history with custom limit"""
        from api.routes.status_webhooks import get_webhook_history
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.lrange = AsyncMock(return_value=[])
            
            await get_webhook_history("abc123", limit=10)
            
            mock_redis.lrange.assert_called_with("webhook:history:abc123", 0, 9)


# ============================================
# SEND WEBHOOK TESTS
# ============================================

class TestSendWebhook:
    """Test send_webhook function"""
    
    @pytest.mark.asyncio
    async def test_send_webhook_success(self):
        """Test sending a webhook successfully"""
        import httpx
        from api.routes.status_webhooks import (WebhookConfig, WebhookEvent,
                                                send_webhook)
        
        webhook = WebhookConfig(
            id="abc123",
            url="https://example.com/webhook",
            events=["post.completed"]
        )
        
        event = WebhookEvent(
            event_type="post.completed",
            timestamp=datetime.now(timezone.utc),
            data={"post_id": "123"}
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis, \
             patch("httpx.AsyncClient") as mock_client:
            mock_redis.hset = AsyncMock()
            mock_redis.hincrby = AsyncMock()
            mock_redis.lpush = AsyncMock()
            mock_redis.ltrim = AsyncMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            await send_webhook(webhook, event)
            
            mock_client_instance.post.assert_called_once()
            mock_redis.hset.assert_called()
    
    @pytest.mark.asyncio
    async def test_send_webhook_with_secret(self):
        """Test sending a webhook with HMAC signature"""
        from api.routes.status_webhooks import (WebhookConfig, WebhookEvent,
                                                send_webhook)
        
        webhook = WebhookConfig(
            id="abc123",
            url="https://example.com/webhook",
            events=["post.completed"],
            secret="mysecret"
        )
        
        event = WebhookEvent(
            event_type="post.completed",
            timestamp=datetime.now(timezone.utc),
            data={"post_id": "123"}
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis, \
             patch("httpx.AsyncClient") as mock_client:
            mock_redis.hset = AsyncMock()
            mock_redis.hincrby = AsyncMock()
            mock_redis.lpush = AsyncMock()
            mock_redis.ltrim = AsyncMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            await send_webhook(webhook, event)
            
            # Verify signature header was included
            call_args = mock_client_instance.post.call_args
            headers = call_args[1]["headers"]
            assert "X-TikTrend-Signature" in headers
            assert headers["X-TikTrend-Signature"].startswith("sha256=")
    
    @pytest.mark.asyncio
    async def test_send_webhook_failure(self):
        """Test sending a webhook that fails"""
        from api.routes.status_webhooks import (WebhookConfig, WebhookEvent,
                                                send_webhook)
        
        webhook = WebhookConfig(
            id="abc123",
            url="https://example.com/webhook",
            events=["post.completed"]
        )
        
        event = WebhookEvent(
            event_type="post.completed",
            timestamp=datetime.now(timezone.utc),
            data={"post_id": "123"}
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis, \
             patch("httpx.AsyncClient") as mock_client:
            mock_redis.hset = AsyncMock()
            mock_redis.hincrby = AsyncMock()
            mock_redis.lpush = AsyncMock()
            mock_redis.ltrim = AsyncMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            await send_webhook(webhook, event)
            
            # Verify failure count was incremented
            mock_redis.hincrby.assert_called()
    
    @pytest.mark.asyncio
    async def test_send_webhook_timeout(self):
        """Test sending a webhook that times out"""
        import httpx
        from api.routes.status_webhooks import (WebhookConfig, WebhookEvent,
                                                send_webhook)
        
        webhook = WebhookConfig(
            id="abc123",
            url="https://example.com/webhook",
            events=["post.completed"]
        )
        
        event = WebhookEvent(
            event_type="post.completed",
            timestamp=datetime.now(timezone.utc),
            data={"post_id": "123"}
        )
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis, \
             patch("httpx.AsyncClient") as mock_client:
            mock_redis.hset = AsyncMock()
            mock_redis.hincrby = AsyncMock()
            mock_redis.lpush = AsyncMock()
            mock_redis.ltrim = AsyncMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            await send_webhook(webhook, event)
            
            # Should handle timeout gracefully
            mock_redis.hincrby.assert_called()
    
    @pytest.mark.asyncio
    async def test_send_webhook_request_error(self):
        """Test sending a webhook with request error"""
        import httpx
        from api.routes.status_webhooks import (WebhookConfig, WebhookEvent,
                                                send_webhook)
        
        webhook = WebhookConfig(
            id="abc123",
            url="https://example.com/webhook",
            events=["post.completed"]
        )
        
        event = WebhookEvent(
            event_type="post.completed",
            timestamp=datetime.now(timezone.utc),
            data={"post_id": "123"}
        )
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis, \
             patch("httpx.AsyncClient") as mock_client:
            mock_redis.hset = AsyncMock()
            mock_redis.hincrby = AsyncMock()
            mock_redis.lpush = AsyncMock()
            mock_redis.ltrim = AsyncMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(
                side_effect=httpx.RequestError("Connection failed")
            )
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            await send_webhook(webhook, event)
            
            # Should handle request error gracefully
            mock_redis.hincrby.assert_called()


# ============================================
# TRIGGER EVENT TESTS
# ============================================

class TestTriggerEvent:
    """Test trigger_event function"""
    
    @pytest.mark.asyncio
    async def test_trigger_event_to_active_webhooks(self):
        """Test triggering an event to active webhooks"""
        from api.routes.status_webhooks import WebhookConfig, trigger_event
        
        webhook_data = {
            "id": "abc123",
            "url": "https://example.com/webhook",
            "events": '["post.completed"]',
            "active": "true",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "failure_count": "0"
        }
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis, \
             patch("api.routes.status_webhooks.send_webhook") as mock_send:
            mock_redis.keys = AsyncMock(return_value=["webhook:config:abc123"])
            mock_redis.hgetall = AsyncMock(return_value=webhook_data)
            
            await trigger_event("post.completed", {"post_id": "123"})
            
            # Should create task to send webhook
    
    @pytest.mark.asyncio
    async def test_trigger_event_skips_inactive_webhooks(self):
        """Test that trigger_event skips inactive webhooks"""
        from api.routes.status_webhooks import trigger_event
        
        webhook_data = {
            "id": "abc123",
            "url": "https://example.com/webhook",
            "events": '["post.completed"]',
            "active": "false",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "failure_count": "0"
        }
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=["webhook:config:abc123"])
            mock_redis.hgetall = AsyncMock(return_value=webhook_data)
            
            await trigger_event("post.completed", {"post_id": "123"})
            
            # Should not create task for inactive webhook
    
    @pytest.mark.asyncio
    async def test_trigger_event_wildcard_subscription(self):
        """Test triggering an event with wildcard subscription"""
        from api.routes.status_webhooks import trigger_event
        
        webhook_data = {
            "id": "abc123",
            "url": "https://example.com/webhook",
            "events": '["*"]',
            "active": "true",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "failure_count": "0"
        }
        
        with patch("api.routes.status_webhooks.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=["webhook:config:abc123"])
            mock_redis.hgetall = AsyncMock(return_value=webhook_data)
            
            await trigger_event("any.event", {"data": "test"})
            
            # Should create task for wildcard webhook


# ============================================
# EVENT TYPES DOCUMENTATION TESTS
# ============================================

class TestListEventTypes:
    """Test list_event_types endpoint"""
    
    @pytest.mark.asyncio
    async def test_list_event_types_success(self):
        """Test listing all available event types"""
        from api.routes.status_webhooks import list_event_types
        
        result = await list_event_types()
        
        assert "events" in result
        assert len(result["events"]) > 0
        
        event_types = [e["type"] for e in result["events"]]
        assert "post.scheduled" in event_types
        assert "post.processing" in event_types
        assert "post.completed" in event_types
        assert "post.failed" in event_types
        assert "quota.warning" in event_types
        assert "session.expired" in event_types
        assert "challenge.detected" in event_types
    
    @pytest.mark.asyncio
    async def test_list_event_types_structure(self):
        """Test event types have proper structure"""
        from api.routes.status_webhooks import list_event_types
        
        result = await list_event_types()
        
        for event in result["events"]:
            assert "type" in event
            assert "description" in event
            assert "payload" in event


# ============================================
# ROUTER TESTS
# ============================================

class TestStatusWebhooksRouter:
    """Test router configuration"""
    
    def test_router_exists(self):
        """Test that router is defined"""
        from api.routes.status_webhooks import router
        
        assert router is not None
    
    def test_router_has_routes(self):
        """Test that router has expected routes"""
        from api.routes.status_webhooks import router
        
        routes = [r.path for r in router.routes]
        
        assert "/webhooks" in routes
        assert "/webhooks/{webhook_id}" in routes
        assert "/webhooks/{webhook_id}/test" in routes
        assert "/webhooks/{webhook_id}/history" in routes
        assert "/webhooks/events/types" in routes
