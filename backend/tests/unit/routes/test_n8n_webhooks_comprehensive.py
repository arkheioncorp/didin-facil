"""
Comprehensive tests for n8n_webhooks.py
========================================
Tests for n8n webhook integration routes.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.n8n_webhooks import (N8nEventRequest,
                                     PriceAlertTriggeredRequest,
                                     ProductSearchRequest,
                                     ProductSearchResponse,
                                     WorkflowExecutionRequest,
                                     generic_event_webhook, list_workflows,
                                     price_alert_webhook,
                                     product_search_webhook, router,
                                     trigger_new_user_onboarding,
                                     trigger_price_drop_alert,
                                     trigger_workflow_manually)

# ==================== FIXTURES ====================


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    user = MagicMock()
    user.id = "user123"
    user.email = "test@example.com"
    user.name = "Test User"
    user.created_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def mock_n8n_client():
    """Mock n8n client."""
    client = MagicMock()
    client.trigger_webhook = AsyncMock()
    client.trigger_workflow_by_id = AsyncMock()
    client.list_workflows = AsyncMock(return_value=[])
    client.list_executions = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_scraper():
    """Mock scraper orchestrator."""
    scraper = MagicMock()
    scraper.search_products = AsyncMock(return_value=[
        {
            "title": "iPhone 15",
            "price": 4999.00,
            "discount_percentage": 10,
            "store": "Amazon",
            "url": "https://example.com/iphone",
        }
    ])
    return scraper


@pytest.fixture
def mock_background_tasks():
    """Mock background tasks."""
    tasks = MagicMock()
    tasks.add_task = MagicMock()
    return tasks


# ==================== SCHEMA TESTS ====================


class TestSchemas:
    """Test Pydantic schemas."""
    
    def test_product_search_request(self):
        """Test ProductSearchRequest schema."""
        req = ProductSearchRequest(
            query="iphone 15",
            conversation_id="conv123",
        )
        assert req.query == "iphone 15"
        assert req.limit == 5
    
    def test_product_search_request_custom_limit(self):
        """Test ProductSearchRequest with custom limit."""
        req = ProductSearchRequest(
            query="macbook",
            conversation_id="conv123",
            limit=10,
        )
        assert req.limit == 10
    
    def test_price_alert_triggered_request(self):
        """Test PriceAlertTriggeredRequest schema."""
        req = PriceAlertTriggeredRequest(
            user_id="user123",
            product_id="prod456",
            old_price=5999.00,
            new_price=4999.00,
            discount_percentage=16.67,
        )
        assert req.old_price == 5999.00
        assert req.new_price == 4999.00
    
    def test_workflow_execution_request(self):
        """Test WorkflowExecutionRequest schema."""
        req = WorkflowExecutionRequest(
            workflow_id="wf123",
            data={"param1": "value1"},
        )
        assert req.workflow_id == "wf123"
        assert req.data["param1"] == "value1"
    
    def test_n8n_event_request(self):
        """Test N8nEventRequest schema."""
        req = N8nEventRequest(
            event_type="user_interaction",
            conversation_id="conv123",
            data={"action": "clicked_button"},
        )
        assert req.event_type == "user_interaction"
    
    def test_n8n_event_request_minimal(self):
        """Test N8nEventRequest with minimal fields."""
        req = N8nEventRequest(
            event_type="workflow_completed",
            data={},
        )
        assert req.conversation_id is None
    
    def test_product_search_response(self):
        """Test ProductSearchResponse schema."""
        resp = ProductSearchResponse(
            products=[{"name": "iPhone", "price": "R$ 4999.00"}],
            total=1,
            query="iphone",
        )
        assert resp.total == 1
        assert len(resp.products) == 1


# ==================== WEBHOOK ENDPOINT TESTS ====================


class TestProductSearchWebhook:
    """Test product search webhook."""
    
    @pytest.mark.asyncio
    async def test_search_success(self, mock_scraper, mock_background_tasks):
        """Test successful product search."""
        with patch(
            'api.services.scraper.ScraperOrchestrator',
            return_value=mock_scraper
        ):
            req = ProductSearchRequest(
                query="iphone",
                conversation_id="conv123",
            )
            result = await product_search_webhook(req, mock_background_tasks)
            
            assert result.total == 1
            assert len(result.products) == 1
            mock_background_tasks.add_task.assert_called()
    
    @pytest.mark.asyncio
    async def test_search_empty_results(self, mock_background_tasks):
        """Test product search with no results."""
        mock_scraper = MagicMock()
        mock_scraper.search_products = AsyncMock(return_value=[])
        
        with patch(
            'api.services.scraper.ScraperOrchestrator',
            return_value=mock_scraper
        ):
            req = ProductSearchRequest(
                query="nonexistent",
                conversation_id="conv123",
            )
            result = await product_search_webhook(req, mock_background_tasks)
            
            assert result.total == 0


class TestPriceAlertWebhook:
    """Test price alert webhook."""
    
    @pytest.mark.asyncio
    async def test_price_alert_success(self, mock_background_tasks):
        """Test successful price alert."""
        req = PriceAlertTriggeredRequest(
            user_id="user123",
            product_id="prod456",
            old_price=5999.00,
            new_price=4999.00,
            discount_percentage=16.67,
        )
        result = await price_alert_webhook(req, mock_background_tasks)
        
        assert result["success"] is True
        mock_background_tasks.add_task.assert_called()


class TestGenericEventWebhook:
    """Test generic event webhook."""
    
    @pytest.mark.asyncio
    async def test_user_interaction_event(self):
        """Test user interaction event."""
        with patch(
            'api.routes.n8n_webhooks._track_interaction',
            new_callable=AsyncMock
        ):
            req = N8nEventRequest(
                event_type="user_interaction",
                conversation_id="conv123",
                data={"action": "button_click"},
            )
            result = await generic_event_webhook(req)
            
            assert result["success"] is True
            assert result["event_processed"] == "user_interaction"
    
    @pytest.mark.asyncio
    async def test_workflow_completed_event(self):
        """Test workflow completed event."""
        with patch(
            'api.routes.n8n_webhooks._track_workflow_completion',
            new_callable=AsyncMock
        ):
            req = N8nEventRequest(
                event_type="workflow_completed",
                data={"workflow_id": "wf123"},
            )
            result = await generic_event_webhook(req)
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_error_occurred_event(self):
        """Test error occurred event."""
        req = N8nEventRequest(
            event_type="error_occurred",
            data={"error": "Something went wrong"},
        )
        result = await generic_event_webhook(req)
        
        assert result["success"] is True


# ==================== TRIGGER ENDPOINT TESTS ====================


class TestTriggerEndpoints:
    """Test trigger endpoints."""
    
    @pytest.mark.asyncio
    async def test_trigger_new_user(self, mock_user, mock_n8n_client):
        """Test new user onboarding trigger."""
        with patch(
            'api.routes.n8n_webhooks.get_n8n_client',
            return_value=mock_n8n_client
        ):
            result = await trigger_new_user_onboarding(mock_user)
            
            assert result["success"] is True
            mock_n8n_client.trigger_webhook.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_trigger_price_drop(self, mock_user, mock_n8n_client):
        """Test price drop alert trigger."""
        with patch(
            'api.routes.n8n_webhooks.get_n8n_client',
            return_value=mock_n8n_client
        ):
            result = await trigger_price_drop_alert(
                product_id="prod123",
                old_price=5999.00,
                new_price=4999.00,
                user=mock_user,
            )
            
            assert result["success"] is True
            mock_n8n_client.trigger_webhook.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_trigger_workflow_manually(self, mock_user, mock_n8n_client):
        """Test manual workflow trigger."""
        mock_execution = MagicMock()
        mock_execution.id = "exec123"
        mock_execution.status = MagicMock(value="running")
        mock_n8n_client.trigger_workflow_by_id = AsyncMock(
            return_value=mock_execution
        )
        
        with patch(
            'api.routes.n8n_webhooks.get_n8n_client',
            return_value=mock_n8n_client
        ):
            req = WorkflowExecutionRequest(
                workflow_id="wf123",
                data={"test": True},
            )
            result = await trigger_workflow_manually(req, mock_user)
            
            assert result["success"] is True
            assert result["execution_id"] == "exec123"


class TestAdminEndpoints:
    """Test admin endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_workflows(self, mock_user, mock_n8n_client):
        """Test listing workflows."""
        mock_workflow = MagicMock()
        mock_workflow.id = "wf123"
        mock_workflow.name = "Test Workflow"
        mock_workflow.active = True
        mock_workflow.updated_at = datetime.now(timezone.utc)
        
        mock_n8n_client.list_workflows = AsyncMock(
            return_value=[mock_workflow]
        )
        
        with patch(
            'api.routes.n8n_webhooks.get_n8n_client',
            return_value=mock_n8n_client
        ):
            result = await list_workflows(mock_user)
            
            assert result["total"] == 1
            assert len(result["workflows"]) == 1


# ==================== ROUTER TESTS ====================


class TestRouter:
    """Test router configuration."""
    
    def test_router_exists(self):
        """Test that router is defined."""
        assert router is not None
    
    def test_router_prefix(self):
        """Test router has correct prefix."""
        assert router.prefix == "/n8n"
    
    def test_router_tags(self):
        """Test router has correct tags."""
        assert "n8n" in router.tags
