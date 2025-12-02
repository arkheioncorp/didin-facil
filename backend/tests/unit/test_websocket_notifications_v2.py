"""
Testes para api/routes/websocket_notifications.py
WebSocket Notifications Endpoint
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.websocket_notifications import (ConnectionManager,
                                                NotificationType,
                                                WebSocketNotification,
                                                create_notification,
                                                publish_notification)

# ==================== TEST NOTIFICATION TYPE ====================

class TestNotificationType:
    """Testes para NotificationType."""

    def test_post_published_constant(self):
        """POST_PUBLISHED deve ter valor correto."""
        assert NotificationType.POST_PUBLISHED == "post_published"

    def test_post_failed_constant(self):
        """POST_FAILED deve ter valor correto."""
        assert NotificationType.POST_FAILED == "post_failed"

    def test_post_scheduled_constant(self):
        """POST_SCHEDULED deve ter valor correto."""
        assert NotificationType.POST_SCHEDULED == "post_scheduled"

    def test_account_connected_constant(self):
        """ACCOUNT_CONNECTED deve ter valor correto."""
        assert NotificationType.ACCOUNT_CONNECTED == "account_connected"

    def test_account_disconnected_constant(self):
        """ACCOUNT_DISCONNECTED deve ter valor correto."""
        assert NotificationType.ACCOUNT_DISCONNECTED == "account_disconnected"

    def test_account_expired_constant(self):
        """ACCOUNT_EXPIRED deve ter valor correto."""
        assert NotificationType.ACCOUNT_EXPIRED == "account_expired"

    def test_challenge_required_constant(self):
        """CHALLENGE_REQUIRED deve ter valor correto."""
        assert NotificationType.CHALLENGE_REQUIRED == "challenge_required"

    def test_quota_warning_constant(self):
        """QUOTA_WARNING deve ter valor correto."""
        assert NotificationType.QUOTA_WARNING == "quota_warning"

    def test_error_constant(self):
        """ERROR deve ter valor correto."""
        assert NotificationType.ERROR == "error"

    def test_info_constant(self):
        """INFO deve ter valor correto."""
        assert NotificationType.INFO == "info"


# ==================== TEST WEBSOCKET NOTIFICATION MODEL ====================

class TestWebSocketNotificationModel:
    """Testes para modelo WebSocketNotification."""

    def test_minimal_notification(self):
        """Notification com campos mínimos."""
        notif = WebSocketNotification(
            id="123",
            type="info",
            title="Test",
            message="Test message",
            timestamp="2024-01-01T00:00:00"
        )
        
        assert notif.id == "123"
        assert notif.type == "info"
        assert notif.platform is None
        assert notif.data is None
        assert notif.read is False

    def test_full_notification(self):
        """Notification com todos os campos."""
        notif = WebSocketNotification(
            id="456",
            type="post_published",
            platform="instagram",
            title="Post Published",
            message="Your post was published",
            timestamp="2024-01-01T12:00:00",
            data={"post_id": "abc123"},
            read=True
        )
        
        assert notif.platform == "instagram"
        assert notif.data == {"post_id": "abc123"}
        assert notif.read is True


# ==================== TEST CONNECTION MANAGER ====================

class TestConnectionManager:
    """Testes para ConnectionManager."""

    @pytest.fixture
    def manager(self):
        """Manager limpo para cada teste."""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """WebSocket mockado."""
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect_authenticated_user(self, manager, mock_websocket):
        """Conexão de usuário autenticado."""
        await manager.connect(mock_websocket, user_id="user_123")
        
        mock_websocket.accept.assert_called_once()
        assert "user_123" in manager.active_connections
        assert mock_websocket in manager.active_connections["user_123"]

    @pytest.mark.asyncio
    async def test_connect_anonymous_user(self, manager, mock_websocket):
        """Conexão anônima."""
        await manager.connect(mock_websocket, user_id=None)
        
        mock_websocket.accept.assert_called_once()
        assert mock_websocket in manager.anonymous_connections

    @pytest.mark.asyncio
    async def test_connect_multiple_same_user(self, manager):
        """Múltiplas conexões do mesmo usuário."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        
        await manager.connect(ws1, "user_1")
        await manager.connect(ws2, "user_1")
        
        assert len(manager.active_connections["user_1"]) == 2

    def test_disconnect_authenticated_user(self, manager, mock_websocket):
        """Desconexão de usuário autenticado."""
        # Setup: Add connection first
        manager.active_connections["user_123"] = {mock_websocket}
        
        manager.disconnect(mock_websocket, user_id="user_123")
        
        assert "user_123" not in manager.active_connections

    def test_disconnect_removes_subscriptions(self, manager, mock_websocket):
        """Desconexão deve remover subscriptions."""
        manager.active_connections["user_123"] = {mock_websocket}
        manager.platform_subscriptions["user_123"] = {"instagram", "tiktok"}
        
        manager.disconnect(mock_websocket, user_id="user_123")
        
        assert "user_123" not in manager.platform_subscriptions

    def test_disconnect_keeps_other_connections(self, manager):
        """Desconexão mantém outras conexões do mesmo usuário."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        manager.active_connections["user_123"] = {ws1, ws2}
        
        manager.disconnect(ws1, user_id="user_123")
        
        assert "user_123" in manager.active_connections
        assert ws2 in manager.active_connections["user_123"]

    def test_disconnect_anonymous(self, manager, mock_websocket):
        """Desconexão anônima."""
        manager.anonymous_connections.add(mock_websocket)
        
        manager.disconnect(mock_websocket, user_id=None)
        
        assert mock_websocket not in manager.anonymous_connections

    def test_subscribe_to_platform(self, manager):
        """Subscribe a plataforma."""
        manager.subscribe_to_platform("user_123", "instagram")
        
        assert "instagram" in manager.platform_subscriptions["user_123"]

    def test_subscribe_multiple_platforms(self, manager):
        """Subscribe a múltiplas plataformas."""
        manager.subscribe_to_platform("user_123", "instagram")
        manager.subscribe_to_platform("user_123", "tiktok")
        
        assert "instagram" in manager.platform_subscriptions["user_123"]
        assert "tiktok" in manager.platform_subscriptions["user_123"]

    def test_unsubscribe_from_platform(self, manager):
        """Unsubscribe de plataforma."""
        manager.platform_subscriptions["user_123"] = {"instagram", "tiktok"}
        
        manager.unsubscribe_from_platform("user_123", "instagram")
        
        assert "instagram" not in manager.platform_subscriptions["user_123"]
        assert "tiktok" in manager.platform_subscriptions["user_123"]

    def test_unsubscribe_nonexistent_user(self, manager):
        """Unsubscribe de usuário não existente não deve falhar."""
        manager.unsubscribe_from_platform("nonexistent", "instagram")
        # Não deve levantar exceção

    @pytest.mark.asyncio
    async def test_send_to_user(self, manager):
        """Enviar mensagem para usuário específico."""
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        manager.active_connections["user_123"] = {ws}
        
        message = {"event": "test", "data": {}}
        await manager.send_to_user("user_123", message)
        
        ws.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_to_user_multiple_connections(self, manager):
        """Enviar para múltiplas conexões do mesmo usuário."""
        ws1 = AsyncMock()
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock()
        ws2.send_json = AsyncMock()
        manager.active_connections["user_123"] = {ws1, ws2}
        
        message = {"event": "test"}
        await manager.send_to_user("user_123", message)
        
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_to_user_removes_dead_connections(self, manager):
        """Dead connections devem ser removidas."""
        ws_alive = AsyncMock()
        ws_alive.send_json = AsyncMock()
        ws_dead = AsyncMock()
        ws_dead.send_json = AsyncMock(side_effect=Exception("Connection closed"))
        
        manager.active_connections["user_123"] = {ws_alive, ws_dead}
        
        await manager.send_to_user("user_123", {"event": "test"})
        
        # ws_dead deve ter sido removido
        assert ws_dead not in manager.active_connections["user_123"]
        assert ws_alive in manager.active_connections["user_123"]

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_user(self, manager):
        """Enviar para usuário inexistente não deve falhar."""
        await manager.send_to_user("nonexistent", {"event": "test"})
        # Não deve levantar exceção

    @pytest.mark.asyncio
    async def test_broadcast_to_all(self, manager):
        """Broadcast para todos os usuários."""
        ws1 = AsyncMock()
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock()
        ws2.send_json = AsyncMock()
        ws_anon = AsyncMock()
        ws_anon.send_json = AsyncMock()
        
        manager.active_connections["user_1"] = {ws1}
        manager.active_connections["user_2"] = {ws2}
        manager.anonymous_connections.add(ws_anon)
        
        message = {"event": "broadcast"}
        await manager.broadcast(message)
        
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)
        ws_anon.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_with_platform_filter(self, manager):
        """Broadcast filtrado por plataforma."""
        ws_subscribed = AsyncMock()
        ws_subscribed.send_json = AsyncMock()
        ws_not_subscribed = AsyncMock()
        ws_not_subscribed.send_json = AsyncMock()
        
        manager.active_connections["user_1"] = {ws_subscribed}
        manager.active_connections["user_2"] = {ws_not_subscribed}
        manager.platform_subscriptions["user_1"] = {"instagram"}
        # user_2 não tem subscription
        
        message = {"event": "instagram_update"}
        await manager.broadcast(message, platform="instagram")
        
        ws_subscribed.send_json.assert_called_once_with(message)
        ws_not_subscribed.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_with_all_subscription(self, manager):
        """User com subscription 'all' recebe todas as plataformas."""
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        
        manager.active_connections["user_1"] = {ws}
        manager.platform_subscriptions["user_1"] = {"all"}
        
        await manager.broadcast({"event": "any_platform"}, platform="youtube")
        
        ws.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_removes_dead_connections(self, manager):
        """Broadcast remove dead connections."""
        ws_alive = AsyncMock()
        ws_alive.send_json = AsyncMock()
        ws_dead = AsyncMock()
        ws_dead.send_json = AsyncMock(side_effect=Exception("Dead"))
        
        manager.active_connections["user_1"] = {ws_alive, ws_dead}
        manager.anonymous_connections.add(ws_dead)
        
        await manager.broadcast({"event": "test"})
        
        assert ws_dead not in manager.active_connections["user_1"]

    def test_get_connection_count(self, manager):
        """Contar total de conexões."""
        manager.active_connections["user_1"] = {AsyncMock(), AsyncMock()}
        manager.active_connections["user_2"] = {AsyncMock()}
        manager.anonymous_connections = {AsyncMock(), AsyncMock()}
        
        count = manager.get_connection_count()
        
        assert count == 5  # 2 + 1 + 2

    def test_get_connection_count_empty(self, manager):
        """Count com zero conexões."""
        assert manager.get_connection_count() == 0


# ==================== TEST CREATE NOTIFICATION ====================

class TestCreateNotification:
    """Testes para create_notification."""

    def test_creates_valid_structure(self):
        """Deve criar estrutura válida."""
        result = create_notification(
            notification_type="info",
            title="Test Title",
            message="Test message"
        )
        
        assert result["event"] == "notification"
        assert "data" in result
        assert "timestamp" in result

    def test_notification_data_fields(self):
        """Data deve ter todos os campos necessários."""
        result = create_notification(
            notification_type="post_published",
            title="Published",
            message="Your post is live"
        )
        
        data = result["data"]
        assert "id" in data
        assert data["type"] == "post_published"
        assert data["title"] == "Published"
        assert data["message"] == "Your post is live"
        assert data["read"] is False
        assert "timestamp" in data

    def test_with_platform(self):
        """Deve incluir platform quando fornecido."""
        result = create_notification(
            notification_type="info",
            title="Test",
            message="Test",
            platform="instagram"
        )
        
        assert result["data"]["platform"] == "instagram"

    def test_with_custom_data(self):
        """Deve incluir data customizado."""
        custom_data = {"post_id": "123", "url": "https://example.com"}
        result = create_notification(
            notification_type="info",
            title="Test",
            message="Test",
            data=custom_data
        )
        
        assert result["data"]["data"] == custom_data

    def test_generates_unique_ids(self):
        """Deve gerar IDs únicos."""
        result1 = create_notification("info", "Test", "Test")
        result2 = create_notification("info", "Test", "Test")
        
        assert result1["data"]["id"] != result2["data"]["id"]


# ==================== TEST PUBLISH NOTIFICATION ====================

class TestPublishNotification:
    """Testes para publish_notification."""

    @pytest.fixture
    def mock_manager(self):
        """Manager mockado."""
        with patch('api.routes.websocket_notifications.manager') as m:
            m.send_to_user = AsyncMock()
            m.broadcast = AsyncMock()
            yield m

    @pytest.fixture
    def mock_redis(self):
        """Redis mockado."""
        redis = AsyncMock()
        redis.lpush = AsyncMock()
        redis.ltrim = AsyncMock()
        redis.expire = AsyncMock()
        return redis

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.get_redis')
    async def test_publish_to_specific_user(self, mock_get_redis, mock_manager, mock_redis):
        """Publicar para usuário específico."""
        mock_get_redis.return_value = mock_redis
        
        await publish_notification(
            notification_type="info",
            title="Test",
            message="Test message",
            user_id="user_123"
        )
        
        mock_manager.send_to_user.assert_called_once()
        call_args = mock_manager.send_to_user.call_args
        assert call_args[0][0] == "user_123"

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.get_redis')
    async def test_publish_broadcast(self, mock_get_redis, mock_manager, mock_redis):
        """Publicar broadcast para todos."""
        mock_get_redis.return_value = mock_redis
        
        await publish_notification(
            notification_type="info",
            title="Broadcast",
            message="All users"
        )
        
        mock_manager.broadcast.assert_called_once()

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.get_redis')
    async def test_publish_with_platform_filter(self, mock_get_redis, mock_manager, mock_redis):
        """Publicar com filtro de plataforma."""
        mock_get_redis.return_value = mock_redis
        
        await publish_notification(
            notification_type="post_published",
            title="Published",
            message="Post live",
            platform="tiktok"
        )
        
        mock_manager.broadcast.assert_called_once()
        call_args = mock_manager.broadcast.call_args
        assert call_args[1]["platform"] == "tiktok"

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.get_redis')
    async def test_stores_in_redis(self, mock_get_redis, mock_manager, mock_redis):
        """Deve armazenar notificação no Redis."""
        mock_get_redis.return_value = mock_redis
        
        await publish_notification(
            notification_type="info",
            title="Test",
            message="Test",
            user_id="user_123"
        )
        
        mock_redis.lpush.assert_called_once()
        call_args = mock_redis.lpush.call_args
        assert "notifications:user_123" in call_args[0][0]
        
        mock_redis.ltrim.assert_called_once()
        mock_redis.expire.assert_called_once()

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.get_redis')
    async def test_stores_broadcast_in_redis(self, mock_get_redis, mock_manager, mock_redis):
        """Broadcast deve ser armazenado com key 'broadcast'."""
        mock_get_redis.return_value = mock_redis
        
        await publish_notification(
            notification_type="info",
            title="Broadcast",
            message="All"
        )
        
        call_args = mock_redis.lpush.call_args
        assert "notifications:broadcast" in call_args[0][0]

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.get_redis')
    async def test_handles_redis_failure(self, mock_get_redis, mock_manager):
        """Deve tratar falha do Redis graciosamente."""
        mock_get_redis.side_effect = Exception("Redis down")
        
        # Não deve levantar exceção
        await publish_notification(
            notification_type="info",
            title="Test",
            message="Test"
        )

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.get_redis')
    async def test_handles_redis_none(self, mock_get_redis, mock_manager):
        """Deve tratar Redis None graciosamente."""
        mock_get_redis.return_value = None
        
        await publish_notification(
            notification_type="info",
            title="Test",
            message="Test"
        )


# ==================== TEST GET NOTIFICATIONS ENDPOINT ====================

class TestGetNotificationsEndpoint:
    """Testes para endpoint get_notifications."""

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.get_redis')
    async def test_get_notifications_success(self, mock_get_redis):
        """Deve retornar notificações do Redis."""
        from api.routes.websocket_notifications import get_notifications
        
        mock_redis = AsyncMock()
        notifications = [
            json.dumps({"id": "1", "type": "info", "message": "First"}),
            json.dumps({"id": "2", "type": "error", "message": "Second"})
        ]
        mock_redis.lrange = AsyncMock(return_value=notifications)
        mock_get_redis.return_value = mock_redis
        
        result = await get_notifications(user_id="user_123", limit=20)
        
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.get_redis')
    async def test_get_notifications_empty(self, mock_get_redis):
        """Deve retornar lista vazia quando não há notificações."""
        from api.routes.websocket_notifications import get_notifications
        
        mock_redis = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=[])
        mock_get_redis.return_value = mock_redis
        
        result = await get_notifications(user_id="user_123")
        
        assert result == []

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.get_redis')
    async def test_get_notifications_redis_none(self, mock_get_redis):
        """Deve retornar lista vazia se Redis é None."""
        from api.routes.websocket_notifications import get_notifications
        
        mock_get_redis.return_value = None
        
        result = await get_notifications(user_id="user_123")
        
        assert result == []

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.get_redis')
    async def test_get_notifications_redis_error(self, mock_get_redis):
        """Deve retornar lista vazia em caso de erro."""
        from api.routes.websocket_notifications import get_notifications
        
        mock_get_redis.side_effect = Exception("Redis error")
        
        result = await get_notifications()
        
        assert result == []

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.get_redis')
    async def test_get_notifications_uses_correct_key(self, mock_get_redis):
        """Deve usar key correta baseada no user_id."""
        from api.routes.websocket_notifications import get_notifications
        
        mock_redis = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=[])
        mock_get_redis.return_value = mock_redis
        
        # Passar limit como int, não Query
        await get_notifications(user_id="specific_user", limit=20)
        
        mock_redis.lrange.assert_called_once()
        call_args = mock_redis.lrange.call_args
        assert "notifications:specific_user" == call_args[0][0]


# ==================== TEST SEND NOTIFICATION ENDPOINT ====================

class TestSendNotificationEndpoint:
    """Testes para endpoint send_notification."""

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.publish_notification')
    @patch('api.routes.websocket_notifications.manager')
    async def test_send_notification_success(self, mock_manager, mock_publish):
        """Deve enviar notificação e retornar status."""
        from api.routes.websocket_notifications import send_notification
        
        mock_publish.return_value = None
        mock_manager.get_connection_count.return_value = 5
        
        result = await send_notification(
            notification_type="info",
            title="Test",
            message="Test message"
        )
        
        assert result["status"] == "sent"
        assert result["connections"] == 5
        mock_publish.assert_called_once()

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.publish_notification')
    @patch('api.routes.websocket_notifications.manager')
    async def test_send_notification_to_user(self, mock_manager, mock_publish):
        """Deve enviar para usuário específico."""
        from api.routes.websocket_notifications import send_notification
        
        mock_manager.get_connection_count.return_value = 1
        
        await send_notification(
            notification_type="info",
            title="Test",
            message="Test",
            user_id="user_123"
        )
        
        call_kwargs = mock_publish.call_args[1]
        assert call_kwargs["user_id"] == "user_123"

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.publish_notification')
    @patch('api.routes.websocket_notifications.manager')
    async def test_send_notification_with_platform(self, mock_manager, mock_publish):
        """Deve enviar com filtro de plataforma."""
        from api.routes.websocket_notifications import send_notification
        
        mock_manager.get_connection_count.return_value = 3
        
        await send_notification(
            notification_type="post_published",
            title="Published",
            message="Live",
            platform="instagram"
        )
        
        call_kwargs = mock_publish.call_args[1]
        assert call_kwargs["platform"] == "instagram"


# ==================== TEST CONNECTION STATS ENDPOINT ====================

class TestConnectionStatsEndpoint:
    """Testes para endpoint get_connection_stats."""

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.manager')
    async def test_get_connection_stats(self, mock_manager):
        """Deve retornar estatísticas de conexão."""
        from api.routes.websocket_notifications import get_connection_stats
        
        mock_manager.get_connection_count.return_value = 10
        mock_manager.active_connections = {"user_1": set(), "user_2": set()}
        mock_manager.anonymous_connections = {AsyncMock()}
        
        result = await get_connection_stats()
        
        assert result["total_connections"] == 10
        assert result["authenticated_users"] == 2
        assert result["anonymous_connections"] == 1

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.manager')
    async def test_get_connection_stats_empty(self, mock_manager):
        """Stats com zero conexões."""
        from api.routes.websocket_notifications import get_connection_stats
        
        mock_manager.get_connection_count.return_value = 0
        mock_manager.active_connections = {}
        mock_manager.anonymous_connections = set()
        
        result = await get_connection_stats()
        
        assert result["total_connections"] == 0
        assert result["authenticated_users"] == 0
        assert result["anonymous_connections"] == 0


# ==================== TEST WEBSOCKET ENDPOINT ====================

class TestWebSocketEndpoint:
    """Testes para WebSocket endpoint."""

    @pytest.fixture
    def mock_websocket(self):
        """WebSocket mockado."""
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.receive_json = AsyncMock()
        return ws

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.get_redis')
    @patch('api.routes.websocket_notifications.manager')
    async def test_websocket_connects_with_token(self, mock_manager, mock_get_redis, mock_websocket):
        """WebSocket deve conectar com token."""
        from api.routes.websocket_notifications import websocket_endpoint
        from fastapi import WebSocketDisconnect
        
        mock_get_redis.return_value = AsyncMock(lrange=AsyncMock(return_value=[]))
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = MagicMock()
        
        # Simular desconexão após primeira mensagem
        mock_websocket.receive_json = AsyncMock(side_effect=WebSocketDisconnect())
        
        await websocket_endpoint(mock_websocket, token="user_token")
        
        mock_manager.connect.assert_called_once()
        # user_id deve ser o token (placeholder)
        assert mock_manager.connect.call_args[0][1] == "user_token"

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.get_redis')
    @patch('api.routes.websocket_notifications.manager')
    async def test_websocket_sends_connected_event(self, mock_manager, mock_get_redis, mock_websocket):
        """Deve enviar evento 'connected' após conexão."""
        from api.routes.websocket_notifications import websocket_endpoint
        from fastapi import WebSocketDisconnect
        
        mock_redis = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=[])
        mock_get_redis.return_value = mock_redis
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = MagicMock()
        mock_websocket.receive_json = AsyncMock(side_effect=WebSocketDisconnect())
        
        await websocket_endpoint(mock_websocket, token="user_123")
        
        # Verificar que send_json foi chamado com evento connected
        calls = mock_websocket.send_json.call_args_list
        connected_call = calls[0]
        assert connected_call[0][0]["event"] == "connected"

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.get_redis')
    @patch('api.routes.websocket_notifications.manager')
    async def test_websocket_handles_ping_event(self, mock_manager, mock_get_redis, mock_websocket):
        """Deve responder ping com pong."""
        from api.routes.websocket_notifications import websocket_endpoint
        from fastapi import WebSocketDisconnect
        
        mock_get_redis.return_value = AsyncMock(lrange=AsyncMock(return_value=[]))
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = MagicMock()
        
        # Primeiro recebe ping, depois desconecta
        mock_websocket.receive_json = AsyncMock(side_effect=[
            {"event": "ping"},
            WebSocketDisconnect()
        ])
        
        await websocket_endpoint(mock_websocket, token="user_123")
        
        # Deve ter enviado pong
        calls = [c[0][0] for c in mock_websocket.send_json.call_args_list]
        pong_sent = any(c.get("event") == "pong" for c in calls)
        assert pong_sent

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.get_redis')
    @patch('api.routes.websocket_notifications.manager')
    async def test_websocket_handles_subscribe_event(self, mock_manager, mock_get_redis, mock_websocket):
        """Deve processar evento subscribe."""
        from api.routes.websocket_notifications import websocket_endpoint
        from fastapi import WebSocketDisconnect
        
        mock_get_redis.return_value = AsyncMock(lrange=AsyncMock(return_value=[]))
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = MagicMock()
        mock_manager.subscribe_to_platform = MagicMock()
        
        mock_websocket.receive_json = AsyncMock(side_effect=[
            {"event": "subscribe", "data": {"platform": "instagram"}},
            WebSocketDisconnect()
        ])
        
        await websocket_endpoint(mock_websocket, token="user_123")
        
        mock_manager.subscribe_to_platform.assert_called_once_with("user_123", "instagram")

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.get_redis')
    @patch('api.routes.websocket_notifications.manager')
    async def test_websocket_handles_unsubscribe_event(self, mock_manager, mock_get_redis, mock_websocket):
        """Deve processar evento unsubscribe."""
        from api.routes.websocket_notifications import websocket_endpoint
        from fastapi import WebSocketDisconnect
        
        mock_get_redis.return_value = AsyncMock(lrange=AsyncMock(return_value=[]))
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = MagicMock()
        mock_manager.unsubscribe_from_platform = MagicMock()
        
        mock_websocket.receive_json = AsyncMock(side_effect=[
            {"event": "unsubscribe", "data": {"platform": "tiktok"}},
            WebSocketDisconnect()
        ])
        
        await websocket_endpoint(mock_websocket, token="user_123")
        
        mock_manager.unsubscribe_from_platform.assert_called_once_with("user_123", "tiktok")

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.get_redis')
    @patch('api.routes.websocket_notifications.manager')
    async def test_websocket_loads_recent_notifications(self, mock_manager, mock_get_redis, mock_websocket):
        """Deve carregar notificações recentes do Redis."""
        from api.routes.websocket_notifications import websocket_endpoint
        from fastapi import WebSocketDisconnect
        
        notifications = [
            json.dumps({"id": "1", "type": "info", "message": "Old"}),
            json.dumps({"id": "2", "type": "info", "message": "Older"})
        ]
        
        mock_redis = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=notifications)
        mock_get_redis.return_value = mock_redis
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = MagicMock()
        mock_websocket.receive_json = AsyncMock(side_effect=WebSocketDisconnect())
        
        await websocket_endpoint(mock_websocket, token="user_123")
        
        # Deve ter enviado as notificações (conectado + 2 notificações)
        assert mock_websocket.send_json.call_count >= 3

    @pytest.mark.asyncio
    @patch('api.routes.websocket_notifications.get_redis')
    @patch('api.routes.websocket_notifications.manager')
    async def test_websocket_handles_error(self, mock_manager, mock_get_redis, mock_websocket):
        """Deve tratar erros graciosamente."""
        from api.routes.websocket_notifications import websocket_endpoint
        
        mock_get_redis.return_value = AsyncMock(lrange=AsyncMock(return_value=[]))
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = MagicMock()
        mock_websocket.receive_json = AsyncMock(side_effect=Exception("Unknown error"))
        
        await websocket_endpoint(mock_websocket, token="user_123")
        
        mock_manager.disconnect.assert_called_once()
