"""Testes abrangentes para WhatsApp Routes (Legacy v1)."""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_user():
    user = MagicMock()
    user_id = uuid.uuid4()
    user.__getitem__ = lambda self, key: {"id": user_id, "email": "test@example.com"}.get(key)
    user.is_admin = False
    return user


@pytest.fixture
def mock_admin_user():
    user = MagicMock()
    user_id = uuid.uuid4()
    user.__getitem__ = lambda self, key: {"id": user_id, "email": "admin@example.com"}.get(key)
    user.is_admin = True
    return user


@pytest.fixture
def mock_subscription_service():
    service = MagicMock()
    service.get_subscription = AsyncMock(return_value=MagicMock(plan="pro"))
    service.get_plan_config = MagicMock(return_value=MagicMock(
        limits={"whatsapp_instances": 5, "whatsapp_messages": 1000}
    ))
    service.can_use_feature = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_hub():
    hub = MagicMock()
    hub.create_instance = AsyncMock(return_value={
        "status": "created",
        "instance_name": "test-instance"
    })
    hub.get_qr_code = AsyncMock(return_value={"base64": "qr_code_base64_data"})
    hub.send_message = AsyncMock(return_value={"status": "sent", "message_id": "msg123"})
    return hub


@pytest.fixture
def mock_database():
    db = MagicMock()
    db.fetch_val = AsyncMock(return_value=0)
    db.fetch_one = AsyncMock(return_value=None)
    db.fetch_all = AsyncMock(return_value=[])
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_redis():
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.zadd = AsyncMock()
    return redis


@pytest.fixture
def mock_instance():
    instance = MagicMock()
    instance.id = uuid.uuid4()
    instance.user_id = uuid.uuid4()
    instance.name = "test-instance"
    instance.status = "connected"
    instance.updated_at = datetime.now(timezone.utc)
    return instance


# =============================================================================
# TEST MODELS
# =============================================================================

class TestWhatsAppModels:
    """Testa modelos Pydantic."""

    def test_instance_create_model(self):
        from api.routes.whatsapp import WhatsAppInstanceCreate

        data = WhatsAppInstanceCreate(
            instance_name="my-instance",
            webhook_url="https://example.com/webhook"
        )
        assert data.instance_name == "my-instance"
        assert data.webhook_url == "https://example.com/webhook"

    def test_instance_create_model_default_webhook(self):
        from api.routes.whatsapp import WhatsAppInstanceCreate

        data = WhatsAppInstanceCreate(instance_name="my-instance")
        assert data.instance_name == "my-instance"
        assert data.webhook_url is None

    def test_message_send_model(self):
        from api.routes.whatsapp import WhatsAppMessageSend

        data = WhatsAppMessageSend(
            instance_name="my-instance",
            to="5511999999999",
            content="Hello World!"
        )
        assert data.instance_name == "my-instance"
        assert data.to == "5511999999999"
        assert data.content == "Hello World!"


# =============================================================================
# TEST GET_HUB
# =============================================================================

class TestGetHub:
    """Testa a função get_hub."""

    def test_get_hub_returns_singleton(self):
        from api.routes.whatsapp import get_hub

        with patch('api.routes.whatsapp.get_whatsapp_hub') as mock_get_hub:
            mock_hub = MagicMock()
            mock_get_hub.return_value = mock_hub

            # Reset global
            import api.routes.whatsapp as whatsapp_module
            whatsapp_module._hub = None

            hub1 = get_hub()
            hub2 = get_hub()

            # Should call get_whatsapp_hub only once
            assert mock_get_hub.call_count == 1
            assert hub1 is hub2


# =============================================================================
# TEST CREATE INSTANCE
# =============================================================================

class TestCreateInstance:
    """Testa criação de instâncias."""

    async def test_create_instance_success(
        self, mock_user, mock_subscription_service, mock_hub, mock_database
    ):
        from api.routes.whatsapp import WhatsAppInstanceCreate, create_instance

        data = WhatsAppInstanceCreate(instance_name="new-instance")

        with patch('api.routes.whatsapp.get_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp.database', mock_database):

            result = await create_instance(data, mock_user, mock_subscription_service)

            assert result["status"] == "created"
            mock_hub.create_instance.assert_called_once()

    async def test_create_instance_limit_reached(
        self, mock_user, mock_subscription_service, mock_database
    ):
        from api.routes.whatsapp import WhatsAppInstanceCreate, create_instance

        # Simular limite atingido
        mock_database.fetch_val = AsyncMock(return_value=5)  # Already at limit
        mock_subscription_service.get_plan_config.return_value.limits = {
            "whatsapp_instances": 5
        }

        data = WhatsAppInstanceCreate(instance_name="new-instance")

        with patch('api.routes.whatsapp.database', mock_database):
            with pytest.raises(HTTPException) as exc:
                await create_instance(data, mock_user, mock_subscription_service)

            assert exc.value.status_code == 402
            assert "Limite de instâncias atingido" in exc.value.detail

    async def test_create_instance_unlimited(
        self, mock_user, mock_subscription_service, mock_hub, mock_database
    ):
        from api.routes.whatsapp import WhatsAppInstanceCreate, create_instance

        # Simular plano ilimitado
        mock_subscription_service.get_plan_config.return_value.limits = {
            "whatsapp_instances": -1
        }

        data = WhatsAppInstanceCreate(instance_name="new-instance")

        with patch('api.routes.whatsapp.get_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp.database', mock_database):

            result = await create_instance(data, mock_user, mock_subscription_service)

            assert result["status"] == "created"

    async def test_create_instance_hub_error(
        self, mock_user, mock_subscription_service, mock_hub, mock_database
    ):
        from api.routes.whatsapp import WhatsAppInstanceCreate, create_instance

        mock_hub.create_instance = AsyncMock(side_effect=Exception("Hub error"))

        data = WhatsAppInstanceCreate(instance_name="new-instance")

        with patch('api.routes.whatsapp.get_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp.database', mock_database):

            with pytest.raises(HTTPException) as exc:
                await create_instance(data, mock_user, mock_subscription_service)

            assert exc.value.status_code == 400
            assert "Hub error" in exc.value.detail


# =============================================================================
# TEST GET QR CODE
# =============================================================================

class TestGetQRCode:
    """Testa obtenção de QR code."""

    async def test_get_qrcode_success(self, mock_user, mock_hub):
        from api.routes.whatsapp import get_qrcode

        with patch('api.routes.whatsapp.get_hub', return_value=mock_hub):
            result = await get_qrcode("test-instance", mock_user)

            assert result["base64"] == "qr_code_base64_data"
            mock_hub.get_qr_code.assert_called_once_with(instance_name="test-instance")

    async def test_get_qrcode_error(self, mock_user, mock_hub):
        from api.routes.whatsapp import get_qrcode

        mock_hub.get_qr_code = AsyncMock(side_effect=Exception("QR code error"))

        with patch('api.routes.whatsapp.get_hub', return_value=mock_hub):
            with pytest.raises(HTTPException) as exc:
                await get_qrcode("test-instance", mock_user)

            assert exc.value.status_code == 400


# =============================================================================
# TEST SEND MESSAGE
# =============================================================================

class TestSendMessage:
    """Testa envio de mensagens."""

    async def test_send_message_success(
        self, mock_user, mock_subscription_service, mock_hub, mock_database, mock_instance
    ):
        from api.routes.whatsapp import WhatsAppMessageSend, send_message

        mock_database.fetch_one = AsyncMock(return_value=mock_instance)

        data = WhatsAppMessageSend(
            instance_name="test-instance",
            to="5511999999999",
            content="Hello!"
        )

        with patch('api.routes.whatsapp.get_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp.database', mock_database):

            result = await send_message(data, mock_user, mock_subscription_service)

            assert result["status"] == "sent"
            mock_hub.send_message.assert_called_once()

    async def test_send_message_limit_reached(self, mock_user, mock_subscription_service):
        from api.routes.whatsapp import WhatsAppMessageSend, send_message

        mock_subscription_service.can_use_feature = AsyncMock(return_value=False)

        data = WhatsAppMessageSend(
            instance_name="test-instance",
            to="5511999999999",
            content="Hello!"
        )

        with pytest.raises(HTTPException) as exc:
            await send_message(data, mock_user, mock_subscription_service)

        assert exc.value.status_code == 402
        assert "Limite de mensagens atingido" in exc.value.detail

    async def test_send_message_no_instance(
        self, mock_user, mock_subscription_service, mock_hub, mock_database
    ):
        from api.routes.whatsapp import WhatsAppMessageSend, send_message

        mock_database.fetch_one = AsyncMock(return_value=None)

        data = WhatsAppMessageSend(
            instance_name="test-instance",
            to="5511999999999",
            content="Hello!"
        )

        with patch('api.routes.whatsapp.get_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp.database', mock_database):

            # Should still work, just not save to DB
            result = await send_message(data, mock_user, mock_subscription_service)
            assert result["status"] == "sent"


# =============================================================================
# TEST WEBHOOK
# =============================================================================

class TestWebhook:
    """Testa processamento de webhooks."""

    async def test_webhook_no_instance_name(self, mock_database):
        from api.routes.whatsapp import whatsapp_webhook

        request = MagicMock()
        request.json = AsyncMock(return_value={"event": "test"})

        with patch('api.routes.whatsapp.database', mock_database):
            result = await whatsapp_webhook(request)

            assert result["status"] == "ignored"
            assert result["reason"] == "no_instance"

    async def test_webhook_instance_not_found(self, mock_database):
        from api.routes.whatsapp import whatsapp_webhook

        mock_database.fetch_one = AsyncMock(return_value=None)

        request = MagicMock()
        request.json = AsyncMock(return_value={
            "event": "test",
            "instance": "unknown-instance"
        })

        with patch('api.routes.whatsapp.database', mock_database):
            result = await whatsapp_webhook(request)

            assert result["status"] == "ignored"
            assert result["reason"] == "instance_not_found"

    async def test_webhook_connection_update_open(
        self, mock_database, mock_instance, mock_redis
    ):
        from api.routes.whatsapp import whatsapp_webhook

        mock_database.fetch_one = AsyncMock(return_value=mock_instance)

        request = MagicMock()
        request.json = AsyncMock(return_value={
            "event": "connection.update",
            "instance": "test-instance",
            "data": {"state": "open"}
        })

        with patch('api.routes.whatsapp.database', mock_database):
            result = await whatsapp_webhook(request)

            assert result["status"] == "processed"
            assert result["event"] == "connection.update"
            assert result["new_status"] == "connected"

    async def test_webhook_connection_update_close(
        self, mock_database, mock_instance, mock_redis
    ):
        from api.routes.whatsapp import whatsapp_webhook

        mock_database.fetch_one = AsyncMock(return_value=mock_instance)

        request = MagicMock()
        request.json = AsyncMock(return_value={
            "event": "connection.update",
            "instance": "test-instance",
            "data": {"state": "close"}
        })

        with patch('api.routes.whatsapp.database', mock_database), \
             patch('api.routes.whatsapp._schedule_reconnection', new_callable=AsyncMock):
            result = await whatsapp_webhook(request)

            assert result["new_status"] == "disconnected"

    async def test_webhook_qrcode_updated(
        self, mock_database, mock_instance, mock_redis
    ):
        from api.routes.whatsapp import whatsapp_webhook

        mock_database.fetch_one = AsyncMock(return_value=mock_instance)

        request = MagicMock()
        request.json = AsyncMock(return_value={
            "event": "qrcode.updated",
            "instance": "test-instance",
            "data": {"qrcode": {"base64": "qr_data_here"}}
        })

        with patch('api.routes.whatsapp.database', mock_database), \
             patch('shared.redis.get_redis', new_callable=AsyncMock, return_value=mock_redis):
            result = await whatsapp_webhook(request)

            assert result["status"] == "processed"
            assert result["event"] == "qrcode.updated"

    async def test_webhook_messages_upsert_conversation(self, mock_database, mock_instance):
        from api.routes.whatsapp import whatsapp_webhook

        mock_database.fetch_one = AsyncMock(return_value=mock_instance)

        request = MagicMock()
        request.json = AsyncMock(return_value={
            "event": "messages.upsert",
            "instance": "test-instance",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": False,
                    "id": "msg123"
                },
                "message": {"conversation": "Hello there!"}
            }
        })

        with patch('api.routes.whatsapp.database', mock_database):
            result = await whatsapp_webhook(request)

            assert result["status"] == "processed"
            mock_database.execute.assert_called()

    async def test_webhook_messages_upsert_extended_text(self, mock_database, mock_instance):
        from api.routes.whatsapp import whatsapp_webhook

        mock_database.fetch_one = AsyncMock(return_value=mock_instance)

        request = MagicMock()
        request.json = AsyncMock(return_value={
            "event": "messages.upsert",
            "instance": "test-instance",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": True,
                    "id": "msg456"
                },
                "message": {"extendedTextMessage": {"text": "Extended message"}}
            }
        })

        with patch('api.routes.whatsapp.database', mock_database):
            result = await whatsapp_webhook(request)

            assert result["status"] == "processed"


# =============================================================================
# TEST SCHEDULE RECONNECTION
# =============================================================================

class TestScheduleReconnection:
    """Testa agendamento de reconexão."""

    async def test_schedule_reconnection_first_attempt(self, mock_redis):
        from api.routes.whatsapp import _schedule_reconnection

        mock_redis.get = AsyncMock(return_value=None)

        with patch('shared.redis.get_redis', new_callable=AsyncMock, return_value=mock_redis):
            await _schedule_reconnection("test-instance", "user-123")

            mock_redis.set.assert_called()
            mock_redis.zadd.assert_called()

    async def test_schedule_reconnection_max_attempts(self, mock_redis):
        from api.routes.whatsapp import _schedule_reconnection

        mock_redis.get = AsyncMock(return_value=json.dumps({"attempts": 5}))

        with patch('shared.redis.get_redis', new_callable=AsyncMock, return_value=mock_redis):
            await _schedule_reconnection("test-instance", "user-123")

            # Should not schedule more reconnections
            mock_redis.zadd.assert_not_called()

    async def test_schedule_reconnection_increment_attempts(self, mock_redis):
        from api.routes.whatsapp import _schedule_reconnection

        mock_redis.get = AsyncMock(return_value=json.dumps({"attempts": 2}))

        with patch('shared.redis.get_redis', new_callable=AsyncMock, return_value=mock_redis):
            await _schedule_reconnection("test-instance", "user-123")

            # Should increment and save
            mock_redis.set.assert_called()
            call_args = mock_redis.set.call_args
            saved_data = json.loads(call_args[0][1])
            assert saved_data["attempts"] == 3


# =============================================================================
# TEST GET INSTANCE STATUS
# =============================================================================

class TestGetInstanceStatus:
    """Testa obtenção de status de instância."""

    async def test_get_instance_status_success(
        self, mock_database, mock_instance, mock_redis, mock_user
    ):
        from api.routes.whatsapp import get_instance_status

        mock_instance.user_id = mock_user["id"]
        mock_database.fetch_one = AsyncMock(return_value=mock_instance)

        with patch('api.routes.whatsapp.database', mock_database), \
             patch('shared.redis.get_redis', new_callable=AsyncMock, return_value=mock_redis):
            result = await get_instance_status("test-instance", mock_user)

            assert result["instance_name"] == "test-instance"
            assert result["status"] == "connected"

    async def test_get_instance_status_not_found(self, mock_database, mock_user):
        from api.routes.whatsapp import get_instance_status

        mock_database.fetch_one = AsyncMock(return_value=None)

        with patch('api.routes.whatsapp.database', mock_database):
            with pytest.raises(HTTPException) as exc:
                await get_instance_status("unknown-instance", mock_user)

            assert exc.value.status_code == 404

    async def test_get_instance_status_not_authorized(
        self, mock_database, mock_instance, mock_user
    ):
        from api.routes.whatsapp import get_instance_status

        # Instance belongs to different user
        mock_instance.user_id = uuid.uuid4()
        mock_database.fetch_one = AsyncMock(return_value=mock_instance)

        with patch('api.routes.whatsapp.database', mock_database):
            with pytest.raises(HTTPException) as exc:
                await get_instance_status("test-instance", mock_user)

            assert exc.value.status_code == 403

    async def test_get_instance_status_with_qrcode(
        self, mock_database, mock_instance, mock_redis, mock_user
    ):
        from api.routes.whatsapp import get_instance_status

        mock_instance.user_id = mock_user["id"]
        mock_instance.status = "awaiting_scan"
        mock_database.fetch_one = AsyncMock(return_value=mock_instance)
        mock_redis.get = AsyncMock(side_effect=["qr_code_data", None])

        with patch('api.routes.whatsapp.database', mock_database), \
             patch('shared.redis.get_redis', new_callable=AsyncMock, return_value=mock_redis):
            result = await get_instance_status("test-instance", mock_user)

            assert result["qr_code"] == "qr_code_data"


# =============================================================================
# TEST FORCE RECONNECT
# =============================================================================

class TestForceReconnect:
    """Testa reconexão forçada."""

    async def test_force_reconnect_success(
        self, mock_database, mock_instance, mock_hub, mock_user
    ):
        from api.routes.whatsapp import force_reconnect

        mock_instance.user_id = mock_user["id"]
        mock_database.fetch_one = AsyncMock(return_value=mock_instance)

        with patch('api.routes.whatsapp.database', mock_database), \
             patch('api.routes.whatsapp.get_hub', return_value=mock_hub):
            result = await force_reconnect("test-instance", mock_user)

            assert result["status"] == "reconnecting"
            assert result["qr_code"] == "qr_code_base64_data"

    async def test_force_reconnect_not_found(self, mock_database, mock_user):
        from api.routes.whatsapp import force_reconnect

        mock_database.fetch_one = AsyncMock(return_value=None)

        with patch('api.routes.whatsapp.database', mock_database):
            with pytest.raises(HTTPException) as exc:
                await force_reconnect("unknown-instance", mock_user)

            assert exc.value.status_code == 404

    async def test_force_reconnect_not_authorized(
        self, mock_database, mock_instance, mock_user
    ):
        from api.routes.whatsapp import force_reconnect

        mock_instance.user_id = uuid.uuid4()  # Different user
        mock_database.fetch_one = AsyncMock(return_value=mock_instance)

        with patch('api.routes.whatsapp.database', mock_database):
            with pytest.raises(HTTPException) as exc:
                await force_reconnect("test-instance", mock_user)

            assert exc.value.status_code == 403

    async def test_force_reconnect_hub_error(
        self, mock_database, mock_instance, mock_hub, mock_user
    ):
        from api.routes.whatsapp import force_reconnect

        mock_instance.user_id = mock_user["id"]
        mock_database.fetch_one = AsyncMock(return_value=mock_instance)
        mock_hub.get_qr_code = AsyncMock(side_effect=Exception("Hub error"))

        with patch('api.routes.whatsapp.database', mock_database), \
             patch('api.routes.whatsapp.get_hub', return_value=mock_hub):
            with pytest.raises(HTTPException) as exc:
                await force_reconnect("test-instance", mock_user)

            assert exc.value.status_code == 400


# =============================================================================
# TEST LIST MESSAGES
# =============================================================================

class TestListMessages:
    """Testa listagem de mensagens."""

    async def test_list_messages_success(self, mock_database, mock_instance, mock_user):
        from api.routes.whatsapp import list_messages

        mock_instance.user_id = mock_user["id"]
        mock_database.fetch_one = AsyncMock(return_value=mock_instance)
        mock_database.fetch_all = AsyncMock(return_value=[
            {"id": "msg1", "content": "Hello"},
            {"id": "msg2", "content": "World"}
        ])

        with patch('api.routes.whatsapp.database', mock_database):
            result = await list_messages("test-instance", 50, 0, mock_user)

            assert len(result) == 2

    async def test_list_messages_not_found(self, mock_database, mock_user):
        from api.routes.whatsapp import list_messages

        mock_database.fetch_one = AsyncMock(return_value=None)

        with patch('api.routes.whatsapp.database', mock_database):
            with pytest.raises(HTTPException) as exc:
                await list_messages("unknown-instance", 50, 0, mock_user)

            assert exc.value.status_code == 404

    async def test_list_messages_not_authorized(
        self, mock_database, mock_instance, mock_user
    ):
        from api.routes.whatsapp import list_messages

        mock_instance.user_id = uuid.uuid4()  # Different user
        mock_database.fetch_one = AsyncMock(return_value=mock_instance)

        with patch('api.routes.whatsapp.database', mock_database):
            with pytest.raises(HTTPException) as exc:
                await list_messages("test-instance", 50, 0, mock_user)

            assert exc.value.status_code == 403

    async def test_list_messages_admin_access(
        self, mock_database, mock_instance, mock_admin_user
    ):
        from api.routes.whatsapp import list_messages

        mock_instance.user_id = uuid.uuid4()  # Different user but admin can access
        mock_database.fetch_one = AsyncMock(return_value=mock_instance)
        mock_database.fetch_all = AsyncMock(return_value=[])

        with patch('api.routes.whatsapp.database', mock_database):
            result = await list_messages("test-instance", 50, 0, mock_admin_user)

            assert result == []


# =============================================================================
# TEST ROUTER
# =============================================================================

class TestRouter:
    """Testa configuração do router."""

    def test_router_exists(self):
        from api.routes.whatsapp import router
        assert router is not None

    def test_router_has_endpoints(self):
        from api.routes.whatsapp import router

        routes = [r.path for r in router.routes]
        assert "/instances" in routes
        assert "/messages/text" in routes
        assert "/webhook" in routes
