"""
Testes Unitários - TikTok Hub
=============================
Testes para o hub centralizado de TikTok.

Autor: Didin Fácil
Versão: 1.0.0
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from typing import Dict, List

from integrations.tiktok_hub import (
    TikTokHub,
    TikTokHubConfig,
    get_tiktok_hub,
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def hub_config():
    """Configuração de teste para o hub."""
    return TikTokHubConfig(
        headless=True,
        upload_timeout=60,  # Reduzido para testes
    )


@pytest.fixture
def tiktok_hub(hub_config):
    """Hub de teste."""
    return TikTokHub(hub_config)


@pytest.fixture
def sample_cookies():
    """Cookies de exemplo para testes."""
    return [
        {"name": "sessionid", "value": "test-session-123", "domain": ".tiktok.com"},
        {"name": "tt_webid", "value": "123456789", "domain": ".tiktok.com"},
        {"name": "passport_csrf_token", "value": "csrf-token", "domain": ".tiktok.com"},
    ]


@pytest.fixture
def mock_session():
    """Mock de sessão TikTok."""
    mock = MagicMock()
    mock.id = "session-123"
    mock.user_id = "user-456"
    mock.account_name = "test_account"
    mock.cookies = []
    mock.created_at = datetime.now(timezone.utc)
    mock.expires_at = None
    return mock


# ============================================
# TESTES DE CONFIGURAÇÃO
# ============================================

class TestTikTokHubConfig:
    """Testes para a configuração do hub."""

    def test_default_config_values(self):
        """Verifica valores padrão da configuração."""
        config = TikTokHubConfig()
        
        assert config.headless is True
        assert config.upload_timeout == 300

    def test_custom_config_values(self, hub_config):
        """Verifica configuração customizada."""
        assert hub_config.headless is True
        assert hub_config.upload_timeout == 60


# ============================================
# TESTES DE SINGLETON
# ============================================

class TestTikTokHubSingleton:
    """Testes para o padrão singleton."""

    def test_get_tiktok_hub_returns_hub(self):
        """Verifica que get_tiktok_hub retorna uma instância válida."""
        # Limpar singleton
        with patch('integrations.tiktok_hub._tiktok_hub', None):
            hub = get_tiktok_hub()
            assert isinstance(hub, TikTokHub)

    def test_get_tiktok_hub_same_instance(self):
        """Verifica que a mesma instância é retornada."""
        # O singleton global mantém a mesma instância
        hub1 = get_tiktok_hub()
        hub2 = get_tiktok_hub()
        
        assert hub1 is hub2


# ============================================
# TESTES DE GERENCIAMENTO DE SESSÃO
# ============================================

class TestTikTokHubSessionManagement:
    """Testes para gerenciamento de sessões."""

    @pytest.mark.asyncio
    async def test_save_session_success(self, tiktok_hub, sample_cookies, mock_session):
        """Testa salvamento de sessão com sucesso."""
        with patch.object(
            tiktok_hub.session_manager,
            'save_session',
            new_callable=AsyncMock
        ) as mock_save:
            mock_save.return_value = mock_session
            
            result = await tiktok_hub.save_session(
                user_id="user-123",
                account_name="test_account",
                cookies=sample_cookies
            )
            
            mock_save.assert_called_once()
            call_kwargs = mock_save.call_args[1]
            assert call_kwargs["user_id"] == "user-123"
            assert call_kwargs["account_name"] == "test_account"
            assert call_kwargs["cookies"] == sample_cookies

    @pytest.mark.asyncio
    async def test_get_session_found(self, tiktok_hub, mock_session):
        """Testa recuperação de sessão existente."""
        with patch.object(
            tiktok_hub.session_manager,
            'get_session',
            new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_session
            
            result = await tiktok_hub.get_session(
                user_id="user-123",
                account_name="test_account"
            )
            
            mock_get.assert_called_once_with("user-123", "test_account")
            assert result == mock_session

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, tiktok_hub):
        """Testa recuperação de sessão inexistente."""
        with patch.object(
            tiktok_hub.session_manager,
            'get_session',
            new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None
            
            result = await tiktok_hub.get_session(
                user_id="user-123",
                account_name="nonexistent"
            )
            
            assert result is None

    @pytest.mark.asyncio
    async def test_list_sessions(self, tiktok_hub, mock_session):
        """Testa listagem de sessões de um usuário."""
        sessions = [mock_session, mock_session]
        
        with patch.object(
            tiktok_hub.session_manager,
            'list_sessions',
            new_callable=AsyncMock
        ) as mock_list:
            mock_list.return_value = sessions
            
            result = await tiktok_hub.list_sessions(user_id="user-123")
            
            mock_list.assert_called_once_with("user-123")
            assert len(result) == 2


# ============================================
# TESTES DE UPLOAD DE VÍDEO
# ============================================

class TestTikTokHubUpload:
    """Testes para upload de vídeos."""

    @pytest.mark.asyncio
    async def test_upload_video_session_not_found(self, tiktok_hub):
        """Testa upload quando sessão não existe."""
        with patch.object(
            tiktok_hub,
            'get_session',
            new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None
            
            with pytest.raises(ValueError) as exc_info:
                await tiktok_hub.upload_video(
                    user_id="user-123",
                    account_name="nonexistent",
                    video_path="/path/to/video.mp4",
                    caption="Test video"
                )
            
            assert "Sessão não encontrada" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_video_with_session(self, tiktok_hub, mock_session):
        """Testa upload quando sessão existe (simulação)."""
        with patch.object(
            tiktok_hub,
            'get_session',
            new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_session
            
            result = await tiktok_hub.upload_video(
                user_id="user-123",
                account_name="test_account",
                video_path="/path/to/video.mp4",
                caption="Test video"
            )
            
            # Por enquanto retorna simulação
            assert result["status"] == "pending"


# ============================================
# TESTES DE MENSAGENS (NOT IMPLEMENTED)
# ============================================

class TestTikTokHubMessaging:
    """Testes para envio de mensagens (não implementado)."""

    @pytest.mark.asyncio
    async def test_send_message_not_implemented(self, tiktok_hub):
        """Testa que envio de mensagem levanta NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await tiktok_hub.send_message(
                recipient_id="123456",
                text="Olá!"
            )


# ============================================
# TESTES DE INICIALIZAÇÃO
# ============================================

class TestTikTokHubInitialization:
    """Testes para inicialização do hub."""

    def test_hub_initialization_default_config(self):
        """Testa inicialização com config padrão."""
        hub = TikTokHub()
        
        assert hub.config is not None
        assert hub.session_manager is not None
        assert hub.config.headless is True

    def test_hub_initialization_custom_config(self, hub_config):
        """Testa inicialização com config customizada."""
        hub = TikTokHub(hub_config)
        
        assert hub.config == hub_config
        assert hub.config.upload_timeout == 60

    def test_hub_has_session_manager(self, tiktok_hub):
        """Verifica que hub tem session manager."""
        assert hasattr(tiktok_hub, 'session_manager')
        assert tiktok_hub.session_manager is not None


# ============================================
# TESTES DE COOKIES
# ============================================

class TestTikTokCookies:
    """Testes para validação de cookies."""

    def test_sample_cookies_structure(self, sample_cookies):
        """Verifica estrutura de cookies de exemplo."""
        assert len(sample_cookies) == 3
        
        for cookie in sample_cookies:
            assert "name" in cookie
            assert "value" in cookie
            assert "domain" in cookie
            assert cookie["domain"] == ".tiktok.com"

    def test_required_cookie_sessionid(self, sample_cookies):
        """Verifica presença de sessionid."""
        session_cookie = next(
            (c for c in sample_cookies if c["name"] == "sessionid"),
            None
        )
        
        assert session_cookie is not None
        assert session_cookie["value"] == "test-session-123"


# ============================================
# TESTES DE INTEGRAÇÃO COM SESSION MANAGER
# ============================================

class TestTikTokHubSessionManagerIntegration:
    """Testes de integração com o session manager."""

    @pytest.mark.asyncio
    async def test_save_and_get_session_flow(self, tiktok_hub, sample_cookies, mock_session):
        """Testa fluxo completo de salvar e recuperar sessão."""
        with patch.object(
            tiktok_hub.session_manager,
            'save_session',
            new_callable=AsyncMock
        ) as mock_save:
            with patch.object(
                tiktok_hub.session_manager,
                'get_session',
                new_callable=AsyncMock
            ) as mock_get:
                mock_save.return_value = mock_session
                mock_get.return_value = mock_session
                
                # Salvar sessão
                saved = await tiktok_hub.save_session(
                    user_id="user-123",
                    account_name="test_account",
                    cookies=sample_cookies
                )
                
                # Recuperar sessão
                retrieved = await tiktok_hub.get_session(
                    user_id="user-123",
                    account_name="test_account"
                )
                
                assert saved.account_name == retrieved.account_name


# ============================================
# TESTES DE PRIVACY (FUTURO)
# ============================================

class TestTikTokPrivacy:
    """Testes para configurações de privacidade de vídeos."""

    def test_privacy_options(self):
        """Verifica opções de privacidade disponíveis."""
        # Importar enum de privacidade se existir
        try:
            from vendor.tiktok.client import Privacy
            
            assert hasattr(Privacy, 'PUBLIC') or Privacy.PUBLIC is not None
            assert hasattr(Privacy, 'FRIENDS') or Privacy.FRIENDS is not None
            assert hasattr(Privacy, 'PRIVATE') or Privacy.PRIVATE is not None
        except ImportError:
            # Se não existir, pular teste
            pytest.skip("Privacy enum não disponível")


# ============================================
# TESTES DE ERROS
# ============================================

class TestTikTokHubErrors:
    """Testes para tratamento de erros."""

    @pytest.mark.asyncio
    async def test_session_manager_error_propagation(self, tiktok_hub):
        """Testa que erros do session manager são propagados."""
        with patch.object(
            tiktok_hub.session_manager,
            'save_session',
            new_callable=AsyncMock
        ) as mock_save:
            mock_save.side_effect = Exception("Redis connection failed")
            
            with pytest.raises(Exception) as exc_info:
                await tiktok_hub.save_session(
                    user_id="user-123",
                    account_name="test",
                    cookies=[]
                )
            
            assert "Redis connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_invalid_path(self, tiktok_hub, mock_session):
        """Testa upload com caminho inválido."""
        with patch.object(
            tiktok_hub,
            'get_session',
            new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_session
            
            # O hub atual retorna pending, mas um hub real deveria
            # validar o caminho do arquivo
            result = await tiktok_hub.upload_video(
                user_id="user-123",
                account_name="test",
                video_path="/invalid/path.mp4",
                caption="Test"
            )
            
            # Por enquanto aceita qualquer path (simulação)
            assert result["status"] == "pending"
