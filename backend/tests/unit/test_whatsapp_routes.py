"""
Testes para api/routes/whatsapp.py

Testes dos endpoints de integração WhatsApp.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from fastapi import HTTPException


class TestWhatsAppModels:
    """Testes para modelos Pydantic"""
    
    def test_instance_create_model(self):
        """Deve criar WhatsAppInstanceCreate válido"""
        from api.routes.whatsapp import WhatsAppInstanceCreate
        
        data = WhatsAppInstanceCreate(
            instance_name="test-instance",
            webhook_url="https://example.com/webhook"
        )
        
        assert data.instance_name == "test-instance"
        assert data.webhook_url == "https://example.com/webhook"
    
    def test_instance_create_without_webhook(self):
        """Deve criar WhatsAppInstanceCreate sem webhook"""
        from api.routes.whatsapp import WhatsAppInstanceCreate
        
        data = WhatsAppInstanceCreate(instance_name="test")
        
        assert data.instance_name == "test"
        assert data.webhook_url is None
    
    def test_message_send_model(self):
        """Deve criar WhatsAppMessageSend válido"""
        from api.routes.whatsapp import WhatsAppMessageSend
        
        data = WhatsAppMessageSend(
            instance_name="test",
            to="5511999999999",
            content="Hello World"
        )
        
        assert data.instance_name == "test"
        assert data.to == "5511999999999"
        assert data.content == "Hello World"


class TestGetWhatsAppClient:
    """Testes para get_whatsapp_client dependency"""
    
    def test_get_client_without_api_key(self):
        """Deve lançar 503 se API Key não configurada"""
        from api.routes.whatsapp import get_whatsapp_client
        
        with patch("api.routes.whatsapp.settings") as mock_settings:
            mock_settings.EVOLUTION_API_KEY = None
            
            with pytest.raises(HTTPException) as exc:
                get_whatsapp_client("test-instance")
            
            assert exc.value.status_code == 503
            assert "API Key" in str(exc.value.detail)
    
    def test_get_client_success(self):
        """Deve criar cliente com sucesso"""
        from api.routes.whatsapp import get_whatsapp_client
        
        with patch("api.routes.whatsapp.settings") as mock_settings:
            mock_settings.EVOLUTION_API_KEY = "test-key"
            mock_settings.EVOLUTION_API_URL = "https://api.test.com"
            
            with patch("api.routes.whatsapp.WhatsAppClient") as MockClient:
                mock_client = MagicMock()
                MockClient.return_value = mock_client
                
                result = get_whatsapp_client("my-instance")
                
                MockClient.assert_called_once()
                assert result == mock_client


class TestCreateInstance:
    """Testes para endpoint create_instance"""
    
    @pytest.mark.asyncio
    async def test_create_instance_success(self):
        """Deve criar instância com sucesso"""
        from api.routes.whatsapp import create_instance, WhatsAppInstanceCreate
        
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        
        mock_client = AsyncMock()
        mock_client.create_instance.return_value = {
            "status": "success",
            "instance": {"name": "test-instance"}
        }
        mock_client.close = AsyncMock()
        
        data = WhatsAppInstanceCreate(
            instance_name="test-instance",
            webhook_url="https://example.com/webhook"
        )
        
        with patch("api.routes.whatsapp.get_whatsapp_client") as mock_get:
            mock_get.return_value = mock_client
            
            with patch("api.routes.whatsapp.database") as mock_db:
                mock_db.execute = AsyncMock()
                
                result = await create_instance(data, mock_user)
                
                assert result["status"] == "success"
                mock_client.create_instance.assert_awaited_once()
                mock_db.execute.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_create_instance_with_default_webhook(self):
        """Deve usar webhook padrão se não fornecido"""
        from api.routes.whatsapp import create_instance, WhatsAppInstanceCreate
        
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        
        mock_client = AsyncMock()
        mock_client.create_instance.return_value = {"status": "success"}
        mock_client.close = AsyncMock()
        
        data = WhatsAppInstanceCreate(instance_name="test")
        
        with patch("api.routes.whatsapp.get_whatsapp_client") as mock_get:
            mock_get.return_value = mock_client
            
            with patch("api.routes.whatsapp.database") as mock_db:
                mock_db.execute = AsyncMock()
                
                with patch("api.routes.whatsapp.settings") as mock_settings:
                    mock_settings.API_URL = "https://api.didin.com"
                    
                    await create_instance(data, mock_user)
                    
                    # Webhook deve ser construído com API_URL
                    call_args = mock_client.create_instance.call_args
                    assert "webhook_url" in call_args.kwargs
    
    @pytest.mark.asyncio
    async def test_create_instance_error(self):
        """Deve retornar 400 em caso de erro"""
        from api.routes.whatsapp import create_instance, WhatsAppInstanceCreate
        
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        
        mock_client = AsyncMock()
        mock_client.create_instance.side_effect = Exception("API Error")
        mock_client.close = AsyncMock()
        
        data = WhatsAppInstanceCreate(instance_name="test")
        
        with patch("api.routes.whatsapp.get_whatsapp_client") as mock_get:
            mock_get.return_value = mock_client
            
            with pytest.raises(HTTPException) as exc:
                await create_instance(data, mock_user)
            
            assert exc.value.status_code == 400


class TestGetQRCode:
    """Testes para endpoint get_qrcode"""
    
    @pytest.mark.asyncio
    async def test_get_qrcode_success(self):
        """Deve retornar QR code com sucesso"""
        from api.routes.whatsapp import get_qrcode
        
        mock_user = MagicMock()
        mock_client = AsyncMock()
        mock_client.get_qr_code.return_value = {
            "base64": "data:image/png;base64,QRCODE_DATA"
        }
        mock_client.close = AsyncMock()
        
        with patch("api.routes.whatsapp.get_whatsapp_client") as mock_get:
            mock_get.return_value = mock_client
            
            result = await get_qrcode("my-instance", mock_user)
            
            assert result["base64"].startswith("data:image")
    
    @pytest.mark.asyncio
    async def test_get_qrcode_error(self):
        """Deve retornar 400 em caso de erro"""
        from api.routes.whatsapp import get_qrcode
        
        mock_user = MagicMock()
        mock_client = AsyncMock()
        mock_client.get_qr_code.side_effect = Exception("Not connected")
        mock_client.close = AsyncMock()
        
        with patch("api.routes.whatsapp.get_whatsapp_client") as mock_get:
            mock_get.return_value = mock_client
            
            with pytest.raises(HTTPException) as exc:
                await get_qrcode("my-instance", mock_user)
            
            assert exc.value.status_code == 400


class TestSendMessage:
    """Testes para endpoint send_message"""
    
    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Deve enviar mensagem com sucesso"""
        from api.routes.whatsapp import send_message, WhatsAppMessageSend
        
        mock_user = MagicMock()
        mock_client = AsyncMock()
        mock_client.send_text.return_value = {"status": "SENT", "id": "msg-123"}
        mock_client.close = AsyncMock()
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        
        data = WhatsAppMessageSend(
            instance_name="test",
            to="5511999999999",
            content="Hello!"
        )
        
        with patch("api.routes.whatsapp.get_whatsapp_client") as mock_get:
            mock_get.return_value = mock_client
            
            with patch("api.routes.whatsapp.database") as mock_db:
                mock_db.fetch_one = AsyncMock(return_value=mock_instance)
                mock_db.execute = AsyncMock()
                
                result = await send_message(data, mock_user)
                
                assert result["status"] == "SENT"
                mock_db.execute.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_send_message_instance_not_found(self):
        """Deve funcionar sem salvar se instância não encontrada"""
        from api.routes.whatsapp import send_message, WhatsAppMessageSend
        
        mock_user = MagicMock()
        mock_client = AsyncMock()
        mock_client.send_text.return_value = {"status": "SENT"}
        mock_client.close = AsyncMock()
        
        data = WhatsAppMessageSend(
            instance_name="test",
            to="5511999999999",
            content="Hello!"
        )
        
        with patch("api.routes.whatsapp.get_whatsapp_client") as mock_get:
            mock_get.return_value = mock_client
            
            with patch("api.routes.whatsapp.database") as mock_db:
                mock_db.fetch_one = AsyncMock(return_value=None)
                mock_db.execute = AsyncMock()
                
                result = await send_message(data, mock_user)
                
                assert result["status"] == "SENT"
                mock_db.execute.assert_not_called()
                assert mock_db.execute.await_count == 0
    
    @pytest.mark.asyncio
    async def test_send_message_error(self):
        """Deve retornar 400 em caso de erro"""
        from api.routes.whatsapp import send_message, WhatsAppMessageSend
        
        mock_user = MagicMock()
        mock_client = AsyncMock()
        mock_client.send_text.side_effect = Exception("Send failed")
        mock_client.close = AsyncMock()
        
        data = WhatsAppMessageSend(
            instance_name="test",
            to="5511999999999",
            content="Hello!"
        )
        
        with patch("api.routes.whatsapp.get_whatsapp_client") as mock_get:
            mock_get.return_value = mock_client
            
            with pytest.raises(HTTPException) as exc:
                await send_message(data, mock_user)
            
            assert exc.value.status_code == 400


class TestWhatsAppWebhook:
    """Testes para endpoint webhook"""
    
    @pytest.mark.asyncio
    async def test_webhook_no_instance(self):
        """Deve ignorar webhook sem instance_name"""
        from api.routes.whatsapp import whatsapp_webhook
        
        mock_request = AsyncMock()
        mock_request.json.return_value = {
            "event": "messages.upsert",
            "data": {}
        }
        
        result = await whatsapp_webhook(mock_request)
        
        assert result["status"] == "ignored"
        assert result["reason"] == "no_instance"
    
    @pytest.mark.asyncio
    async def test_webhook_instance_not_found(self):
        """Deve ignorar webhook se instância não existe no DB"""
        from api.routes.whatsapp import whatsapp_webhook
        
        mock_request = AsyncMock()
        mock_request.json.return_value = {
            "event": "messages.upsert",
            "instance": "unknown-instance",
            "data": {}
        }
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=None)
            
            result = await whatsapp_webhook(mock_request)
            
            assert result["status"] == "ignored"
            assert result["reason"] == "instance_not_found"
    
    @pytest.mark.asyncio
    async def test_webhook_messages_upsert_conversation(self):
        """Deve processar mensagem com conversation"""
        from api.routes.whatsapp import whatsapp_webhook
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        
        mock_request = AsyncMock()
        mock_request.json.return_value = {
            "event": "messages.upsert",
            "instance": "test-instance",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": False,
                    "id": "msg-123"
                },
                "message": {
                    "conversation": "Hello, I need help!"
                }
            }
        }
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            mock_db.execute = AsyncMock()
            
            result = await whatsapp_webhook(mock_request)
            
            assert result["status"] == "processed"
            mock_db.execute.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_webhook_messages_upsert_extended_text(self):
        """Deve processar mensagem com extendedTextMessage"""
        from api.routes.whatsapp import whatsapp_webhook
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        
        mock_request = AsyncMock()
        mock_request.json.return_value = {
            "event": "messages.upsert",
            "instance": "test-instance",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": True,
                    "id": "msg-456"
                },
                "message": {
                    "extendedTextMessage": {
                        "text": "Here is your answer"
                    }
                }
            }
        }
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            mock_db.execute = AsyncMock()
            
            result = await whatsapp_webhook(mock_request)
            
            assert result["status"] == "processed"
    
    @pytest.mark.asyncio
    async def test_webhook_messages_empty_content(self):
        """Deve ignorar mensagem sem conteúdo de texto"""
        from api.routes.whatsapp import whatsapp_webhook
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        
        mock_request = AsyncMock()
        mock_request.json.return_value = {
            "event": "messages.upsert",
            "instance": "test-instance",
            "data": {
                "key": {"remoteJid": "test", "fromMe": False},
                "message": {
                    "imageMessage": {}
                }
            }
        }
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            mock_db.execute = AsyncMock()
            
            result = await whatsapp_webhook(mock_request)
            
            assert result["status"] == "processed"
            # Não deve salvar mensagem sem conteúdo
            assert mock_db.execute.await_count == 0
    
    @pytest.mark.asyncio
    async def test_webhook_other_event(self):
        """Deve processar outros tipos de evento"""
        from api.routes.whatsapp import whatsapp_webhook
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.status = "connected"
        
        mock_request = MagicMock()
        # json() returns a coroutine, so use AsyncMock
        mock_request.json = AsyncMock(return_value={
            "event": "connection.update",
            "instance": "test-instance",
            "data": {"state": "open"}
        })
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            mock_db.execute = AsyncMock(return_value=None)
            
            result = await whatsapp_webhook(mock_request)
            
            assert result["status"] == "processed"
            assert result["event"] == "connection.update"


class TestListMessages:
    """Testes para endpoint list_messages"""
    
    @pytest.mark.asyncio
    async def test_list_messages_success(self):
        """Deve listar mensagens com sucesso"""
        from api.routes.whatsapp import list_messages
        
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.is_admin = False
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = mock_user.id
        
        mock_messages = [
            MagicMock(id=uuid.uuid4(), content="Message 1"),
            MagicMock(id=uuid.uuid4(), content="Message 2")
        ]
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            mock_db.fetch_all = AsyncMock(return_value=mock_messages)
            
            result = await list_messages("test-instance", 50, 0, mock_user)
            
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_list_messages_instance_not_found(self):
        """Deve retornar 404 se instância não existe"""
        from api.routes.whatsapp import list_messages
        
        mock_user = MagicMock()
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=None)
            
            with pytest.raises(HTTPException) as exc:
                await list_messages("unknown", 50, 0, mock_user)
            
            assert exc.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_list_messages_not_authorized(self):
        """Deve retornar 403 se não é dono da instância"""
        from api.routes.whatsapp import list_messages
        
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.is_admin = False
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = uuid.uuid4()
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            
            with pytest.raises(HTTPException) as exc:
                await list_messages("test-instance", 50, 0, mock_user)
            
            assert exc.value.status_code == 403
    
    @pytest.mark.asyncio
    async def test_list_messages_admin_access(self):
        """Deve permitir acesso admin a qualquer instância"""
        from api.routes.whatsapp import list_messages
        
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.is_admin = True
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = uuid.uuid4()
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            mock_db.fetch_all = AsyncMock(return_value=[])
            
            result = await list_messages("test-instance", 50, 0, mock_user)
            
            assert result == []


class TestScheduleReconnection:
    """Testes para função _schedule_reconnection"""
    
    @pytest.mark.asyncio
    async def test_schedule_reconnection_first_attempt(self):
        """Deve agendar primeira reconexão com delay de 30s"""
        from api.routes.whatsapp import _schedule_reconnection
        import json
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()
        mock_redis.zadd = AsyncMock()
        
        with patch("shared.redis.get_redis", return_value=mock_redis):
            await _schedule_reconnection("test-instance", str(uuid.uuid4()))
        
        # Deve salvar estado com 1 tentativa
        set_call = mock_redis.set.call_args
        saved_data = json.loads(set_call[0][1])
        assert saved_data["attempts"] == 1
        
        # Deve agendar no Redis
        mock_redis.zadd.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_schedule_reconnection_increment_attempts(self):
        """Deve incrementar tentativas de reconexão"""
        from api.routes.whatsapp import _schedule_reconnection
        import json
        
        existing_data = json.dumps({"attempts": 2, "instance_name": "test-instance"})
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=existing_data)
        mock_redis.set = AsyncMock()
        mock_redis.zadd = AsyncMock()
        
        with patch("shared.redis.get_redis", return_value=mock_redis):
            await _schedule_reconnection("test-instance", str(uuid.uuid4()))
        
        # Deve salvar estado com 3 tentativas
        set_call = mock_redis.set.call_args
        saved_data = json.loads(set_call[0][1])
        assert saved_data["attempts"] == 3
    
    @pytest.mark.asyncio
    async def test_schedule_reconnection_max_attempts(self):
        """Deve parar após 5 tentativas"""
        from api.routes.whatsapp import _schedule_reconnection
        import json
        
        existing_data = json.dumps({"attempts": 5, "instance_name": "test-instance"})
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=existing_data)
        mock_redis.set = AsyncMock()
        mock_redis.zadd = AsyncMock()
        
        with patch("shared.redis.get_redis", return_value=mock_redis):
            await _schedule_reconnection("test-instance", str(uuid.uuid4()))
        
        # Não deve salvar ou agendar
        mock_redis.set.assert_not_called()
        mock_redis.zadd.assert_not_called()


class TestGetInstanceStatus:
    """Testes para endpoint get_instance_status"""
    
    @pytest.mark.asyncio
    async def test_get_status_success(self):
        """Deve retornar status da instância"""
        from api.routes.whatsapp import get_instance_status
        from datetime import datetime, timezone
        
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = mock_user.id
        mock_instance.status = "connected"
        mock_instance.updated_at = datetime.now(timezone.utc)
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            
            with patch("shared.redis.get_redis", return_value=mock_redis):
                result = await get_instance_status("test-instance", mock_user)
        
        assert result["instance_name"] == "test-instance"
        assert result["status"] == "connected"
        assert result["qr_code"] is None
    
    @pytest.mark.asyncio
    async def test_get_status_with_qr_code(self):
        """Deve retornar QR code quando status é awaiting_scan"""
        from api.routes.whatsapp import get_instance_status
        from datetime import datetime, timezone
        
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = mock_user.id
        mock_instance.status = "awaiting_scan"
        mock_instance.updated_at = datetime.now(timezone.utc)
        
        qr_code_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=[qr_code_base64, None])
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            
            with patch("shared.redis.get_redis", return_value=mock_redis):
                result = await get_instance_status("test-instance", mock_user)
        
        assert result["status"] == "awaiting_scan"
        assert result["qr_code"] == qr_code_base64
    
    @pytest.mark.asyncio
    async def test_get_status_with_reconnection_info(self):
        """Deve retornar info de reconexão se disponível"""
        from api.routes.whatsapp import get_instance_status
        from datetime import datetime, timezone
        import json
        
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = mock_user.id
        mock_instance.status = "disconnected"
        mock_instance.updated_at = datetime.now(timezone.utc)
        
        reconnect_info = json.dumps({"attempts": 2, "instance_name": "test-instance"})
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=[None, reconnect_info])
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            
            with patch("shared.redis.get_redis", return_value=mock_redis):
                result = await get_instance_status("test-instance", mock_user)
        
        assert result["reconnection"] is not None
        assert result["reconnection"]["attempts"] == 2
    
    @pytest.mark.asyncio
    async def test_get_status_instance_not_found(self):
        """Deve retornar 404 para instância não encontrada"""
        from api.routes.whatsapp import get_instance_status
        
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=None)
            
            with pytest.raises(HTTPException) as exc:
                await get_instance_status("unknown", mock_user)
            
            assert exc.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_status_not_authorized(self):
        """Deve retornar 403 se não é dono da instância"""
        from api.routes.whatsapp import get_instance_status
        
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = uuid.uuid4()  # Diferente user
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            
            with pytest.raises(HTTPException) as exc:
                await get_instance_status("test-instance", mock_user)
            
            assert exc.value.status_code == 403


class TestForceReconnect:
    """Testes para endpoint force_reconnect"""
    
    @pytest.mark.asyncio
    async def test_force_reconnect_success(self):
        """Deve forçar reconexão com sucesso"""
        from api.routes.whatsapp import force_reconnect
        from datetime import datetime, timezone
        
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = mock_user.id
        mock_instance.status = "disconnected"
        
        mock_client = AsyncMock()
        mock_client.get_qr_code = AsyncMock(return_value={"base64": "qr-code-data"})
        mock_client.close = AsyncMock()
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            mock_db.execute = AsyncMock()
            
            with patch("api.routes.whatsapp.get_whatsapp_client", return_value=mock_client):
                result = await force_reconnect("test-instance", mock_user)
        
        assert result["status"] == "reconnecting"
        assert result["qr_code"] == "qr-code-data"
        mock_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_force_reconnect_api_error(self):
        """Deve retornar 400 em caso de erro da API"""
        from api.routes.whatsapp import force_reconnect
        
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = mock_user.id
        
        mock_client = AsyncMock()
        mock_client.get_qr_code = AsyncMock(side_effect=Exception("API Error"))
        mock_client.close = AsyncMock()
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            
            with patch("api.routes.whatsapp.get_whatsapp_client", return_value=mock_client):
                with pytest.raises(HTTPException) as exc:
                    await force_reconnect("test-instance", mock_user)
                
                assert exc.value.status_code == 400
                assert "API Error" in str(exc.value.detail)
        
        mock_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_force_reconnect_not_found(self):
        """Deve retornar 404 para instância não encontrada"""
        from api.routes.whatsapp import force_reconnect
        
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=None)
            
            with pytest.raises(HTTPException) as exc:
                await force_reconnect("unknown", mock_user)
            
            assert exc.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_force_reconnect_not_authorized(self):
        """Deve retornar 403 se não é dono da instância"""
        from api.routes.whatsapp import force_reconnect
        
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = uuid.uuid4()
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            
            with pytest.raises(HTTPException) as exc:
                await force_reconnect("test-instance", mock_user)
            
            assert exc.value.status_code == 403


class TestWebhookConnectionUpdate:
    """Testes para webhook de atualização de conexão"""
    
    @pytest.mark.asyncio
    async def test_webhook_connection_update_connected(self):
        """Deve atualizar status para connected quando connection.update com state=open"""
        from api.routes.whatsapp import webhook_handler
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = uuid.uuid4()
        mock_instance.name = "test-instance"
        
        webhook_payload = {
            "event": "connection.update",
            "instance": "test-instance",
            "data": {"state": "open"}
        }
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            mock_db.execute = AsyncMock()
            
            result = await webhook_handler(webhook_payload)
        
        assert result["status"] == "processed"
        assert result["event"] == "connection.update"
        assert result["new_status"] == "connected"
    
    @pytest.mark.asyncio
    async def test_webhook_connection_update_disconnected(self):
        """Deve agendar reconexão quando connection.update com state=close"""
        from api.routes.whatsapp import webhook_handler
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = uuid.uuid4()
        mock_instance.name = "test-instance"
        
        webhook_payload = {
            "event": "connection.update",
            "instance": "test-instance",
            "data": {"state": "close"}
        }
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()
        mock_redis.zadd = AsyncMock()
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            mock_db.execute = AsyncMock()
            
            with patch("shared.redis.get_redis", return_value=mock_redis):
                result = await webhook_handler(webhook_payload)
        
        assert result["new_status"] == "disconnected"
        # Deve ter agendado reconexão
        mock_redis.zadd.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_webhook_connection_update_connecting(self):
        """Deve atualizar para connecting"""
        from api.routes.whatsapp import webhook_handler
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = uuid.uuid4()
        mock_instance.name = "test-instance"
        
        webhook_payload = {
            "event": "connection.update",
            "instance": "test-instance",
            "data": {"state": "connecting"}
        }
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            mock_db.execute = AsyncMock()
            
            result = await webhook_handler(webhook_payload)
        
        assert result["new_status"] == "connecting"
    
    @pytest.mark.asyncio
    async def test_webhook_connection_update_error(self):
        """Deve atualizar para error quando refused"""
        from api.routes.whatsapp import webhook_handler
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = uuid.uuid4()
        mock_instance.name = "test-instance"
        
        webhook_payload = {
            "event": "connection.update",
            "instance": "test-instance",
            "data": {"state": "refused"}
        }
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            mock_db.execute = AsyncMock()
            
            result = await webhook_handler(webhook_payload)
        
        assert result["new_status"] == "error"
    
    @pytest.mark.asyncio
    async def test_webhook_connection_update_unknown_state(self):
        """Deve atualizar para unknown quando estado não reconhecido"""
        from api.routes.whatsapp import webhook_handler
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = uuid.uuid4()
        mock_instance.name = "test-instance"
        
        webhook_payload = {
            "event": "connection.update",
            "instance": "test-instance",
            "data": {"state": "weird_state"}
        }
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            mock_db.execute = AsyncMock()
            
            result = await webhook_handler(webhook_payload)
        
        assert result["new_status"] == "unknown"


class TestWebhookQRCodeUpdate:
    """Testes para webhook de atualização de QR code"""
    
    @pytest.mark.asyncio
    async def test_webhook_qrcode_updated(self):
        """Deve armazenar QR code no Redis e atualizar status"""
        from api.routes.whatsapp import webhook_handler
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = uuid.uuid4()
        mock_instance.name = "test-instance"
        
        qr_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."
        
        webhook_payload = {
            "event": "qrcode.updated",
            "instance": "test-instance",
            "data": {"qrcode": {"base64": qr_base64}}
        }
        
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock()
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            mock_db.execute = AsyncMock()
            
            with patch("shared.redis.get_redis", return_value=mock_redis):
                result = await webhook_handler(webhook_payload)
        
        assert result["status"] == "processed"
        assert result["event"] == "qrcode.updated"
        
        # Deve ter armazenado QR code no Redis
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert "whatsapp:qrcode:test-instance" in call_args[0]
        assert qr_base64 in call_args[0]
    
    @pytest.mark.asyncio
    async def test_webhook_qrcode_updated_empty(self):
        """Deve processar mesmo com QR code vazio"""
        from api.routes.whatsapp import webhook_handler
        
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user_id = uuid.uuid4()
        mock_instance.name = "test-instance"
        
        webhook_payload = {
            "event": "qrcode.updated",
            "instance": "test-instance",
            "data": {"qrcode": {}}
        }
        
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock()
        
        with patch("api.routes.whatsapp.database") as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=mock_instance)
            mock_db.execute = AsyncMock()
            
            with patch("shared.redis.get_redis", return_value=mock_redis):
                result = await webhook_handler(webhook_payload)
        
        assert result["status"] == "processed"
