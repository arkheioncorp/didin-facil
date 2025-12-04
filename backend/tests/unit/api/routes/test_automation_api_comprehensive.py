"""
Comprehensive Tests for Automation API Routes
==============================================
Testes unitários abrangentes para automation_api.py com 80%+ coverage.

Coverage Target:
- Todos os endpoints (trigger, onboarding, cart-abandoned, price-drop, etc.)
- Validação de schemas Pydantic
- Tratamento de erros e edge cases
- Integração com orchestrator mockado
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.automation_api import router
from fastapi import FastAPI
from fastapi.testclient import TestClient
from modules.automation.n8n_orchestrator import (AutomationPriority,
                                                 AutomationType, ChannelType)

# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def app():
    """Create a test FastAPI app with the automation router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator."""
    mock = MagicMock()
    mock.trigger_automation = AsyncMock()
    mock.trigger_onboarding = AsyncMock()
    mock.trigger_cart_abandoned = AsyncMock()
    mock.trigger_price_drop = AsyncMock()
    mock.trigger_post_purchase = AsyncMock()
    mock.trigger_lead_qualified = AsyncMock()
    mock.trigger_reengagement = AsyncMock()
    mock.get_automation_stats = MagicMock()
    mock.get_pending_events = MagicMock()
    mock.process_pending_events = AsyncMock()
    mock.update_automation_config = MagicMock()
    mock.enable_automation = MagicMock()
    mock.disable_automation = MagicMock()
    mock.automations = {}
    return mock


@pytest.fixture
def mock_automation_result_success():
    """Create a successful automation result that simulates success."""
    # Use MagicMock to simulate the result object
    result = MagicMock()
    result.success = True
    result.event_id = "evt_123456"
    result.error = None
    result.scheduled_at = datetime.now()
    return result


@pytest.fixture
def mock_automation_result_failure():
    """Create a failed automation result that simulates failure."""
    # Note: AutomationResult from n8n_orchestrator requires event_id
    # For failures, the endpoint returns a different response pattern
    result = MagicMock()
    result.success = False
    result.event_id = None
    result.error = "Rate limit exceeded"
    result.scheduled_at = None
    return result


# ============================================
# SCHEMA VALIDATION TESTS
# ============================================

class TestTriggerRequestSchema:
    """Tests for TriggerRequest schema validation."""

    def test_valid_trigger_request(self, client, mock_orchestrator, mock_automation_result_success):
        """Test valid trigger request is accepted."""
        mock_orchestrator.trigger_automation.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/trigger", json={
                "automation_type": "new_user_welcome",
                "user_id": "user_123",
                "channel": "whatsapp",
                "data": {"name": "John"},
                "force": False
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["event_id"] == "evt_123456"

    def test_trigger_request_minimal(self, client, mock_orchestrator, mock_automation_result_success):
        """Test trigger request with only required fields."""
        mock_orchestrator.trigger_automation.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/trigger", json={
                "automation_type": "cart_abandoned",
                "user_id": "user_456"
            })
        
        assert response.status_code == 200

    def test_trigger_request_invalid_automation_type(self, client):
        """Test invalid automation type returns 422."""
        response = client.post("/automation/trigger", json={
            "automation_type": "invalid_type",
            "user_id": "user_123"
        })
        
        assert response.status_code == 422

    def test_trigger_request_missing_user_id(self, client):
        """Test missing user_id returns 422."""
        response = client.post("/automation/trigger", json={
            "automation_type": "new_user_welcome"
        })
        
        assert response.status_code == 422

    def test_trigger_request_with_all_channels(self, client, mock_orchestrator, mock_automation_result_success):
        """Test all channel types are valid."""
        mock_orchestrator.trigger_automation.return_value = mock_automation_result_success
        
        channels = ["whatsapp", "instagram_dm", "email", "sms", "push"]
        
        for channel in channels:
            with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
                response = client.post("/automation/trigger", json={
                    "automation_type": "new_user_welcome",
                    "user_id": "user_123",
                    "channel": channel
                })
            
            assert response.status_code == 200, f"Channel {channel} should be valid"


class TestOnboardingRequestSchema:
    """Tests for OnboardingRequest schema validation."""

    def test_valid_onboarding_request(self, client, mock_orchestrator, mock_automation_result_success):
        """Test valid onboarding request."""
        mock_orchestrator.trigger_onboarding.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/onboarding", json={
                "user_id": "user_123",
                "name": "João Silva",
                "phone": "+5511999999999",
                "email": "joao@email.com",
                "channel": "whatsapp"
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_onboarding_minimal_fields(self, client, mock_orchestrator, mock_automation_result_success):
        """Test onboarding with only required fields."""
        mock_orchestrator.trigger_onboarding.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/onboarding", json={
                "user_id": "user_123",
                "name": "João"
            })
        
        assert response.status_code == 200

    def test_onboarding_missing_user_id(self, client):
        """Test missing user_id returns 422."""
        response = client.post("/automation/onboarding", json={
            "name": "João"
        })
        
        assert response.status_code == 422

    def test_onboarding_missing_name(self, client):
        """Test missing name returns 422."""
        response = client.post("/automation/onboarding", json={
            "user_id": "user_123"
        })
        
        assert response.status_code == 422


class TestCartAbandonedRequestSchema:
    """Tests for CartAbandonedRequest schema validation."""

    def test_valid_cart_abandoned_request(self, client, mock_orchestrator, mock_automation_result_success):
        """Test valid cart abandoned request."""
        mock_orchestrator.trigger_cart_abandoned.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/cart-abandoned", json={
                "user_id": "user_123",
                "name": "Maria",
                "product_name": "Notebook Dell",
                "product_url": "https://loja.com/notebook",
                "price": 2999.99,
                "channel": "whatsapp"
            })
        
        assert response.status_code == 200

    def test_cart_abandoned_missing_product_url(self, client):
        """Test missing product_url returns 422."""
        response = client.post("/automation/cart-abandoned", json={
            "user_id": "user_123",
            "name": "Maria",
            "product_name": "Notebook",
            "price": 2999.99
        })
        
        assert response.status_code == 422


class TestPriceDropRequestSchema:
    """Tests for PriceDropRequest schema validation."""

    def test_valid_price_drop_request(self, client, mock_orchestrator, mock_automation_result_success):
        """Test valid price drop request."""
        mock_orchestrator.trigger_price_drop.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/price-drop", json={
                "user_id": "user_123",
                "name": "Carlos",
                "product_name": "iPhone 15",
                "product_url": "https://loja.com/iphone",
                "old_price": 5999.00,
                "new_price": 4999.00
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Alerta de preço enviado"

    def test_price_drop_missing_old_price(self, client):
        """Test missing old_price returns 422."""
        response = client.post("/automation/price-drop", json={
            "user_id": "user_123",
            "name": "Carlos",
            "product_name": "iPhone",
            "product_url": "https://loja.com/iphone",
            "new_price": 4999.00
        })
        
        assert response.status_code == 422


class TestPostPurchaseRequestSchema:
    """Tests for PostPurchaseRequest schema validation."""

    def test_valid_post_purchase_request(self, client, mock_orchestrator, mock_automation_result_success):
        """Test valid post purchase request."""
        mock_orchestrator.trigger_post_purchase.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/post-purchase", json={
                "user_id": "user_123",
                "name": "Ana",
                "order_id": "ORD-12345",
                "product_name": "Fone Bluetooth",
                "total": 199.99
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Agradecimento enviado"


class TestLeadQualifiedRequestSchema:
    """Tests for LeadQualifiedRequest schema validation."""

    def test_valid_lead_qualified_request(self, client, mock_orchestrator, mock_automation_result_success):
        """Test valid lead qualified request."""
        mock_orchestrator.trigger_lead_qualified.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/lead-qualified", json={
                "user_id": "user_123",
                "name": "Pedro",
                "lead_score": 85,
                "interested_products": ["notebooks", "smartphones"],
                "channel": "email"
            })
        
        assert response.status_code == 200

    def test_lead_qualified_empty_products(self, client, mock_orchestrator, mock_automation_result_success):
        """Test lead qualified with empty product list."""
        mock_orchestrator.trigger_lead_qualified.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/lead-qualified", json={
                "user_id": "user_123",
                "name": "Pedro",
                "lead_score": 50
            })
        
        assert response.status_code == 200


class TestReengagementRequestSchema:
    """Tests for ReengagementRequest schema validation."""

    def test_valid_reengagement_request(self, client, mock_orchestrator, mock_automation_result_success):
        """Test valid reengagement request."""
        mock_orchestrator.trigger_reengagement.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/reengagement", json={
                "user_id": "user_123",
                "name": "Lucia",
                "days_inactive": 30,
                "last_product_viewed": "Smart TV Samsung"
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Campanha de reengajamento iniciada"


# ============================================
# ENDPOINT TESTS
# ============================================

class TestTriggerEndpoint:
    """Tests for /automation/trigger endpoint."""

    def test_trigger_success(self, client, mock_orchestrator, mock_automation_result_success):
        """Test successful trigger."""
        mock_orchestrator.trigger_automation.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/trigger", json={
                "automation_type": "new_user_welcome",
                "user_id": "user_123",
                "data": {"welcome": True}
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Automação disparada com sucesso"
        
        mock_orchestrator.trigger_automation.assert_called_once()

    def test_trigger_failure(self, client, mock_orchestrator, mock_automation_result_failure):
        """Test trigger failure response."""
        mock_orchestrator.trigger_automation.return_value = mock_automation_result_failure
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/trigger", json={
                "automation_type": "cart_abandoned",
                "user_id": "user_123"
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Rate limit exceeded"
        assert data["message"] is None

    def test_trigger_with_force(self, client, mock_orchestrator, mock_automation_result_success):
        """Test trigger with force=True."""
        mock_orchestrator.trigger_automation.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/trigger", json={
                "automation_type": "inactive_user",
                "user_id": "user_123",
                "force": True
            })
        
        assert response.status_code == 200
        
        call_kwargs = mock_orchestrator.trigger_automation.call_args.kwargs
        assert call_kwargs["force"] is True


class TestOnboardingEndpoint:
    """Tests for /automation/onboarding endpoint."""

    def test_onboarding_success(self, client, mock_orchestrator, mock_automation_result_success):
        """Test successful onboarding trigger."""
        mock_orchestrator.trigger_onboarding.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/onboarding", json={
                "user_id": "user_123",
                "name": "João Silva",
                "phone": "+5511999999999",
                "email": "joao@email.com"
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Onboarding iniciado"

    def test_onboarding_passes_all_fields(self, client, mock_orchestrator, mock_automation_result_success):
        """Test all fields are passed to orchestrator."""
        mock_orchestrator.trigger_onboarding.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/onboarding", json={
                "user_id": "user_123",
                "name": "Maria",
                "phone": "+5511888888888",
                "email": "maria@test.com",
                "channel": "email"
            })
        
        assert response.status_code == 200
        
        call_kwargs = mock_orchestrator.trigger_onboarding.call_args.kwargs
        assert call_kwargs["user_id"] == "user_123"
        assert call_kwargs["name"] == "Maria"
        assert call_kwargs["phone"] == "+5511888888888"
        assert call_kwargs["email"] == "maria@test.com"


class TestCartAbandonedEndpoint:
    """Tests for /automation/cart-abandoned endpoint."""

    def test_cart_abandoned_success(self, client, mock_orchestrator, mock_automation_result_success):
        """Test successful cart abandoned trigger."""
        mock_orchestrator.trigger_cart_abandoned.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/cart-abandoned", json={
                "user_id": "user_123",
                "name": "Cliente",
                "product_name": "Notebook",
                "product_url": "https://loja.com/notebook",
                "price": 2500.00
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Recuperação de carrinho agendada"


class TestPriceDropEndpoint:
    """Tests for /automation/price-drop endpoint."""

    def test_price_drop_success(self, client, mock_orchestrator, mock_automation_result_success):
        """Test successful price drop alert."""
        mock_orchestrator.trigger_price_drop.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/price-drop", json={
                "user_id": "user_123",
                "name": "Cliente",
                "product_name": "TV 55\"",
                "product_url": "https://loja.com/tv",
                "old_price": 3000.00,
                "new_price": 2500.00
            })
        
        assert response.status_code == 200

    def test_price_drop_passes_prices(self, client, mock_orchestrator, mock_automation_result_success):
        """Test price values are passed correctly."""
        mock_orchestrator.trigger_price_drop.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/price-drop", json={
                "user_id": "user_123",
                "name": "Cliente",
                "product_name": "Produto",
                "product_url": "https://loja.com",
                "old_price": 1000.50,
                "new_price": 899.99
            })
        
        call_kwargs = mock_orchestrator.trigger_price_drop.call_args.kwargs
        assert call_kwargs["old_price"] == 1000.50
        assert call_kwargs["new_price"] == 899.99


class TestPostPurchaseEndpoint:
    """Tests for /automation/post-purchase endpoint."""

    def test_post_purchase_success(self, client, mock_orchestrator, mock_automation_result_success):
        """Test successful post purchase trigger."""
        mock_orchestrator.trigger_post_purchase.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/post-purchase", json={
                "user_id": "user_123",
                "name": "Comprador",
                "order_id": "ORD-99999",
                "product_name": "Smartphone",
                "total": 1599.00
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Agradecimento enviado"


class TestStatsEndpoint:
    """Tests for /automation/stats endpoint."""

    def test_get_stats(self, client, mock_orchestrator):
        """Test getting automation stats."""
        mock_stats = {
            "total_automations": 6,
            "enabled_automations": 4,
            "pending_events": 10,
            "processed_today": 150
        }
        mock_orchestrator.get_automation_stats.return_value = mock_stats
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.get("/automation/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_automations"] == 6
        assert data["pending_events"] == 10


class TestListAutomationsEndpoint:
    """Tests for /automation/list endpoint."""

    def test_list_automations_empty(self, client, mock_orchestrator):
        """Test listing automations when empty."""
        mock_orchestrator.automations = {}
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.get("/automation/list")
        
        assert response.status_code == 200
        data = response.json()
        assert data["automations"] == []

    def test_list_automations_with_data(self, client, mock_orchestrator):
        """Test listing automations with configured data."""
        mock_config = MagicMock()
        mock_config.enabled = True
        mock_config.priority = AutomationPriority.HIGH
        mock_config.channels = [ChannelType.WHATSAPP, ChannelType.EMAIL]
        mock_config.delay_minutes = 5
        mock_config.webhook_path = "/webhook/onboarding"
        mock_config.min_delay_between_triggers_hours = 24
        mock_config.max_triggers_per_user_per_day = 3
        mock_config.allowed_hours_start = 9
        mock_config.allowed_hours_end = 21
        
        mock_orchestrator.automations = {
            AutomationType.NEW_USER_WELCOME: mock_config
        }
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.get("/automation/list")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["automations"]) == 1
        automation = data["automations"][0]
        assert automation["type"] == "new_user_welcome"
        assert automation["enabled"] is True
        assert automation["channels"] == ["whatsapp", "email"]


class TestPendingEventsEndpoint:
    """Tests for /automation/pending endpoint."""

    def test_list_pending_empty(self, client, mock_orchestrator):
        """Test listing pending events when empty."""
        mock_orchestrator.get_pending_events.return_value = []
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.get("/automation/pending")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["events"] == []

    def test_list_pending_with_events(self, client, mock_orchestrator):
        """Test listing pending events with data."""
        mock_event = MagicMock()
        mock_event.id = "evt_123"
        mock_event.automation_type = AutomationType.CART_ABANDONED
        mock_event.user_id = "user_456"
        mock_event.channel = ChannelType.WHATSAPP
        mock_event.scheduled_at = datetime(2024, 1, 15, 10, 30)
        mock_event.status = "pending"
        
        mock_orchestrator.get_pending_events.return_value = [mock_event]
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.get("/automation/pending")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["events"][0]["id"] == "evt_123"
        assert data["events"][0]["type"] == "cart_abandoned"


class TestProcessPendingEndpoint:
    """Tests for /automation/process-pending endpoint."""

    def test_process_pending(self, client, mock_orchestrator):
        """Test processing pending events."""
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/process-pending")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Processamento iniciado em background"


class TestUpdateConfigEndpoint:
    """Tests for /automation/{automation_type}/config endpoint."""

    def test_update_config_success(self, client, mock_orchestrator):
        """Test updating automation config."""
        mock_orchestrator.automations = {
            AutomationType.CART_ABANDONED: MagicMock()
        }
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.put("/automation/cart_abandoned/config", json={
                "enabled": False,
                "delay_minutes": 30
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "cart_abandoned" in data["message"]
        
        mock_orchestrator.update_automation_config.assert_called_once()

    def test_update_config_not_found(self, client, mock_orchestrator):
        """Test updating non-existent automation config."""
        mock_orchestrator.automations = {}
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.put("/automation/cart_abandoned/config", json={
                "enabled": False
            })
        
        assert response.status_code == 404
        data = response.json()
        assert "não encontrada" in data["detail"]

    def test_update_config_partial(self, client, mock_orchestrator):
        """Test partial config update."""
        mock_orchestrator.automations = {
            AutomationType.NEW_USER_WELCOME: MagicMock()
        }
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.put("/automation/new_user_welcome/config", json={
                "priority": "high"
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["updates"]["priority"] == "high"


class TestEnableDisableEndpoints:
    """Tests for enable/disable automation endpoints."""

    def test_enable_automation(self, client, mock_orchestrator):
        """Test enabling an automation."""
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/cart_abandoned/enable")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "habilitada" in data["message"]
        
        mock_orchestrator.enable_automation.assert_called_once_with(AutomationType.CART_ABANDONED)

    def test_disable_automation(self, client, mock_orchestrator):
        """Test disabling an automation."""
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/price_drop_alert/disable")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "desabilitada" in data["message"]
        
        mock_orchestrator.disable_automation.assert_called_once_with(AutomationType.PRICE_DROP_ALERT)


# ============================================
# EDGE CASES AND ERROR HANDLING
# ============================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_data_dict(self, client, mock_orchestrator, mock_automation_result_success):
        """Test trigger with empty data dict."""
        mock_orchestrator.trigger_automation.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/trigger", json={
                "automation_type": "new_user_welcome",
                "user_id": "user_123",
                "data": {}
            })
        
        assert response.status_code == 200

    def test_special_characters_in_user_id(self, client, mock_orchestrator, mock_automation_result_success):
        """Test user_id with special characters."""
        mock_orchestrator.trigger_automation.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/trigger", json={
                "automation_type": "cart_abandoned",
                "user_id": "user@123_test-id"
            })
        
        assert response.status_code == 200

    def test_unicode_in_name(self, client, mock_orchestrator, mock_automation_result_success):
        """Test unicode characters in name field."""
        mock_orchestrator.trigger_onboarding.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/onboarding", json={
                "user_id": "user_123",
                "name": "José María Fernández García 日本語"
            })
        
        assert response.status_code == 200

    def test_very_long_product_url(self, client, mock_orchestrator, mock_automation_result_success):
        """Test very long product URL."""
        mock_orchestrator.trigger_cart_abandoned.return_value = mock_automation_result_success
        
        long_url = "https://loja.com/" + "a" * 2000
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/cart-abandoned", json={
                "user_id": "user_123",
                "name": "Cliente",
                "product_name": "Produto",
                "product_url": long_url,
                "price": 100.00
            })
        
        assert response.status_code == 200

    def test_zero_price(self, client, mock_orchestrator, mock_automation_result_success):
        """Test zero price value."""
        mock_orchestrator.trigger_cart_abandoned.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/cart-abandoned", json={
                "user_id": "user_123",
                "name": "Cliente",
                "product_name": "Produto Grátis",
                "product_url": "https://loja.com",
                "price": 0.0
            })
        
        assert response.status_code == 200

    def test_negative_lead_score(self, client, mock_orchestrator, mock_automation_result_success):
        """Test negative lead score."""
        mock_orchestrator.trigger_lead_qualified.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/lead-qualified", json={
                "user_id": "user_123",
                "name": "Lead",
                "lead_score": -10
            })
        
        # Should accept as Pydantic doesn't validate range
        assert response.status_code == 200

    def test_high_days_inactive(self, client, mock_orchestrator, mock_automation_result_success):
        """Test very high days_inactive value."""
        mock_orchestrator.trigger_reengagement.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/reengagement", json={
                "user_id": "user_123",
                "name": "Usuário",
                "days_inactive": 365
            })
        
        assert response.status_code == 200


class TestAllAutomationTypes:
    """Tests to ensure all automation types work."""

    @pytest.mark.parametrize("automation_type", [
        "new_user_welcome",
        "new_lead_nurturing", 
        "cart_abandoned",
        "price_drop_alert",
        "stock_low_alert",
        "product_available",
        "post_purchase_thanks",
        "review_request",
        "cross_sell",
        "upsell",
        "inactive_user",
        "birthday_greeting",
        "anniversary_discount",
        "ticket_created",
        "ticket_resolved",
        "nps_survey",
        "complaint_alert",
        "human_handoff",
        "new_post_scheduled",
        "post_published",
        "engagement_spike",
        "lead_qualified",
        "deal_won",
        "deal_lost"
    ])
    def test_all_automation_types(self, client, mock_orchestrator, mock_automation_result_success, automation_type):
        """Test all automation types are valid."""
        mock_orchestrator.trigger_automation.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/trigger", json={
                "automation_type": automation_type,
                "user_id": "user_123"
            })
        
        assert response.status_code == 200, f"Automation type {automation_type} should be valid"


# ============================================
# RESPONSE FORMAT TESTS
# ============================================

class TestResponseFormat:
    """Tests for response format consistency."""

    def test_success_response_format(self, client, mock_orchestrator, mock_automation_result_success):
        """Test success response has all expected fields."""
        mock_orchestrator.trigger_automation.return_value = mock_automation_result_success
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/trigger", json={
                "automation_type": "new_user_welcome",
                "user_id": "user_123"
            })
        
        data = response.json()
        assert "success" in data
        assert "event_id" in data
        assert "message" in data
        assert "error" in data

    def test_failure_response_format(self, client, mock_orchestrator, mock_automation_result_failure):
        """Test failure response has all expected fields."""
        mock_orchestrator.trigger_automation.return_value = mock_automation_result_failure
        
        with patch('api.routes.automation_api.get_orchestrator', return_value=mock_orchestrator):
            response = client.post("/automation/trigger", json={
                "automation_type": "cart_abandoned",
                "user_id": "user_123"
            })
        
        data = response.json()
        assert data["success"] is False
        assert data["error"] is not None
        assert data["message"] is None
        assert data["event_id"] is None
