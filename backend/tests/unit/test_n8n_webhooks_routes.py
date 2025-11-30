"""
Tests for api/routes/n8n_webhooks.py
n8n webhook integration routes testing
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from api.routes.n8n_webhooks import (
    router,
    product_search_webhook,
    price_alert_webhook,
    generic_event_webhook,
    trigger_new_user_onboarding,
    ProductSearchRequest,
    PriceAlertTriggeredRequest,
    WorkflowExecutionRequest,
    N8nEventRequest,
    ProductSearchResponse,
)


# ==================== FIXTURES ====================

@pytest.fixture
def mock_background_tasks():
    """Mock BackgroundTasks."""
    return MagicMock()


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    user = MagicMock()
    user.id = "user-123"
    user.email = "test@example.com"
    user.name = "Test User"
    user.created_at = MagicMock()
    user.created_at.isoformat = MagicMock(return_value="2024-01-01T00:00:00")
    return user


@pytest.fixture
def product_search_request():
    """Sample product search request."""
    return ProductSearchRequest(
        query="smartphone",
        conversation_id="conv-123",
        limit=5
    )


@pytest.fixture
def price_alert_request():
    """Sample price alert request."""
    return PriceAlertTriggeredRequest(
        user_id="user-123",
        product_id="prod-456",
        old_price=1000.00,
        new_price=800.00,
        discount_percentage=20.0
    )


@pytest.fixture
def n8n_event_request():
    """Sample n8n event request."""
    return N8nEventRequest(
        event_type="user_interaction",
        conversation_id="conv-123",
        data={"action": "clicked_button"}
    )


# ==================== PRODUCT SEARCH WEBHOOK TESTS ====================

class TestProductSearchWebhook:
    """Tests for product search webhook."""

    @pytest.mark.asyncio
    @patch("api.services.scraper.ScraperOrchestrator")
    async def test_product_search_success(
        self, mock_orchestrator_class, product_search_request, mock_background_tasks
    ):
        """Test successful product search."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.search_products = AsyncMock(return_value=[
            {
                "title": "Smartphone XYZ",
                "price": 999.99,
                "discount_percentage": 15,
                "store": "Amazon",
                "url": "https://example.com/product"
            },
            {
                "title": "Smartphone ABC",
                "price": 799.99,
                "discount_percentage": 10,
                "store": "Mercado Livre",
                "url": "https://example.com/product2"
            }
        ])
        mock_orchestrator_class.return_value = mock_orchestrator

        response = await product_search_webhook(
            request=product_search_request,
            background_tasks=mock_background_tasks
        )

        assert isinstance(response, ProductSearchResponse)
        assert response.total == 2
        assert response.query == "smartphone"
        assert len(response.products) == 2

    @pytest.mark.asyncio
    @patch("api.services.scraper.ScraperOrchestrator")
    async def test_product_search_empty_results(
        self, mock_orchestrator_class, product_search_request, mock_background_tasks
    ):
        """Test product search with no results."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.search_products = AsyncMock(return_value=[])
        mock_orchestrator_class.return_value = mock_orchestrator

        response = await product_search_webhook(
            request=product_search_request,
            background_tasks=mock_background_tasks
        )

        assert response.total == 0
        assert response.products == []

    @pytest.mark.asyncio
    @patch("api.services.scraper.ScraperOrchestrator")
    async def test_product_search_error(
        self, mock_orchestrator_class, product_search_request, mock_background_tasks
    ):
        """Test product search with error."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.search_products = AsyncMock(side_effect=Exception("Scraper error"))
        mock_orchestrator_class.return_value = mock_orchestrator

        with pytest.raises(HTTPException) as exc_info:
            await product_search_webhook(
                request=product_search_request,
                background_tasks=mock_background_tasks
            )

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    @patch("api.services.scraper.ScraperOrchestrator")
    async def test_product_search_formats_price(
        self, mock_orchestrator_class, product_search_request, mock_background_tasks
    ):
        """Test that prices are formatted correctly."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.search_products = AsyncMock(return_value=[
            {"title": "Product", "price": 123.45, "store": "Store", "url": "#"}
        ])
        mock_orchestrator_class.return_value = mock_orchestrator

        response = await product_search_webhook(
            request=product_search_request,
            background_tasks=mock_background_tasks
        )

        assert response.products[0]["price"] == "R$ 123.45"


# ==================== PRICE ALERT WEBHOOK TESTS ====================

class TestPriceAlertWebhook:
    """Tests for price alert webhook."""

    @pytest.mark.asyncio
    async def test_price_alert_success(self, price_alert_request, mock_background_tasks):
        """Test successful price alert logging."""
        response = await price_alert_webhook(
            request=price_alert_request,
            background_tasks=mock_background_tasks
        )

        assert response["success"] is True
        assert response["message"] == "Price alert logged"
        mock_background_tasks.add_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_price_alert_logs_correct_data(
        self, price_alert_request, mock_background_tasks
    ):
        """Test that price alert logs correct data."""
        await price_alert_webhook(
            request=price_alert_request,
            background_tasks=mock_background_tasks
        )

        # Verify background task was called with correct params
        call_args = mock_background_tasks.add_task.call_args
        assert call_args[0][1] == "user-123"  # user_id
        assert call_args[0][2] == "prod-456"  # product_id


# ==================== GENERIC EVENT WEBHOOK TESTS ====================

class TestGenericEventWebhook:
    """Tests for generic n8n event webhook."""

    @pytest.mark.asyncio
    @patch("api.routes.n8n_webhooks._track_interaction")
    async def test_user_interaction_event(self, mock_track, n8n_event_request):
        """Test processing user interaction event."""
        response = await generic_event_webhook(request=n8n_event_request)

        assert response["success"] is True
        assert response["event_processed"] == "user_interaction"
        mock_track.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("api.routes.n8n_webhooks._track_workflow_completion")
    async def test_workflow_completed_event(self, mock_track):
        """Test processing workflow completed event."""
        request = N8nEventRequest(
            event_type="workflow_completed",
            data={"workflow_id": "wf-123", "duration": 1500}
        )

        response = await generic_event_webhook(request=request)

        assert response["success"] is True
        assert response["event_processed"] == "workflow_completed"
        mock_track.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_error_occurred_event(self):
        """Test processing error event."""
        request = N8nEventRequest(
            event_type="error_occurred",
            data={"error": "Something went wrong", "workflow_id": "wf-456"}
        )

        response = await generic_event_webhook(request=request)

        assert response["success"] is True
        assert response["event_processed"] == "error_occurred"

    @pytest.mark.asyncio
    async def test_unknown_event_type(self):
        """Test processing unknown event type."""
        request = N8nEventRequest(
            event_type="unknown_event",
            data={}
        )

        response = await generic_event_webhook(request=request)

        assert response["success"] is True


# ==================== TRIGGER ENDPOINTS TESTS ====================

class TestTriggerNewUserOnboarding:
    """Tests for new user onboarding trigger."""

    @pytest.mark.asyncio
    @patch("api.routes.n8n_webhooks.get_n8n_client")
    async def test_trigger_onboarding_success(self, mock_get_client, mock_user):
        """Test successful onboarding trigger."""
        mock_client = MagicMock()
        mock_client.trigger_webhook = AsyncMock()
        mock_get_client.return_value = mock_client

        response = await trigger_new_user_onboarding(user=mock_user)

        assert response["success"] is True
        assert response["message"] == "Onboarding triggered"
        mock_client.trigger_webhook.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("api.routes.n8n_webhooks.get_n8n_client")
    async def test_trigger_onboarding_sends_user_data(self, mock_get_client, mock_user):
        """Test that onboarding trigger sends correct user data."""
        mock_client = MagicMock()
        mock_client.trigger_webhook = AsyncMock()
        mock_get_client.return_value = mock_client

        await trigger_new_user_onboarding(user=mock_user)

        call_args = mock_client.trigger_webhook.call_args
        assert call_args[1]["webhook_path"] == "/didin/new-user"
        assert call_args[1]["data"]["user_id"] == "user-123"
        assert call_args[1]["data"]["email"] == "test@example.com"


# ==================== MODEL TESTS ====================

class TestModels:
    """Tests for Pydantic models."""

    def test_product_search_request(self):
        """Test ProductSearchRequest model."""
        request = ProductSearchRequest(
            query="laptop",
            conversation_id="conv-1",
            limit=10
        )
        assert request.query == "laptop"
        assert request.limit == 10

    def test_product_search_request_default_limit(self):
        """Test ProductSearchRequest default limit."""
        request = ProductSearchRequest(
            query="phone",
            conversation_id="conv-1"
        )
        assert request.limit == 5

    def test_price_alert_request(self):
        """Test PriceAlertTriggeredRequest model."""
        request = PriceAlertTriggeredRequest(
            user_id="user-1",
            product_id="prod-1",
            old_price=100.0,
            new_price=80.0,
            discount_percentage=20.0
        )
        assert request.discount_percentage == 20.0

    def test_workflow_execution_request(self):
        """Test WorkflowExecutionRequest model."""
        request = WorkflowExecutionRequest(
            workflow_id="wf-123",
            data={"key": "value"}
        )
        assert request.workflow_id == "wf-123"

    def test_n8n_event_request(self):
        """Test N8nEventRequest model."""
        request = N8nEventRequest(
            event_type="custom_event",
            conversation_id="conv-1",
            data={"action": "test"}
        )
        assert request.event_type == "custom_event"

    def test_n8n_event_request_optional_fields(self):
        """Test N8nEventRequest optional fields."""
        request = N8nEventRequest(
            event_type="event",
            data={}
        )
        assert request.conversation_id is None

    def test_product_search_response(self):
        """Test ProductSearchResponse model."""
        response = ProductSearchResponse(
            products=[{"name": "Test"}],
            total=1,
            query="test"
        )
        assert response.total == 1


# ==================== ROUTER TESTS ====================

class TestRouter:
    """Tests for router configuration."""

    def test_router_prefix(self):
        """Verify router has correct prefix."""
        assert router.prefix == "/n8n"

    def test_router_has_webhook_endpoints(self):
        """Verify router has webhook endpoints."""
        routes = [r.path for r in router.routes]
        
        assert "/n8n/webhook/product-search" in routes
        assert "/n8n/webhook/price-alert" in routes
        assert "/n8n/webhook/event" in routes

    def test_router_has_trigger_endpoints(self):
        """Verify router has trigger endpoints."""
        routes = [r.path for r in router.routes]
        
        assert "/n8n/trigger/new-user" in routes
