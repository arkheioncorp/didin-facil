"""
Testes para Automation Routes - api/routes/automation.py
Cobertura: list_workflows, get_workflow, activate_workflow, deactivate_workflow,
           execute_workflow, trigger_webhook, list_didin_workflows, list_executions
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from fastapi import HTTPException


# ============================================
# MOCKS & FIXTURES
# ============================================

@pytest.fixture
def mock_user():
    """Mock de usuário autenticado"""
    user = MagicMock()
    user.id = "user-123"
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_workflow():
    """Mock de workflow"""
    wf = MagicMock()
    wf.id = "wf-123"
    wf.name = "Test Workflow"
    wf.active = True
    wf.nodes = [MagicMock(), MagicMock()]
    wf.created_at = datetime(2024, 1, 1)
    wf.updated_at = datetime(2024, 1, 15)
    return wf


@pytest.fixture
def mock_execution():
    """Mock de execução de workflow"""
    exec = MagicMock()
    exec.id = "exec-123"
    exec.workflow_id = "wf-123"
    # status é um Enum com atributo .value
    status_mock = MagicMock()
    status_mock.value = "success"
    exec.status = status_mock
    exec.started_at = datetime(2024, 1, 15, 10, 0, 0)
    exec.finished_at = datetime(2024, 1, 15, 10, 0, 5)
    exec.data = {"result": "ok"}
    return exec


@pytest.fixture
def mock_n8n_client(mock_workflow, mock_execution):
    """Mock do N8nClient"""
    client = AsyncMock()
    client.list_workflows.return_value = [mock_workflow]
    client.get_workflow.return_value = mock_workflow
    client.activate_workflow.return_value = True
    client.deactivate_workflow.return_value = True
    client.execute_workflow.return_value = mock_execution
    client.trigger_webhook.return_value = {"success": True}
    client.list_executions.return_value = [mock_execution]
    return client


# ============================================
# TESTS: List Workflows
# ============================================

class TestListWorkflows:
    """Testes do endpoint list_workflows"""
    
    @pytest.mark.asyncio
    async def test_list_workflows_success(self, mock_user, mock_n8n_client):
        """Deve listar workflows com sucesso"""
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            from api.routes.automation import list_workflows
            
            response = await list_workflows(current_user=mock_user)
            
            assert "workflows" in response
            assert len(response["workflows"]) == 1
            assert response["workflows"][0]["id"] == "wf-123"
            assert response["workflows"][0]["name"] == "Test Workflow"
    
    @pytest.mark.asyncio
    async def test_list_workflows_with_active_filter(self, mock_user, mock_n8n_client):
        """Deve filtrar por status ativo"""
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            from api.routes.automation import list_workflows
            
            await list_workflows(active=True, current_user=mock_user)
            
            mock_n8n_client.list_workflows.assert_called_once_with(True, 50)
    
    @pytest.mark.asyncio
    async def test_list_workflows_with_limit(self, mock_user, mock_n8n_client):
        """Deve respeitar o limite"""
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            from api.routes.automation import list_workflows
            
            await list_workflows(limit=10, current_user=mock_user)
            
            mock_n8n_client.list_workflows.assert_called_once_with(None, 10)
    
    @pytest.mark.asyncio
    async def test_list_workflows_error(self, mock_user, mock_n8n_client):
        """Deve retornar 500 em caso de erro"""
        mock_n8n_client.list_workflows.side_effect = Exception("API Error")
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            from api.routes.automation import list_workflows
            
            with pytest.raises(HTTPException) as exc_info:
                await list_workflows(current_user=mock_user)
            
            assert exc_info.value.status_code == 500


# ============================================
# TESTS: Get Workflow
# ============================================

class TestGetWorkflow:
    """Testes do endpoint get_workflow"""
    
    @pytest.mark.asyncio
    async def test_get_workflow_success(self, mock_user, mock_n8n_client, mock_workflow):
        """Deve retornar workflow existente"""
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            from api.routes.automation import get_workflow
            
            response = await get_workflow(
                workflow_id="wf-123",
                current_user=mock_user
            )
            
            assert response["id"] == "wf-123"
            assert response["name"] == "Test Workflow"
            assert response["nodes_count"] == 2
    
    @pytest.mark.asyncio
    async def test_get_workflow_not_found(self, mock_user, mock_n8n_client):
        """Deve retornar 404 se não encontrado"""
        mock_n8n_client.get_workflow.return_value = None
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            from api.routes.automation import get_workflow
            
            with pytest.raises(HTTPException) as exc_info:
                await get_workflow(workflow_id="invalid", current_user=mock_user)
            
            assert exc_info.value.status_code == 404


# ============================================
# TESTS: Activate Workflow
# ============================================

class TestActivateWorkflow:
    """Testes do endpoint activate_workflow"""
    
    @pytest.mark.asyncio
    async def test_activate_success(self, mock_user, mock_n8n_client):
        """Deve ativar workflow com sucesso"""
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            from api.routes.automation import activate_workflow
            
            response = await activate_workflow(
                workflow_id="wf-123",
                current_user=mock_user
            )
            
            assert response["status"] == "activated"
            assert response["workflow_id"] == "wf-123"
    
    @pytest.mark.asyncio
    async def test_activate_failure(self, mock_user, mock_n8n_client):
        """Deve retornar 500 se falhar ao ativar"""
        mock_n8n_client.activate_workflow.return_value = False
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            from api.routes.automation import activate_workflow
            
            with pytest.raises(HTTPException) as exc_info:
                await activate_workflow(workflow_id="wf-123", current_user=mock_user)
            
            assert exc_info.value.status_code == 500


# ============================================
# TESTS: Deactivate Workflow
# ============================================

class TestDeactivateWorkflow:
    """Testes do endpoint deactivate_workflow"""
    
    @pytest.mark.asyncio
    async def test_deactivate_success(self, mock_user, mock_n8n_client):
        """Deve desativar workflow com sucesso"""
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            from api.routes.automation import deactivate_workflow
            
            response = await deactivate_workflow(
                workflow_id="wf-123",
                current_user=mock_user
            )
            
            assert response["status"] == "deactivated"
            assert response["workflow_id"] == "wf-123"
    
    @pytest.mark.asyncio
    async def test_deactivate_failure(self, mock_user, mock_n8n_client):
        """Deve retornar 500 se falhar ao desativar"""
        mock_n8n_client.deactivate_workflow.return_value = False
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            from api.routes.automation import deactivate_workflow
            
            with pytest.raises(HTTPException) as exc_info:
                await deactivate_workflow(workflow_id="wf-123", current_user=mock_user)
            
            assert exc_info.value.status_code == 500


# ============================================
# TESTS: Execute Workflow
# ============================================

class TestExecuteWorkflow:
    """Testes do endpoint execute_workflow"""
    
    @pytest.mark.asyncio
    async def test_execute_success(self, mock_user, mock_n8n_client, mock_execution):
        """Deve executar workflow com sucesso"""
        mock_n8n_client.trigger_workflow_by_id.return_value = mock_execution
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            from api.routes.automation import execute_workflow
            
            response = await execute_workflow(
                workflow_id="wf-123",
                data={"key": "value"},
                current_user=mock_user
            )
            
            assert response["execution_id"] == "exec-123"
    
    @pytest.mark.asyncio
    async def test_execute_error(self, mock_user, mock_n8n_client):
        """Deve retornar 500 em caso de erro"""
        mock_n8n_client.trigger_workflow_by_id.side_effect = Exception("Execution failed")
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            from api.routes.automation import execute_workflow
            
            with pytest.raises(HTTPException) as exc_info:
                await execute_workflow(
                    workflow_id="wf-123",
                    data=None,
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 500


# ============================================
# TESTS: Trigger Webhook
# ============================================

class TestTriggerWebhook:
    """Testes do endpoint trigger_webhook"""
    
    @pytest.mark.asyncio
    async def test_trigger_webhook_success(self, mock_user, mock_n8n_client):
        """Deve disparar webhook com sucesso"""
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            from api.routes.automation import trigger_webhook, TriggerWebhookRequest
            
            request = TriggerWebhookRequest(
                webhook_path="/webhook/test",
                data={"event": "test"}
            )
            
            response = await trigger_webhook(data=request, current_user=mock_user)
            
            assert response["status"] == "triggered"
    
    @pytest.mark.asyncio
    async def test_trigger_webhook_error(self, mock_user, mock_n8n_client):
        """Deve retornar 500 em caso de erro"""
        mock_n8n_client.trigger_webhook.side_effect = Exception("Webhook failed")
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            from api.routes.automation import trigger_webhook, TriggerWebhookRequest
            
            request = TriggerWebhookRequest(
                webhook_path="/webhook/test",
                data={}
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await trigger_webhook(data=request, current_user=mock_user)
            
            assert exc_info.value.status_code == 500


# ============================================
# TESTS: Workflow Templates
# ============================================

class TestWorkflowTemplates:
    """Testes dos endpoints de templates"""
    
    @pytest.mark.asyncio
    async def test_list_templates(self):
        """Deve listar templates de workflows"""
        mock_workflows = {
            "price_alert": {
                "name": "Price Alert",
                "description": "Alerta de preço",
                "trigger": MagicMock(value="webhook"),
                "webhook_path": "/test",
                "actions": ["notify"]
            }
        }
        
        with patch("api.routes.automation.DIDIN_N8N_WORKFLOWS", mock_workflows):
            from api.routes.automation import list_workflow_templates
            
            response = await list_workflow_templates()
            
            assert "templates" in response
            assert len(response["templates"]) == 1
    
    @pytest.mark.asyncio
    async def test_get_template_success(self):
        """Deve retornar template existente"""
        mock_trigger = MagicMock()
        mock_trigger.value = "webhook"
        
        mock_workflows = {
            "price_alert": {
                "name": "Price Alert",
                "description": "Alerta de preço",
                "trigger": mock_trigger,
                "actions": ["notify"]
            }
        }
        
        with patch("api.routes.automation.DIDIN_N8N_WORKFLOWS", mock_workflows):
            from api.routes.automation import get_workflow_template
            
            response = await get_workflow_template("price_alert")
            
            assert response["id"] == "price_alert"
            assert response["name"] == "Price Alert"
    
    @pytest.mark.asyncio
    async def test_get_template_not_found(self):
        """Deve retornar 404 para template inexistente"""
        with patch("api.routes.automation.DIDIN_N8N_WORKFLOWS", {}):
            from api.routes.automation import get_workflow_template
            
            with pytest.raises(HTTPException) as exc_info:
                await get_workflow_template("nonexistent")
            
            assert exc_info.value.status_code == 404


# ============================================
# TESTS: List Executions
# ============================================

class TestListExecutions:
    """Testes do endpoint list_executions"""
    
    @pytest.mark.asyncio
    async def test_list_executions_success(self, mock_user, mock_n8n_client, mock_execution):
        """Deve listar execuções com sucesso"""
        mock_n8n_client.get_executions.return_value = [mock_execution]
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            with patch("api.routes.automation.WorkflowStatus"):
                from api.routes.automation import list_executions
                
                response = await list_executions(
                    workflow_id="wf-123",
                    current_user=mock_user
                )
                
                assert "executions" in response
    
    @pytest.mark.asyncio
    async def test_list_executions_invalid_status(self, mock_user):
        """Deve retornar 400 para status inválido"""
        with patch("api.routes.automation.WorkflowStatus") as MockStatus:
            MockStatus.side_effect = ValueError("Invalid status")
            
            from api.routes.automation import list_executions
            
            with pytest.raises(HTTPException) as exc_info:
                await list_executions(
                    status="invalid_status",
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 400


# ============================================
# TESTS: Quick Actions
# ============================================

class TestQuickActions:
    """Testes dos endpoints de quick actions"""
    
    @pytest.mark.asyncio
    async def test_price_drop_alert_success(self, mock_user, mock_n8n_client):
        """Deve disparar alerta de queda de preço"""
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            from api.routes.automation import trigger_price_drop_alert
            
            response = await trigger_price_drop_alert(
                product_name="Test Product",
                old_price=100.0,
                new_price=80.0,
                product_url="https://example.com/product",
                current_user=mock_user
            )
            
            assert response["status"] == "triggered"
    
    @pytest.mark.asyncio
    async def test_price_drop_alert_webhook_not_configured(self, mock_user, mock_n8n_client):
        """Deve retornar skipped se webhook não configurado"""
        mock_n8n_client.trigger_webhook.side_effect = Exception("Not found")
        
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            from api.routes.automation import trigger_price_drop_alert
            
            response = await trigger_price_drop_alert(
                product_name="Test",
                old_price=100.0,
                new_price=80.0,
                product_url="https://example.com",
                current_user=mock_user
            )
            
            assert response["status"] == "skipped"
    
    @pytest.mark.asyncio
    async def test_new_lead_success(self, mock_user, mock_n8n_client):
        """Deve disparar automação de novo lead"""
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            from api.routes.automation import trigger_new_lead
            
            response = await trigger_new_lead(
                name="John Doe",
                phone="+5511999999999",
                email="john@example.com",
                current_user=mock_user
            )
            
            assert response["status"] == "triggered"
    
    @pytest.mark.asyncio
    async def test_post_published_success(self, mock_user, mock_n8n_client):
        """Deve disparar automação de post publicado"""
        with patch("api.routes.automation.n8n_client", mock_n8n_client):
            from api.routes.automation import trigger_post_published
            
            response = await trigger_post_published(
                platform="instagram",
                post_id="post123",
                post_url="https://instagram.com/p/123",
                current_user=mock_user
            )
            
            assert response["status"] == "triggered"


# ============================================
# TESTS: Models
# ============================================

class TestAutomationModels:
    """Testes dos modelos Pydantic"""
    
    def test_trigger_webhook_request(self):
        """Deve criar TriggerWebhookRequest corretamente"""
        from api.routes.automation import TriggerWebhookRequest
        
        req = TriggerWebhookRequest(
            webhook_path="/webhook/test",
            data={"key": "value"}
        )
        
        assert req.webhook_path == "/webhook/test"
        assert req.data["key"] == "value"
    
    def test_execute_workflow_request(self):
        """Deve criar ExecuteWorkflowRequest corretamente"""
        from api.routes.automation import ExecuteWorkflowRequest
        
        req = ExecuteWorkflowRequest(
            workflow_id="wf-123",
            data={"param": "value"}
        )
        
        assert req.workflow_id == "wf-123"
        assert req.data["param"] == "value"
    
    def test_execute_workflow_request_optional_data(self):
        """Data deve ser opcional"""
        from api.routes.automation import ExecuteWorkflowRequest
        
        req = ExecuteWorkflowRequest(workflow_id="wf-123")
        
        assert req.workflow_id == "wf-123"
        assert req.data is None
