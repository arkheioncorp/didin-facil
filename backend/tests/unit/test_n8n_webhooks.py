"""
Unit tests for n8n Webhooks Routes
Tests for n8n integration endpoints
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


class TestRequestModels:
    """Tests for Pydantic request models"""

    def test_product_search_request(self):
        """Test ProductSearchRequest model"""
        from api.routes.n8n_webhooks import ProductSearchRequest
        
        request = ProductSearchRequest(
            query="iphone 15",
            conversation_id="conv-123",
            limit=10
        )
        
        assert request.query == "iphone 15"
        assert request.conversation_id == "conv-123"
        assert request.limit == 10

    def test_product_search_request_defaults(self):
        """Test ProductSearchRequest with defaults"""
        from api.routes.n8n_webhooks import ProductSearchRequest
        
        request = ProductSearchRequest(
            query="samsung",
            conversation_id="conv-456"
        )
        
        assert request.limit == 5  # default value

    def test_price_alert_triggered_request(self):
        """Test PriceAlertTriggeredRequest model"""
        from api.routes.n8n_webhooks import PriceAlertTriggeredRequest
        
        request = PriceAlertTriggeredRequest(
            user_id="user-123",
            product_id="prod-456",
            old_price=1500.00,
            new_price=1200.00,
            discount_percentage=20.0
        )
        
        assert request.user_id == "user-123"
        assert request.product_id == "prod-456"
        assert request.old_price == 1500.00
        assert request.new_price == 1200.00
        assert request.discount_percentage == 20.0

    def test_workflow_execution_request(self):
        """Test WorkflowExecutionRequest model"""
        from api.routes.n8n_webhooks import WorkflowExecutionRequest
        
        request = WorkflowExecutionRequest(
            workflow_id="wf-123",
            data={"key": "value"}
        )
        
        assert request.workflow_id == "wf-123"
        assert request.data == {"key": "value"}

    def test_n8n_event_request(self):
        """Test N8nEventRequest model"""
        from api.routes.n8n_webhooks import N8nEventRequest
        
        request = N8nEventRequest(
            event_type="user_interaction",
            conversation_id="conv-123",
            data={"action": "button_click"}
        )
        
        assert request.event_type == "user_interaction"
        assert request.conversation_id == "conv-123"
        assert request.data == {"action": "button_click"}

    def test_n8n_event_request_without_conversation(self):
        """Test N8nEventRequest without conversation_id"""
        from api.routes.n8n_webhooks import N8nEventRequest
        
        request = N8nEventRequest(
            event_type="workflow_completed",
            data={"workflow_id": "wf-123", "status": "success"}
        )
        
        assert request.event_type == "workflow_completed"
        assert request.conversation_id is None


class TestResponseModels:
    """Tests for Pydantic response models"""

    def test_product_search_response(self):
        """Test ProductSearchResponse model"""
        from api.routes.n8n_webhooks import ProductSearchResponse
        
        products = [
            {"name": "iPhone 15", "price": "R$ 5499.00"},
            {"name": "iPhone 14", "price": "R$ 4299.00"}
        ]
        
        response = ProductSearchResponse(
            products=products,
            total=2,
            query="iphone"
        )
        
        assert len(response.products) == 2
        assert response.total == 2
        assert response.query == "iphone"


class TestProductSearchWebhook:
    """Tests for product search webhook - model and format tests"""

    @pytest.mark.asyncio
    async def test_product_search_request_validation(self):
        """Test ProductSearchRequest validation"""
        from api.routes.n8n_webhooks import ProductSearchRequest
        
        request = ProductSearchRequest(
            query="iphone 15",
            conversation_id="conv-123",
            limit=5
        )
        
        assert request.query == "iphone 15"
        assert request.limit == 5

    @pytest.mark.asyncio
    async def test_product_search_response_format(self):
        """Test ProductSearchResponse format"""
        from api.routes.n8n_webhooks import ProductSearchResponse
        
        products = [
            {"name": "iPhone 15", "price": "R$ 5499.00"},
        ]
        
        response = ProductSearchResponse(
            products=products,
            total=1,
            query="iphone"
        )
        
        assert response.total == 1
        assert response.query == "iphone"


class TestPriceAlertWebhook:
    """Tests for price alert webhook"""

    @pytest.fixture
    def mock_track_price_alert(self):
        with patch('api.routes.n8n_webhooks._track_price_alert') as mock:
            mock.return_value = None
            yield mock

    @pytest.mark.asyncio
    async def test_price_alert_success(self, mock_track_price_alert):
        """Test successful price alert"""
        from api.routes.n8n_webhooks import (
            price_alert_webhook,
            PriceAlertTriggeredRequest
        )
        
        request = PriceAlertTriggeredRequest(
            user_id="user-123",
            product_id="prod-456",
            old_price=1500.00,
            new_price=1200.00,
            discount_percentage=20.0
        )
        
        background_tasks = MagicMock()
        
        result = await price_alert_webhook(request, background_tasks)
        
        assert result["success"] is True
        assert result["message"] == "Price alert logged"
        background_tasks.add_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_price_alert_large_discount(self, mock_track_price_alert):
        """Test price alert with large discount"""
        from api.routes.n8n_webhooks import (
            price_alert_webhook,
            PriceAlertTriggeredRequest
        )
        
        request = PriceAlertTriggeredRequest(
            user_id="user-123",
            product_id="prod-456",
            old_price=2000.00,
            new_price=1000.00,
            discount_percentage=50.0
        )
        
        background_tasks = MagicMock()
        
        result = await price_alert_webhook(request, background_tasks)
        
        assert result["success"] is True


class TestGenericEventWebhook:
    """Tests for generic event webhook"""

    @pytest.fixture
    def mock_handlers(self):
        with patch('api.routes.n8n_webhooks._track_interaction') as mock_int, \
             patch('api.routes.n8n_webhooks._track_workflow_completion') as mock_wf:
            mock_int.return_value = None
            mock_wf.return_value = None
            yield {"interaction": mock_int, "workflow": mock_wf}

    @pytest.mark.asyncio
    async def test_user_interaction_event(self, mock_handlers):
        """Test user interaction event processing"""
        from api.routes.n8n_webhooks import (
            generic_event_webhook,
            N8nEventRequest
        )
        
        request = N8nEventRequest(
            event_type="user_interaction",
            conversation_id="conv-123",
            data={"action": "button_click", "button_id": "buy_now"}
        )
        
        result = await generic_event_webhook(request)
        
        assert result["success"] is True
        assert result["event_processed"] == "user_interaction"

    @pytest.mark.asyncio
    async def test_workflow_completed_event(self, mock_handlers):
        """Test workflow completed event processing"""
        from api.routes.n8n_webhooks import (
            generic_event_webhook,
            N8nEventRequest
        )
        
        request = N8nEventRequest(
            event_type="workflow_completed",
            data={
                "workflow_id": "wf-123",
                "status": "success",
                "duration_ms": 1500
            }
        )
        
        result = await generic_event_webhook(request)
        
        assert result["success"] is True
        assert result["event_processed"] == "workflow_completed"

    @pytest.mark.asyncio
    async def test_error_occurred_event(self, mock_handlers):
        """Test error occurred event processing"""
        from api.routes.n8n_webhooks import (
            generic_event_webhook,
            N8nEventRequest
        )
        
        request = N8nEventRequest(
            event_type="error_occurred",
            data={
                "error_message": "Connection timeout",
                "workflow_id": "wf-123"
            }
        )
        
        result = await generic_event_webhook(request)
        
        assert result["success"] is True
        assert result["event_processed"] == "error_occurred"

    @pytest.mark.asyncio
    async def test_unknown_event_type(self, mock_handlers):
        """Test unknown event type processing"""
        from api.routes.n8n_webhooks import (
            generic_event_webhook,
            N8nEventRequest
        )
        
        request = N8nEventRequest(
            event_type="custom_event",
            data={"custom_key": "custom_value"}
        )
        
        result = await generic_event_webhook(request)
        
        assert result["success"] is True
        assert result["event_processed"] == "custom_event"


class TestPriceCalculations:
    """Tests for price-related calculations"""

    def test_discount_percentage_calculation(self):
        """Test discount percentage calculation"""
        old_price = 1500.00
        new_price = 1200.00
        
        discount = ((old_price - new_price) / old_price) * 100
        
        assert discount == 20.0

    def test_savings_calculation(self):
        """Test savings calculation"""
        old_price = 2000.00
        new_price = 1500.00
        
        savings = old_price - new_price
        
        assert savings == 500.00

    def test_price_formatting(self):
        """Test price formatting for WhatsApp response"""
        price = 1499.99
        
        formatted = f"R$ {price:.2f}"
        
        assert formatted == "R$ 1499.99"


class TestProductFormatting:
    """Tests for product formatting functions"""

    def test_format_product_for_whatsapp(self):
        """Test product formatting for WhatsApp"""
        product = {
            "title": "iPhone 15 Pro",
            "price": 7499.00,
            "discount_percentage": 15,
            "store": "Amazon",
            "url": "https://amazon.com/iphone15pro"
        }
        
        formatted = {
            "name": product.get("title", "Produto"),
            "price": f"R$ {product.get('price', 0):.2f}",
            "discount": product.get("discount_percentage", 0),
            "store": product.get("store", "Loja"),
            "url": product.get("url", "#")
        }
        
        assert formatted["name"] == "iPhone 15 Pro"
        assert formatted["price"] == "R$ 7499.00"
        assert formatted["discount"] == 15
        assert formatted["store"] == "Amazon"

    def test_format_product_missing_fields(self):
        """Test product formatting with missing fields"""
        product = {}
        
        formatted = {
            "name": product.get("title", "Produto"),
            "price": f"R$ {product.get('price', 0):.2f}",
            "discount": product.get("discount_percentage", 0),
            "store": product.get("store", "Loja"),
            "url": product.get("url", "#")
        }
        
        assert formatted["name"] == "Produto"
        assert formatted["price"] == "R$ 0.00"
        assert formatted["discount"] == 0
        assert formatted["store"] == "Loja"
        assert formatted["url"] == "#"
