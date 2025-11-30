"""
Testes para integrações Typebot e n8n.
"""
import pytest
from unittest.mock import AsyncMock, patch

from backend.integrations.typebot import (
    TypebotClient,
    TypebotSession,
    TypebotWebhookHandler,
)
from backend.integrations.n8n import (
    N8nClient,
    WorkflowStatus,
    TriggerType,
)


class TestTypebotClient:
    """Testes para o cliente Typebot."""
    
    @pytest.fixture
    def client(self):
        """Cria instância do cliente para testes."""
        return TypebotClient(
            base_url="https://typebot.test",
            api_key="test-api-key"
        )
    
    @pytest.mark.asyncio
    async def test_start_chat_success(self, client):
        """Testa início de sessão de chat."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {
                "sessionId": "session-123",
                "typebot": {"id": "bot-456"},
                "messages": [{"type": "text", "content": "Olá!"}],
            }
            
            result = await client.start_chat("bot-456", {"name": "Test"})
            
            assert result["sessionId"] == "session-123"
            mock_req.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_message(self, client):
        """Testa envio de mensagem."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {
                "messages": [{"type": "text", "content": "Resposta"}],
            }
            
            result = await client.send_message("session-123", "Oi")
            
            assert len(result["messages"]) > 0
    
    @pytest.mark.asyncio
    async def test_list_typebots(self, client):
        """Testa listagem de typebots."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {
                "typebots": [
                    {"id": "1", "name": "Bot 1"},
                    {"id": "2", "name": "Bot 2"},
                ]
            }
            
            result = await client.list_typebots()
            
            assert len(result["typebots"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_results(self, client):
        """Testa obtenção de resultados."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {
                "results": [
                    {"createdAt": "2024-01-01", "variables": []}
                ]
            }
            
            result = await client.get_results("bot-123")
            
            assert "results" in result


class TestTypebotSession:
    """Testes para sessões Typebot."""
    
    def test_session_creation(self):
        """Testa criação de sessão."""
        session = TypebotSession(
            session_id="test-session",
            typebot_id="test-bot",
            user_id="user-123",
        )
        
        assert session.session_id == "test-session"
        assert session.is_active is True
    
    def test_session_update_context(self):
        """Testa atualização de contexto."""
        session = TypebotSession(
            session_id="test-session",
            typebot_id="test-bot",
        )
        
        session.update_context({"key": "value"})
        
        assert session.context["key"] == "value"
    
    def test_session_close(self):
        """Testa fechamento de sessão."""
        session = TypebotSession(
            session_id="test-session",
            typebot_id="test-bot",
        )
        
        session.close()
        
        assert session.is_active is False


class TestTypebotWebhookHandler:
    """Testes para handler de webhooks Typebot."""
    
    @pytest.fixture
    def handler(self):
        """Cria handler para testes."""
        return TypebotWebhookHandler(
            secret="webhook-secret"
        )
    
    def test_validate_signature_success(self, handler):
        """Testa validação de assinatura válida."""
        payload = '{"test": "data"}'
        # Gera assinatura válida
        import hmac
        import hashlib
        signature = hmac.new(
            "webhook-secret".encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        result = handler.validate_signature(payload, f"sha256={signature}")
        
        assert result is True
    
    def test_validate_signature_invalid(self, handler):
        """Testa validação de assinatura inválida."""
        result = handler.validate_signature('{"test": "data"}', "sha256=invalid")
        
        assert result is False
    
    def test_parse_webhook_event(self, handler):
        """Testa parsing de evento webhook."""
        payload = {
            "type": "message.received",
            "data": {
                "sessionId": "session-123",
                "message": "Teste"
            }
        }
        
        event = handler.parse_event(payload)
        
        assert event["type"] == "message.received"
        assert event["data"]["sessionId"] == "session-123"


class TestN8nClient:
    """Testes para o cliente n8n."""
    
    @pytest.fixture
    def client(self):
        """Cria instância do cliente para testes."""
        return N8nClient(
            base_url="https://n8n.test",
            api_key="test-api-key"
        )
    
    @pytest.mark.asyncio
    async def test_list_workflows(self, client):
        """Testa listagem de workflows."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {
                "data": [
                    {"id": "1", "name": "Workflow 1", "active": True},
                    {"id": "2", "name": "Workflow 2", "active": False},
                ]
            }
            
            result = await client.list_workflows()
            
            assert len(result["data"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_workflow(self, client):
        """Testa obtenção de workflow específico."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {
                "id": "workflow-123",
                "name": "Test Workflow",
                "active": True,
                "nodes": []
            }
            
            result = await client.get_workflow("workflow-123")
            
            assert result["id"] == "workflow-123"
            assert result["active"] is True
    
    @pytest.mark.asyncio
    async def test_activate_workflow(self, client):
        """Testa ativação de workflow."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"active": True}
            
            result = await client.activate_workflow("workflow-123")
            
            assert result["active"] is True
    
    @pytest.mark.asyncio
    async def test_deactivate_workflow(self, client):
        """Testa desativação de workflow."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"active": False}
            
            result = await client.deactivate_workflow("workflow-123")
            
            assert result["active"] is False
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self, client):
        """Testa execução de workflow."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {
                "executionId": "exec-456",
                "status": "success",
                "data": {"result": "ok"}
            }
            
            result = await client.execute_workflow(
                "workflow-123",
                data={"input": "test"}
            )
            
            assert result["executionId"] == "exec-456"
            assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_get_executions(self, client):
        """Testa listagem de execuções."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {
                "data": [
                    {"id": "exec-1", "status": "success"},
                    {"id": "exec-2", "status": "error"},
                ]
            }
            
            result = await client.get_executions("workflow-123")
            
            assert len(result["data"]) == 2
    
    @pytest.mark.asyncio
    async def test_trigger_webhook(self, client):
        """Testa trigger via webhook."""
        with patch('aiohttp.ClientSession.post', new_callable=AsyncMock) as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"success": True})
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await client.trigger_webhook(
                "https://n8n.test/webhook/abc123",
                data={"event": "test"}
            )
            
            assert result is not None


class TestWorkflowEnums:
    """Testes para enums de workflow."""
    
    def test_workflow_status_values(self):
        """Testa valores de WorkflowStatus."""
        assert WorkflowStatus.ACTIVE.value == "active"
        assert WorkflowStatus.INACTIVE.value == "inactive"
        assert WorkflowStatus.ERROR.value == "error"
    
    def test_trigger_type_values(self):
        """Testa valores de TriggerType."""
        assert TriggerType.WEBHOOK.value == "webhook"
        assert TriggerType.SCHEDULE.value == "schedule"
        assert TriggerType.MANUAL.value == "manual"


class TestIntegrationErrorHandling:
    """Testes para tratamento de erros nas integrações."""
    
    @pytest.mark.asyncio
    async def test_typebot_connection_error(self):
        """Testa erro de conexão Typebot."""
        client = TypebotClient(
            base_url="https://invalid.test",
            api_key="test-key"
        )
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = ConnectionError("Connection refused")
            
            with pytest.raises(ConnectionError):
                await client.list_typebots()
    
    @pytest.mark.asyncio
    async def test_n8n_api_error(self):
        """Testa erro de API n8n."""
        client = N8nClient(
            base_url="https://n8n.test",
            api_key="test-key"
        )
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = Exception("API Error: 500")
            
            with pytest.raises(Exception) as exc_info:
                await client.list_workflows()
            
            assert "API Error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Testa tratamento de timeout."""
        import asyncio
        
        client = N8nClient(
            base_url="https://n8n.test",
            api_key="test-key"
        )
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = asyncio.TimeoutError("Request timeout")
            
            with pytest.raises(asyncio.TimeoutError):
                await client.execute_workflow("workflow-123")
