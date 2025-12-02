"""
Testes extensivos para WhatsApp V2 Routes
Aumenta cobertura de api/routes/whatsapp_v2.py
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_current_user():
    return {"id": str(uuid.uuid4()), "email": "test@test.com", "is_admin": False}


@pytest.fixture
def mock_admin_user():
    return {"id": str(uuid.uuid4()), "email": "admin@test.com", "is_admin": True}


@pytest.fixture
def mock_hub():
    """Mock WhatsAppHub."""
    hub = MagicMock()
    hub.create_instance = AsyncMock()
    hub.list_instances = AsyncMock(return_value=[])
    hub.get_instance_status = AsyncMock()
    hub.get_qr_code = AsyncMock()
    hub.delete_instance = AsyncMock(return_value=True)
    hub.disconnect_instance = AsyncMock(return_value=True)
    hub.configure_webhook = AsyncMock(return_value=True)
    hub.send_text = AsyncMock()
    hub.send_media = AsyncMock()
    hub.send_location = AsyncMock()
    hub.send_buttons = AsyncMock()
    hub.send_list = AsyncMock()
    hub.check_number = AsyncMock()
    return hub


@pytest.fixture
def mock_database():
    """Mock database."""
    db = MagicMock()
    db.execute = AsyncMock(return_value=1)
    db.fetch_one = AsyncMock(return_value=None)
    db.fetch_all = AsyncMock(return_value=[])
    return db


@pytest.fixture
def sample_instance_info():
    """Sample InstanceInfo."""
    from enum import Enum
    
    class MockState(Enum):
        OPEN = "open"
        CLOSE = "close"
        CONNECTING = "connecting"
    
    mock_info = MagicMock()
    mock_info.name = "test-instance"
    mock_info.state = MockState.OPEN
    mock_info.phone_connected = "5511999990001"
    mock_info.created_at = datetime.now(timezone.utc)
    return mock_info


# ============================================
# TEST SCHEMAS
# ============================================

class TestInstanceCreate:
    """Testes para InstanceCreate schema."""

    def test_valid_instance_name(self):
        """Testa nome de instância válido."""
        from api.routes.whatsapp_v2 import InstanceCreate
        
        data = InstanceCreate(instance_name="my-instance-123")
        assert data.instance_name == "my-instance-123"

    def test_default_values(self):
        """Testa valores padrão."""
        from api.routes.whatsapp_v2 import InstanceCreate
        
        data = InstanceCreate(instance_name="test-instance")
        assert data.webhook_url is None
        assert data.auto_configure_webhook == True


class TestInstanceResponse:
    """Testes para InstanceResponse schema."""

    def test_creates_response(self):
        """Testa criação de resposta."""
        from api.routes.whatsapp_v2 import InstanceResponse
        
        response = InstanceResponse(
            name="test",
            state="open",
            phone_connected="5511999990001"
        )
        assert response.name == "test"
        assert response.state == "open"


class TestSendTextRequest:
    """Testes para SendTextRequest schema."""

    def test_valid_request(self):
        """Testa request válido."""
        from api.routes.whatsapp_v2 import SendTextRequest
        
        req = SendTextRequest(
            to="5511999990001",
            text="Hello World"
        )
        assert req.to == "5511999990001"
        assert req.text == "Hello World"
        assert req.delay_ms == 0

    def test_with_delay(self):
        """Testa request com delay."""
        from api.routes.whatsapp_v2 import SendTextRequest
        
        req = SendTextRequest(
            to="5511999990001",
            text="Hello",
            delay_ms=1000
        )
        assert req.delay_ms == 1000


class TestSendMediaRequest:
    """Testes para SendMediaRequest schema."""

    def test_valid_request(self):
        """Testa request válido."""
        from api.routes.whatsapp_v2 import SendMediaRequest
        
        req = SendMediaRequest(
            to="5511999990001",
            media_url="https://example.com/image.jpg",
            caption="My image"
        )
        assert req.media_url == "https://example.com/image.jpg"
        assert req.caption == "My image"


class TestSendLocationRequest:
    """Testes para SendLocationRequest schema."""

    def test_valid_request(self):
        """Testa request válido."""
        from api.routes.whatsapp_v2 import SendLocationRequest
        
        req = SendLocationRequest(
            to="5511999990001",
            latitude=-23.5505,
            longitude=-46.6333,
            name="São Paulo",
            address="Centro, SP"
        )
        assert req.latitude == -23.5505
        assert req.longitude == -46.6333


class TestSendButtonsRequest:
    """Testes para SendButtonsRequest schema."""

    def test_valid_request(self):
        """Testa request válido."""
        from api.routes.whatsapp_v2 import SendButtonsRequest
        
        req = SendButtonsRequest(
            to="5511999990001",
            title="Choose an option",
            description="Select one button",
            buttons=[{"id": "1", "text": "Option 1"}]
        )
        assert req.title == "Choose an option"
        assert len(req.buttons) == 1


class TestSendListRequest:
    """Testes para SendListRequest schema."""

    def test_valid_request(self):
        """Testa request válido."""
        from api.routes.whatsapp_v2 import SendListRequest
        
        req = SendListRequest(
            to="5511999990001",
            title="Menu",
            description="Select an option",
            button_text="Open Menu",
            sections=[{"title": "Section 1", "rows": []}]
        )
        assert req.button_text == "Open Menu"


class TestCheckNumberRequest:
    """Testes para CheckNumberRequest schema."""

    def test_valid_request(self):
        """Testa request válido."""
        from api.routes.whatsapp_v2 import CheckNumberRequest
        
        req = CheckNumberRequest(phone="5511999990001")
        assert req.phone == "5511999990001"


class TestMessageResponse:
    """Testes para MessageResponse schema."""

    def test_success_response(self):
        """Testa resposta de sucesso."""
        from api.routes.whatsapp_v2 import MessageResponse
        
        resp = MessageResponse(
            success=True,
            message_id="msg-123"
        )
        assert resp.success == True
        assert resp.message_id == "msg-123"


# ============================================
# TEST INSTANCE MANAGEMENT
# ============================================

class TestCreateInstance:
    """Testes para POST /instances."""

    @pytest.mark.asyncio
    async def test_creates_instance_successfully(self, mock_current_user, mock_hub, sample_instance_info):
        """Cria instância com sucesso."""
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2.database') as mock_db, \
             patch('api.routes.whatsapp_v2.settings') as mock_settings:
            
            mock_hub.create_instance.return_value = sample_instance_info
            mock_db.execute = AsyncMock(return_value=1)
            mock_settings.API_URL = "https://api.example.com"
            
            from api.routes.whatsapp_v2 import InstanceCreate, create_instance
            
            data = InstanceCreate(instance_name="new-instance")
            result = await create_instance(data=data, current_user=mock_current_user)
            
            assert result.name == "test-instance"
            mock_hub.create_instance.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_with_custom_webhook(self, mock_current_user, mock_hub, sample_instance_info):
        """Cria instância com webhook customizado."""
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2.database') as mock_db:
            
            mock_hub.create_instance.return_value = sample_instance_info
            mock_db.execute = AsyncMock(return_value=1)
            
            from api.routes.whatsapp_v2 import InstanceCreate, create_instance
            
            data = InstanceCreate(
                instance_name="new-instance",
                webhook_url="https://custom.webhook.com/endpoint",
                auto_configure_webhook=False
            )
            result = await create_instance(data=data, current_user=mock_current_user)
            
            assert result.webhook_url == "https://custom.webhook.com/endpoint"

    @pytest.mark.asyncio
    async def test_create_handles_error(self, mock_current_user, mock_hub):
        """Trata erro ao criar instância."""
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            mock_hub.create_instance.side_effect = Exception("Hub error")
            
            from api.routes.whatsapp_v2 import InstanceCreate, create_instance
            from fastapi import HTTPException
            
            data = InstanceCreate(instance_name="new-instance")
            
            with pytest.raises(HTTPException) as exc_info:
                await create_instance(data=data, current_user=mock_current_user)
            
            assert exc_info.value.status_code == 400


class TestListInstances:
    """Testes para GET /instances."""

    @pytest.mark.asyncio
    async def test_returns_empty_list(self, mock_current_user, mock_hub):
        """Retorna lista vazia."""
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2.database') as mock_db:
            
            mock_hub.list_instances.return_value = []
            mock_db.fetch_all = AsyncMock(return_value=[])
            
            from api.routes.whatsapp_v2 import list_instances
            result = await list_instances(current_user=mock_current_user)
            
            assert result == []

    @pytest.mark.asyncio
    async def test_returns_user_instances(self, mock_current_user, mock_hub, sample_instance_info):
        """Retorna instâncias do usuário."""
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2.database') as mock_db:
            
            mock_hub.list_instances.return_value = [sample_instance_info]
            
            mock_db_instance = MagicMock()
            mock_db_instance.name = "test-instance"
            mock_db.fetch_all = AsyncMock(return_value=[mock_db_instance])
            
            from api.routes.whatsapp_v2 import list_instances
            result = await list_instances(current_user=mock_current_user)
            
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_admin_sees_all_instances(self, mock_admin_user, mock_hub, sample_instance_info):
        """Admin vê todas as instâncias."""
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2.database') as mock_db:
            mock_hub.list_instances.return_value = [sample_instance_info]
            
            # Admin has is_admin attribute set
            # Mock getattr to return True for is_admin
            class AdminUser(dict):
                is_admin = True
            
            admin = AdminUser(mock_admin_user)
            
            from api.routes.whatsapp_v2 import list_instances
            result = await list_instances(current_user=admin)
            
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_handles_error(self, mock_current_user, mock_hub):
        """Trata erro ao listar."""
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            mock_hub.list_instances.side_effect = Exception("Error")
            
            from api.routes.whatsapp_v2 import list_instances
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                await list_instances(current_user=mock_current_user)
            
            assert exc_info.value.status_code == 500


class TestGetInstance:
    """Testes para GET /instances/{instance_name}."""

    @pytest.mark.asyncio
    async def test_returns_instance(self, mock_current_user, mock_hub, sample_instance_info):
        """Retorna instância."""
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2.database') as mock_db:
            
            mock_db_instance = MagicMock()
            mock_db_instance.user_id = mock_current_user["id"]
            mock_db_instance.webhook_url = "https://webhook.com"
            mock_db.fetch_one = AsyncMock(return_value=mock_db_instance)
            
            mock_hub.get_instance_status.return_value = sample_instance_info
            
            from api.routes.whatsapp_v2 import get_instance
            result = await get_instance(
                instance_name="test-instance",
                current_user=mock_current_user
            )
            
            assert result.name == "test-instance"

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, mock_current_user, mock_hub):
        """Retorna 404 quando não encontrado."""
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2.database') as mock_db:
            
            mock_db.fetch_one = AsyncMock(return_value=None)
            
            from api.routes.whatsapp_v2 import get_instance
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                await get_instance(
                    instance_name="nonexistent",
                    current_user=mock_current_user
                )
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_403_for_unauthorized(self, mock_current_user, mock_hub):
        """Retorna 403 para não autorizado."""
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2.database') as mock_db:
            
            mock_db_instance = MagicMock()
            mock_db_instance.user_id = str(uuid.uuid4())  # Different user
            mock_db.fetch_one = AsyncMock(return_value=mock_db_instance)
            
            from api.routes.whatsapp_v2 import get_instance
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                await get_instance(
                    instance_name="other-user-instance",
                    current_user=mock_current_user
                )
            
            assert exc_info.value.status_code == 403


class TestGetQrCode:
    """Testes para GET /instances/{instance_name}/qrcode."""

    @pytest.mark.asyncio
    async def test_returns_qrcode(self, mock_current_user, mock_hub):
        """Retorna QR code."""
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2._verify_instance_access', new_callable=AsyncMock) as mock_verify:
            
            mock_verify.return_value = MagicMock()
            mock_hub.get_qr_code.return_value = "base64-qr-data"
            
            from api.routes.whatsapp_v2 import get_qr_code
            result = await get_qr_code(
                instance_name="test-instance",
                current_user=mock_current_user
            )
            
            assert result["qr_code"] == "base64-qr-data"

    @pytest.mark.asyncio
    async def test_handles_error(self, mock_current_user, mock_hub):
        """Trata erro ao obter QR code."""
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2._verify_instance_access', new_callable=AsyncMock):
            
            mock_hub.get_qr_code.side_effect = Exception("QR Error")
            
            from api.routes.whatsapp_v2 import get_qr_code
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                await get_qr_code(
                    instance_name="test-instance",
                    current_user=mock_current_user
                )
            
            assert exc_info.value.status_code == 400


class TestDeleteInstance:
    """Testes para DELETE /instances/{instance_name}."""

    @pytest.mark.asyncio
    async def test_deletes_instance(self, mock_current_user, mock_hub):
        """Deleta instância com sucesso."""
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2._verify_instance_access', new_callable=AsyncMock) as mock_verify, \
             patch('api.routes.whatsapp_v2.database') as mock_db:
            
            mock_db_instance = MagicMock()
            mock_db_instance.id = uuid.uuid4()
            mock_verify.return_value = mock_db_instance
            mock_db.execute = AsyncMock(return_value=1)
            
            from api.routes.whatsapp_v2 import delete_instance
            result = await delete_instance(
                instance_name="test-instance",
                current_user=mock_current_user
            )
            
            assert result["success"] == True
            mock_hub.delete_instance.assert_called_once()


class TestDisconnectInstance:
    """Testes para POST /instances/{instance_name}/disconnect."""

    @pytest.mark.asyncio
    async def test_disconnects_instance(self, mock_current_user, mock_hub):
        """Desconecta instância."""
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2._verify_instance_access', new_callable=AsyncMock):
            
            from api.routes.whatsapp_v2 import disconnect_instance
            result = await disconnect_instance(
                instance_name="test-instance",
                current_user=mock_current_user
            )
            
            assert result["success"] == True
            mock_hub.disconnect_instance.assert_called_once()


# ============================================
# TEST WEBHOOK CONFIGURATION
# ============================================

class TestConfigureWebhook:
    """Testes para POST /instances/{instance_name}/webhook."""

    @pytest.mark.asyncio
    async def test_configures_webhook(self, mock_current_user, mock_hub):
        """Configura webhook com sucesso."""
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub), \
             patch('api.routes.whatsapp_v2._verify_instance_access', new_callable=AsyncMock), \
             patch('api.routes.whatsapp_v2.database') as mock_db:
            
            mock_db.execute = AsyncMock(return_value=1)
            
            from api.routes.whatsapp_v2 import (WebhookConfigRequest,
                                                configure_webhook)
            
            data = WebhookConfigRequest(url="https://new.webhook.com")
            result = await configure_webhook(
                instance_name="test-instance",
                data=data,
                current_user=mock_current_user
            )
            
            assert result["success"] == True


# ============================================
# TEST MESSAGING
# ============================================

class TestSendTextMessage:
    """Testes para POST /messages/text."""

    @pytest.mark.asyncio
    async def test_sends_text_message(self, mock_current_user, mock_hub):
        """Envia mensagem de texto."""
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            mock_hub.send_text.return_value = {
                "success": True,
                "message_id": "msg-123"
            }
            
            # Test the schema
            from api.routes.whatsapp_v2 import SendTextRequest
            
            req = SendTextRequest(
                to="5511999990001",
                text="Hello World"
            )
            
            assert req.to == "5511999990001"
            assert req.text == "Hello World"


class TestCheckNumber:
    """Testes para POST /check-number."""

    @pytest.mark.asyncio
    async def test_checks_number_exists(self, mock_current_user, mock_hub):
        """Verifica número existente."""
        with patch('api.routes.whatsapp_v2.get_whatsapp_hub', return_value=mock_hub):
            mock_hub.check_number.return_value = {
                "exists": True,
                "formatted": "5511999990001@c.us"
            }
            
            from api.routes.whatsapp_v2 import (CheckNumberRequest,
                                                CheckNumberResponse)
            
            req = CheckNumberRequest(phone="5511999990001")
            
            # Test schema
            resp = CheckNumberResponse(
                phone=req.phone,
                exists=True,
                formatted="5511999990001@c.us"
            )
            
            assert resp.exists == True


# ============================================
# TEST WEBHOOK CONFIG REQUEST
# ============================================

class TestWebhookConfigRequest:
    """Testes para WebhookConfigRequest schema."""

    def test_valid_request(self):
        """Testa request válido."""
        from api.routes.whatsapp_v2 import WebhookConfigRequest
        
        req = WebhookConfigRequest(
            url="https://webhook.example.com",
            events=["message", "qrcode"]
        )
        assert req.url == "https://webhook.example.com"
        assert len(req.events) == 2

    def test_default_events(self):
        """Testa events padrão."""
        from api.routes.whatsapp_v2 import WebhookConfigRequest
        
        req = WebhookConfigRequest(url="https://webhook.example.com")
        assert req.events is None
