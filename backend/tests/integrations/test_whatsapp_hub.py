"""
Testes Unitários - WhatsApp Hub
===============================
Testes para o hub centralizado de WhatsApp.

Autor: TikTrend Finder
Versão: 1.0.0
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import httpx

from integrations.whatsapp_hub import (
    WhatsAppHub,
    WhatsAppHubConfig,
    WhatsAppMessage,
    InstanceInfo,
    MessageType,
    ConnectionState,
    get_whatsapp_hub,
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def hub_config():
    """Configuração de teste para o hub."""
    return WhatsAppHubConfig(
        evolution_api_url="http://test-evolution:8082",
        evolution_api_key="test-api-key-12345",
        default_instance="test-instance",
        max_retries=2,
        retry_delay=0.1,
        messages_per_minute=100,
    )


@pytest.fixture
def whatsapp_hub(hub_config):
    """Hub de teste."""
    return WhatsAppHub(hub_config)


@pytest.fixture
def mock_httpx_client():
    """Mock do cliente HTTP."""
    client = AsyncMock(spec=httpx.AsyncClient)
    client.is_closed = False
    return client


# ============================================
# TESTES DE CONFIGURAÇÃO
# ============================================

class TestWhatsAppHubConfig:
    """Testes para a configuração do hub."""

    def test_default_config_values(self):
        """Verifica valores padrão da configuração."""
        config = WhatsAppHubConfig()
        
        assert config.evolution_api_url == "http://localhost:8082"
        assert config.evolution_api_key == ""
        assert config.default_instance == "tiktrend-bot"
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.messages_per_minute == 60

    def test_custom_config_values(self, hub_config):
        """Verifica configuração customizada."""
        assert hub_config.evolution_api_url == "http://test-evolution:8082"
        assert hub_config.evolution_api_key == "test-api-key-12345"
        assert hub_config.default_instance == "test-instance"


# ============================================
# TESTES DE SINGLETON
# ============================================

class TestWhatsAppHubSingleton:
    """Testes para o padrão singleton."""

    def test_get_instance_returns_same_object(self):
        """Verifica que get_instance retorna sempre a mesma instância."""
        # Limpar singleton existente
        WhatsAppHub._instance = None
        
        with patch('integrations.whatsapp_hub.WhatsAppHub.from_settings') as mock_from:
            mock_hub = MagicMock()
            mock_from.return_value = mock_hub
            
            hub1 = WhatsAppHub.get_instance()
            hub2 = WhatsAppHub.get_instance()
            
            # from_settings só é chamado uma vez (singleton)
            assert hub1 is hub2

    def test_get_whatsapp_hub_singleton(self):
        """Verifica função get_whatsapp_hub."""
        with patch('integrations.whatsapp_hub.WhatsAppHub.get_instance') as mock_get:
            mock_hub = MagicMock()
            mock_get.return_value = mock_hub
            
            result = get_whatsapp_hub()
            
            assert result == mock_hub
            mock_get.assert_called_once()


# ============================================
# TESTES DE DATACLASSES
# ============================================

class TestWhatsAppMessage:
    """Testes para a dataclass de mensagem."""

    def test_message_creation(self):
        """Testa criação de mensagem."""
        msg = WhatsAppMessage(
            message_id="msg123",
            remote_jid="5511999999999@s.whatsapp.net",
            from_me=False,
            timestamp=datetime.now(timezone.utc),
            message_type=MessageType.TEXT,
            content="Olá, mundo!",
        )
        
        assert msg.message_id == "msg123"
        assert msg.content == "Olá, mundo!"
        assert msg.from_me is False

    def test_phone_number_extraction(self):
        """Testa extração de número de telefone."""
        msg = WhatsAppMessage(
            message_id="msg123",
            remote_jid="5511999999999@s.whatsapp.net",
            from_me=False,
            timestamp=datetime.now(timezone.utc),
            message_type=MessageType.TEXT,
            content="Test",
        )
        
        assert msg.phone_number == "5511999999999"

    def test_is_group_detection(self):
        """Testa detecção de mensagem de grupo."""
        # Mensagem privada
        private_msg = WhatsAppMessage(
            message_id="msg1",
            remote_jid="5511999999999@s.whatsapp.net",
            from_me=False,
            timestamp=datetime.now(timezone.utc),
            message_type=MessageType.TEXT,
            content="Privado",
        )
        
        # Mensagem de grupo
        group_msg = WhatsAppMessage(
            message_id="msg2",
            remote_jid="123456789@g.us",
            from_me=False,
            timestamp=datetime.now(timezone.utc),
            message_type=MessageType.TEXT,
            content="Grupo",
        )
        
        assert private_msg.is_group is False
        assert group_msg.is_group is True


class TestInstanceInfo:
    """Testes para InstanceInfo."""

    def test_instance_info_creation(self):
        """Testa criação de InstanceInfo."""
        info = InstanceInfo(
            name="test-instance",
            state=ConnectionState.CONNECTED,
            phone_connected="5511999999999",
        )
        
        assert info.name == "test-instance"
        assert info.state == ConnectionState.CONNECTED
        assert info.phone_connected == "5511999999999"


# ============================================
# TESTES DE CLIENT HTTP
# ============================================

class TestWhatsAppHubClient:
    """Testes para gerenciamento de cliente HTTP."""

    @pytest.mark.asyncio
    async def test_get_client_lazy_initialization(self, whatsapp_hub):
        """Testa inicialização lazy do cliente."""
        assert whatsapp_hub._client is None
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_instance = AsyncMock()
            mock_instance.is_closed = False
            mock_client_class.return_value = mock_instance
            
            client = await whatsapp_hub._get_client()
            
            assert client is not None
            mock_client_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_client(self, whatsapp_hub, mock_httpx_client):
        """Testa fechamento do cliente."""
        whatsapp_hub._client = mock_httpx_client
        
        await whatsapp_hub.close()
        
        mock_httpx_client.aclose.assert_called_once()
        assert whatsapp_hub._client is None

    @pytest.mark.asyncio
    async def test_context_manager(self, whatsapp_hub):
        """Testa uso como context manager."""
        with patch.object(whatsapp_hub, 'close', new_callable=AsyncMock) as mock_close:
            async with whatsapp_hub:
                pass
            
            mock_close.assert_called_once()


# ============================================
# TESTES DE INSTÂNCIAS
# ============================================

class TestWhatsAppHubInstances:
    """Testes para gerenciamento de instâncias."""

    @pytest.mark.asyncio
    async def test_create_instance_success(self, whatsapp_hub, mock_httpx_client):
        """Testa criação de instância com sucesso."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "instance": {
                "instanceName": "new-instance",
                "status": "created"
            }
        }
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        
        with patch.object(whatsapp_hub, '_get_client', return_value=mock_httpx_client):
            result = await whatsapp_hub.create_instance(
                instance_name="new-instance",
                webhook_url="https://example.com/webhook"
            )
        
        assert result.name == "new-instance"
        mock_httpx_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_qr_code(self, whatsapp_hub, mock_httpx_client):
        """Testa obtenção de QR code."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "base64": "data:image/png;base64,iVBORw0KGgoAAAANS...",
            "code": "2@abc123..."
        }
        mock_httpx_client.get = AsyncMock(return_value=mock_response)
        
        with patch.object(whatsapp_hub, '_get_client', return_value=mock_httpx_client):
            result = await whatsapp_hub.get_qr_code(instance_name="test-instance")
        
        assert "base64" in result
        mock_httpx_client.get.assert_called_once()


# ============================================
# TESTES DE MENSAGENS
# ============================================

class TestWhatsAppHubMessaging:
    """Testes para envio de mensagens."""

    @pytest.mark.asyncio
    async def test_send_text_success(self, whatsapp_hub, mock_httpx_client):
        """Testa envio de texto com sucesso."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "key": {
                "id": "msg123",
                "fromMe": True
            },
            "status": "sent"
        }
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        
        with patch.object(whatsapp_hub, '_get_client', return_value=mock_httpx_client):
            with patch.object(whatsapp_hub, '_check_rate_limit', return_value=True):
                result = await whatsapp_hub.send_text(
                    to="5511999999999",
                    text="Olá, teste!",
                    instance_name="test-instance"
                )
        
        assert result["status"] == "sent"

    @pytest.mark.asyncio
    async def test_send_text_formats_phone(self, whatsapp_hub, mock_httpx_client):
        """Testa que telefone é formatado corretamente."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "sent"}
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        
        with patch.object(whatsapp_hub, '_get_client', return_value=mock_httpx_client):
            with patch.object(whatsapp_hub, '_check_rate_limit', return_value=True):
                with patch.object(whatsapp_hub, '_format_phone', return_value="5511999999999") as mock_format:
                    await whatsapp_hub.send_text(
                        to="+55 (11) 99999-9999",
                        text="Test",
                        instance_name="test"
                    )
                    mock_format.assert_called()


# ============================================
# TESTES DE RATE LIMITING
# ============================================

class TestWhatsAppHubRateLimiting:
    """Testes para rate limiting."""

    @pytest.mark.asyncio
    async def test_rate_limit_allows_within_limit(self, whatsapp_hub):
        """Testa que requisições dentro do limite são permitidas."""
        whatsapp_hub._rate_limiter = {}
        
        result = await whatsapp_hub._check_rate_limit("test-instance")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_excess(self, whatsapp_hub):
        """Testa que requisições em excesso são bloqueadas."""
        # Simular muitas requisições recentes
        now = datetime.now(timezone.utc)
        whatsapp_hub._rate_limiter = {
            "test-instance": [now] * (whatsapp_hub.config.messages_per_minute + 1)
        }
        
        result = await whatsapp_hub._check_rate_limit("test-instance")
        
        assert result is False


# ============================================
# TESTES DE FORMAT PHONE
# ============================================

class TestFormatPhone:
    """Testes para formatação de telefone."""

    def test_format_phone_removes_special_chars(self, whatsapp_hub):
        """Testa remoção de caracteres especiais."""
        result = whatsapp_hub._format_phone("+55 (11) 99999-9999")
        assert result == "5511999999999"

    def test_format_phone_keeps_digits_only(self, whatsapp_hub):
        """Testa que apenas dígitos são mantidos."""
        result = whatsapp_hub._format_phone("55.11.999.999.999")
        assert result == "5511999999999"


# ============================================
# TESTES DE ENUMS
# ============================================

class TestEnums:
    """Testes para enumerações."""

    def test_message_type_values(self):
        """Verifica valores de MessageType."""
        assert MessageType.TEXT.value == "text"
        assert MessageType.IMAGE.value == "image"
        assert MessageType.VIDEO.value == "video"
        assert MessageType.AUDIO.value == "audio"
        assert MessageType.DOCUMENT.value == "document"
        assert MessageType.LOCATION.value == "location"

    def test_connection_state_values(self):
        """Verifica valores de ConnectionState."""
        assert ConnectionState.DISCONNECTED.value == "disconnected"
        assert ConnectionState.CONNECTING.value == "connecting"
        assert ConnectionState.CONNECTED.value == "connected"
        assert ConnectionState.AWAITING_SCAN.value == "awaiting_scan"
        assert ConnectionState.ERROR.value == "error"
