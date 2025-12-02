"""
Tests for WhatsApp Routes (Legacy v1) - Extended Coverage
Tests for WhatsApp instance management and messaging.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class TestModels:
    """Tests for WhatsApp Pydantic models"""

    def test_instance_create(self):
        """Test WhatsAppInstanceCreate model"""
        from api.routes.whatsapp import WhatsAppInstanceCreate

        data = WhatsAppInstanceCreate(
            instance_name="test-instance",
            webhook_url="https://example.com/webhook"
        )

        assert data.instance_name == "test-instance"
        assert data.webhook_url == "https://example.com/webhook"

    def test_instance_create_defaults(self):
        """Test WhatsAppInstanceCreate default values"""
        from api.routes.whatsapp import WhatsAppInstanceCreate

        data = WhatsAppInstanceCreate(instance_name="test")

        assert data.webhook_url is None

    def test_message_send(self):
        """Test WhatsAppMessageSend model"""
        from api.routes.whatsapp import WhatsAppMessageSend

        data = WhatsAppMessageSend(
            instance_name="test-instance",
            to="5511999999999",
            content="Hello!"
        )

        assert data.instance_name == "test-instance"
        assert data.to == "5511999999999"
        assert data.content == "Hello!"


class TestGetHub:
    """Tests for get_hub function"""

    def test_get_hub_singleton(self):
        """Test hub singleton creation"""
        from api.routes.whatsapp import get_hub

        with patch('api.routes.whatsapp.get_whatsapp_hub') as mock_get_hub:
            mock_hub = MagicMock()
            mock_get_hub.return_value = mock_hub

            # Reset singleton
            import api.routes.whatsapp as module
            module._hub = None

            hub1 = get_hub()
            hub2 = get_hub()

            # Should only create once
            assert hub1 is hub2


class TestCreateInstance:
    """Tests for create_instance endpoint"""

    @pytest.mark.asyncio
    async def test_create_instance_success(self):
        """Test successful instance creation"""
        from api.routes.whatsapp import WhatsAppInstanceCreate, create_instance

        data = WhatsAppInstanceCreate(
            instance_name="new-instance",
            webhook_url="https://example.com/webhook"
        )

        mock_user = {"id": "user-123"}

        with patch('api.routes.whatsapp.get_hub') as mock_get_hub:
            mock_hub = MagicMock()
            mock_hub.create_instance = AsyncMock(return_value={"status": "created"})
            mock_get_hub.return_value = mock_hub

            with patch('api.routes.whatsapp.database.execute', new_callable=AsyncMock):
                result = await create_instance(data, mock_user)

        assert result["status"] == "created"

    @pytest.mark.asyncio
    async def test_create_instance_default_webhook(self):
        """Test instance creation with default webhook URL"""
        from api.routes.whatsapp import WhatsAppInstanceCreate, create_instance

        data = WhatsAppInstanceCreate(instance_name="new-instance")
        mock_user = {"id": "user-123"}

        with patch('api.routes.whatsapp.get_hub') as mock_get_hub:
            mock_hub = MagicMock()
            mock_hub.create_instance = AsyncMock(return_value={"status": "created"})
            mock_get_hub.return_value = mock_hub

            with patch('api.routes.whatsapp.database.execute', new_callable=AsyncMock):
                result = await create_instance(data, mock_user)

        assert result["status"] == "created"

    @pytest.mark.asyncio
    async def test_create_instance_error(self):
        """Test instance creation error"""
        from api.routes.whatsapp import WhatsAppInstanceCreate, create_instance

        data = WhatsAppInstanceCreate(instance_name="error-instance")
        mock_user = {"id": "user-123"}

        with patch('api.routes.whatsapp.get_hub') as mock_get_hub:
            mock_hub = MagicMock()
            mock_hub.create_instance = AsyncMock(side_effect=Exception("Hub error"))
            mock_get_hub.return_value = mock_hub

            with pytest.raises(HTTPException) as exc_info:
                await create_instance(data, mock_user)

            assert exc_info.value.status_code == 400


class TestGetQRCode:
    """Tests for get_qrcode endpoint"""

    @pytest.mark.asyncio
    async def test_get_qrcode_success(self):
        """Test successful QR code retrieval"""
        from api.routes.whatsapp import get_qrcode

        mock_user = {"id": "user-123"}

        with patch('api.routes.whatsapp.get_hub') as mock_get_hub:
            mock_hub = MagicMock()
            mock_hub.get_qr_code = AsyncMock(return_value={"base64": "qrcode-data"})
            mock_get_hub.return_value = mock_hub

            result = await get_qrcode("test-instance", mock_user)

        assert result["base64"] == "qrcode-data"

    @pytest.mark.asyncio
    async def test_get_qrcode_error(self):
        """Test QR code retrieval error"""
        from api.routes.whatsapp import get_qrcode

        mock_user = {"id": "user-123"}

        with patch('api.routes.whatsapp.get_hub') as mock_get_hub:
            mock_hub = MagicMock()
            mock_hub.get_qr_code = AsyncMock(side_effect=Exception("Not connected"))
            mock_get_hub.return_value = mock_hub

            with pytest.raises(HTTPException) as exc_info:
                await get_qrcode("error-instance", mock_user)

            assert exc_info.value.status_code == 400


class TestSendMessage:
    """Tests for send_message endpoint"""

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Test successful message sending"""
        from api.routes.whatsapp import WhatsAppMessageSend, send_message

        data = WhatsAppMessageSend(
            instance_name="test-instance",
            to="5511999999999",
            content="Hello!"
        )

        mock_user = {"id": "user-123"}
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()

        with patch('api.routes.whatsapp.get_hub') as mock_get_hub:
            mock_hub = MagicMock()
            mock_hub.send_message = AsyncMock(return_value={"status": "sent"})
            mock_get_hub.return_value = mock_hub

            with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = mock_instance

                with patch('api.routes.whatsapp.database.execute', new_callable=AsyncMock):
                    result = await send_message(data, mock_user)

        assert result["status"] == "sent"

    @pytest.mark.asyncio
    async def test_send_message_no_instance(self):
        """Test message sending without instance in DB"""
        from api.routes.whatsapp import WhatsAppMessageSend, send_message

        data = WhatsAppMessageSend(
            instance_name="nonexistent",
            to="5511999999999",
            content="Hello!"
        )

        mock_user = {"id": "user-123"}

        with patch('api.routes.whatsapp.get_hub') as mock_get_hub:
            mock_hub = MagicMock()
            mock_hub.send_message = AsyncMock(return_value={"status": "sent"})
            mock_get_hub.return_value = mock_hub

            with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = None  # No instance found

                result = await send_message(data, mock_user)

        assert result["status"] == "sent"

    @pytest.mark.asyncio
    async def test_send_message_error(self):
        """Test message sending error"""
        from api.routes.whatsapp import WhatsAppMessageSend, send_message

        data = WhatsAppMessageSend(
            instance_name="test-instance",
            to="5511999999999",
            content="Hello!"
        )

        mock_user = {"id": "user-123"}

        with patch('api.routes.whatsapp.get_hub') as mock_get_hub:
            mock_hub = MagicMock()
            mock_hub.send_message = AsyncMock(side_effect=Exception("Send failed"))
            mock_get_hub.return_value = mock_hub

            with pytest.raises(HTTPException) as exc_info:
                await send_message(data, mock_user)

            assert exc_info.value.status_code == 400


class TestWhatsAppWebhook:
    """Tests for whatsapp_webhook endpoint"""

    @pytest.mark.asyncio
    async def test_webhook_no_instance(self):
        """Test webhook without instance name"""
        from api.routes.whatsapp import whatsapp_webhook

        request = MagicMock()
        request.json = AsyncMock(return_value={
            "event": "messages.upsert",
            "data": {}
        })

        result = await whatsapp_webhook(request)

        assert result["status"] == "ignored"
        assert result["reason"] == "no_instance"

    @pytest.mark.asyncio
    async def test_webhook_instance_not_found(self):
        """Test webhook with non-existent instance"""
        from api.routes.whatsapp import whatsapp_webhook

        request = MagicMock()
        request.json = AsyncMock(return_value={
            "event": "messages.upsert",
            "instance": "nonexistent",
            "data": {}
        })

        with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None

            result = await whatsapp_webhook(request)

        assert result["status"] == "ignored"
        assert result["reason"] == "instance_not_found"

    @pytest.mark.asyncio
    async def test_webhook_connection_update_open(self):
        """Test webhook connection update - open"""
        from api.routes.whatsapp import whatsapp_webhook

        request = MagicMock()
        request.json = AsyncMock(return_value={
            "event": "connection.update",
            "instance": "test-instance",
            "data": {"state": "open"}
        })

        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = "user-123"

        with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_instance

            with patch('api.routes.whatsapp.database.execute', new_callable=AsyncMock):
                result = await whatsapp_webhook(request)

        assert result["status"] == "processed"
        assert result["new_status"] == "connected"

    @pytest.mark.asyncio
    async def test_webhook_connection_update_disconnected(self):
        """Test webhook connection update - close with reconnection"""
        from api.routes.whatsapp import whatsapp_webhook

        request = MagicMock()
        request.json = AsyncMock(return_value={
            "event": "connection.update",
            "instance": "test-instance",
            "data": {"state": "close"}
        })

        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = "user-123"

        with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_instance

            with patch('api.routes.whatsapp.database.execute', new_callable=AsyncMock):
                with patch('api.routes.whatsapp._schedule_reconnection', new_callable=AsyncMock):
                    result = await whatsapp_webhook(request)

        assert result["status"] == "processed"
        assert result["new_status"] == "disconnected"

    @pytest.mark.asyncio
    async def test_webhook_connection_update_unknown_state(self):
        """Test webhook connection update with unknown state"""
        from api.routes.whatsapp import whatsapp_webhook

        request = MagicMock()
        request.json = AsyncMock(return_value={
            "event": "connection.update",
            "instance": "test-instance",
            "data": {"state": "weird_state"}
        })

        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = "user-123"

        with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_instance

            with patch('api.routes.whatsapp.database.execute', new_callable=AsyncMock):
                result = await whatsapp_webhook(request)

        assert result["status"] == "processed"
        assert result["new_status"] == "unknown"

    @pytest.mark.asyncio
    async def test_webhook_qrcode_updated(self):
        """Test webhook QR code updated"""
        from api.routes.whatsapp import whatsapp_webhook

        request = MagicMock()
        request.json = AsyncMock(return_value={
            "event": "qrcode.updated",
            "instance": "test-instance",
            "data": {"qrcode": {"base64": "qrcode-data"}}
        })

        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()

        with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_instance

            with patch('api.routes.whatsapp.database.execute', new_callable=AsyncMock):
                with patch('shared.redis.get_redis', new_callable=AsyncMock) as mock_get_redis:
                    mock_redis = MagicMock()
                    mock_redis.set = AsyncMock()
                    mock_get_redis.return_value = mock_redis

                    result = await whatsapp_webhook(request)

        assert result["status"] == "processed"
        assert result["event"] == "qrcode.updated"

    @pytest.mark.asyncio
    async def test_webhook_messages_upsert_conversation(self):
        """Test webhook message upsert with conversation"""
        from api.routes.whatsapp import whatsapp_webhook

        request = MagicMock()
        request.json = AsyncMock(return_value={
            "event": "messages.upsert",
            "instance": "test-instance",
            "data": {
                "message": {"conversation": "Hello!"},
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": False,
                    "id": "MSG123"
                }
            }
        })

        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()

        with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_instance

            with patch('api.routes.whatsapp.database.execute', new_callable=AsyncMock):
                result = await whatsapp_webhook(request)

        assert result["status"] == "processed"

    @pytest.mark.asyncio
    async def test_webhook_messages_upsert_extended(self):
        """Test webhook message upsert with extended text"""
        from api.routes.whatsapp import whatsapp_webhook

        request = MagicMock()
        request.json = AsyncMock(return_value={
            "event": "messages.upsert",
            "instance": "test-instance",
            "data": {
                "message": {"extendedTextMessage": {"text": "Extended message"}},
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": True,
                    "id": "MSG456"
                }
            }
        })

        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()

        with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_instance

            with patch('api.routes.whatsapp.database.execute', new_callable=AsyncMock):
                result = await whatsapp_webhook(request)

        assert result["status"] == "processed"


class TestScheduleReconnection:
    """Tests for _schedule_reconnection function"""

    @pytest.mark.asyncio
    async def test_schedule_reconnection_first_attempt(self):
        """Test first reconnection attempt"""
        from api.routes.whatsapp import _schedule_reconnection

        with patch('shared.redis.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value=None)  # No previous attempts
            mock_redis.set = AsyncMock()
            mock_redis.zadd = AsyncMock()
            mock_get_redis.return_value = mock_redis

            await _schedule_reconnection("test-instance", "user-123")

            mock_redis.set.assert_called_once()
            mock_redis.zadd.assert_called_once()

    @pytest.mark.asyncio
    async def test_schedule_reconnection_subsequent_attempt(self):
        """Test subsequent reconnection attempt"""
        import json

        from api.routes.whatsapp import _schedule_reconnection

        with patch('shared.redis.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value=json.dumps({"attempts": 2}))
            mock_redis.set = AsyncMock()
            mock_redis.zadd = AsyncMock()
            mock_get_redis.return_value = mock_redis

            await _schedule_reconnection("test-instance", "user-123")

            mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_schedule_reconnection_max_attempts(self):
        """Test max reconnection attempts reached"""
        import json

        from api.routes.whatsapp import _schedule_reconnection

        with patch('shared.redis.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value=json.dumps({"attempts": 5}))  # Max reached
            mock_redis.set = AsyncMock()
            mock_redis.zadd = AsyncMock()
            mock_get_redis.return_value = mock_redis

            await _schedule_reconnection("test-instance", "user-123")

            mock_redis.set.assert_not_called()
            mock_redis.zadd.assert_not_called()


class TestGetInstanceStatus:
    """Tests for get_instance_status endpoint"""

    @pytest.mark.asyncio
    async def test_get_status_success(self):
        """Test successful status retrieval"""
        from api.routes.whatsapp import get_instance_status

        mock_user = {"id": "user-123"}
        mock_instance = MagicMock()
        mock_instance.user_id = "user-123"
        mock_instance.status = "connected"
        mock_instance.updated_at = datetime.now(timezone.utc)

        with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_instance

            with patch('shared.redis.get_redis', new_callable=AsyncMock) as mock_get_redis:
                mock_redis = MagicMock()
                mock_redis.get = AsyncMock(side_effect=[None, None])  # No QR, no reconnect
                mock_get_redis.return_value = mock_redis

                result = await get_instance_status("test-instance", mock_user)

        assert result["status"] == "connected"

    @pytest.mark.asyncio
    async def test_get_status_with_qrcode(self):
        """Test status with QR code"""
        from api.routes.whatsapp import get_instance_status

        mock_user = {"id": "user-123"}
        mock_instance = MagicMock()
        mock_instance.user_id = "user-123"
        mock_instance.status = "awaiting_scan"
        mock_instance.updated_at = datetime.now(timezone.utc)

        with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_instance

            with patch('shared.redis.get_redis', new_callable=AsyncMock) as mock_get_redis:
                mock_redis = MagicMock()
                mock_redis.get = AsyncMock(side_effect=["qrcode-data", None])
                mock_get_redis.return_value = mock_redis

                result = await get_instance_status("test-instance", mock_user)

        assert result["qr_code"] == "qrcode-data"

    @pytest.mark.asyncio
    async def test_get_status_not_found(self):
        """Test status for non-existent instance"""
        from api.routes.whatsapp import get_instance_status

        mock_user = {"id": "user-123"}

        with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await get_instance_status("nonexistent", mock_user)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_status_not_authorized(self):
        """Test status for instance owned by another user"""
        from api.routes.whatsapp import get_instance_status

        mock_user = {"id": "user-123"}
        mock_instance = MagicMock()
        mock_instance.user_id = "different-user"

        with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_instance

            with pytest.raises(HTTPException) as exc_info:
                await get_instance_status("test-instance", mock_user)

            assert exc_info.value.status_code == 403


class TestForceReconnect:
    """Tests for force_reconnect endpoint"""

    @pytest.mark.asyncio
    async def test_force_reconnect_success(self):
        """Test successful force reconnect"""
        from api.routes.whatsapp import force_reconnect

        mock_user = {"id": "user-123"}
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = "user-123"

        with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_instance

            with patch('api.routes.whatsapp.get_hub') as mock_get_hub:
                mock_hub = MagicMock()
                mock_hub.get_qr_code = AsyncMock(return_value={"base64": "qrcode"})
                mock_get_hub.return_value = mock_hub

                with patch('api.routes.whatsapp.database.execute', new_callable=AsyncMock):
                    result = await force_reconnect("test-instance", mock_user)

        assert result["status"] == "reconnecting"

    @pytest.mark.asyncio
    async def test_force_reconnect_not_found(self):
        """Test force reconnect for non-existent instance"""
        from api.routes.whatsapp import force_reconnect

        mock_user = {"id": "user-123"}

        with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await force_reconnect("nonexistent", mock_user)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_force_reconnect_not_authorized(self):
        """Test force reconnect for unauthorized user"""
        from api.routes.whatsapp import force_reconnect

        mock_user = {"id": "user-123"}
        mock_instance = MagicMock()
        mock_instance.user_id = "different-user"

        with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_instance

            with pytest.raises(HTTPException) as exc_info:
                await force_reconnect("test-instance", mock_user)

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_force_reconnect_error(self):
        """Test force reconnect error"""
        from api.routes.whatsapp import force_reconnect

        mock_user = {"id": "user-123"}
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = "user-123"

        with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_instance

            with patch('api.routes.whatsapp.get_hub') as mock_get_hub:
                mock_hub = MagicMock()
                mock_hub.get_qr_code = AsyncMock(side_effect=Exception("Reconnect failed"))
                mock_get_hub.return_value = mock_hub

                with pytest.raises(HTTPException) as exc_info:
                    await force_reconnect("test-instance", mock_user)

                assert exc_info.value.status_code == 400


class TestListMessages:
    """Tests for list_messages endpoint"""

    @pytest.mark.asyncio
    async def test_list_messages_success(self):
        """Test successful message listing"""
        from api.routes.whatsapp import list_messages

        mock_user = {"id": "user-123", "is_admin": False}
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = "user-123"

        mock_messages = [
            {"id": "msg1", "content": "Hello"},
            {"id": "msg2", "content": "World"}
        ]

        with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_instance

            with patch('api.routes.whatsapp.database.fetch_all', new_callable=AsyncMock) as mock_fetch_all:
                mock_fetch_all.return_value = mock_messages

                result = await list_messages("test-instance", 50, 0, mock_user)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_messages_not_found(self):
        """Test message listing for non-existent instance"""
        from api.routes.whatsapp import list_messages

        mock_user = {"id": "user-123", "is_admin": False}

        with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await list_messages("nonexistent", 50, 0, mock_user)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_list_messages_admin_access(self):
        """Test admin can access any instance messages"""
        from api.routes.whatsapp import list_messages

        mock_user = MagicMock()
        mock_user.__getitem__ = MagicMock(side_effect=lambda k: "admin-user" if k == "id" else None)
        mock_user.is_admin = True
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = "different-user"  # Different owner

        with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_instance

            with patch('api.routes.whatsapp.database.fetch_all', new_callable=AsyncMock) as mock_fetch_all:
                mock_fetch_all.return_value = []

                result = await list_messages("test-instance", 50, 0, mock_user)

        assert result == []

    @pytest.mark.asyncio
    async def test_list_messages_not_authorized(self):
        """Test non-admin cannot access other user's messages"""
        from api.routes.whatsapp import list_messages

        mock_user = MagicMock()
        mock_user.__getitem__ = MagicMock(side_effect=lambda k: "user-123" if k == "id" else None)
        mock_user.is_admin = False
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = "different-user"

        with patch('api.routes.whatsapp.database.fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_instance

            with pytest.raises(HTTPException) as exc_info:
                await list_messages("test-instance", 50, 0, mock_user)

            assert exc_info.value.status_code == 403


class TestRouterConfiguration:
    """Tests for router configuration"""

    def test_router_exists(self):
        """Test router exists"""
        from api.routes.whatsapp import router

        assert router is not None
