"""
Comprehensive tests for automation_api.py
==========================================
Tests for automation API routes (Seller Bot).
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.automation_api import (AutomationResponse,
                                       CartAbandonedRequest,
                                       LeadQualifiedRequest, OnboardingRequest,
                                       PostPurchaseRequest, PriceDropRequest,
                                       ReengagementRequest, TriggerRequest,
                                       UpdateConfigRequest, router,
                                       trigger_automation,
                                       trigger_cart_abandoned,
                                       trigger_lead_qualified,
                                       trigger_onboarding,
                                       trigger_post_purchase,
                                       trigger_price_drop,
                                       trigger_reengagement)
from modules.automation.n8n_orchestrator import (AutomationPriority,
                                                 AutomationType, ChannelType)

# ==================== FIXTURES ====================


@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator."""
    orchestrator = MagicMock()
    
    # Create mock result
    result = MagicMock()
    result.success = True
    result.event_id = "evt123"
    result.error = None
    
    orchestrator.trigger_automation = AsyncMock(return_value=result)
    orchestrator.trigger_onboarding = AsyncMock(return_value=result)
    orchestrator.trigger_cart_abandoned = AsyncMock(return_value=result)
    orchestrator.trigger_price_drop = AsyncMock(return_value=result)
    orchestrator.trigger_post_purchase = AsyncMock(return_value=result)
    orchestrator.trigger_lead_qualified = AsyncMock(return_value=result)
    orchestrator.trigger_reengagement = AsyncMock(return_value=result)
    orchestrator.get_stats = AsyncMock(return_value={})
    orchestrator.list_automations = AsyncMock(return_value=[])
    orchestrator.update_config = AsyncMock(return_value=True)
    orchestrator.process_pending_events = AsyncMock(return_value={"processed": 0})
    
    return orchestrator


@pytest.fixture
def mock_failed_result():
    """Mock failed result."""
    result = MagicMock()
    result.success = False
    result.event_id = None
    result.error = "Rate limit exceeded"
    return result


# ==================== SCHEMA TESTS ====================


class TestSchemas:
    """Test Pydantic schemas."""
    
    def test_trigger_request(self):
        """Test TriggerRequest schema."""
        req = TriggerRequest(
            automation_type=AutomationType.NEW_USER_WELCOME,
            user_id="user123",
        )
        assert req.automation_type == AutomationType.NEW_USER_WELCOME
        assert req.channel == ChannelType.WHATSAPP
        assert req.force is False
    
    def test_trigger_request_with_force(self):
        """Test TriggerRequest with force flag."""
        req = TriggerRequest(
            automation_type=AutomationType.CART_ABANDONED,
            user_id="user123",
            force=True,
            data={"product_id": "123"},
        )
        assert req.force is True
        assert req.data["product_id"] == "123"
    
    def test_onboarding_request(self):
        """Test OnboardingRequest schema."""
        req = OnboardingRequest(
            user_id="user123",
            name="John Doe",
            phone="+5511999999999",
            email="john@example.com",
        )
        assert req.name == "John Doe"
        assert req.channel == ChannelType.WHATSAPP
    
    def test_cart_abandoned_request(self):
        """Test CartAbandonedRequest schema."""
        req = CartAbandonedRequest(
            user_id="user123",
            name="John",
            product_name="iPhone 15",
            product_url="https://example.com/iphone",
            price=4999.99,
        )
        assert req.product_name == "iPhone 15"
        assert req.price == 4999.99
    
    def test_price_drop_request(self):
        """Test PriceDropRequest schema."""
        req = PriceDropRequest(
            user_id="user123",
            name="John",
            product_name="iPhone 15",
            product_url="https://example.com/iphone",
            old_price=5999.00,
            new_price=4999.00,
        )
        assert req.old_price == 5999.00
        assert req.new_price == 4999.00
    
    def test_post_purchase_request(self):
        """Test PostPurchaseRequest schema."""
        req = PostPurchaseRequest(
            user_id="user123",
            name="John",
            order_id="ORD-123",
            product_name="iPhone 15",
            total=4999.99,
        )
        assert req.order_id == "ORD-123"
        assert req.total == 4999.99
    
    def test_lead_qualified_request(self):
        """Test LeadQualifiedRequest schema."""
        req = LeadQualifiedRequest(
            user_id="user123",
            name="John",
            lead_score=85,
            interested_products=["iPhone", "MacBook"],
        )
        assert req.lead_score == 85
        assert len(req.interested_products) == 2
    
    def test_reengagement_request(self):
        """Test ReengagementRequest schema."""
        req = ReengagementRequest(
            user_id="user123",
            name="John",
            days_inactive=30,
            last_product_viewed="iPhone 15",
        )
        assert req.days_inactive == 30
    
    def test_update_config_request(self):
        """Test UpdateConfigRequest schema."""
        req = UpdateConfigRequest(
            enabled=True,
            delay_minutes=30,
            priority=AutomationPriority.HIGH,
        )
        assert req.enabled is True
        assert req.delay_minutes == 30
    
    def test_automation_response(self):
        """Test AutomationResponse schema."""
        resp = AutomationResponse(
            success=True,
            event_id="evt123",
            message="Success",
        )
        assert resp.success is True
        assert resp.event_id == "evt123"
    
    def test_automation_response_error(self):
        """Test AutomationResponse with error."""
        resp = AutomationResponse(
            success=False,
            error="Rate limit exceeded",
        )
        assert resp.success is False
        assert resp.error is not None


# ==================== ENDPOINT TESTS ====================


class TestTriggerEndpoint:
    """Test trigger automation endpoint."""
    
    @pytest.mark.asyncio
    async def test_trigger_success(self, mock_orchestrator):
        """Test successful trigger."""
        with patch(
            'api.routes.automation_api.get_orchestrator',
            return_value=mock_orchestrator
        ):
            req = TriggerRequest(
                automation_type=AutomationType.NEW_USER_WELCOME,
                user_id="user123",
            )
            result = await trigger_automation(req)
            
            assert result.success is True
            assert result.event_id == "evt123"
            mock_orchestrator.trigger_automation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_trigger_failed(self, mock_orchestrator, mock_failed_result):
        """Test failed trigger."""
        mock_orchestrator.trigger_automation = AsyncMock(
            return_value=mock_failed_result
        )
        
        with patch(
            'api.routes.automation_api.get_orchestrator',
            return_value=mock_orchestrator
        ):
            req = TriggerRequest(
                automation_type=AutomationType.CART_ABANDONED,
                user_id="user123",
            )
            result = await trigger_automation(req)
            
            assert result.success is False
            assert result.error is not None


class TestOnboardingEndpoint:
    """Test onboarding endpoint."""
    
    @pytest.mark.asyncio
    async def test_onboarding_success(self, mock_orchestrator):
        """Test successful onboarding trigger."""
        with patch(
            'api.routes.automation_api.get_orchestrator',
            return_value=mock_orchestrator
        ):
            req = OnboardingRequest(
                user_id="user123",
                name="John Doe",
            )
            result = await trigger_onboarding(req)
            
            assert result.success is True
            mock_orchestrator.trigger_onboarding.assert_called_once()


class TestCartAbandonedEndpoint:
    """Test cart abandoned endpoint."""
    
    @pytest.mark.asyncio
    async def test_cart_abandoned_success(self, mock_orchestrator):
        """Test successful cart abandoned trigger."""
        with patch(
            'api.routes.automation_api.get_orchestrator',
            return_value=mock_orchestrator
        ):
            req = CartAbandonedRequest(
                user_id="user123",
                name="John",
                product_name="iPhone",
                product_url="https://example.com",
                price=4999.00,
            )
            result = await trigger_cart_abandoned(req)
            
            assert result.success is True
            mock_orchestrator.trigger_cart_abandoned.assert_called_once()


class TestPriceDropEndpoint:
    """Test price drop endpoint."""
    
    @pytest.mark.asyncio
    async def test_price_drop_success(self, mock_orchestrator):
        """Test successful price drop trigger."""
        with patch(
            'api.routes.automation_api.get_orchestrator',
            return_value=mock_orchestrator
        ):
            req = PriceDropRequest(
                user_id="user123",
                name="John",
                product_name="iPhone",
                product_url="https://example.com",
                old_price=5999.00,
                new_price=4999.00,
            )
            result = await trigger_price_drop(req)
            
            assert result.success is True
            mock_orchestrator.trigger_price_drop.assert_called_once()


class TestPostPurchaseEndpoint:
    """Test post purchase endpoint."""
    
    @pytest.mark.asyncio
    async def test_post_purchase_success(self, mock_orchestrator):
        """Test successful post purchase trigger."""
        with patch(
            'api.routes.automation_api.get_orchestrator',
            return_value=mock_orchestrator
        ):
            req = PostPurchaseRequest(
                user_id="user123",
                name="John",
                order_id="ORD-123",
                product_name="iPhone",
                total=4999.00,
            )
            result = await trigger_post_purchase(req)
            
            assert result.success is True
            mock_orchestrator.trigger_post_purchase.assert_called_once()


class TestLeadQualifiedEndpoint:
    """Test lead qualified endpoint."""
    
    @pytest.mark.asyncio
    async def test_lead_qualified_success(self, mock_orchestrator):
        """Test successful lead qualified trigger."""
        with patch(
            'api.routes.automation_api.get_orchestrator',
            return_value=mock_orchestrator
        ):
            req = LeadQualifiedRequest(
                user_id="user123",
                name="John",
                lead_score=90,
            )
            result = await trigger_lead_qualified(req)
            
            assert result.success is True
            mock_orchestrator.trigger_lead_qualified.assert_called_once()


class TestReengagementEndpoint:
    """Test reengagement endpoint."""
    
    @pytest.mark.asyncio
    async def test_reengagement_success(self, mock_orchestrator):
        """Test successful reengagement trigger."""
        with patch(
            'api.routes.automation_api.get_orchestrator',
            return_value=mock_orchestrator
        ):
            req = ReengagementRequest(
                user_id="user123",
                name="John",
                days_inactive=30,
            )
            result = await trigger_reengagement(req)
            
            assert result.success is True
            mock_orchestrator.trigger_reengagement.assert_called_once()


# ==================== ROUTER TESTS ====================


class TestRouter:
    """Test router configuration."""
    
    def test_router_exists(self):
        """Test that router is defined."""
        assert router is not None
    
    def test_router_prefix(self):
        """Test router has correct prefix."""
        assert router.prefix == "/automation"
    
    def test_router_tags(self):
        """Test router has correct tags."""
        assert "Seller Bot Automation" in router.tags
