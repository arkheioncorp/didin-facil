"""Testes abrangentes para Automation Routes (n8n)."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class MockWorkflow:
    """Mock de Workflow do n8n."""
    def __init__(self, id="wf-123", name="Test Workflow", active=True):
        self.id = id
        self.name = name
        self.active = active
        self.nodes = [{"type": "start"}, {"type": "end"}]
        self.created_at = datetime(2024, 1, 1, 0, 0, 0)
        self.updated_at = datetime(2024, 1, 2, 0, 0, 0)


class MockExecution:
    """Mock de Execution do n8n."""
    def __init__(self, id="exec-123", workflow_id="wf-123", status=None, error=None):
        from integrations.n8n import WorkflowStatus
        self.id = id
        self.workflow_id = workflow_id
        self.status = status or WorkflowStatus.SUCCESS
        self.started_at = datetime(2024, 1, 1, 12, 0, 0)
        self.finished_at = datetime(2024, 1, 1, 12, 0, 30)
        self.data = {"result": "success"}
        self.error = error


@pytest.fixture
def mock_current_user():
    return {"id": "user-123", "email": "test@example.com"}


@pytest.fixture
def mock_subscription_service():
    service = AsyncMock()
    service.can_use_feature = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_n8n_client():
    client = AsyncMock()
    client.list_workflows = AsyncMock(return_value=[MockWorkflow()])
    client.get_workflow = AsyncMock(return_value=MockWorkflow())
    client.activate_workflow = AsyncMock(return_value=True)
    client.deactivate_workflow = AsyncMock(return_value=True)
    client.trigger_workflow_by_id = AsyncMock(return_value=MockExecution())
    client.trigger_webhook = AsyncMock(return_value={"ok": True})
    client.get_executions = AsyncMock(return_value=[MockExecution()])
    return client


class TestModels:
    """Testes para os modelos de request."""

    def test_trigger_webhook_request(self):
        """Teste do modelo TriggerWebhookRequest."""
        from api.routes.automation import TriggerWebhookRequest
        req = TriggerWebhookRequest(
            webhook_path="/test",
            data={"key": "value"}
        )
        assert req.webhook_path == "/test"
        assert req.data["key"] == "value"

    def test_execute_workflow_request_minimal(self):
        """Teste do modelo ExecuteWorkflowRequest mínimo."""
        from api.routes.automation import ExecuteWorkflowRequest
        req = ExecuteWorkflowRequest(workflow_id="wf-123")
        assert req.workflow_id == "wf-123"
        assert req.data is None

    def test_execute_workflow_request_full(self):
        """Teste do modelo ExecuteWorkflowRequest completo."""
        from api.routes.automation import ExecuteWorkflowRequest
        req = ExecuteWorkflowRequest(
            workflow_id="wf-123",
            data={"param": "value"}
        )
        assert req.data == {"param": "value"}


class TestListWorkflows:
    """Testes para list_workflows."""

    async def test_list_workflows_success(self, mock_current_user, mock_n8n_client):
        """Teste de listagem bem-sucedida."""
        from api.routes.automation import list_workflows
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            result = await list_workflows(
                active=True,
                limit=10,
                current_user=mock_current_user
            )
        
        assert "workflows" in result
        assert len(result["workflows"]) == 1
        assert result["workflows"][0]["id"] == "wf-123"
        assert result["workflows"][0]["name"] == "Test Workflow"

    async def test_list_workflows_error(self, mock_current_user, mock_n8n_client):
        """Teste de erro na listagem."""
        from api.routes.automation import list_workflows
        
        mock_n8n_client.list_workflows = AsyncMock(side_effect=Exception("API Error"))
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            with pytest.raises(HTTPException) as exc:
                await list_workflows(current_user=mock_current_user)
        
        assert exc.value.status_code == 500


class TestGetWorkflow:
    """Testes para get_workflow."""

    async def test_get_workflow_success(self, mock_current_user, mock_n8n_client):
        """Teste de obtenção bem-sucedida."""
        from api.routes.automation import get_workflow
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            result = await get_workflow(
                workflow_id="wf-123",
                current_user=mock_current_user
            )
        
        assert result["id"] == "wf-123"
        assert result["nodes_count"] == 2

    async def test_get_workflow_not_found(self, mock_current_user, mock_n8n_client):
        """Teste de workflow não encontrado."""
        from api.routes.automation import get_workflow
        
        mock_n8n_client.get_workflow = AsyncMock(return_value=None)
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            with pytest.raises(HTTPException) as exc:
                await get_workflow(
                    workflow_id="wf-invalid",
                    current_user=mock_current_user
                )
        
        assert exc.value.status_code == 404


class TestActivateWorkflow:
    """Testes para activate_workflow."""

    async def test_activate_workflow_success(self, mock_current_user, mock_n8n_client, mock_subscription_service):
        """Teste de ativação bem-sucedida."""
        from api.routes.automation import activate_workflow
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            result = await activate_workflow(
                workflow_id="wf-123",
                current_user=mock_current_user,
                service=mock_subscription_service
            )
        
        assert result["status"] == "activated"
        assert result["workflow_id"] == "wf-123"

    async def test_activate_workflow_limit_reached(self, mock_current_user, mock_n8n_client, mock_subscription_service):
        """Teste de limite atingido."""
        from api.routes.automation import activate_workflow
        
        mock_subscription_service.can_use_feature = AsyncMock(return_value=False)
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            with pytest.raises(HTTPException) as exc:
                await activate_workflow(
                    workflow_id="wf-123",
                    current_user=mock_current_user,
                    service=mock_subscription_service
                )
        
        assert exc.value.status_code == 402

    async def test_activate_workflow_failed(self, mock_current_user, mock_n8n_client, mock_subscription_service):
        """Teste de falha na ativação."""
        from api.routes.automation import activate_workflow
        
        mock_n8n_client.activate_workflow = AsyncMock(return_value=False)
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            with pytest.raises(HTTPException) as exc:
                await activate_workflow(
                    workflow_id="wf-123",
                    current_user=mock_current_user,
                    service=mock_subscription_service
                )
        
        assert exc.value.status_code == 500


class TestDeactivateWorkflow:
    """Testes para deactivate_workflow."""

    async def test_deactivate_workflow_success(self, mock_current_user, mock_n8n_client):
        """Teste de desativação bem-sucedida."""
        from api.routes.automation import deactivate_workflow
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            result = await deactivate_workflow(
                workflow_id="wf-123",
                current_user=mock_current_user
            )
        
        assert result["status"] == "deactivated"

    async def test_deactivate_workflow_failed(self, mock_current_user, mock_n8n_client):
        """Teste de falha na desativação."""
        from api.routes.automation import deactivate_workflow
        
        mock_n8n_client.deactivate_workflow = AsyncMock(return_value=False)
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            with pytest.raises(HTTPException) as exc:
                await deactivate_workflow(
                    workflow_id="wf-123",
                    current_user=mock_current_user
                )
        
        assert exc.value.status_code == 500


class TestExecuteWorkflow:
    """Testes para execute_workflow."""

    async def test_execute_workflow_success(self, mock_current_user, mock_n8n_client):
        """Teste de execução bem-sucedida."""
        from api.routes.automation import execute_workflow
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            result = await execute_workflow(
                workflow_id="wf-123",
                data={"param": "value"},
                current_user=mock_current_user
            )
        
        assert result["execution_id"] == "exec-123"
        assert result["status"] == "success"

    async def test_execute_workflow_error(self, mock_current_user, mock_n8n_client):
        """Teste de erro na execução."""
        from api.routes.automation import execute_workflow
        
        mock_n8n_client.trigger_workflow_by_id = AsyncMock(side_effect=Exception("Execution failed"))
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            with pytest.raises(HTTPException) as exc:
                await execute_workflow(
                    workflow_id="wf-123",
                    current_user=mock_current_user
                )
        
        assert exc.value.status_code == 500


class TestTriggerWebhook:
    """Testes para trigger_webhook."""

    async def test_trigger_webhook_success(self, mock_current_user, mock_n8n_client):
        """Teste de disparo bem-sucedido."""
        from api.routes.automation import (TriggerWebhookRequest,
                                           trigger_webhook)
        
        request = TriggerWebhookRequest(
            webhook_path="/test",
            data={"key": "value"}
        )
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            result = await trigger_webhook(
                data=request,
                current_user=mock_current_user
            )
        
        assert result["status"] == "triggered"

    async def test_trigger_webhook_error(self, mock_current_user, mock_n8n_client):
        """Teste de erro no disparo."""
        from api.routes.automation import (TriggerWebhookRequest,
                                           trigger_webhook)
        
        request = TriggerWebhookRequest(
            webhook_path="/test",
            data={"key": "value"}
        )
        
        mock_n8n_client.trigger_webhook = AsyncMock(side_effect=Exception("Webhook failed"))
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            with pytest.raises(HTTPException) as exc:
                await trigger_webhook(
                    data=request,
                    current_user=mock_current_user
                )
        
        assert exc.value.status_code == 500


class TestListExecutions:
    """Testes para list_executions."""

    async def test_list_executions_success(self, mock_current_user, mock_n8n_client):
        """Teste de listagem bem-sucedida."""
        from api.routes.automation import list_executions
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            result = await list_executions(
                workflow_id="wf-123",
                limit=10,
                current_user=mock_current_user
            )
        
        assert "executions" in result
        assert len(result["executions"]) == 1

    async def test_list_executions_with_status(self, mock_current_user, mock_n8n_client):
        """Teste de listagem com filtro de status."""
        from api.routes.automation import list_executions
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            result = await list_executions(
                status="success",
                current_user=mock_current_user
            )
        
        assert "executions" in result

    async def test_list_executions_invalid_status(self, mock_current_user, mock_n8n_client):
        """Teste de status inválido."""
        from api.routes.automation import list_executions
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            with pytest.raises(HTTPException) as exc:
                await list_executions(
                    status="invalid_status",
                    current_user=mock_current_user
                )
        
        assert exc.value.status_code == 400


class TestWorkflowTemplates:
    """Testes para templates de workflow."""

    async def test_list_workflow_templates(self):
        """Teste de listagem de templates."""
        from api.routes.automation import list_workflow_templates
        
        result = await list_workflow_templates()
        
        assert "templates" in result
        assert isinstance(result["templates"], list)

    async def test_get_workflow_template_not_found(self):
        """Teste de template não encontrado."""
        from api.routes.automation import get_workflow_template
        
        with pytest.raises(HTTPException) as exc:
            await get_workflow_template("invalid-template")
        
        assert exc.value.status_code == 404


class TestQuickActions:
    """Testes para ações rápidas."""

    async def test_trigger_price_drop_alert_success(self, mock_current_user, mock_n8n_client):
        """Teste de alerta de queda de preço."""
        from api.routes.automation import trigger_price_drop_alert
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            result = await trigger_price_drop_alert(
                product_name="Produto Teste",
                old_price=100.0,
                new_price=80.0,
                product_url="https://example.com/produto",
                current_user=mock_current_user
            )
        
        assert result["status"] == "triggered"

    async def test_trigger_price_drop_alert_webhook_not_configured(self, mock_current_user, mock_n8n_client):
        """Teste de webhook não configurado."""
        from api.routes.automation import trigger_price_drop_alert
        
        mock_n8n_client.trigger_webhook = AsyncMock(side_effect=Exception("Not configured"))
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            result = await trigger_price_drop_alert(
                product_name="Produto",
                old_price=100.0,
                new_price=80.0,
                product_url="https://example.com",
                current_user=mock_current_user
            )
        
        assert result["status"] == "skipped"

    async def test_trigger_new_lead_success(self, mock_current_user, mock_n8n_client):
        """Teste de novo lead."""
        from api.routes.automation import trigger_new_lead
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            result = await trigger_new_lead(
                name="João Silva",
                phone="5511999999999",
                email="joao@example.com",
                source="instagram",
                current_user=mock_current_user
            )
        
        assert result["status"] == "triggered"

    async def test_trigger_new_lead_webhook_not_configured(self, mock_current_user, mock_n8n_client):
        """Teste de webhook não configurado para lead."""
        from api.routes.automation import trigger_new_lead
        
        mock_n8n_client.trigger_webhook = AsyncMock(side_effect=Exception("Not configured"))
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            result = await trigger_new_lead(
                name="João",
                phone="5511999999999",
                current_user=mock_current_user
            )
        
        assert result["status"] == "skipped"

    async def test_trigger_post_published_success(self, mock_current_user, mock_n8n_client):
        """Teste de post publicado."""
        from api.routes.automation import trigger_post_published
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            result = await trigger_post_published(
                platform="instagram",
                post_id="post-123",
                post_url="https://instagram.com/p/abc123",
                current_user=mock_current_user
            )
        
        assert result["status"] == "triggered"

    async def test_trigger_post_published_webhook_not_configured(self, mock_current_user, mock_n8n_client):
        """Teste de webhook não configurado para post."""
        from api.routes.automation import trigger_post_published
        
        mock_n8n_client.trigger_webhook = AsyncMock(side_effect=Exception("Not configured"))
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            result = await trigger_post_published(
                platform="tiktok",
                post_id="post-456",
                post_url="https://tiktok.com/@user/123",
                current_user=mock_current_user
            )
        
        assert result["status"] == "skipped"


class TestRouterConfig:
    """Testes para configuração do router."""

    def test_router_exists(self):
        """Teste se router existe."""
        from api.routes.automation import router
        assert router is not None

    def test_n8n_client_exists(self):
        """Teste se cliente n8n existe."""
        from api.routes.automation import n8n_client
        assert n8n_client is not None
