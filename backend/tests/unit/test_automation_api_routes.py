"""
Unit Tests for Automation API Routes
====================================
Tests for automation_api.py endpoints.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from modules.automation.n8n_orchestrator import AutomationType, ChannelType

# ============================================
# MOCK CLASSES
# ============================================

class MockAutomationResult:
    """Mock automation result"""

    def __init__(self, success=True, event_id="evt-123", error=None):
        self.success = success
        self.event_id = event_id
        self.error = error


# ============================================
# SCHEMA TESTS
# ============================================

class TestRequestSchemas:
    """Tests for request schemas"""

    def test_trigger_request_schema(self):
        """Test TriggerRequest model"""
        from api.routes.automation_api import TriggerRequest

        request = TriggerRequest(
            automation_type=AutomationType.NEW_USER_WELCOME,
            user_id="user-123",
            data={"name": "Test User"}
        )

        assert request.automation_type == AutomationType.NEW_USER_WELCOME
        assert request.user_id == "user-123"
        assert request.channel == ChannelType.WHATSAPP
        assert request.force is False

    def test_trigger_request_with_force(self):
        """Test TriggerRequest with force=True"""
        from api.routes.automation_api import TriggerRequest

        request = TriggerRequest(
            automation_type=AutomationType.CART_ABANDONED,
            user_id="user-456",
            force=True
        )

        assert request.force is True

    def test_onboarding_request_schema(self):
        """Test OnboardingRequest model"""
        from api.routes.automation_api import OnboardingRequest

        request = OnboardingRequest(
            user_id="user-123",
            name="Test User",
            phone="+5511999999999",
            email="test@example.com"
        )

        assert request.user_id == "user-123"
        assert request.name == "Test User"
        assert request.channel == ChannelType.WHATSAPP

    def test_cart_abandoned_request_schema(self):
        """Test CartAbandonedRequest model"""
        from api.routes.automation_api import CartAbandonedRequest

        request = CartAbandonedRequest(
            user_id="user-123",
            name="Test User",
            product_name="iPhone 15",
            product_url="https://example.com/iphone",
            price=5999.00
        )

        assert request.product_name == "iPhone 15"
        assert request.price == 5999.00

    def test_price_drop_request_schema(self):
        """Test PriceDropRequest model"""
        from api.routes.automation_api import PriceDropRequest

        request = PriceDropRequest(
            user_id="user-123",
            name="Test User",
            product_name="TV Samsung",
            product_url="https://example.com/tv",
            old_price=2500.00,
            new_price=1999.00
        )

        assert request.old_price == 2500.00
        assert request.new_price == 1999.00

    def test_post_purchase_request_schema(self):
        """Test PostPurchaseRequest model"""
        from api.routes.automation_api import PostPurchaseRequest

        request = PostPurchaseRequest(
            user_id="user-123",
            name="Test User",
            order_id="order-456",
            product_name="Test Product",
            total=199.90
        )

        assert request.order_id == "order-456"
        assert request.total == 199.90

    def test_lead_qualified_request_schema(self):
        """Test LeadQualifiedRequest model"""
        from api.routes.automation_api import LeadQualifiedRequest

        request = LeadQualifiedRequest(
            user_id="user-123",
            name="Test User",
            lead_score=85,
            interested_products=["Product A", "Product B"]
        )

        assert request.lead_score == 85
        assert len(request.interested_products) == 2

    def test_reengagement_request_schema(self):
        """Test ReengagementRequest model"""
        from api.routes.automation_api import ReengagementRequest

        request = ReengagementRequest(
            user_id="user-123",
            name="Test User",
            days_inactive=30,
            last_product_viewed="iPhone 15"
        )

        assert request.days_inactive == 30
        assert request.last_product_viewed == "iPhone 15"


class TestResponseSchemas:
    """Tests for response schemas"""

    def test_automation_response_success(self):
        """Test AutomationResponse model"""
        from api.routes.automation_api import AutomationResponse

        response = AutomationResponse(
            success=True,
            event_id="event-123",
            message="Automation triggered"
        )

        assert response.success is True
        assert response.event_id == "event-123"

    def test_automation_response_error(self):
        """Test AutomationResponse with error"""
        from api.routes.automation_api import AutomationResponse

        response = AutomationResponse(
            success=False,
            error="Rate limit exceeded"
        )

        assert response.success is False
        assert response.error == "Rate limit exceeded"

    def test_automation_response_with_scheduled_at(self):
        """Test AutomationResponse with scheduled_at"""
        from api.routes.automation_api import AutomationResponse

        scheduled = datetime.now()
        response = AutomationResponse(
            success=True,
            event_id="event-123",
            scheduled_at=scheduled
        )

        assert response.scheduled_at == scheduled


# ============================================
# ENDPOINT TESTS
# ============================================

class TestTriggerAutomationEndpoint:
    """Tests for trigger automation endpoint"""

    @pytest.mark.asyncio
    async def test_trigger_automation_success(self):
        """Test successful automation trigger"""
        from api.routes.automation_api import (TriggerRequest,
                                               trigger_automation)

        mock_orchestrator = MagicMock()
        mock_orchestrator.trigger_automation = AsyncMock(
            return_value=MockAutomationResult(success=True)
        )

        with patch(
            'api.routes.automation_api.get_orchestrator',
            return_value=mock_orchestrator
        ):
            request = TriggerRequest(
                automation_type=AutomationType.NEW_USER_WELCOME,
                user_id="user-123"
            )

            result = await trigger_automation(request)

            assert result.success is True
            mock_orchestrator.trigger_automation.assert_called_once()


class TestOnboardingEndpoint:
    """Tests for onboarding endpoint"""

    @pytest.mark.asyncio
    async def test_trigger_onboarding_success(self):
        """Test successful onboarding trigger"""
        from api.routes.automation_api import (OnboardingRequest,
                                               trigger_onboarding)

        mock_orchestrator = MagicMock()
        mock_orchestrator.trigger_onboarding = AsyncMock(
            return_value=MockAutomationResult(success=True, event_id="evt-123")
        )

        with patch(
            'api.routes.automation_api.get_orchestrator',
            return_value=mock_orchestrator
        ):
            request = OnboardingRequest(
                user_id="user-123",
                name="Test User",
                phone="+5511999999999"
            )

            result = await trigger_onboarding(request)

            assert result.success is True


class TestCartAbandonedEndpoint:
    """Tests for cart abandoned endpoint"""

    @pytest.mark.asyncio
    async def test_trigger_cart_abandoned_success(self):
        """Test successful cart abandoned trigger"""
        from api.routes.automation_api import (CartAbandonedRequest,
                                               trigger_cart_abandoned)

        mock_orchestrator = MagicMock()
        mock_orchestrator.trigger_cart_abandoned = AsyncMock(
            return_value=MockAutomationResult(success=True)
        )

        with patch(
            'api.routes.automation_api.get_orchestrator',
            return_value=mock_orchestrator
        ):
            request = CartAbandonedRequest(
                user_id="user-123",
                name="Test User",
                product_name="Test Product",
                product_url="https://example.com/product",
                price=99.90
            )

            result = await trigger_cart_abandoned(request)

            assert result.success is True


class TestPriceDropEndpoint:
    """Tests for price drop endpoint"""

    @pytest.mark.asyncio
    async def test_trigger_price_drop_success(self):
        """Test successful price drop trigger"""
        from api.routes.automation_api import (PriceDropRequest,
                                               trigger_price_drop)

        mock_orchestrator = MagicMock()
        mock_orchestrator.trigger_price_drop = AsyncMock(
            return_value=MockAutomationResult(success=True)
        )

        with patch(
            'api.routes.automation_api.get_orchestrator',
            return_value=mock_orchestrator
        ):
            request = PriceDropRequest(
                user_id="user-123",
                name="Test User",
                product_name="Test Product",
                product_url="https://example.com/product",
                old_price=199.90,
                new_price=149.90
            )

            result = await trigger_price_drop(request)

            assert result.success is True


class TestPostPurchaseEndpoint:
    """Tests for post purchase endpoint"""

    @pytest.mark.asyncio
    async def test_trigger_post_purchase_success(self):
        """Test successful post purchase trigger"""
        from api.routes.automation_api import (PostPurchaseRequest,
                                               trigger_post_purchase)

        mock_orchestrator = MagicMock()
        mock_orchestrator.trigger_post_purchase = AsyncMock(
            return_value=MockAutomationResult(success=True)
        )

        with patch(
            'api.routes.automation_api.get_orchestrator',
            return_value=mock_orchestrator
        ):
            request = PostPurchaseRequest(
                user_id="user-123",
                name="Test User",
                order_id="order-456",
                product_name="Test Product",
                total=199.90
            )

            result = await trigger_post_purchase(request)

            assert result.success is True


class TestLeadQualifiedEndpoint:
    """Tests for lead qualified endpoint"""

    @pytest.mark.asyncio
    async def test_trigger_lead_qualified_success(self):
        """Test successful lead qualified trigger"""
        from api.routes.automation_api import (LeadQualifiedRequest,
                                               trigger_lead_qualified)

        mock_orchestrator = MagicMock()
        mock_orchestrator.trigger_lead_qualified = AsyncMock(
            return_value=MockAutomationResult(success=True)
        )

        with patch(
            'api.routes.automation_api.get_orchestrator',
            return_value=mock_orchestrator
        ):
            request = LeadQualifiedRequest(
                user_id="user-123",
                name="Test User",
                lead_score=85
            )

            result = await trigger_lead_qualified(request)

            assert result.success is True


class TestReengagementEndpoint:
    """Tests for reengagement endpoint"""

    @pytest.mark.asyncio
    async def test_trigger_reengagement_success(self):
        """Test successful reengagement trigger"""
        from api.routes.automation_api import (ReengagementRequest,
                                               trigger_reengagement)

        mock_orchestrator = MagicMock()
        mock_orchestrator.trigger_reengagement = AsyncMock(
            return_value=MockAutomationResult(success=True)
        )

        with patch(
            'api.routes.automation_api.get_orchestrator',
            return_value=mock_orchestrator
        ):
            request = ReengagementRequest(
                user_id="user-123",
                name="Test User",
                days_inactive=30
            )

            result = await trigger_reengagement(request)

            assert result.success is True


class TestStatsEndpoint:
    """Tests for stats endpoint"""

    @pytest.mark.asyncio
    async def test_get_automation_stats(self):
        """Test get automation stats"""
        from api.routes.automation_api import get_automation_stats

        mock_orchestrator = MagicMock()
        mock_orchestrator.get_automation_stats = MagicMock(
            return_value={
                "total_triggered": 100,
                "successful": 95,
                "failed": 5
            }
        )

        with patch(
            'api.routes.automation_api.get_orchestrator',
            return_value=mock_orchestrator
        ):
            result = await get_automation_stats()

            assert "total_triggered" in result


class TestListAutomationsEndpoint:
    """Tests for list automations endpoint"""

    @pytest.mark.asyncio
    async def test_list_automations(self):
        """Test list automations"""
        from api.routes.automation_api import list_automations

        mock_orchestrator = MagicMock()
        mock_orchestrator.list_automations = AsyncMock(
            return_value=[
                {"type": "new_user_welcome", "enabled": True},
                {"type": "cart_abandoned", "enabled": True},
            ]
        )

        with patch(
            'api.routes.automation_api.get_orchestrator',
            return_value=mock_orchestrator
        ):
            result = await list_automations()

            assert "automations" in result
