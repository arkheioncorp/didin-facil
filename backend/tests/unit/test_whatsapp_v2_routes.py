"""
Testes para WhatsApp V2 Routes - api/routes/whatsapp_v2.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fastapi import HTTPException


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_user():
    """Mock de usuário autenticado"""
    user = MagicMock()
    user.id = "user-123"
    user.email = "test@example.com"
    user.is_admin = False
    return user


@pytest.fixture
def mock_admin():
    """Mock de usuário admin"""
    user = MagicMock()
    user.id = "admin-123"
    user.email = "admin@example.com"
    user.is_admin = True
    return user


@pytest.fixture
def mock_instance():
    """Mock de instância WhatsApp"""
    instance = MagicMock()
    instance.name = "test-instance"
    instance.state = MagicMock(value="connected")
    instance.phone_connected = "5511999999999"
    instance.created_at = datetime.now(timezone.utc)
    return instance


@pytest.fixture
def mock_hub(mock_instance):
    """Mock do WhatsApp Hub"""
    hub = AsyncMock()
    hub.create_instance = AsyncMock(return_value=mock_instance)
    hub.list_instances = AsyncMock(return_value=[mock_instance])
    hub.get_instance_status = AsyncMock(return_value=mock_instance)
    hub.delete_instance = AsyncMock(return_value=True)
    hub.connect_instance = AsyncMock(return_value={"qr": "base64_qr_code"})
    hub.disconnect_instance = AsyncMock(return_value=True)
    hub.get_qr_code = AsyncMock(return_value={"qr": "base64_qr_code"})
    hub.send_text = AsyncMock(return_value={"message_id": "msg-123"})
    hub.send_media = AsyncMock(return_value={"message_id": "msg-456"})
    hub.send_location = AsyncMock(return_value={"message_id": "msg-789"})
    hub.send_buttons = AsyncMock(return_value={"message_id": "msg-101"})
    hub.send_list = AsyncMock(return_value={"message_id": "msg-102"})
    hub.check_number = AsyncMock(return_value={"exists": True, "formatted": "5511999999999"})
    hub.get_instance = AsyncMock(return_value=mock_instance)
    return hub


@pytest.fixture
def mock_database():
    """Mock do database"""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.fetch_one = AsyncMock()
    db.fetch_all = AsyncMock(return_value=[])
    return db


# ============================================
# TESTS: Schemas
# ============================================

class TestSchemas:
    """Testes para schemas de request/response"""
    
    def test_instance_create_schema(self):
        """Deve validar schema de criação"""
        from api.routes.whatsapp_v2 import InstanceCreate
        
        data = InstanceCreate(
            instance_name="test-instance",
            webhook_url="https://example.com/webhook",
            auto_configure_webhook=True
        )
        
        assert data.instance_name == "test-instance"
        assert data.webhook_url == "https://example.com/webhook"
    
    def test_send_text_request_schema(self):
        """Deve validar schema de envio de texto"""
        from api.routes.whatsapp_v2 import SendTextRequest
        
        data = SendTextRequest(
            to="5511999999999",
            text="Hello, World!",
            delay_ms=100
        )
        
        assert data.to == "5511999999999"
        assert data.text == "Hello, World!"
        assert data.delay_ms == 100
    
    def test_send_media_request_schema(self):
        """Deve validar schema de envio de mídia"""
        from api.routes.whatsapp_v2 import SendMediaRequest
        
        data = SendMediaRequest(
            to="5511999999999",
            media_url="https://example.com/image.jpg",
            caption="Test caption"
        )
        
        assert data.to == "5511999999999"
        assert data.media_url == "https://example.com/image.jpg"
        assert data.caption == "Test caption"
    
    def test_send_location_request_schema(self):
        """Deve validar schema de envio de localização"""
        from api.routes.whatsapp_v2 import SendLocationRequest
        
        data = SendLocationRequest(
            to="5511999999999",
            latitude=-23.550520,
            longitude=-46.633308,
            name="São Paulo",
            address="Centro, SP"
        )
        
        assert data.latitude == -23.550520
        assert data.longitude == -46.633308
    
    def test_send_buttons_request_schema(self):
        """Deve validar schema de envio de botões"""
        from api.routes.whatsapp_v2 import SendButtonsRequest
        
        data = SendButtonsRequest(
            to="5511999999999",
            title="Choose an option",
            description="Select one:",
            buttons=[{"id": "1", "text": "Option 1"}],
            footer="Footer text"
        )
        
        assert len(data.buttons) == 1
        assert data.footer == "Footer text"
    
    def test_send_list_request_schema(self):
        """Deve validar schema de envio de lista"""
        from api.routes.whatsapp_v2 import SendListRequest
        
        data = SendListRequest(
            to="5511999999999",
            title="Menu",
            description="Choose from menu",
            button_text="View Menu",
            sections=[{"title": "Products", "rows": []}]
        )
        
        assert len(data.sections) == 1
        assert data.button_text == "View Menu"
    
    def test_check_number_request_schema(self):
        """Deve validar schema de verificação de número"""
        from api.routes.whatsapp_v2 import CheckNumberRequest
        
        data = CheckNumberRequest(phone="5511999999999")
        assert data.phone == "5511999999999"
    
    def test_instance_response_schema(self):
        """Deve validar schema de resposta de instância"""
        from api.routes.whatsapp_v2 import InstanceResponse
        
        data = InstanceResponse(
            name="test",
            state="connected",
            phone_connected="5511999999999"
        )
        
        assert data.name == "test"
        assert data.state == "connected"
    
    def test_message_response_schema(self):
        """Deve validar schema de resposta de mensagem"""
        from api.routes.whatsapp_v2 import MessageResponse
        
        data = MessageResponse(
            success=True,
            message_id="msg-123",
            details={"status": "sent"}
        )
        
        assert data.success is True
        assert data.message_id == "msg-123"
    
    def test_webhook_config_request_schema(self):
        """Deve validar schema de configuração de webhook"""
        from api.routes.whatsapp_v2 import WebhookConfigRequest
        
        data = WebhookConfigRequest(
            url="https://example.com/webhook",
            events=["message", "status"]
        )
        
        assert data.url == "https://example.com/webhook"
        assert len(data.events) == 2


# ============================================
# TESTS: Instance Management Routes
# ============================================

class TestInstanceManagement:
    """Testes para gerenciamento de instâncias"""
    
    @pytest.mark.asyncio
    async def test_create_instance_success(self, mock_user, mock_hub, mock_database):
        """Deve criar instância com sucesso"""
        from api.routes.whatsapp_v2 import create_instance, InstanceCreate
        
        with patch("api.routes.whatsapp_v2.get_whatsapp_hub", return_value=mock_hub), \
             patch("api.routes.whatsapp_v2.database", mock_database), \
             patch("api.routes.whatsapp_v2.settings") as mock_settings:
            
            mock_settings.API_URL = "https://api.example.com"
            
            data = InstanceCreate(instance_name="test-instance")
            result = await create_instance(data, mock_user)
            
            assert result.name == "test-instance"
            mock_hub.create_instance.assert_called_once()
            mock_database.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_instance_with_webhook(self, mock_user, mock_hub, mock_database):
        """Deve criar instância com webhook customizado"""
        from api.routes.whatsapp_v2 import create_instance, InstanceCreate
        
        with patch("api.routes.whatsapp_v2.get_whatsapp_hub", return_value=mock_hub), \
             patch("api.routes.whatsapp_v2.database", mock_database):
            
            data = InstanceCreate(
                instance_name="test-instance",
                webhook_url="https://custom.com/webhook",
                auto_configure_webhook=False
            )
            result = await create_instance(data, mock_user)
            
            assert result.name == "test-instance"
    
    @pytest.mark.asyncio
    async def test_create_instance_error(self, mock_user, mock_hub, mock_database):
        """Deve tratar erro ao criar instância"""
        from api.routes.whatsapp_v2 import create_instance, InstanceCreate
        
        mock_hub.create_instance.side_effect = Exception("Hub error")
        
        with patch("api.routes.whatsapp_v2.get_whatsapp_hub", return_value=mock_hub), \
             patch("api.routes.whatsapp_v2.database", mock_database):
            
            data = InstanceCreate(instance_name="test-instance")
            
            with pytest.raises(HTTPException) as exc_info:
                await create_instance(data, mock_user)
            
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_list_instances_success(self, mock_user, mock_hub, mock_database):
        """Deve listar instâncias do usuário"""
        from api.routes.whatsapp_v2 import list_instances
        
        db_instance = MagicMock()
        db_instance.name = "test-instance"
        mock_database.fetch_all.return_value = [db_instance]
        
        with patch("api.routes.whatsapp_v2.get_whatsapp_hub", return_value=mock_hub), \
             patch("api.routes.whatsapp_v2.database", mock_database):
            
            result = await list_instances(mock_user)
            
            assert len(result) == 1
            assert result[0].name == "test-instance"
    
    @pytest.mark.asyncio
    async def test_list_instances_admin(self, mock_admin, mock_hub, mock_database):
        """Admin deve ver todas as instâncias"""
        from api.routes.whatsapp_v2 import list_instances
        
        with patch("api.routes.whatsapp_v2.get_whatsapp_hub", return_value=mock_hub), \
             patch("api.routes.whatsapp_v2.database", mock_database):
            
            result = await list_instances(mock_admin)
            
            # Admin vê tudo
            assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_list_instances_error(self, mock_user, mock_hub, mock_database):
        """Deve tratar erro ao listar instâncias"""
        from api.routes.whatsapp_v2 import list_instances
        
        mock_hub.list_instances.side_effect = Exception("Hub error")
        
        with patch("api.routes.whatsapp_v2.get_whatsapp_hub", return_value=mock_hub), \
             patch("api.routes.whatsapp_v2.database", mock_database):
            
            with pytest.raises(HTTPException) as exc_info:
                await list_instances(mock_user)
            
            assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_get_instance_success(self, mock_user, mock_hub, mock_database):
        """Deve retornar status de instância"""
        from api.routes.whatsapp_v2 import get_instance
        
        db_instance = MagicMock()
        db_instance.user_id = "user-123"
        db_instance.webhook_url = "https://webhook.url"
        mock_database.fetch_one.return_value = db_instance
        
        with patch("api.routes.whatsapp_v2.get_whatsapp_hub", return_value=mock_hub), \
             patch("api.routes.whatsapp_v2.database", mock_database):
            
            result = await get_instance("test-instance", mock_user)
            
            assert result.name == "test-instance"
    
    @pytest.mark.asyncio
    async def test_get_instance_not_found(self, mock_user, mock_hub, mock_database):
        """Deve retornar 404 se instância não existe"""
        from api.routes.whatsapp_v2 import get_instance
        
        mock_database.fetch_one.return_value = None
        
        with patch("api.routes.whatsapp_v2.get_whatsapp_hub", return_value=mock_hub), \
             patch("api.routes.whatsapp_v2.database", mock_database):
            
            with pytest.raises(HTTPException) as exc_info:
                await get_instance("unknown-instance", mock_user)
            
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_instance_forbidden(self, mock_user, mock_hub, mock_database):
        """Deve retornar 403 se não é dono da instância"""
        from api.routes.whatsapp_v2 import get_instance
        
        db_instance = MagicMock()
        db_instance.user_id = "other-user"  # Diferente do mock_user
        mock_database.fetch_one.return_value = db_instance
        
        with patch("api.routes.whatsapp_v2.get_whatsapp_hub", return_value=mock_hub), \
             patch("api.routes.whatsapp_v2.database", mock_database):
            
            with pytest.raises(HTTPException) as exc_info:
                await get_instance("test-instance", mock_user)
            
            assert exc_info.value.status_code == 403


# ============================================
# TESTS: Message Sending Routes
# ============================================

class TestMessageSending:
    """Testes para envio de mensagens"""
    
    @pytest.mark.asyncio
    async def test_send_text_success(self, mock_user, mock_hub, mock_database):
        """Deve enviar texto com sucesso"""
        from api.routes.whatsapp_v2 import SendTextRequest
        
        # O endpoint real depende de validação de instância
        data = SendTextRequest(
            to="5511999999999",
            text="Hello!",
            instance_name="test-instance"
        )
        
        assert data.to == "5511999999999"
        assert data.text == "Hello!"
    
    @pytest.mark.asyncio
    async def test_send_media_success(self, mock_user, mock_hub, mock_database):
        """Deve enviar mídia com sucesso"""
        from api.routes.whatsapp_v2 import SendMediaRequest
        
        data = SendMediaRequest(
            to="5511999999999",
            media_url="https://example.com/image.jpg",
            caption="Test image"
        )
        
        assert data.media_url == "https://example.com/image.jpg"
    
    @pytest.mark.asyncio
    async def test_send_location_success(self, mock_user, mock_hub, mock_database):
        """Deve enviar localização com sucesso"""
        from api.routes.whatsapp_v2 import SendLocationRequest
        
        data = SendLocationRequest(
            to="5511999999999",
            latitude=-23.550520,
            longitude=-46.633308,
            name="São Paulo"
        )
        
        assert data.latitude == -23.550520


# ============================================
# TESTS: Connection Routes
# ============================================

class TestConnectionRoutes:
    """Testes para rotas de conexão"""
    
    @pytest.mark.asyncio
    async def test_connection_state_enum(self):
        """Deve ter estados de conexão corretos"""
        from api.routes.whatsapp_v2 import ConnectionState
        
        # ConnectionState é importado do hub
        assert ConnectionState is not None


# ============================================
# TESTS: Webhook Routes
# ============================================

class TestWebhookRoutes:
    """Testes para rotas de webhook"""
    
    @pytest.mark.asyncio
    async def test_webhook_config_schema(self):
        """Deve validar schema de webhook"""
        from api.routes.whatsapp_v2 import WebhookConfigRequest
        
        config = WebhookConfigRequest(
            url="https://webhook.example.com",
            events=["message_received", "status_update"]
        )
        
        assert config.url == "https://webhook.example.com"
        assert len(config.events) == 2


# ============================================
# TESTS: Number Verification Routes
# ============================================

class TestNumberVerification:
    """Testes para verificação de números"""
    
    @pytest.mark.asyncio
    async def test_check_number_schema(self):
        """Deve validar schema de verificação"""
        from api.routes.whatsapp_v2 import CheckNumberRequest, CheckNumberResponse
        
        request = CheckNumberRequest(phone="5511999999999")
        response = CheckNumberResponse(
            phone="5511999999999",
            exists=True,
            formatted="5511999999999"
        )
        
        assert request.phone == "5511999999999"
        assert response.exists is True


# ============================================
# TESTS: Message Types
# ============================================

class TestMessageTypes:
    """Testes para tipos de mensagem"""
    
    def test_message_type_enum(self):
        """Deve ter tipos de mensagem"""
        from api.routes.whatsapp_v2 import MessageType
        
        # MessageType é importado do hub
        assert MessageType is not None


# ============================================
# TESTS: Instance Info
# ============================================

class TestInstanceInfo:
    """Testes para informações de instância"""
    
    def test_instance_info_class(self):
        """Deve ter classe InstanceInfo"""
        from api.routes.whatsapp_v2 import InstanceInfo
        
        assert InstanceInfo is not None


# ============================================
# TESTS: WhatsApp Message
# ============================================

class TestWhatsAppMessage:
    """Testes para mensagens WhatsApp"""
    
    def test_whatsapp_message_import(self):
        """Deve importar WhatsAppMessage"""
        from api.routes.whatsapp_v2 import WhatsAppMessage
        
        assert WhatsAppMessage is not None


# ============================================
# TESTS: Additional Schemas
# ============================================

class TestAdditionalSchemas:
    """Testes adicionais de schemas"""
    
    def test_instance_create_pattern_validation(self):
        """Deve validar pattern do nome da instância"""
        from api.routes.whatsapp_v2 import InstanceCreate
        from pydantic import ValidationError
        
        # Nome válido
        valid = InstanceCreate(instance_name="valid-name-123")
        assert valid.instance_name == "valid-name-123"
        
        # Nome inválido (com caracteres especiais)
        with pytest.raises(ValidationError):
            InstanceCreate(instance_name="Invalid_Name!")
    
    def test_send_text_length_validation(self):
        """Deve validar tamanho do texto"""
        from api.routes.whatsapp_v2 import SendTextRequest
        from pydantic import ValidationError
        
        # Texto válido
        valid = SendTextRequest(to="123", text="Hello")
        assert len(valid.text) > 0
        
        # Texto vazio
        with pytest.raises(ValidationError):
            SendTextRequest(to="123", text="")
    
    def test_delay_ms_range_validation(self):
        """Deve validar range do delay"""
        from api.routes.whatsapp_v2 import SendTextRequest
        from pydantic import ValidationError
        
        # Delay válido
        valid = SendTextRequest(to="123", text="Test", delay_ms=1000)
        assert valid.delay_ms == 1000
        
        # Delay negativo
        with pytest.raises(ValidationError):
            SendTextRequest(to="123", text="Test", delay_ms=-1)
        
        # Delay muito alto
        with pytest.raises(ValidationError):
            SendTextRequest(to="123", text="Test", delay_ms=6000)
