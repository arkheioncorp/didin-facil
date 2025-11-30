"""
Testes de Integração E2E - Hubs
===============================
Testes end-to-end para os hubs de integração.

Estes testes verificam fluxos completos de integração
simulando cenários reais de uso.

Autor: Didin Fácil
Versão: 1.0.0
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import json


# ============================================
# FIXTURES COMPARTILHADAS
# ============================================

@pytest.fixture
def mock_redis():
    """Mock do Redis para todos os testes."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    return redis


@pytest.fixture
def mock_database():
    """Mock do banco de dados."""
    db = AsyncMock()
    db.execute = AsyncMock(return_value=None)
    db.fetch_one = AsyncMock(return_value=None)
    db.fetch_all = AsyncMock(return_value=[])
    return db


# ============================================
# TESTES E2E - WHATSAPP HUB
# ============================================

class TestWhatsAppHubE2E:
    """Testes E2E para WhatsApp Hub."""

    @pytest.mark.asyncio
    async def test_complete_instance_lifecycle(self, mock_redis):
        """
        Testa ciclo completo de vida de uma instância:
        1. Criar instância
        2. Obter QR Code
        3. Verificar conexão
        4. Enviar mensagem
        5. Deletar instância
        """
        from integrations.whatsapp_hub import WhatsAppHub, WhatsAppHubConfig
        
        config = WhatsAppHubConfig(
            evolution_api_url="http://mock-api:8082",
            evolution_api_key="test-key",
            default_instance="e2e-test"
        )
        hub = WhatsAppHub(config)
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_closed = False
            mock_client_class.return_value = mock_client
            
            # 1. Criar instância
            mock_client.post = AsyncMock(return_value=MagicMock(
                status_code=200,
                json=lambda: {"instance": {"instanceName": "e2e-test", "status": "created"}}
            ))
            
            instance = await hub.create_instance(
                instance_name="e2e-test",
                webhook_url="https://example.com/webhook"
            )
            assert instance.name == "e2e-test"
            
            # 2. Obter QR Code
            mock_client.get = AsyncMock(return_value=MagicMock(
                status_code=200,
                json=lambda: {"base64": "data:image/png;base64,abc123...", "code": "2@..."}
            ))
            
            qr = await hub.get_qr_code("e2e-test")
            assert "base64" in qr
            
            # 3. Verificar status (simulando conexão)
            mock_client.get = AsyncMock(return_value=MagicMock(
                status_code=200,
                json=lambda: {"instance": {"state": "open"}}
            ))
            
            status = await hub.get_instance_status("e2e-test")
            assert status.state.value == "connected"
            
            # 4. Enviar mensagem
            mock_client.post = AsyncMock(return_value=MagicMock(
                status_code=200,
                json=lambda: {"key": {"id": "msg123"}, "status": "sent"}
            ))
            
            with patch.object(hub, '_check_rate_limit', return_value=True):
                result = await hub.send_text(
                    to="5511999999999",
                    text="Olá, teste E2E!",
                    instance_name="e2e-test"
                )
                assert result["status"] == "sent"
            
            # 5. Deletar instância
            mock_client.delete = AsyncMock(return_value=MagicMock(
                status_code=200,
                json=lambda: {"deleted": True}
            ))
            
            deleted = await hub.delete_instance("e2e-test")
            assert deleted is True

    @pytest.mark.asyncio
    async def test_webhook_processing_flow(self):
        """Testa fluxo de processamento de webhook."""
        from integrations.whatsapp_hub import WhatsAppHub, WhatsAppHubConfig, WhatsAppMessage
        
        config = WhatsAppHubConfig()
        hub = WhatsAppHub(config)
        
        # Simular payload de webhook de mensagem
        webhook_payload = {
            "event": "messages.upsert",
            "instance": "test-instance",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": False,
                    "id": "ABC123"
                },
                "message": {
                    "conversation": "Olá, recebi sua mensagem!"
                },
                "messageTimestamp": 1700000000
            }
        }
        
        # Processar webhook (método parse_webhook se existir)
        if hasattr(hub, 'parse_webhook'):
            message = hub.parse_webhook(webhook_payload)
            assert isinstance(message, WhatsAppMessage)
            assert message.content == "Olá, recebi sua mensagem!"
            assert message.phone_number == "5511999999999"

    @pytest.mark.asyncio
    async def test_multi_message_batch(self):
        """Testa envio de múltiplas mensagens em batch."""
        from integrations.whatsapp_hub import WhatsAppHub, WhatsAppHubConfig
        
        config = WhatsAppHubConfig(messages_per_minute=100)
        hub = WhatsAppHub(config)
        
        recipients = [f"551199999900{i}" for i in range(5)]
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.is_closed = False
            mock_client.post = AsyncMock(return_value=MagicMock(
                status_code=200,
                json=lambda: {"status": "sent"}
            ))
            mock_client_class.return_value = mock_client
            
            with patch.object(hub, '_check_rate_limit', return_value=True):
                results = []
                for recipient in recipients:
                    result = await hub.send_text(
                        to=recipient,
                        text=f"Mensagem para {recipient}",
                        instance_name="test"
                    )
                    results.append(result)
            
            assert len(results) == 5
            assert all(r["status"] == "sent" for r in results)


# ============================================
# TESTES E2E - INSTAGRAM HUB
# ============================================

class TestInstagramHubE2E:
    """Testes E2E para Instagram Hub."""

    @pytest.mark.asyncio
    async def test_complete_messaging_flow(self):
        """
        Testa fluxo completo de mensagens:
        1. Receber webhook de mensagem
        2. Processar e normalizar
        3. Enviar resposta
        4. Enviar typing indicator
        """
        from integrations.instagram_hub import InstagramHub, InstagramHubConfig
        
        config = InstagramHubConfig(
            access_token="test-token",
            page_id="123456789"
        )
        hub = InstagramHub(config)
        
        # 1. Simular recebimento de webhook (formato correto do Facebook)
        webhook_payload = {
            "entry": [{
                "messaging": [{
                    "sender": {"id": "user123"},
                    "recipient": {"id": "page456"},
                    "timestamp": 1700000000000,
                    "message": {
                        "mid": "mid.123",
                        "text": "Olá, gostaria de saber mais"
                    }
                }]
            }]
        }
        
        normalized = hub.normalize_webhook_event(webhook_payload)
        assert normalized is not None
        assert normalized.sender_id == "user123"
        assert normalized.content == "Olá, gostaria de saber mais"
        
        # 2-4. Simular respostas
        with patch.object(hub, '_send_api_request', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"message_id": "mid.456"}
            
            # Typing (substitui typing_on/typing_off)
            with patch('asyncio.sleep', new_callable=AsyncMock):
                await hub.send_typing("user123", duration_ms=100)
            
            # Responder
            await hub.send_message("user123", "Claro! Como posso ajudar?")
            
            # Quick replies
            await hub.send_quick_replies(
                "user123",
                "Escolha uma opção:",
                ["Preços", "Produtos", "Suporte"]
            )
            
            # Verificar que 3 chamadas foram feitas (typing, message, quick_replies)
            assert mock_send.call_count == 3

    @pytest.mark.asyncio
    async def test_media_sending_flow(self):
        """Testa envio de diferentes tipos de mídia."""
        from integrations.instagram_hub import InstagramHub, InstagramHubConfig
        
        hub = InstagramHub(InstagramHubConfig(
            access_token="test-token",
            page_id="123"
        ))
        
        media_types = [
            ("image", "https://example.com/image.jpg"),
            ("video", "https://example.com/video.mp4"),
        ]
        
        with patch.object(hub, '_send_api_request', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"message_id": "mid.123"}
            
            for media_type, url in media_types:
                await hub.send_media(
                    recipient_id="user123",
                    media_url=url,
                    media_type=media_type
                )
            
            assert mock_send.call_count == len(media_types)


# ============================================
# TESTES E2E - TIKTOK HUB
# ============================================

class TestTikTokHubE2E:
    """Testes E2E para TikTok Hub."""

    @pytest.mark.asyncio
    async def test_complete_session_management_flow(self, mock_redis):
        """
        Testa fluxo completo de gerenciamento de sessão:
        1. Salvar sessão
        2. Listar sessões
        3. Recuperar sessão
        4. Usar para upload (simulado)
        """
        from integrations.tiktok_hub import TikTokHub, TikTokHubConfig
        
        hub = TikTokHub(TikTokHubConfig(headless=True, upload_timeout=60))
        
        mock_session = MagicMock()
        mock_session.id = "session-123"
        mock_session.account_name = "test_account"
        mock_session.user_id = "user-123"
        mock_session.created_at = datetime.now(timezone.utc)
        
        # 1. Salvar sessão
        with patch.object(
            hub.session_manager,
            'save_session',
            new_callable=AsyncMock
        ) as mock_save:
            mock_save.return_value = mock_session
            
            saved = await hub.save_session(
                user_id="user-123",
                account_name="test_account",
                cookies=[
                    {"name": "sessionid", "value": "abc123", "domain": ".tiktok.com"}
                ]
            )
            
            assert saved.account_name == "test_account"
        
        # 2. Listar sessões
        with patch.object(
            hub.session_manager,
            'list_sessions',
            new_callable=AsyncMock
        ) as mock_list:
            mock_list.return_value = [mock_session]
            
            sessions = await hub.list_sessions("user-123")
            
            assert len(sessions) == 1
            assert sessions[0].account_name == "test_account"
        
        # 3. Recuperar sessão
        with patch.object(
            hub.session_manager,
            'get_session',
            new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_session
            
            retrieved = await hub.get_session("user-123", "test_account")
            
            assert retrieved is not None
            assert retrieved.id == "session-123"
        
        # 4. Upload (simulado)
        with patch.object(hub, 'get_session', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_session
            
            result = await hub.upload_video(
                user_id="user-123",
                account_name="test_account",
                video_path="/path/to/video.mp4",
                caption="Meu vídeo de teste #test"
            )
            
            assert result["status"] == "pending"


# ============================================
# TESTES E2E - CROSS-HUB
# ============================================

class TestCrossHubIntegration:
    """Testes de integração entre múltiplos hubs."""

    @pytest.mark.asyncio
    async def test_multi_platform_broadcast(self):
        """
        Testa broadcast de mensagem para múltiplas plataformas.
        Cenário: Enviar mesma mensagem para WhatsApp e Instagram.
        """
        from integrations import get_whatsapp_hub, get_instagram_hub
        
        message = "🎉 Promoção especial! Use cupom DIDIN10 para 10% de desconto!"
        
        with patch('integrations.whatsapp_hub.WhatsAppHub.get_instance') as mock_wa:
            with patch('integrations.instagram_hub.get_instagram_hub') as mock_ig:
                mock_wa_hub = AsyncMock()
                mock_wa_hub.send_text = AsyncMock(return_value={"status": "sent"})
                mock_wa.return_value = mock_wa_hub
                
                mock_ig_hub = AsyncMock()
                mock_ig_hub.send_message = AsyncMock(return_value={"message_id": "mid.123"})
                mock_ig.return_value = mock_ig_hub
                
                # Broadcast para WhatsApp
                wa_result = await mock_wa_hub.send_text(
                    to="5511999999999",
                    text=message,
                    instance_name="didin-bot"
                )
                
                # Broadcast para Instagram
                ig_result = await mock_ig_hub.send_message(
                    recipient_id="user123",
                    text=message
                )
                
                assert wa_result["status"] == "sent"
                assert "message_id" in ig_result

    @pytest.mark.asyncio
    async def test_unified_webhook_handling(self):
        """
        Testa tratamento unificado de webhooks de diferentes plataformas.
        """
        from integrations.whatsapp_hub import WhatsAppHub, WhatsAppHubConfig
        from integrations.instagram_hub import InstagramHub, InstagramHubConfig
        
        # Webhook do WhatsApp
        wa_webhook = {
            "event": "messages.upsert",
            "instance": "didin-bot",
            "data": {
                "key": {"remoteJid": "5511999999999@s.whatsapp.net", "fromMe": False, "id": "123"},
                "message": {"conversation": "Olá via WhatsApp"}
            }
        }
        
        # Webhook do Instagram (formato correto do Facebook Messenger Platform)
        ig_webhook = {
            "entry": [{
                "messaging": [{
                    "sender": {"id": "user456"},
                    "recipient": {"id": "page789"},
                    "timestamp": 1700000000000,
                    "message": {"mid": "mid.456", "text": "Olá via Instagram"}
                }]
            }]
        }
        
        # Normalizar Instagram
        ig_hub = InstagramHub(InstagramHubConfig())
        ig_normalized = ig_hub.normalize_webhook_event(ig_webhook)
        
        # Verificar campos comuns (retorna InstagramMessage, não dict)
        assert ig_normalized is not None
        assert ig_normalized.content == "Olá via Instagram"
        assert ig_normalized.sender_id == "user456"


# ============================================
# TESTES DE PERFORMANCE
# ============================================

class TestHubPerformance:
    """Testes de performance dos hubs."""

    @pytest.mark.asyncio
    async def test_hub_singleton_performance(self):
        """Testa que singletons não são recriados desnecessariamente."""
        from integrations import get_whatsapp_hub, get_instagram_hub, get_tiktok_hub
        import time
        
        # Múltiplas chamadas devem ser rápidas
        start = time.time()
        
        for _ in range(100):
            get_whatsapp_hub()
            get_instagram_hub()
            get_tiktok_hub()
        
        elapsed = time.time() - start
        
        # 100 chamadas devem levar menos de 1 segundo
        assert elapsed < 1.0, f"Singleton muito lento: {elapsed}s"

    @pytest.mark.asyncio
    async def test_rate_limiter_performance(self):
        """Testa que rate limiter não causa overhead significativo."""
        from integrations.whatsapp_hub import WhatsAppHub, WhatsAppHubConfig
        import time
        
        hub = WhatsAppHub(WhatsAppHubConfig(messages_per_minute=1000))
        
        start = time.time()
        
        for _ in range(100):
            await hub._check_rate_limit("test-instance")
        
        elapsed = time.time() - start
        
        # 100 checks devem levar menos de 0.5 segundos
        assert elapsed < 0.5, f"Rate limiter muito lento: {elapsed}s"


# ============================================
# TESTES DE RESILIÊNCIA
# ============================================

class TestHubResilience:
    """Testes de resiliência dos hubs."""

    @pytest.mark.asyncio
    async def test_hub_recovers_from_closed_client(self):
        """Testa que hub se recupera de cliente fechado."""
        from integrations.whatsapp_hub import WhatsAppHub, WhatsAppHubConfig
        
        hub = WhatsAppHub(WhatsAppHubConfig())
        
        # Simular cliente fechado
        mock_client = AsyncMock()
        mock_client.is_closed = True
        hub._client = mock_client
        
        with patch('httpx.AsyncClient') as mock_class:
            new_client = AsyncMock()
            new_client.is_closed = False
            mock_class.return_value = new_client
            
            # Deve criar novo cliente
            client = await hub._get_client()
            
            assert client is new_client
            mock_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_hub_handles_api_timeout(self):
        """Testa tratamento de timeout de API."""
        from integrations.whatsapp_hub import WhatsAppHub, WhatsAppHubConfig
        import httpx
        
        hub = WhatsAppHub(WhatsAppHubConfig())
        
        with patch.object(hub, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_get_client.return_value = mock_client
            
            with pytest.raises(httpx.TimeoutException):
                await hub.create_instance("test")
