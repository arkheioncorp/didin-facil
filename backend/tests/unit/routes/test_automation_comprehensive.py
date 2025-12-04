"""
Comprehensive tests for automation routes.
Coverage target: 90%+
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


@pytest.fixture
def mock_user():
    """Standard test user."""
    return {"id": "user-123", "email": "test@example.com"}


@pytest.fixture
def mock_subscription_service():
    """Mock subscription service."""
    service = MagicMock()
    service.can_use_feature = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_n8n_client():
    """Mock n8n client."""
    with patch("api.routes.automation.n8n_client") as mock:
        yield mock


@pytest.fixture
def mock_workflow():
    """Mock n8n workflow."""
    workflow = MagicMock()
    workflow.id = "wf-001"
    workflow.name = "Test Workflow"
    workflow.active = True
    workflow.nodes = [{"type": "webhook"}, {"type": "http"}]
    workflow.created_at = datetime.now(timezone.utc)
    workflow.updated_at = datetime.now(timezone.utc)
    return workflow


@pytest.fixture
def mock_execution():
    """Mock workflow execution."""
    from integrations.n8n import WorkflowStatus
    
    execution = MagicMock()
    execution.id = "exec-001"
    execution.workflow_id = "wf-001"
    execution.status = WorkflowStatus.SUCCESS
    execution.started_at = datetime.now(timezone.utc)
    execution.finished_at = datetime.now(timezone.utc)
    execution.data = {"result": "ok"}
    execution.error = None
    return execution


class TestListWorkflows:
    """Tests for GET /workflows endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_workflows_success(self, mock_n8n_client, mock_user, mock_workflow):
        """Test listing workflows successfully."""
        from api.routes.automation import list_workflows
        
        mock_n8n_client.list_workflows = AsyncMock(return_value=[mock_workflow])
        
        result = await list_workflows(active=None, limit=50, current_user=mock_user)
        
        assert "workflows" in result
        assert len(result["workflows"]) == 1
        assert result["workflows"][0]["id"] == "wf-001"
        assert result["workflows"][0]["active"] is True
    
    @pytest.mark.asyncio
    async def test_list_workflows_filter_active(self, mock_n8n_client, mock_user, mock_workflow):
        """Test listing only active workflows."""
        from api.routes.automation import list_workflows
        
        mock_n8n_client.list_workflows = AsyncMock(return_value=[mock_workflow])
        
        result = await list_workflows(active=True, limit=10, current_user=mock_user)
        
        mock_n8n_client.list_workflows.assert_called_once_with(True, 10)
    
    @pytest.mark.asyncio
    async def test_list_workflows_error(self, mock_n8n_client, mock_user):
        """Test error handling when listing workflows."""
        from api.routes.automation import list_workflows
        
        mock_n8n_client.list_workflows = AsyncMock(
            side_effect=Exception("n8n connection failed")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await list_workflows(current_user=mock_user)
        
        assert exc_info.value.status_code == 500


class TestGetWorkflow:
    """Tests for GET /workflows/{workflow_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_workflow_success(self, mock_n8n_client, mock_user, mock_workflow):
        """Test getting workflow details."""
        from api.routes.automation import get_workflow
        
        mock_n8n_client.get_workflow = AsyncMock(return_value=mock_workflow)
        
        result = await get_workflow("wf-001", mock_user)
        
        assert result["id"] == "wf-001"
        assert result["name"] == "Test Workflow"
        assert result["nodes_count"] == 2
    
    @pytest.mark.asyncio
    async def test_get_workflow_not_found(self, mock_n8n_client, mock_user):
        """Test getting non-existent workflow."""
        from api.routes.automation import get_workflow
        
        mock_n8n_client.get_workflow = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_workflow("nonexistent", mock_user)
        
        assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_workflow_no_nodes(self, mock_n8n_client, mock_user):
        """Test workflow without nodes."""
        from api.routes.automation import get_workflow
        
        workflow = MagicMock()
        workflow.id = "wf-empty"
        workflow.name = "Empty"
        workflow.active = False
        workflow.nodes = None
        workflow.created_at = datetime.now(timezone.utc)
        workflow.updated_at = datetime.now(timezone.utc)
        
        mock_n8n_client.get_workflow = AsyncMock(return_value=workflow)
        
        result = await get_workflow("wf-empty", mock_user)
        
        assert result["nodes_count"] == 0


class TestActivateWorkflow:
    """Tests for POST /workflows/{workflow_id}/activate endpoint."""
    
    @pytest.mark.asyncio
    async def test_activate_workflow_success(self, mock_n8n_client, mock_user, mock_subscription_service):
        """Test activating workflow successfully."""
        from api.routes.automation import activate_workflow
        
        mock_n8n_client.activate_workflow = AsyncMock(return_value=True)
        
        result = await activate_workflow("wf-001", mock_user, mock_subscription_service)
        
        assert result["status"] == "activated"
        assert result["workflow_id"] == "wf-001"
    
    @pytest.mark.asyncio
    async def test_activate_workflow_limit_exceeded(self, mock_n8n_client, mock_user):
        """Test activating workflow when limit exceeded."""
        from api.routes.automation import activate_workflow
        
        mock_service = MagicMock()
        mock_service.can_use_feature = AsyncMock(return_value=False)
        
        with pytest.raises(HTTPException) as exc_info:
            await activate_workflow("wf-001", mock_user, mock_service)
        
        assert exc_info.value.status_code == 402
    
    @pytest.mark.asyncio
    async def test_activate_workflow_failure(self, mock_n8n_client, mock_user, mock_subscription_service):
        """Test activation failure."""
        from api.routes.automation import activate_workflow
        
        mock_n8n_client.activate_workflow = AsyncMock(return_value=False)
        
        with pytest.raises(HTTPException) as exc_info:
            await activate_workflow("wf-001", mock_user, mock_subscription_service)
        
        assert exc_info.value.status_code == 500


class TestDeactivateWorkflow:
    """Tests for POST /workflows/{workflow_id}/deactivate endpoint."""
    
    @pytest.mark.asyncio
    async def test_deactivate_workflow_success(self, mock_n8n_client, mock_user):
        """Test deactivating workflow successfully."""
        from api.routes.automation import deactivate_workflow
        
        mock_n8n_client.deactivate_workflow = AsyncMock(return_value=True)
        
        result = await deactivate_workflow("wf-001", mock_user)
        
        assert result["status"] == "deactivated"
    
    @pytest.mark.asyncio
    async def test_deactivate_workflow_failure(self, mock_n8n_client, mock_user):
        """Test deactivation failure."""
        from api.routes.automation import deactivate_workflow
        
        mock_n8n_client.deactivate_workflow = AsyncMock(return_value=False)
        
        with pytest.raises(HTTPException) as exc_info:
            await deactivate_workflow("wf-001", mock_user)
        
        assert exc_info.value.status_code == 500


class TestExecuteWorkflow:
    """Tests for POST /workflows/{workflow_id}/execute endpoint."""
    
    @pytest.mark.asyncio
    async def test_execute_workflow_success(self, mock_n8n_client, mock_user, mock_execution):
        """Test executing workflow successfully."""
        from api.routes.automation import execute_workflow
        
        mock_n8n_client.trigger_workflow_by_id = AsyncMock(return_value=mock_execution)
        
        result = await execute_workflow("wf-001", {"input": "data"}, mock_user)
        
        assert result["execution_id"] == "exec-001"
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_execute_workflow_no_data(self, mock_n8n_client, mock_user, mock_execution):
        """Test executing workflow without data."""
        from api.routes.automation import execute_workflow
        
        mock_n8n_client.trigger_workflow_by_id = AsyncMock(return_value=mock_execution)
        
        result = await execute_workflow("wf-001", None, mock_user)
        
        mock_n8n_client.trigger_workflow_by_id.assert_called_once_with(
            workflow_id="wf-001",
            data=None
        )
    
    @pytest.mark.asyncio
    async def test_execute_workflow_error(self, mock_n8n_client, mock_user):
        """Test execution error handling."""
        from api.routes.automation import execute_workflow
        
        mock_n8n_client.trigger_workflow_by_id = AsyncMock(
            side_effect=Exception("Execution failed")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await execute_workflow("wf-001", {}, mock_user)
        
        assert exc_info.value.status_code == 500


class TestTriggerWebhook:
    """Tests for POST /webhook/trigger endpoint."""
    
    @pytest.mark.asyncio
    async def test_trigger_webhook_success(self, mock_n8n_client, mock_user):
        """Test triggering webhook successfully."""
        from api.routes.automation import (TriggerWebhookRequest,
                                           trigger_webhook)
        
        mock_n8n_client.trigger_webhook = AsyncMock(return_value={"ok": True})
        
        data = TriggerWebhookRequest(
            webhook_path="/test/webhook",
            data={"key": "value"}
        )
        
        result = await trigger_webhook(data, mock_user)
        
        assert result["status"] == "triggered"
        assert result["result"]["ok"] is True
    
    @pytest.mark.asyncio
    async def test_trigger_webhook_error(self, mock_n8n_client, mock_user):
        """Test webhook trigger error."""
        from api.routes.automation import (TriggerWebhookRequest,
                                           trigger_webhook)
        
        mock_n8n_client.trigger_webhook = AsyncMock(
            side_effect=Exception("Webhook not found")
        )
        
        data = TriggerWebhookRequest(
            webhook_path="/invalid",
            data={}
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await trigger_webhook(data, mock_user)
        
        assert exc_info.value.status_code == 500


class TestListExecutions:
    """Tests for GET /executions endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_executions_success(self, mock_n8n_client, mock_user, mock_execution):
        """Test listing executions successfully."""
        from api.routes.automation import list_executions
        
        mock_n8n_client.get_executions = AsyncMock(return_value=[mock_execution])
        
        result = await list_executions(
            workflow_id="wf-001",
            status=None,
            limit=20,
            current_user=mock_user
        )
        
        assert "executions" in result
        assert len(result["executions"]) == 1
    
    @pytest.mark.asyncio
    async def test_list_executions_filter_status(self, mock_n8n_client, mock_user, mock_execution):
        """Test listing executions with status filter."""
        from api.routes.automation import list_executions
        
        mock_n8n_client.get_executions = AsyncMock(return_value=[mock_execution])
        
        result = await list_executions(
            workflow_id=None,
            status="success",
            limit=10,
            current_user=mock_user
        )
        
        assert len(result["executions"]) == 1
    
    @pytest.mark.asyncio
    async def test_list_executions_invalid_status(self, mock_n8n_client, mock_user):
        """Test invalid status filter."""
        from api.routes.automation import list_executions
        
        with pytest.raises(HTTPException) as exc_info:
            await list_executions(
                workflow_id=None,
                status="invalid_status",
                limit=20,
                current_user=mock_user
            )
        
        assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_list_executions_error(self, mock_n8n_client, mock_user):
        """Test error when listing executions."""
        from api.routes.automation import list_executions
        
        mock_n8n_client.get_executions = AsyncMock(
            side_effect=Exception("Database error")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await list_executions(
                workflow_id=None,
                status=None,
                limit=20,
                current_user=mock_user
            )
        
        assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_list_executions_with_finished(self, mock_n8n_client, mock_user):
        """Test executions with finished_at field."""
        from api.routes.automation import list_executions
        from integrations.n8n import WorkflowStatus
        
        execution = MagicMock()
        execution.id = "exec-002"
        execution.workflow_id = "wf-001"
        execution.status = WorkflowStatus.SUCCESS
        execution.started_at = datetime.now(timezone.utc)
        execution.finished_at = datetime.now(timezone.utc)
        execution.error = None
        
        mock_n8n_client.get_executions = AsyncMock(return_value=[execution])
        
        result = await list_executions(current_user=mock_user)
        
        assert result["executions"][0]["finished_at"] is not None
    
    @pytest.mark.asyncio
    async def test_list_executions_no_finished(self, mock_n8n_client, mock_user):
        """Test executions without finished_at (running)."""
        from api.routes.automation import list_executions
        from integrations.n8n import WorkflowStatus
        
        execution = MagicMock()
        execution.id = "exec-003"
        execution.workflow_id = "wf-001"
        execution.status = WorkflowStatus.RUNNING
        execution.started_at = datetime.now(timezone.utc)
        execution.finished_at = None
        execution.error = None
        
        mock_n8n_client.get_executions = AsyncMock(return_value=[execution])
        
        result = await list_executions(current_user=mock_user)
        
        assert result["executions"][0]["finished_at"] is None


class TestListWorkflowTemplates:
    """Tests for GET /templates endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_templates(self):
        """Test listing workflow templates."""
        from api.routes.automation import list_workflow_templates
        
        with patch("api.routes.automation.DIDIN_N8N_WORKFLOWS", {
            "price_alert": {
                "name": "Price Alert",
                "description": "Alert on price drop",
                "trigger": MagicMock(value="webhook"),
                "webhook_path": "/price-drop",
                "actions": ["notify"]
            }
        }):
            result = await list_workflow_templates()
        
        assert "templates" in result
        assert len(result["templates"]) == 1
        assert result["templates"][0]["id"] == "price_alert"


class TestGetWorkflowTemplate:
    """Tests for GET /templates/{template_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_template_success(self):
        """Test getting template details."""
        from api.routes.automation import get_workflow_template
        
        mock_template = {
            "name": "Test Template",
            "description": "Test description",
            "trigger": MagicMock(value="schedule"),
            "schedule": "0 * * * *",
            "actions": ["action1", "action2"]
        }
        
        with patch("api.routes.automation.DIDIN_N8N_WORKFLOWS", {"test": mock_template}):
            result = await get_workflow_template("test")
        
        assert result["id"] == "test"
        assert result["name"] == "Test Template"
    
    @pytest.mark.asyncio
    async def test_get_template_not_found(self):
        """Test getting non-existent template."""
        from api.routes.automation import get_workflow_template
        
        with patch("api.routes.automation.DIDIN_N8N_WORKFLOWS", {}):
            with pytest.raises(HTTPException) as exc_info:
                await get_workflow_template("nonexistent")
        
        assert exc_info.value.status_code == 404


class TestTriggerPriceDropAlert:
    """Tests for POST /actions/price-drop endpoint."""
    
    @pytest.mark.asyncio
    async def test_price_drop_success(self, mock_n8n_client, mock_user):
        """Test price drop alert trigger."""
        from api.routes.automation import trigger_price_drop_alert
        
        mock_n8n_client.trigger_webhook = AsyncMock(return_value={"sent": True})
        
        result = await trigger_price_drop_alert(
            product_name="Test Product",
            old_price=100.0,
            new_price=80.0,
            product_url="https://example.com/product",
            current_user=mock_user
        )
        
        assert result["status"] == "triggered"
    
    @pytest.mark.asyncio
    async def test_price_drop_webhook_not_configured(self, mock_n8n_client, mock_user):
        """Test when webhook is not configured."""
        from api.routes.automation import trigger_price_drop_alert
        
        mock_n8n_client.trigger_webhook = AsyncMock(
            side_effect=Exception("Webhook not found")
        )
        
        result = await trigger_price_drop_alert(
            product_name="Product",
            old_price=50.0,
            new_price=40.0,
            product_url="https://example.com",
            current_user=mock_user
        )
        
        assert result["status"] == "skipped"


class TestTriggerNewLead:
    """Tests for POST /actions/new-lead endpoint."""
    
    @pytest.mark.asyncio
    async def test_new_lead_success(self, mock_n8n_client, mock_user):
        """Test new lead trigger."""
        from api.routes.automation import trigger_new_lead
        
        mock_n8n_client.trigger_webhook = AsyncMock(return_value={"ok": True})
        
        result = await trigger_new_lead(
            name="John Doe",
            phone="+5511999999999",
            email="john@example.com",
            source="website",
            current_user=mock_user
        )
        
        assert result["status"] == "triggered"
    
    @pytest.mark.asyncio
    async def test_new_lead_no_email(self, mock_n8n_client, mock_user):
        """Test new lead without email."""
        from api.routes.automation import trigger_new_lead
        
        mock_n8n_client.trigger_webhook = AsyncMock(return_value={"ok": True})
        
        result = await trigger_new_lead(
            name="Jane Doe",
            phone="+5511888888888",
            email=None,
            source="instagram",
            current_user=mock_user
        )
        
        assert result["status"] == "triggered"
    
    @pytest.mark.asyncio
    async def test_new_lead_webhook_not_configured(self, mock_n8n_client, mock_user):
        """Test when webhook is not configured."""
        from api.routes.automation import trigger_new_lead
        
        mock_n8n_client.trigger_webhook = AsyncMock(
            side_effect=Exception("Not found")
        )
        
        result = await trigger_new_lead(
            name="Test",
            phone="123",
            current_user=mock_user
        )
        
        assert result["status"] == "skipped"


class TestTriggerPostPublished:
    """Tests for POST /actions/post-published endpoint."""
    
    @pytest.mark.asyncio
    async def test_post_published_success(self, mock_n8n_client, mock_user):
        """Test post published trigger."""
        from api.routes.automation import trigger_post_published
        
        mock_n8n_client.trigger_webhook = AsyncMock(return_value={"notified": True})
        
        result = await trigger_post_published(
            platform="instagram",
            post_id="post-123",
            post_url="https://instagram.com/p/abc123",
            current_user=mock_user
        )
        
        assert result["status"] == "triggered"
    
    @pytest.mark.asyncio
    async def test_post_published_webhook_not_configured(self, mock_n8n_client, mock_user):
        """Test when webhook is not configured."""
        from api.routes.automation import trigger_post_published
        
        mock_n8n_client.trigger_webhook = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        
        result = await trigger_post_published(
            platform="tiktok",
            post_id="123",
            post_url="https://tiktok.com",
            current_user=mock_user
        )
        
        assert result["status"] == "skipped"


class TestRequestModels:
    """Tests for request model validation."""
    
    def test_trigger_webhook_request(self):
        """Test TriggerWebhookRequest model."""
        from api.routes.automation import TriggerWebhookRequest
        
        data = TriggerWebhookRequest(
            webhook_path="/test",
            data={"key": "value"}
        )
        
        assert data.webhook_path == "/test"
        assert data.data["key"] == "value"
    
    def test_execute_workflow_request(self):
        """Test ExecuteWorkflowRequest model."""
        from api.routes.automation import ExecuteWorkflowRequest
        
        data = ExecuteWorkflowRequest(
            workflow_id="wf-001",
            data={"input": "test"}
        )
        
        assert data.workflow_id == "wf-001"
    
    def test_execute_workflow_request_no_data(self):
        """Test ExecuteWorkflowRequest without data."""
        from api.routes.automation import ExecuteWorkflowRequest
        
        data = ExecuteWorkflowRequest(workflow_id="wf-002")
        
        assert data.data is None
