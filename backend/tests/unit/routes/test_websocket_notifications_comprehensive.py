"""
Comprehensive tests for websocket_notifications.py
Tests for WebSocket connection manager and notifications.
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# ============================================
# NOTIFICATION TYPE TESTS
# ============================================

class TestNotificationType:
    """Tests for NotificationType constants."""

    def test_post_notification_types(self):
        from api.routes.websocket_notifications import NotificationType

        assert NotificationType.POST_PUBLISHED == "post_published"
        assert NotificationType.POST_FAILED == "post_failed"
        assert NotificationType.POST_SCHEDULED == "post_scheduled"

    def test_account_notification_types(self):
        from api.routes.websocket_notifications import NotificationType

        assert NotificationType.ACCOUNT_CONNECTED == "account_connected"
        assert NotificationType.ACCOUNT_DISCONNECTED == "account_disconnected"
        assert NotificationType.ACCOUNT_EXPIRED == "account_expired"

    def test_bot_notification_types(self):
        from api.routes.websocket_notifications import NotificationType

        assert NotificationType.BOT_TASK_STARTED == "bot_task_started"
        assert NotificationType.BOT_TASK_COMPLETED == "bot_task_completed"
        assert NotificationType.BOT_TASK_FAILED == "bot_task_failed"
        assert NotificationType.BOT_TASK_PROGRESS == "bot_task_progress"
        assert NotificationType.BOT_STATS_UPDATE == "bot_stats_update"
        assert NotificationType.BOT_SCREENSHOT == "bot_screenshot"
        assert NotificationType.BOT_WORKER_STARTED == "bot_worker_started"
        assert NotificationType.BOT_WORKER_STOPPED == "bot_worker_stopped"

    def test_other_notification_types(self):
        from api.routes.websocket_notifications import NotificationType

        assert NotificationType.CHALLENGE_REQUIRED == "challenge_required"
        assert NotificationType.QUOTA_WARNING == "quota_warning"
        assert NotificationType.ERROR == "error"
        assert NotificationType.INFO == "info"


# ============================================
# WEBSOCKET NOTIFICATION SCHEMA TESTS
# ============================================

class TestWebSocketNotificationSchema:
    """Tests for WebSocketNotification schema."""

    def test_full_notification(self):
        from api.routes.websocket_notifications import WebSocketNotification

        notif = WebSocketNotification(
            id="abc123",
            type="post_published",
            platform="instagram",
            title="Post Published",
            message="Your post was published successfully",
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={"post_id": "123"},
            read=False
        )

        assert notif.id == "abc123"
        assert notif.type == "post_published"
        assert notif.platform == "instagram"
        assert notif.read is False

    def test_minimal_notification(self):
        from api.routes.websocket_notifications import WebSocketNotification

        notif = WebSocketNotification(
            id="xyz789",
            type="info",
            title="Info",
            message="General info",
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        assert notif.platform is None
        assert notif.data is None
        assert notif.read is False

    def test_notification_with_data(self):
        from api.routes.websocket_notifications import WebSocketNotification

        notif = WebSocketNotification(
            id="test",
            type="error",
            title="Error",
            message="An error occurred",
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={"error_code": 500, "details": "Internal error"}
        )

        assert notif.data["error_code"] == 500


# ============================================
# CONNECTION MANAGER TESTS
# ============================================

class TestConnectionManager:
    """Tests for ConnectionManager class."""

    @pytest.fixture
    def manager(self):
        from api.routes.websocket_notifications import ConnectionManager
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect_authenticated_user(self, manager, mock_websocket):
        await manager.connect(mock_websocket, user_id="user123")

        mock_websocket.accept.assert_called_once()
        assert "user123" in manager.active_connections
        assert mock_websocket in manager.active_connections["user123"]

    @pytest.mark.asyncio
    async def test_connect_anonymous_user(self, manager, mock_websocket):
        await manager.connect(mock_websocket, user_id=None)

        mock_websocket.accept.assert_called_once()
        assert mock_websocket in manager.anonymous_connections

    @pytest.mark.asyncio
    async def test_connect_multiple_same_user(self, manager):
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect(ws1, user_id="user123")
        await manager.connect(ws2, user_id="user123")

        assert len(manager.active_connections["user123"]) == 2

    def test_disconnect_authenticated_user(self, manager, mock_websocket):
        manager.active_connections["user123"] = {mock_websocket}

        manager.disconnect(mock_websocket, user_id="user123")

        assert "user123" not in manager.active_connections

    def test_disconnect_anonymous_user(self, manager, mock_websocket):
        manager.anonymous_connections.add(mock_websocket)

        manager.disconnect(mock_websocket, user_id=None)

        assert mock_websocket not in manager.anonymous_connections

    def test_disconnect_one_of_multiple(self, manager):
        ws1 = MagicMock()
        ws2 = MagicMock()
        manager.active_connections["user123"] = {ws1, ws2}

        manager.disconnect(ws1, user_id="user123")

        assert "user123" in manager.active_connections
        assert ws2 in manager.active_connections["user123"]
        assert ws1 not in manager.active_connections["user123"]

    def test_subscribe_to_platform(self, manager):
        manager.subscribe_to_platform("user123", "instagram")

        assert "instagram" in manager.platform_subscriptions["user123"]

    def test_subscribe_to_multiple_platforms(self, manager):
        manager.subscribe_to_platform("user123", "instagram")
        manager.subscribe_to_platform("user123", "youtube")
        manager.subscribe_to_platform("user123", "tiktok")

        assert len(manager.platform_subscriptions["user123"]) == 3

    def test_unsubscribe_from_platform(self, manager):
        manager.platform_subscriptions["user123"] = {"instagram", "youtube"}

        manager.unsubscribe_from_platform("user123", "instagram")

        assert "instagram" not in manager.platform_subscriptions["user123"]
        assert "youtube" in manager.platform_subscriptions["user123"]

    def test_unsubscribe_nonexistent_user(self, manager):
        # Should not raise
        manager.unsubscribe_from_platform("nonexistent", "instagram")

    @pytest.mark.asyncio
    async def test_send_to_user(self, manager, mock_websocket):
        manager.active_connections["user123"] = {mock_websocket}

        await manager.send_to_user("user123", {"message": "test"})

        mock_websocket.send_json.assert_called_once_with({"message": "test"})

    @pytest.mark.asyncio
    async def test_send_to_user_no_connections(self, manager):
        # Should not raise
        await manager.send_to_user("nonexistent", {"message": "test"})

    @pytest.mark.asyncio
    async def test_send_to_user_handles_dead_connection(self, manager):
        ws1 = AsyncMock()
        ws1.send_json = AsyncMock(side_effect=Exception("Connection closed"))
        ws2 = AsyncMock()
        
        manager.active_connections["user123"] = {ws1, ws2}

        await manager.send_to_user("user123", {"message": "test"})

        # ws1 should be removed, ws2 should receive message
        ws2.send_json.assert_called_once()
        assert ws1 not in manager.active_connections["user123"]

    @pytest.mark.asyncio
    async def test_broadcast_no_filter(self, manager):
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        manager.active_connections["user1"] = {ws1}
        manager.active_connections["user2"] = {ws2}

        await manager.broadcast({"message": "broadcast"})

        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_with_platform_filter(self, manager):
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        manager.active_connections["user1"] = {ws1}
        manager.active_connections["user2"] = {ws2}
        manager.platform_subscriptions["user1"] = {"instagram"}
        manager.platform_subscriptions["user2"] = {"youtube"}

        await manager.broadcast({"message": "broadcast"}, platform="instagram")

        ws1.send_json.assert_called_once()
        ws2.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_all_subscription(self, manager):
        ws = AsyncMock()
        manager.active_connections["user1"] = {ws}
        manager.platform_subscriptions["user1"] = {"all"}

        await manager.broadcast({"message": "broadcast"}, platform="any_platform")

        ws.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_to_anonymous(self, manager):
        ws = AsyncMock()
        manager.anonymous_connections.add(ws)

        await manager.broadcast({"message": "broadcast"})

        ws.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_handles_dead_connection(self, manager):
        ws = AsyncMock()
        ws.send_json = AsyncMock(side_effect=Exception("Dead"))
        manager.anonymous_connections.add(ws)

        await manager.broadcast({"message": "test"})

        assert ws not in manager.anonymous_connections

    def test_get_connection_count_empty(self, manager):
        assert manager.get_connection_count() == 0

    def test_get_connection_count_authenticated(self, manager):
        ws1 = MagicMock()
        ws2 = MagicMock()
        manager.active_connections["user1"] = {ws1}
        manager.active_connections["user2"] = {ws2}

        assert manager.get_connection_count() == 2

    def test_get_connection_count_anonymous(self, manager):
        ws = MagicMock()
        manager.anonymous_connections.add(ws)

        assert manager.get_connection_count() == 1

    def test_get_connection_count_mixed(self, manager):
        ws1 = MagicMock()
        ws2 = MagicMock()
        ws3 = MagicMock()
        manager.active_connections["user1"] = {ws1, ws2}
        manager.anonymous_connections.add(ws3)

        assert manager.get_connection_count() == 3

    def test_disconnect_cleans_subscriptions(self, manager, mock_websocket):
        manager.active_connections["user123"] = {mock_websocket}
        manager.platform_subscriptions["user123"] = {"instagram"}

        manager.disconnect(mock_websocket, user_id="user123")

        assert "user123" not in manager.platform_subscriptions


# ============================================
# HELPER FUNCTION TESTS
# ============================================

class TestCreateNotification:
    """Tests for create_notification helper."""

    def test_create_basic_notification(self):
        from api.routes.websocket_notifications import create_notification

        notif = create_notification(
            notification_type="info",
            title="Test Title",
            message="Test message"
        )

        assert notif["event"] == "notification"
        assert notif["data"]["type"] == "info"
        assert notif["data"]["title"] == "Test Title"
        assert notif["data"]["message"] == "Test message"
        assert notif["data"]["read"] is False

    def test_create_notification_with_platform(self):
        from api.routes.websocket_notifications import create_notification

        notif = create_notification(
            notification_type="post_published",
            title="Published",
            message="Your post is live",
            platform="instagram"
        )

        assert notif["data"]["platform"] == "instagram"

    def test_create_notification_with_data(self):
        from api.routes.websocket_notifications import create_notification

        notif = create_notification(
            notification_type="error",
            title="Error",
            message="An error occurred",
            data={"error_code": 500}
        )

        assert notif["data"]["data"]["error_code"] == 500

    def test_create_notification_has_id(self):
        from api.routes.websocket_notifications import create_notification

        notif = create_notification(
            notification_type="info",
            title="Test",
            message="Test"
        )

        assert "id" in notif["data"]
        assert len(notif["data"]["id"]) > 0

    def test_create_notification_has_timestamp(self):
        from api.routes.websocket_notifications import create_notification

        notif = create_notification(
            notification_type="info",
            title="Test",
            message="Test"
        )

        assert "timestamp" in notif
        assert "timestamp" in notif["data"]


class TestPublishNotification:
    """Tests for publish_notification helper."""

    @pytest.mark.asyncio
    @patch("api.routes.websocket_notifications.manager")
    @patch("api.routes.websocket_notifications.get_redis")
    async def test_publish_to_specific_user(self, mock_get_redis, mock_manager):
        from api.routes.websocket_notifications import publish_notification

        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_manager.send_to_user = AsyncMock()

        await publish_notification(
            notification_type="info",
            title="Test",
            message="Test message",
            user_id="user123"
        )

        mock_manager.send_to_user.assert_called_once()
        call_args = mock_manager.send_to_user.call_args
        assert call_args[0][0] == "user123"

    @pytest.mark.asyncio
    @patch("api.routes.websocket_notifications.manager")
    @patch("api.routes.websocket_notifications.get_redis")
    async def test_publish_broadcast(self, mock_get_redis, mock_manager):
        from api.routes.websocket_notifications import publish_notification

        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_manager.broadcast = AsyncMock()

        await publish_notification(
            notification_type="info",
            title="Broadcast",
            message="Broadcast message"
        )

        mock_manager.broadcast.assert_called_once()

    @pytest.mark.asyncio
    @patch("api.routes.websocket_notifications.manager")
    @patch("api.routes.websocket_notifications.get_redis")
    async def test_publish_stores_in_redis(self, mock_get_redis, mock_manager):
        from api.routes.websocket_notifications import publish_notification

        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_manager.send_to_user = AsyncMock()

        await publish_notification(
            notification_type="info",
            title="Test",
            message="Test",
            user_id="user123"
        )

        mock_redis.lpush.assert_called()
        mock_redis.ltrim.assert_called()
        mock_redis.expire.assert_called()

    @pytest.mark.asyncio
    @patch("api.routes.websocket_notifications.manager")
    @patch("api.routes.websocket_notifications.get_redis")
    async def test_publish_handles_redis_error(self, mock_get_redis, mock_manager):
        from api.routes.websocket_notifications import publish_notification

        mock_redis = AsyncMock()
        mock_redis.lpush = AsyncMock(side_effect=Exception("Redis error"))
        mock_get_redis.return_value = mock_redis
        mock_manager.send_to_user = AsyncMock()

        # Should not raise
        await publish_notification(
            notification_type="info",
            title="Test",
            message="Test",
            user_id="user123"
        )

        mock_manager.send_to_user.assert_called_once()

    @pytest.mark.asyncio
    @patch("api.routes.websocket_notifications.manager")
    @patch("api.routes.websocket_notifications.get_redis")
    async def test_publish_handles_no_redis(self, mock_get_redis, mock_manager):
        from api.routes.websocket_notifications import publish_notification

        mock_get_redis.return_value = None
        mock_manager.send_to_user = AsyncMock()

        # Should not raise
        await publish_notification(
            notification_type="info",
            title="Test",
            message="Test",
            user_id="user123"
        )

        mock_manager.send_to_user.assert_called_once()

    @pytest.mark.asyncio
    @patch("api.routes.websocket_notifications.manager")
    @patch("api.routes.websocket_notifications.get_redis")
    async def test_publish_with_platform(self, mock_get_redis, mock_manager):
        from api.routes.websocket_notifications import publish_notification

        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_manager.broadcast = AsyncMock()

        await publish_notification(
            notification_type="post_published",
            title="Published",
            message="Your post is live",
            platform="instagram"
        )

        call_args = mock_manager.broadcast.call_args
        assert call_args[1]["platform"] == "instagram"


# ============================================
# ROUTER TESTS
# ============================================

class TestRouter:
    """Tests for the router configuration."""

    def test_router_exists(self):
        from api.routes.websocket_notifications import router

        assert router is not None

    def test_router_tags(self):
        from api.routes.websocket_notifications import router

        assert "WebSocket" in router.tags


# ============================================
# GLOBAL MANAGER TESTS
# ============================================

class TestGlobalManager:
    """Tests for the global manager instance."""

    def test_global_manager_exists(self):
        from api.routes.websocket_notifications import manager

        assert manager is not None

    def test_global_manager_is_connection_manager(self):
        from api.routes.websocket_notifications import manager, ConnectionManager

        assert isinstance(manager, ConnectionManager)


# ============================================
# INTEGRATION TESTS
# ============================================

class TestIntegration:
    """Integration tests for WebSocket notifications."""

    @pytest.fixture
    def manager(self):
        from api.routes.websocket_notifications import ConnectionManager
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_full_connection_lifecycle(self, manager):
        ws = AsyncMock()
        
        # Connect
        await manager.connect(ws, user_id="user123")
        assert manager.get_connection_count() == 1
        
        # Subscribe
        manager.subscribe_to_platform("user123", "instagram")
        assert "instagram" in manager.platform_subscriptions["user123"]
        
        # Send message
        await manager.send_to_user("user123", {"test": "message"})
        ws.send_json.assert_called_with({"test": "message"})
        
        # Unsubscribe
        manager.unsubscribe_from_platform("user123", "instagram")
        assert "instagram" not in manager.platform_subscriptions.get("user123", set())
        
        # Disconnect
        manager.disconnect(ws, user_id="user123")
        assert manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_multiple_users_broadcast(self, manager):
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        await manager.connect(ws1, user_id="user1")
        await manager.connect(ws2, user_id="user2")
        await manager.connect(ws3, user_id=None)  # Anonymous

        await manager.broadcast({"type": "announcement"})

        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()
        ws3.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_platform_filtered_broadcast(self, manager):
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect(ws1, user_id="user1")
        await manager.connect(ws2, user_id="user2")
        
        manager.subscribe_to_platform("user1", "instagram")
        manager.subscribe_to_platform("user2", "youtube")

        await manager.broadcast({"type": "instagram_update"}, platform="instagram")

        ws1.send_json.assert_called_once()
        ws2.send_json.assert_not_called()


# ============================================
# EDGE CASES
# ============================================

class TestEdgeCases:
    """Edge case tests."""

    @pytest.fixture
    def manager(self):
        from api.routes.websocket_notifications import ConnectionManager
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_user(self, manager):
        ws = MagicMock()
        
        # Should not raise
        manager.disconnect(ws, user_id="nonexistent")

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_websocket(self, manager):
        ws1 = MagicMock()
        ws2 = MagicMock()
        manager.active_connections["user123"] = {ws1}

        # Should not raise
        manager.disconnect(ws2, user_id="user123")
        
        # ws1 should still be there
        assert ws1 in manager.active_connections["user123"]

    @pytest.mark.asyncio
    async def test_empty_platform_subscriptions(self, manager):
        manager.subscribe_to_platform("user123", "instagram")
        manager.unsubscribe_from_platform("user123", "instagram")

        # Set should be empty but still exist
        assert manager.platform_subscriptions["user123"] == set()

    @pytest.mark.asyncio
    async def test_concurrent_connections(self, manager):
        websockets = [AsyncMock() for _ in range(10)]
        
        # Connect all
        for i, ws in enumerate(websockets):
            await manager.connect(ws, user_id=f"user{i}")

        assert manager.get_connection_count() == 10

        # Disconnect all
        for i, ws in enumerate(websockets):
            manager.disconnect(ws, user_id=f"user{i}")

        assert manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_send_json_serialization(self, manager):
        ws = AsyncMock()
        await manager.connect(ws, user_id="user123")

        complex_message = {
            "type": "test",
            "data": {
                "nested": {"key": "value"},
                "list": [1, 2, 3],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

        await manager.send_to_user("user123", complex_message)
        ws.send_json.assert_called_with(complex_message)
