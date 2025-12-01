"""
Tests for WebSocket Notifications Routes
Real-time notifications via WebSocket.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


class TestNotificationType:
    """Tests for NotificationType constants"""

    def test_notification_types_exist(self):
        """Test all notification types are defined"""
        from api.routes.websocket_notifications import NotificationType

        assert NotificationType.POST_PUBLISHED == "post_published"
        assert NotificationType.POST_FAILED == "post_failed"
        assert NotificationType.POST_SCHEDULED == "post_scheduled"
        assert NotificationType.ACCOUNT_CONNECTED == "account_connected"
        assert NotificationType.ACCOUNT_DISCONNECTED == "account_disconnected"
        assert NotificationType.ACCOUNT_EXPIRED == "account_expired"
        assert NotificationType.CHALLENGE_REQUIRED == "challenge_required"
        assert NotificationType.QUOTA_WARNING == "quota_warning"
        assert NotificationType.ERROR == "error"
        assert NotificationType.INFO == "info"


class TestWebSocketNotificationModel:
    """Tests for WebSocketNotification Pydantic model"""

    def test_notification_model_full(self):
        """Test notification model with all fields"""
        from api.routes.websocket_notifications import WebSocketNotification

        now = datetime.utcnow().isoformat()
        notification = WebSocketNotification(
            id=str(uuid4()),
            type="post_published",
            platform="instagram",
            title="Post Published",
            message="Your post was published successfully",
            timestamp=now,
            data={"post_id": "123"},
            read=False
        )

        assert notification.type == "post_published"
        assert notification.platform == "instagram"
        assert notification.read is False

    def test_notification_model_minimal(self):
        """Test notification model with minimal fields"""
        from api.routes.websocket_notifications import WebSocketNotification

        notification = WebSocketNotification(
            id="test-id",
            type="info",
            title="Info",
            message="Test message",
            timestamp="2024-01-01T00:00:00"
        )

        assert notification.platform is None
        assert notification.data is None
        assert notification.read is False


class TestConnectionManager:
    """Tests for ConnectionManager class"""

    def test_init(self):
        """Test ConnectionManager initialization"""
        from api.routes.websocket_notifications import ConnectionManager

        manager = ConnectionManager()
        assert manager.active_connections == {}
        assert manager.anonymous_connections == set()
        assert manager.platform_subscriptions == {}

    @pytest.mark.asyncio
    async def test_connect_authenticated(self):
        """Test connecting authenticated user"""
        from api.routes.websocket_notifications import ConnectionManager

        manager = ConnectionManager()
        mock_websocket = MagicMock()
        mock_websocket.accept = AsyncMock()

        await manager.connect(mock_websocket, "user-123")

        mock_websocket.accept.assert_called_once()
        assert "user-123" in manager.active_connections
        assert mock_websocket in manager.active_connections["user-123"]

    @pytest.mark.asyncio
    async def test_connect_anonymous(self):
        """Test connecting anonymous user"""
        from api.routes.websocket_notifications import ConnectionManager

        manager = ConnectionManager()
        mock_websocket = MagicMock()
        mock_websocket.accept = AsyncMock()

        await manager.connect(mock_websocket, None)

        mock_websocket.accept.assert_called_once()
        assert mock_websocket in manager.anonymous_connections

    def test_disconnect_authenticated(self):
        """Test disconnecting authenticated user"""
        from api.routes.websocket_notifications import ConnectionManager

        manager = ConnectionManager()
        mock_websocket = MagicMock()

        manager.active_connections["user-123"] = {mock_websocket}
        manager.platform_subscriptions["user-123"] = {"instagram"}

        manager.disconnect(mock_websocket, "user-123")

        assert "user-123" not in manager.active_connections

    def test_disconnect_anonymous(self):
        """Test disconnecting anonymous user"""
        from api.routes.websocket_notifications import ConnectionManager

        manager = ConnectionManager()
        mock_websocket = MagicMock()

        manager.anonymous_connections.add(mock_websocket)
        manager.disconnect(mock_websocket, None)

        assert mock_websocket not in manager.anonymous_connections

    def test_subscribe_to_platform(self):
        """Test subscribing to platform notifications"""
        from api.routes.websocket_notifications import ConnectionManager

        manager = ConnectionManager()
        manager.subscribe_to_platform("user-123", "instagram")

        assert "instagram" in manager.platform_subscriptions["user-123"]

    def test_subscribe_multiple_platforms(self):
        """Test subscribing to multiple platforms"""
        from api.routes.websocket_notifications import ConnectionManager

        manager = ConnectionManager()
        manager.subscribe_to_platform("user-123", "instagram")
        manager.subscribe_to_platform("user-123", "tiktok")

        assert "instagram" in manager.platform_subscriptions["user-123"]
        assert "tiktok" in manager.platform_subscriptions["user-123"]

    def test_unsubscribe_from_platform(self):
        """Test unsubscribing from platform"""
        from api.routes.websocket_notifications import ConnectionManager

        manager = ConnectionManager()
        manager.platform_subscriptions["user-123"] = {"instagram", "tiktok"}

        manager.unsubscribe_from_platform("user-123", "instagram")

        assert "instagram" not in manager.platform_subscriptions["user-123"]
        assert "tiktok" in manager.platform_subscriptions["user-123"]

    @pytest.mark.asyncio
    async def test_send_to_user(self):
        """Test sending message to specific user"""
        from api.routes.websocket_notifications import ConnectionManager

        manager = ConnectionManager()
        mock_websocket = MagicMock()
        mock_websocket.send_json = AsyncMock()

        manager.active_connections["user-123"] = {mock_websocket}

        message = {"event": "test", "data": "hello"}
        await manager.send_to_user("user-123", message)

        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_to_user_with_dead_connection(self):
        """Test handling dead connections when sending"""
        from api.routes.websocket_notifications import ConnectionManager

        manager = ConnectionManager()
        mock_websocket = MagicMock()
        mock_websocket.send_json = AsyncMock(side_effect=Exception("Connection closed"))

        manager.active_connections["user-123"] = {mock_websocket}

        await manager.send_to_user("user-123", {"event": "test"})

        assert mock_websocket not in manager.active_connections.get("user-123", set())

    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting to all users"""
        from api.routes.websocket_notifications import ConnectionManager

        manager = ConnectionManager()

        mock_ws1 = MagicMock()
        mock_ws1.send_json = AsyncMock()
        mock_ws2 = MagicMock()
        mock_ws2.send_json = AsyncMock()

        manager.active_connections["user-1"] = {mock_ws1}
        manager.anonymous_connections.add(mock_ws2)

        await manager.broadcast({"event": "broadcast"})

        mock_ws1.send_json.assert_called_once()
        mock_ws2.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_with_platform_filter(self):
        """Test broadcasting filtered by platform"""
        from api.routes.websocket_notifications import ConnectionManager

        manager = ConnectionManager()

        mock_ws1 = MagicMock()
        mock_ws1.send_json = AsyncMock()
        mock_ws2 = MagicMock()
        mock_ws2.send_json = AsyncMock()

        manager.active_connections["user-1"] = {mock_ws1}
        manager.active_connections["user-2"] = {mock_ws2}
        manager.platform_subscriptions["user-1"] = {"instagram"}
        manager.platform_subscriptions["user-2"] = {"tiktok"}

        await manager.broadcast({"event": "test"}, platform="instagram")

        mock_ws1.send_json.assert_called_once()
        mock_ws2.send_json.assert_not_called()

    def test_get_connection_count(self):
        """Test getting total connection count"""
        from api.routes.websocket_notifications import ConnectionManager

        manager = ConnectionManager()

        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()
        mock_ws3 = MagicMock()

        manager.active_connections["user-1"] = {mock_ws1, mock_ws2}
        manager.anonymous_connections.add(mock_ws3)

        assert manager.get_connection_count() == 3


class TestHelperFunctions:
    """Tests for helper functions"""

    def test_create_notification(self):
        """Test create_notification function"""
        from api.routes.websocket_notifications import create_notification

        notification = create_notification(
            notification_type="post_published",
            title="Success",
            message="Post published",
            platform="instagram",
            data={"post_id": "123"}
        )

        assert notification["event"] == "notification"
        assert notification["data"]["type"] == "post_published"
        assert notification["data"]["platform"] == "instagram"
        assert notification["data"]["title"] == "Success"
        assert notification["data"]["data"]["post_id"] == "123"

    def test_create_notification_minimal(self):
        """Test create_notification with minimal data"""
        from api.routes.websocket_notifications import create_notification

        notification = create_notification(
            notification_type="info",
            title="Info",
            message="Test"
        )

        assert notification["data"]["platform"] is None
        assert notification["data"]["data"] is None


class TestRouter:
    """Tests for router configuration"""

    def test_router_exists(self):
        """Test router is configured"""
        from api.routes.websocket_notifications import router

        assert router is not None
        assert "WebSocket" in router.tags


class TestGlobalManager:
    """Tests for global manager instance"""

    def test_manager_exists(self):
        """Test global manager is instantiated"""
        from api.routes.websocket_notifications import manager

        assert manager is not None
        assert hasattr(manager, 'active_connections')
        assert hasattr(manager, 'anonymous_connections')


class TestImports:
    """Tests for module imports"""

    def test_fastapi_imports(self):
        """Test FastAPI WebSocket imports"""
        from api.routes.websocket_notifications import (WebSocket,
                                                        WebSocketDisconnect)
        assert WebSocket is not None
        assert WebSocketDisconnect is not None

    def test_redis_import(self):
        """Test Redis import"""
        from api.routes.websocket_notifications import get_redis
        assert get_redis is not None
