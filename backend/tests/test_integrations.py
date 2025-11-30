"""
Testes para integrações Typebot e n8n.
"""
import pytest
import respx
from httpx import Response

from integrations.typebot import (
    TypebotClient,
    TypebotSession,
    TypebotWebhookHandler,
    TypebotStatus,
)
from integrations.n8n import (
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
            api_url="https://typebot.test",
            api_key="test-api-key"
        )
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_start_chat_success(self, client):
        """Testa início de sessão de chat."""
        respx.post("https://typebot.test/api/v1/typebots/bot-456/startChat").mock(
            return_value=Response(200, json={
                "sessionId": "session-123",
                "typebot": {"id": "bot-456"},
                "messages": [{"id": "1", "type": "text", "content": "Olá!"}],
            })
        )
        
        result = await client.start_chat("bot-456", variables={"name": "Test"})
        
        assert result.session_id == "session-123"
        assert result.typebot_id == "bot-456"
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_send_message(self, client):
        """Testa envio de mensagem."""
        respx.post("https://typebot.test/api/v1/sessions/session-123/continueChat").mock(
            return_value=Response(200, json={
                "messages": [{"id": "1", "type": "text", "content": "Resposta"}],
            })
        )
        
        result = await client.send_message("session-123", "Oi")
        
        assert len(result) > 0
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_list_typebots(self, client):
        """Testa listagem de typebots."""
        respx.get("https://typebot.test/api/v1/typebots").mock(
            return_value=Response(200, json={
                "typebots": [
                    {"id": "1", "name": "Bot 1"},
                    {"id": "2", "name": "Bot 2"},
                ]
            })
        )
        
        result = await client.list_typebots()
        
        assert len(result) == 2
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_results(self, client):
        """Testa obtenção de resultados."""
        respx.get("https://typebot.test/api/v1/typebots/bot-123/results").mock(
            return_value=Response(200, json={
                "results": [
                    {"createdAt": "2024-01-01", "variables": []}
                ]
            })
        )
        
        result = await client.get_results("bot-123")
        
        assert len(result) >= 0


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
        assert session.typebot_id == "test-bot"
        assert session.user_id == "user-123"
        assert session.status == TypebotStatus.ACTIVE
    
    def test_session_default_values(self):
        """Testa valores padrão da sessão."""
        session = TypebotSession(
            session_id="test-session",
            typebot_id="test-bot",
        )
        
        assert session.variables == {}
        assert session.messages == []
        assert session.created_at is not None
    
    def test_session_with_variables(self):
        """Testa sessão com variáveis."""
        session = TypebotSession(
            session_id="test-session",
            typebot_id="test-bot",
            variables={"key": "value"}
        )
        
        assert session.variables["key"] == "value"


class TestTypebotWebhookHandler:
    """Testes para handler de webhooks Typebot."""
    
    @pytest.fixture
    def handler(self):
        """Cria handler para testes."""
        return TypebotWebhookHandler()
    
    def test_handler_creation(self, handler):
        """Testa criação de handler."""
        assert handler._handlers == {}
    
    def test_on_decorator(self, handler):
        """Testa decorator on()."""
        @handler.on("message.received")
        async def handle_message(payload):
            return {"status": "handled"}
        
        assert "message.received" in handler._handlers
    
    @pytest.mark.asyncio
    async def test_process_webhook_with_handler(self, handler):
        """Testa processamento de webhook com handler registrado."""
        @handler.on("test.event")
        async def handle_test(payload):
            return {"status": "ok", "data": payload.get("data")}
        
        result = await handler.process_webhook({
            "type": "test.event",
            "data": {"key": "value"}
        })
        
        assert result["status"] == "ok"
    
    @pytest.mark.asyncio
    async def test_process_webhook_no_handler(self, handler):
        """Testa processamento sem handler registrado."""
        result = await handler.process_webhook({
            "type": "unknown.event",
            "data": {}
        })
        
        assert result["status"] == "ignored"


class TestN8nClient:
    """Testes para o cliente n8n."""
    
    @pytest.fixture
    def client(self):
        """Cria instância do cliente para testes."""
        return N8nClient(
            api_url="https://n8n.test",
            api_key="test-api-key",
            webhook_url="https://n8n.test/webhook"
        )
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_list_workflows(self, client):
        """Testa listagem de workflows."""
        respx.get("https://n8n.test/api/v1/workflows").mock(
            return_value=Response(200, json={
                "data": [
                    {"id": "1", "name": "Workflow 1", "active": True},
                    {"id": "2", "name": "Workflow 2", "active": False},
                ]
            })
        )
        
        result = await client.list_workflows()
        
        assert len(result) == 2
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_workflow(self, client):
        """Testa obtenção de workflow específico."""
        respx.get("https://n8n.test/api/v1/workflows/workflow-123").mock(
            return_value=Response(200, json={
                "id": "workflow-123",
                "name": "Test Workflow",
                "active": True,
                "nodes": []
            })
        )
        
        result = await client.get_workflow("workflow-123")
        
        assert result is not None
        assert result.id == "workflow-123"
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_activate_workflow(self, client):
        """Testa ativação de workflow."""
        respx.post(
            "https://n8n.test/api/v1/workflows/workflow-123/activate"
        ).mock(
            return_value=Response(200, json={"active": True})
        )
        
        result = await client.activate_workflow("workflow-123")
        
        assert result is True
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_deactivate_workflow(self, client):
        """Testa desativação de workflow."""
        respx.post(
            "https://n8n.test/api/v1/workflows/workflow-123/deactivate"
        ).mock(
            return_value=Response(200, json={"active": False})
        )
        
        result = await client.deactivate_workflow("workflow-123")
        
        assert result is True
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_trigger_workflow_by_id(self, client):
        """Testa execução de workflow por ID."""
        respx.post(
            "https://n8n.test/api/v1/workflows/workflow-123/execute"
        ).mock(
            return_value=Response(200, json={
                "executionId": "exec-456",
                "success": True,
                "data": {"result": "ok"}
            })
        )
        
        result = await client.trigger_workflow_by_id(
            "workflow-123",
            data={"input": "test"}
        )
        
        assert result.workflow_id == "workflow-123"
        assert result.status == WorkflowStatus.SUCCESS
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_executions(self, client):
        """Testa listagem de execuções."""
        respx.get("https://n8n.test/api/v1/executions").mock(
            return_value=Response(200, json={
                "data": [
                    {"id": "exec-1", "status": "success"},
                    {"id": "exec-2", "status": "error"},
                ]
            })
        )
        
        result = await client.get_executions()
        
        assert len(result) == 2
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_trigger_webhook(self, client):
        """Testa trigger via webhook."""
        respx.post("https://n8n.test/webhook/test-path").mock(
            return_value=Response(200, json={"success": True})
        )
        
        result = await client.trigger_webhook(
            "/test-path",
            data={"event": "test"}
        )
        
        assert result["success"] is True


class TestWorkflowEnums:
    """Testes para enums de workflow."""
    
    def test_workflow_status_values(self):
        """Testa valores de WorkflowStatus."""
        assert WorkflowStatus.SUCCESS.value == "success"
        assert WorkflowStatus.ERROR.value == "error"
        assert WorkflowStatus.WAITING.value == "waiting"
        assert WorkflowStatus.RUNNING.value == "running"
    
    def test_trigger_type_values(self):
        """Testa valores de TriggerType."""
        assert TriggerType.WEBHOOK.value == "webhook"
        assert TriggerType.SCHEDULE.value == "schedule"
        assert TriggerType.MANUAL.value == "manual"
        assert TriggerType.EVENT.value == "event"


class TestIntegrationErrorHandling:
    """Testes para tratamento de erros nas integrações."""
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_typebot_connection_error(self):
        """Testa erro de conexão Typebot."""
        import httpx
        
        client = TypebotClient(
            api_url="https://invalid.test",
            api_key="test-key"
        )
        
        respx.get("https://invalid.test/api/v1/typebots").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        
        with pytest.raises(httpx.ConnectError):
            await client.list_typebots()
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_n8n_api_error(self):
        """Testa erro de API n8n."""
        import httpx
        
        client = N8nClient(
            api_url="https://n8n.test",
            api_key="test-key"
        )
        
        respx.get("https://n8n.test/api/v1/workflows").mock(
            return_value=Response(500, json={"error": "Internal Server Error"})
        )
        
        with pytest.raises(httpx.HTTPStatusError):
            await client.list_workflows()
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_timeout_handling(self):
        """Testa tratamento de timeout."""
        import httpx
        
        client = N8nClient(
            api_url="https://n8n.test",
            api_key="test-key",
            webhook_url="https://n8n.test/webhook"
        )
        
        respx.post(
            "https://n8n.test/api/v1/workflows/workflow-123/execute"
        ).mock(
            side_effect=httpx.TimeoutException("Request timeout")
        )
        
        with pytest.raises(httpx.TimeoutException):
            await client.trigger_workflow_by_id("workflow-123")
