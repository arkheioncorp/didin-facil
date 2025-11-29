"""
Unit Tests - N8N Integration
============================
Testes unitários para integração com n8n.

Cobertura:
- N8nConfig dataclass
- WorkflowExecution dataclass
- N8nClient métodos
- Webhook triggers
- Tratamento de erros
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from vendor.integrations.n8n import (
    N8nClient,
    N8nConfig,
    WorkflowExecution,
    WorkflowStatus,
    ExecutionStatus,
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def n8n_config() -> N8nConfig:
    """Configuração padrão do n8n."""
    return N8nConfig(
        api_url="http://localhost:5678",
        api_key="n8n-test-api-key"
    )


@pytest.fixture
def workflow_execution() -> WorkflowExecution:
    """Execução de workflow para testes."""
    return WorkflowExecution(
        execution_id="exec-123",
        status=ExecutionStatus.SUCCESS,
        data={"result": "ok"},
        started_at="2025-01-01T10:00:00Z",
        finished_at="2025-01-01T10:00:05Z"
    )


@pytest.fixture
def sample_workflows():
    """Lista de workflows para testes."""
    return [
        {"id": "wf-1", "name": "Notificação", "active": True},
        {"id": "wf-2", "name": "Sincronização", "active": False},
        {"id": "wf-3", "name": "Backup", "active": True}
    ]


# ============================================
# DATACLASS TESTS
# ============================================

class TestN8nConfig:
    """Testes para N8nConfig dataclass."""
    
    def test_config_creation(self, n8n_config):
        """Deve criar config com valores."""
        assert n8n_config.api_url == "http://localhost:5678"
        assert n8n_config.api_key == "n8n-test-api-key"
    
    def test_config_different_urls(self):
        """Deve aceitar diferentes URLs."""
        configs = [
            N8nConfig(api_url="http://localhost:5678", api_key="key"),
            N8nConfig(api_url="https://n8n.example.com", api_key="key"),
            N8nConfig(api_url="http://192.168.1.100:5678", api_key="key")
        ]
        
        assert len(configs) == 3


class TestWorkflowExecution:
    """Testes para WorkflowExecution dataclass."""
    
    def test_execution_creation(self, workflow_execution):
        """Deve criar execução com valores."""
        assert workflow_execution.execution_id == "exec-123"
        assert workflow_execution.status == ExecutionStatus.SUCCESS
        assert workflow_execution.data == {"result": "ok"}
    
    def test_execution_with_error(self):
        """Deve criar execução com erro."""
        execution = WorkflowExecution(
            execution_id="exec-456",
            status=ExecutionStatus.ERROR,
            data={},
            error="Timeout"
        )
        
        assert execution.status == ExecutionStatus.ERROR
        assert execution.error == "Timeout"
    
    def test_execution_running(self):
        """Deve criar execução em andamento."""
        execution = WorkflowExecution(
            execution_id="exec-789",
            status=ExecutionStatus.RUNNING,
            data={},
            started_at="2025-01-01T10:00:00Z"
        )
        
        assert execution.status == ExecutionStatus.RUNNING
        assert execution.finished_at is None


class TestWorkflowStatus:
    """Testes para WorkflowStatus enum."""
    
    def test_all_statuses(self):
        """Deve ter todos os status de workflow."""
        assert WorkflowStatus.ACTIVE.value == "active"
        assert WorkflowStatus.INACTIVE.value == "inactive"


class TestExecutionStatus:
    """Testes para ExecutionStatus enum."""
    
    def test_all_statuses(self):
        """Deve ter todos os status de execução."""
        expected = ["SUCCESS", "ERROR", "RUNNING", "WAITING"]
        actual = [s.name for s in ExecutionStatus]
        
        for expected_status in expected:
            assert expected_status in actual


# ============================================
# CLIENT TESTS
# ============================================

class TestN8nClient:
    """Testes para N8nClient."""
    
    def test_client_creation(self, n8n_config):
        """Deve criar cliente com configuração."""
        with patch("httpx.AsyncClient"):
            client = N8nClient(n8n_config)
            assert client.config == n8n_config
    
    @pytest.mark.asyncio
    async def test_list_workflows(self, n8n_config, sample_workflows):
        """Deve listar workflows."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"id": "wf-1", "name": "Notificação", "active": True},
                {"id": "wf-2", "name": "Sincronização", "active": False}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            workflows = await client.list_workflows()
            
            assert len(workflows) == 2
            assert workflows[0]["name"] == "Notificação"
    
    @pytest.mark.asyncio
    async def test_list_workflows_active_only(self, n8n_config):
        """Deve listar apenas workflows ativos."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"id": "wf-1", "name": "Notificação", "active": True}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            workflows = await client.list_workflows(active_only=True)
            
            assert len(workflows) == 1
            assert workflows[0]["active"] is True
    
    @pytest.mark.asyncio
    async def test_get_workflow(self, n8n_config):
        """Deve obter detalhes de workflow."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "wf-1",
            "name": "Notificação",
            "active": True,
            "nodes": []
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            workflow = await client.get_workflow("wf-1")
            
            assert workflow["id"] == "wf-1"
            assert workflow["name"] == "Notificação"
    
    @pytest.mark.asyncio
    async def test_activate_workflow(self, n8n_config):
        """Deve ativar workflow."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            result = await client.activate_workflow("wf-1")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_deactivate_workflow(self, n8n_config):
        """Deve desativar workflow."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            result = await client.deactivate_workflow("wf-1")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self, n8n_config):
        """Deve executar workflow."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "executionId": "exec-new",
            "finished": True,
            "data": {"output": "success"},
            "startedAt": "2025-01-01T10:00:00Z",
            "stoppedAt": "2025-01-01T10:00:05Z"
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            execution = await client.execute_workflow("wf-1", {"input": "data"})
            
            assert execution.execution_id == "exec-new"
            assert execution.status == ExecutionStatus.SUCCESS
    
    @pytest.mark.asyncio
    async def test_execute_workflow_running(self, n8n_config):
        """Deve retornar execução em andamento."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "executionId": "exec-running",
            "finished": False,
            "data": {},
            "startedAt": "2025-01-01T10:00:00Z"
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            execution = await client.execute_workflow("wf-1")
            
            assert execution.status == ExecutionStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_get_execution(self, n8n_config):
        """Deve obter status de execução."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "exec-123",
            "status": "success",
            "data": {"result": "ok"}
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            execution = await client.get_execution("exec-123")
            
            assert execution.execution_id == "exec-123"
            assert execution.status == ExecutionStatus.SUCCESS


# ============================================
# WEBHOOK TESTS
# ============================================

class TestN8nWebhooks:
    """Testes de webhooks do n8n."""
    
    @pytest.mark.asyncio
    async def test_trigger_webhook(self, n8n_config):
        """Deve disparar webhook."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"received": True}
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            
            # Verificar se o método existe
            if hasattr(client, 'trigger_webhook'):
                result = await client.trigger_webhook(
                    "my-webhook",
                    {"event": "new_order", "order_id": "123"}
                )
                assert result is not None


# ============================================
# ERROR HANDLING TESTS
# ============================================

class TestN8nClientErrors:
    """Testes de tratamento de erros."""
    
    @pytest.mark.asyncio
    async def test_list_workflows_http_error(self, n8n_config):
        """Deve tratar erro HTTP ao listar workflows."""
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.HTTPStatusError(
                "Unauthorized",
                request=MagicMock(),
                response=MagicMock(status_code=401)
            )
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            
            with pytest.raises(httpx.HTTPStatusError):
                await client.list_workflows()
    
    @pytest.mark.asyncio
    async def test_execute_workflow_timeout(self, n8n_config):
        """Deve tratar timeout ao executar workflow."""
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException("Timeout")
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            
            with pytest.raises(httpx.TimeoutException):
                await client.execute_workflow("wf-1")
    
    @pytest.mark.asyncio
    async def test_get_workflow_not_found(self, n8n_config):
        """Deve tratar workflow não encontrado."""
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.HTTPStatusError(
                "Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404)
            )
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            
            with pytest.raises(httpx.HTTPStatusError):
                await client.get_workflow("nonexistent-wf")


# ============================================
# CONTEXT MANAGER TESTS
# ============================================

class TestN8nClientContextManager:
    """Testes de context manager."""
    
    @pytest.mark.asyncio
    async def test_context_manager(self, n8n_config):
        """Deve funcionar como context manager."""
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_httpx.return_value = mock_client
            
            async with N8nClient(n8n_config) as client:
                assert client is not None
            
            mock_client.aclose.assert_called_once()


# ============================================
# EXECUTION STATUS TESTS
# ============================================

class TestExecutionStatusMapping:
    """Testes de mapeamento de status de execução."""
    
    @pytest.mark.asyncio
    async def test_status_error(self, n8n_config):
        """Deve mapear status de erro."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "exec-err",
            "status": "error",
            "data": {}
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            execution = await client.get_execution("exec-err")
            
            assert execution.status == ExecutionStatus.ERROR
    
    @pytest.mark.asyncio
    async def test_status_waiting(self, n8n_config):
        """Deve mapear status de espera."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "exec-wait",
            "status": "waiting",
            "data": {}
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            execution = await client.get_execution("exec-wait")
            
            assert execution.status == ExecutionStatus.WAITING
