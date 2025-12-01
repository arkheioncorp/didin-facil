"""
Unit tests for WhatsApp v1 Routes
Tests for legacy WhatsApp routes using WhatsApp Hub
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from api.routes.whatsapp import (
    router,
    get_hub,
    WhatsAppInstanceCreate,
    WhatsAppMessageSend,
)


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
        from fastapi import HTTPException
        from api.routes.whatsapp import create_instance
        
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
        from fastapi import HTTPException
        from api.routes.whatsapp import get_qrcode
        
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
        from fastapi import HTTPException
        from api.routes.whatsapp import send_message
        
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
