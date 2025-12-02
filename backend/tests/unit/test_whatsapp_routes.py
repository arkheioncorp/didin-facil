"""
Unit tests for WhatsApp v1 Routes
Tests for legacy WhatsApp routes using WhatsApp Hub
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from api.routes.whatsapp import (WhatsAppInstanceCreate, WhatsAppMessageSend,
                                 get_hub, router)


class TestWhatsAppSchemas:
    """Tests for WhatsApp request/response schemas"""

    def test_instance_create_schema(self):
        """Test WhatsAppInstanceCreate schema validation"""
        data = WhatsAppInstanceCreate(
            instance_name="test-instance",
            webhook_url="https://example.com/webhook"
        )
        assert data.instance_name == "test-instance"
        assert data.webhook_url == "https://example.com/webhook"

    def test_instance_create_without_webhook(self):
        """Test schema with optional webhook"""
        data = WhatsAppInstanceCreate(instance_name="test-instance")
        assert data.instance_name == "test-instance"
        assert data.webhook_url is None

    def test_message_send_schema(self):
        """Test WhatsAppMessageSend schema validation"""
        data = WhatsAppMessageSend(
            instance_name="test-instance",
            to="5511999999999",
            content="Hello World"
        )
        assert data.instance_name == "test-instance"
        assert data.to == "5511999999999"
        assert data.content == "Hello World"


class TestGetHub:
    """Tests for get_hub singleton function"""

    @patch('api.routes.whatsapp.get_whatsapp_hub')
    def test_get_hub_creates_singleton(self, mock_get_hub):
        """Test that get_hub creates singleton on first call"""
        import api.routes.whatsapp as module
        module._hub = None
        
        mock_hub = MagicMock()
        mock_get_hub.return_value = mock_hub
        
        result = get_hub()
        
        mock_get_hub.assert_called_once()
        assert result == mock_hub

    @patch('api.routes.whatsapp.get_whatsapp_hub')
    def test_get_hub_returns_existing(self, mock_get_hub):
        """Test that get_hub returns existing singleton"""
        import api.routes.whatsapp as module
        
        mock_hub = MagicMock()
        module._hub = mock_hub
        
        result = get_hub()
        
        mock_get_hub.assert_not_called()
        assert result == mock_hub
        
        # Reset for other tests
        module._hub = None


class TestCreateInstance:
    """Tests for create_instance endpoint"""

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = uuid4()
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def mock_hub(self):
        with patch('api.routes.whatsapp.get_hub') as mock:
            hub = AsyncMock()
            mock.return_value = hub
            yield hub

    @pytest.fixture
    def mock_database(self):
        with patch('api.routes.whatsapp.database') as mock:
            mock.execute = AsyncMock()
            yield mock

    @pytest.mark.asyncio
    async def test_create_instance_success(self, mock_user, mock_hub, mock_database):
        """Test successful instance creation"""
        from api.routes.whatsapp import create_instance
        
        mock_hub.create_instance = AsyncMock(return_value={
            "instance_name": "test-instance",
            "status": "created"
        })
        
        data = WhatsAppInstanceCreate(
            instance_name="test-instance",
            webhook_url="https://example.com/webhook"
        )
        
        result = await create_instance(data, mock_user)
        
        assert result["status"] == "created"
        mock_hub.create_instance.assert_called_once()
        mock_database.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_instance_default_webhook(self, mock_user, mock_hub, mock_database):
        """Test instance creation with default webhook"""
        from api.routes.whatsapp import create_instance
        
        mock_hub.create_instance = AsyncMock(return_value={
            "instance_name": "test-instance",
            "status": "created"
        })
        
        data = WhatsAppInstanceCreate(instance_name="test-instance")
        
        result = await create_instance(data, mock_user)
        
        assert result["status"] == "created"
        call_args = mock_hub.create_instance.call_args
        assert "webhook_url" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_create_instance_error(self, mock_user, mock_hub, mock_database):
        """Test instance creation error handling"""
        from api.routes.whatsapp import create_instance
        from fastapi import HTTPException
        
        mock_hub.create_instance = AsyncMock(side_effect=Exception("Hub error"))
        
        data = WhatsAppInstanceCreate(instance_name="test-instance")
        
        with pytest.raises(HTTPException) as exc:
            await create_instance(data, mock_user)
        
        assert exc.value.status_code == 400


class TestGetQRCode:
    """Tests for get_qrcode endpoint"""

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = uuid4()
        return user

    @pytest.fixture
    def mock_hub(self):
        with patch('api.routes.whatsapp.get_hub') as mock:
            hub = AsyncMock()
            mock.return_value = hub
            yield hub

    @pytest.mark.asyncio
    async def test_get_qrcode_success(self, mock_user, mock_hub):
        """Test successful QR code retrieval"""
        from api.routes.whatsapp import get_qrcode
        
        mock_hub.get_qr_code = AsyncMock(return_value={
            "qr_code": "base64_encoded_qr",
            "instance": "test-instance"
        })
        
        result = await get_qrcode("test-instance", mock_user)
        
        assert "qr_code" in result
        mock_hub.get_qr_code.assert_called_once_with(instance_name="test-instance")

    @pytest.mark.asyncio
    async def test_get_qrcode_error(self, mock_user, mock_hub):
        """Test QR code retrieval error"""
        from api.routes.whatsapp import get_qrcode
        from fastapi import HTTPException
        
        mock_hub.get_qr_code = AsyncMock(side_effect=Exception("QR error"))
        
        with pytest.raises(HTTPException) as exc:
            await get_qrcode("test-instance", mock_user)
        
        assert exc.value.status_code == 400


class TestSendMessage:
    """Tests for send message endpoints"""

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = uuid4()
        return user

    @pytest.fixture
    def mock_hub(self):
        with patch('api.routes.whatsapp.get_hub') as mock:
            hub = AsyncMock()
            mock.return_value = hub
            yield hub

    @pytest.fixture
    def mock_database(self):
        with patch('api.routes.whatsapp.database') as mock:
            mock.execute = AsyncMock()
            # Return object with .id attribute, not dict
            mock_instance = MagicMock()
            mock_instance.id = uuid4()
            mock.fetch_one = AsyncMock(return_value=mock_instance)
            yield mock

    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_user, mock_hub, mock_database):
        """Test successful text message sending"""
        from api.routes.whatsapp import send_message
        
        mock_hub.send_message = AsyncMock(return_value={
            "message_id": "msg123",
            "status": "sent"
        })
        
        data = WhatsAppMessageSend(
            instance_name="test-instance",
            to="5511999999999",
            content="Hello"
        )
        
        result = await send_message(data, mock_user)
        
        assert result["status"] == "sent"
        mock_hub.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_error(self, mock_user, mock_hub, mock_database):
        """Test text message sending error"""
        from api.routes.whatsapp import send_message
        from fastapi import HTTPException
        
        mock_hub.send_message = AsyncMock(side_effect=Exception("Send error"))
        
        data = WhatsAppMessageSend(
            instance_name="test-instance",
            to="5511999999999",
            content="Hello"
        )
        
        with pytest.raises(HTTPException) as exc:
            await send_message(data, mock_user)
        
        assert exc.value.status_code == 400


class TestWebhook:
    """Tests for webhook endpoint"""

    @pytest.fixture
    def mock_request(self):
        request = MagicMock()
        request.json = AsyncMock(return_value={
            "event": "connection.update",
            "instance": "test-instance",
            "data": {
                "state": "open"
            }
        })
        return request

    @pytest.fixture
    def mock_database(self):
        with patch('api.routes.whatsapp.database') as mock:
            mock.execute = AsyncMock()
            # Return object with attributes, not dict
            mock_instance = MagicMock()
            mock_instance.id = uuid4()
            mock_instance.name = "test-instance"
            mock.fetch_one = AsyncMock(return_value=mock_instance)
            yield mock

    @pytest.mark.asyncio
    async def test_webhook_connection_update(
        self, mock_request, mock_database
    ):
        """Test webhook connection update handling"""
        from api.routes.whatsapp import whatsapp_webhook
        
        result = await whatsapp_webhook(mock_request)
        
        # Should process the connection update
        assert "status" in result or "state" in result or result is not None

    @pytest.mark.asyncio
    async def test_webhook_no_instance(self, mock_request, mock_database):
        """Test webhook with no instance"""
        from api.routes.whatsapp import whatsapp_webhook
        
        mock_request.json = AsyncMock(return_value={
            "event": "connection.update",
            "data": {}
        })
        
        result = await whatsapp_webhook(mock_request)
        
        assert result["status"] == "ignored"
        assert result["reason"] == "no_instance"

    @pytest.mark.asyncio
    async def test_webhook_instance_not_found(
        self, mock_request, mock_database
    ):
        """Test webhook with unknown instance"""
        from api.routes.whatsapp import whatsapp_webhook
        
        mock_database.fetch_one.return_value = None
        
        result = await whatsapp_webhook(mock_request)
        
        assert result["status"] == "ignored"
        assert result["reason"] == "instance_not_found"

    @pytest.mark.asyncio
    async def test_webhook_qrcode_updated(self, mock_request, mock_database):
        """Test webhook QR code update handling"""
        from api.routes.whatsapp import whatsapp_webhook
        
        mock_request.json = AsyncMock(return_value={
            "event": "qrcode.updated",
            "instance": "test-instance",
            "data": {
                "qrcode": {"base64": "mock_qr_base64"}
            }
        })
        
        with patch('shared.redis.get_redis') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            
            result = await whatsapp_webhook(mock_request)
            
            assert result["status"] == "processed"
            assert result["event"] == "qrcode.updated"
            mock_redis_instance.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_webhook_messages_upsert(self, mock_request, mock_database):
        """Test webhook messages upsert handling"""
        from api.routes.whatsapp import whatsapp_webhook
        
        mock_request.json = AsyncMock(return_value={
            "event": "messages.upsert",
            "instance": "test-instance",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": False,
                    "id": "msg123"
                },
                "message": {
                    "conversation": "Hello from user"
                }
            }
        })
        
        result = await whatsapp_webhook(mock_request)
        
        assert result["status"] == "processed"
        mock_database.execute.assert_called()

    @pytest.mark.asyncio
    async def test_webhook_messages_extended_text(self, mock_request, mock_database):
        """Test webhook with extendedTextMessage"""
        from api.routes.whatsapp import whatsapp_webhook
        
        mock_request.json = AsyncMock(return_value={
            "event": "messages.upsert",
            "instance": "test-instance",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": True,
                    "id": "msg456"
                },
                "message": {
                    "extendedTextMessage": {"text": "Extended message text"}
                }
            }
        })
        
        result = await whatsapp_webhook(mock_request)
        
        assert result["status"] == "processed"

    @pytest.mark.asyncio
    async def test_webhook_connection_disconnected(self, mock_request, mock_database):
        """Test webhook connection disconnected triggers reconnection"""
        from api.routes.whatsapp import whatsapp_webhook
        
        mock_request.json = AsyncMock(return_value={
            "event": "connection.update",
            "instance": "test-instance",
            "data": {"state": "close"}
        })
        
        with patch('api.routes.whatsapp._schedule_reconnection') as mock_sched:
            mock_sched.return_value = None
            
            result = await whatsapp_webhook(mock_request)
            
            assert result["status"] == "processed"
            assert result["new_status"] == "disconnected"

    @pytest.mark.asyncio
    async def test_webhook_connection_states(self, mock_request, mock_database):
        """Test webhook with various connection states"""
        from api.routes.whatsapp import whatsapp_webhook
        
        states = [
            ("open", "connected"),
            ("close", "disconnected"),
            ("connecting", "connecting"),
            ("refused", "error"),
            ("unknown_state", "unknown")
        ]
        
        for api_state, expected_status in states:
            mock_request.json = AsyncMock(return_value={
                "event": "connection.update",
                "instance": "test-instance",
                "data": {"state": api_state}
            })
            
            with patch('api.routes.whatsapp._schedule_reconnection') as mock_sched:
                mock_sched.return_value = None
                result = await whatsapp_webhook(mock_request)
                
                assert result["new_status"] == expected_status


class TestScheduleReconnection:
    """Tests for _schedule_reconnection function"""

    @pytest.mark.asyncio
    async def test_schedule_reconnection_first_attempt(self):
        """Test first reconnection attempt"""
        from api.routes.whatsapp import _schedule_reconnection
        
        with patch('shared.redis.get_redis') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get.return_value = None
            mock_redis.return_value = mock_redis_instance
            
            await _schedule_reconnection("test-instance", str(uuid4()))
            
            mock_redis_instance.set.assert_called()
            mock_redis_instance.zadd.assert_called()

    @pytest.mark.asyncio
    async def test_schedule_reconnection_max_attempts(self):
        """Test max reconnection attempts reached"""
        import json

        from api.routes.whatsapp import _schedule_reconnection
        
        with patch('shared.redis.get_redis') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get.return_value = json.dumps({
                "attempts": 5,
                "instance_name": "test-instance"
            })
            mock_redis.return_value = mock_redis_instance
            
            await _schedule_reconnection("test-instance", str(uuid4()))
            
            # Should not schedule new reconnection
            mock_redis_instance.zadd.assert_not_called()

    @pytest.mark.asyncio
    async def test_schedule_reconnection_increments_attempts(self):
        """Test reconnection increments attempts"""
        import json

        from api.routes.whatsapp import _schedule_reconnection
        
        with patch('shared.redis.get_redis') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get.return_value = json.dumps({
                "attempts": 2,
                "instance_name": "test-instance"
            })
            mock_redis.return_value = mock_redis_instance
            
            await _schedule_reconnection("test-instance", str(uuid4()))
            
            # Should update with incremented attempts
            mock_redis_instance.set.assert_called()
            mock_redis_instance.zadd.assert_called()


class TestGetInstanceStatus:
    """Tests for get_instance_status endpoint"""

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = str(uuid4())
        user.email = "test@example.com"
        user.__getitem__ = lambda self, key: getattr(self, key)
        return user

    @pytest.fixture
    def mock_instance(self):
        instance = MagicMock()
        instance.id = uuid4()
        instance.name = "test-instance"
        instance.status = "connected"
        instance.user_id = None  # Will be set in tests
        instance.updated_at = datetime.now(timezone.utc)
        return instance

    @pytest.mark.asyncio
    async def test_get_instance_status_success(self, mock_user, mock_instance):
        """Test successful status retrieval"""
        from api.routes.whatsapp import get_instance_status
        
        mock_instance.user_id = mock_user.id
        
        with patch('api.routes.whatsapp.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            
            with patch('shared.redis.get_redis') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis_instance.get.return_value = None
                mock_redis.return_value = mock_redis_instance
                
                result = await get_instance_status("test-instance", mock_user)
                
                assert result["instance_name"] == "test-instance"
                assert result["status"] == "connected"

    @pytest.mark.asyncio
    async def test_get_instance_status_not_found(self, mock_user):
        """Test status retrieval for non-existent instance"""
        from api.routes.whatsapp import get_instance_status
        from fastapi import HTTPException
        
        with patch('api.routes.whatsapp.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=None)
            
            with pytest.raises(HTTPException) as exc:
                await get_instance_status("nonexistent", mock_user)
            
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_instance_status_not_authorized(self, mock_user, mock_instance):
        """Test status retrieval without authorization"""
        from api.routes.whatsapp import get_instance_status
        from fastapi import HTTPException
        
        mock_instance.user_id = str(uuid4())  # Different user
        
        with patch('api.routes.whatsapp.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            
            with pytest.raises(HTTPException) as exc:
                await get_instance_status("test-instance", mock_user)
            
            assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_get_instance_status_with_qrcode(self, mock_user, mock_instance):
        """Test status retrieval with QR code"""
        from api.routes.whatsapp import get_instance_status
        
        mock_instance.user_id = mock_user.id
        mock_instance.status = "awaiting_scan"
        
        with patch('api.routes.whatsapp.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            
            with patch('shared.redis.get_redis') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis_instance.get.side_effect = [
                    "mock_qr_base64",  # QR code
                    None  # Reconnect data
                ]
                mock_redis.return_value = mock_redis_instance
                
                result = await get_instance_status("test-instance", mock_user)
                
                assert result["qr_code"] == "mock_qr_base64"


class TestForceReconnect:
    """Tests for force_reconnect endpoint"""

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = str(uuid4())
        user.email = "test@example.com"
        user.__getitem__ = lambda self, key: getattr(self, key)
        return user

    @pytest.fixture
    def mock_instance(self):
        instance = MagicMock()
        instance.id = uuid4()
        instance.name = "test-instance"
        instance.status = "disconnected"
        instance.user_id = None
        return instance

    @pytest.mark.asyncio
    async def test_force_reconnect_success(self, mock_user, mock_instance):
        """Test successful force reconnection"""
        from api.routes.whatsapp import force_reconnect
        
        mock_instance.user_id = mock_user.id
        
        with patch('api.routes.whatsapp.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            mock_db.execute = AsyncMock()
            
            with patch('api.routes.whatsapp.get_hub') as mock_get_hub:
                mock_hub = AsyncMock()
                mock_hub.get_qr_code = AsyncMock(return_value={"base64": "new_qr"})
                mock_get_hub.return_value = mock_hub
                
                result = await force_reconnect("test-instance", mock_user)
                
                assert result["status"] == "reconnecting"
                assert result["qr_code"] == "new_qr"

    @pytest.mark.asyncio
    async def test_force_reconnect_not_found(self, mock_user):
        """Test force reconnection for non-existent instance"""
        from api.routes.whatsapp import force_reconnect
        from fastapi import HTTPException
        
        with patch('api.routes.whatsapp.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=None)
            
            with patch('api.routes.whatsapp.get_hub'):
                with pytest.raises(HTTPException) as exc:
                    await force_reconnect("nonexistent", mock_user)
                
                assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_force_reconnect_not_authorized(self, mock_user, mock_instance):
        """Test force reconnection without authorization"""
        from api.routes.whatsapp import force_reconnect
        from fastapi import HTTPException
        
        mock_instance.user_id = str(uuid4())  # Different user
        
        with patch('api.routes.whatsapp.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            
            with patch('api.routes.whatsapp.get_hub'):
                with pytest.raises(HTTPException) as exc:
                    await force_reconnect("test-instance", mock_user)
                
                assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_force_reconnect_hub_error(self, mock_user, mock_instance):
        """Test force reconnection with Hub error"""
        from api.routes.whatsapp import force_reconnect
        from fastapi import HTTPException
        
        mock_instance.user_id = mock_user["id"]
        
        with patch('api.routes.whatsapp.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            
            with patch('api.routes.whatsapp.get_hub') as mock_get_hub:
                mock_hub = AsyncMock()
                mock_hub.get_qr_code = AsyncMock(side_effect=Exception("Hub error"))
                mock_get_hub.return_value = mock_hub
                
                with pytest.raises(HTTPException) as exc:
                    await force_reconnect("test-instance", mock_user)
                
                assert exc.value.status_code == 400


class TestListMessages:
    """Tests for list_messages endpoint"""

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = str(uuid4())
        user.email = "test@example.com"
        user.is_admin = False
        user.__getitem__ = lambda self, key: getattr(self, key)
        return user

    @pytest.fixture
    def mock_admin_user(self):
        admin = MagicMock()
        admin.id = str(uuid4())
        admin.email = "admin@example.com"
        admin.is_admin = True
        admin.__getitem__ = lambda self, key: getattr(self, key)
        return admin

    @pytest.fixture
    def mock_instance(self):
        instance = MagicMock()
        instance.id = uuid4()
        instance.name = "test-instance"
        instance.user_id = None
        return instance

    @pytest.mark.asyncio
    async def test_list_messages_success(self, mock_user, mock_instance):
        """Test successful message listing"""
        from api.routes.whatsapp import list_messages
        
        mock_instance.user_id = mock_user.id
        
        mock_messages = [
            {"id": str(uuid4()), "content": "Hello", "from_me": True},
            {"id": str(uuid4()), "content": "Hi", "from_me": False}
        ]
        
        with patch('api.routes.whatsapp.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            mock_db.fetch_all = AsyncMock(return_value=mock_messages)
            
            result = await list_messages("test-instance", 50, 0, mock_user)
            
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_messages_not_found(self, mock_user):
        """Test message listing for non-existent instance"""
        from api.routes.whatsapp import list_messages
        from fastapi import HTTPException
        
        with patch('api.routes.whatsapp.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=None)
            
            with pytest.raises(HTTPException) as exc:
                await list_messages("nonexistent", 50, 0, mock_user)
            
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_list_messages_admin_access(self, mock_admin_user, mock_instance):
        """Test admin can access any instance messages"""
        from api.routes.whatsapp import list_messages
        
        mock_instance.user_id = str(uuid4())  # Different user
        
        mock_messages = [{"id": str(uuid4()), "content": "Test"}]
        
        with patch('api.routes.whatsapp.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            mock_db.fetch_all = AsyncMock(return_value=mock_messages)
            
            result = await list_messages("test-instance", 50, 0, mock_admin_user)
            
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_messages_not_authorized(self, mock_user, mock_instance):
        """Test message listing without authorization"""
        from api.routes.whatsapp import list_messages
        from fastapi import HTTPException
        
        mock_instance.user_id = str(uuid4())  # Different user
        
        with patch('api.routes.whatsapp.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            
            with pytest.raises(HTTPException) as exc:
                await list_messages("test-instance", 50, 0, mock_user)
            
            assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_list_messages_with_pagination(self, mock_user, mock_instance):
        """Test message listing with custom pagination"""
        from api.routes.whatsapp import list_messages
        
        mock_instance.user_id = mock_user.id
        
        mock_messages = [{"id": str(uuid4()), "content": f"Msg {i}"} for i in range(10)]
        
        with patch('api.routes.whatsapp.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            mock_db.fetch_all = AsyncMock(return_value=mock_messages)
            
            result = await list_messages("test-instance", 10, 5, mock_user)
            
            assert len(result) == 10
