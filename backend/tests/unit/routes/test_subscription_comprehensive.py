"""
Comprehensive Tests for Subscription Routes
============================================
Tests for all subscription management endpoints.
"""

# Mock modules before import
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

sys.modules.setdefault("mercadopago", MagicMock())


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {
        "id": str(uuid4()),
        "email": "test@example.com",
        "name": "Test User"
    }


@pytest.fixture
def mock_service():
    """Mock SubscriptionService."""
    service = MagicMock()
    service.list_plans = MagicMock(return_value=[
        {
            "tier": "free",
            "name": "Free",
            "description": "Plano gratuito",
            "price_monthly": 0.0,
            "price_yearly": 0.0,
            "execution_modes": ["web_only"],
            "marketplaces": ["shopee"],
            "scraper_priority": "low",
            "limits": {"products": 10},
            "features": {"dashboard": True},
            "highlights": ["Acesso básico"],
            "offline_days": 0
        },
        {
            "tier": "starter",
            "name": "Starter",
            "description": "Para iniciantes",
            "price_monthly": 29.90,
            "price_yearly": 299.00,
            "execution_modes": ["web_only", "hybrid"],
            "marketplaces": ["shopee", "mercadolivre"],
            "scraper_priority": "normal",
            "limits": {"products": 100},
            "features": {"dashboard": True, "analytics": True},
            "highlights": ["Suporte básico"],
            "offline_days": 7
        }
    ])
    service.get_subscription = AsyncMock()
    service.get_usage_stats = AsyncMock(return_value=[])
    service.get_usage = AsyncMock(return_value=5)
    service.get_feature_limit = AsyncMock(return_value=100)
    service.can_use_feature = AsyncMock(return_value=True)
    service.upgrade_plan = AsyncMock()
    service.downgrade_plan = AsyncMock()
    service.cancel_subscription = AsyncMock()
    service.set_execution_mode = AsyncMock()
    service.validate_offline_access = AsyncMock(return_value=True)
    return service


# ============================================
# PLANS ENDPOINT TESTS
# ============================================

class TestListPlans:
    """Tests for GET /plans endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_plans_returns_all_plans(self, mock_service):
        """Should return all available plans."""
        from api.routes.subscription import list_plans
        
        result = await list_plans(service=mock_service)
        
        assert len(result) == 2
        assert result[0].tier == "free"
        assert result[1].tier == "starter"
    
    @pytest.mark.asyncio
    async def test_list_plans_includes_required_fields(self, mock_service):
        """Should include all required plan fields."""
        from api.routes.subscription import list_plans
        
        result = await list_plans(service=mock_service)
        
        plan = result[0]
        assert hasattr(plan, 'tier')
        assert hasattr(plan, 'name')
        assert hasattr(plan, 'price_monthly')
        assert hasattr(plan, 'execution_modes')
        assert hasattr(plan, 'marketplaces')
        assert hasattr(plan, 'limits')
        assert hasattr(plan, 'features')


class TestGetPlanDetails:
    """Tests for GET /plans/{plan_tier} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_plan_details_invalid_tier(self, mock_service):
        """Should raise 404 for invalid tier."""
        from api.routes.subscription import get_plan_details
        
        with pytest.raises(HTTPException) as exc_info:
            await get_plan_details("invalid_tier", service=mock_service)
        
        assert exc_info.value.status_code == 404
        assert "não encontrado" in exc_info.value.detail


# ============================================
# USAGE ENDPOINTS TESTS
# ============================================

class TestGetFeatureUsage:
    """Tests for GET /usage/{feature} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_feature_usage_normal(self, mock_user, mock_service):
        """Should return usage for specific feature."""
        from api.routes.subscription import get_feature_usage
        
        mock_service.get_usage.return_value = 50
        mock_service.get_feature_limit.return_value = 100
        
        result = await get_feature_usage(
            feature="products",
            current_user=mock_user,
            service=mock_service
        )
        
        assert result["feature"] == "products"
        assert result["current"] == 50
        assert result["limit"] == 100
        assert result["percentage"] == 50.0
        assert result["can_use"] is True
    
    @pytest.mark.asyncio
    async def test_get_feature_usage_unlimited(self, mock_user, mock_service):
        """Should handle unlimited features."""
        from api.routes.subscription import get_feature_usage
        
        mock_service.get_usage.return_value = 1000
        mock_service.get_feature_limit.return_value = -1
        
        result = await get_feature_usage(
            feature="scrapes",
            current_user=mock_user,
            service=mock_service
        )
        
        assert result["is_unlimited"] is True
        assert result["percentage"] == 0.0
        assert result["can_use"] is True
    
    @pytest.mark.asyncio
    async def test_get_feature_usage_limit_reached(self, mock_user, mock_service):
        """Should detect when limit is reached."""
        from api.routes.subscription import get_feature_usage
        
        mock_service.get_usage.return_value = 100
        mock_service.get_feature_limit.return_value = 100
        
        result = await get_feature_usage(
            feature="products",
            current_user=mock_user,
            service=mock_service
        )
        
        assert result["percentage"] == 100.0
        assert result["can_use"] is False
    
    @pytest.mark.asyncio
    async def test_get_feature_usage_zero_limit(self, mock_user, mock_service):
        """Should handle zero limit (feature disabled)."""
        from api.routes.subscription import get_feature_usage
        
        mock_service.get_usage.return_value = 5
        mock_service.get_feature_limit.return_value = 0
        
        result = await get_feature_usage(
            feature="disabled_feature",
            current_user=mock_user,
            service=mock_service
        )
        
        assert result["percentage"] == 100.0


class TestCheckFeatureAccess:
    """Tests for POST /check-feature endpoint."""
    
    @pytest.mark.asyncio
    async def test_check_feature_allowed(self, mock_user, mock_service):
        """Should return true when feature is allowed."""
        from api.routes.subscription import check_feature_access
        
        mock_service.can_use_feature.return_value = True
        
        result = await check_feature_access(
            feature="analytics",
            current_user=mock_user,
            service=mock_service
        )
        
        assert result["feature"] == "analytics"
        assert result["can_use"] is True
    
    @pytest.mark.asyncio
    async def test_check_feature_denied(self, mock_user, mock_service):
        """Should return false when feature is denied."""
        from api.routes.subscription import check_feature_access
        
        mock_service.can_use_feature.return_value = False
        
        result = await check_feature_access(
            feature="premium_feature",
            current_user=mock_user,
            service=mock_service
        )
        
        assert result["can_use"] is False


# ============================================
# CREATE/UPGRADE ENDPOINTS TESTS
# ============================================

class TestCreateSubscription:
    """Tests for POST /create endpoint."""
    
    @pytest.mark.asyncio
    async def test_create_subscription_free_plan_rejected(self, mock_user, mock_service):
        """Should reject free plan subscription."""
        from api.routes.subscription import (CreateSubscriptionRequest,
                                             create_subscription)
        
        data = CreateSubscriptionRequest(plan_tier="free", billing_cycle="monthly")
        
        with pytest.raises(HTTPException) as exc_info:
            await create_subscription(
                data=data,
                current_user=mock_user,
                service=mock_service
            )
        
        assert exc_info.value.status_code == 400
        assert "FREE" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_create_subscription_enterprise_redirects_to_contact(self, mock_user, mock_service):
        """Should redirect enterprise to sales contact."""
        from api.routes.subscription import (CreateSubscriptionRequest,
                                             create_subscription)
        
        data = CreateSubscriptionRequest(plan_tier="enterprise", billing_cycle="monthly")
        
        with pytest.raises(HTTPException) as exc_info:
            await create_subscription(
                data=data,
                current_user=mock_user,
                service=mock_service
            )
        
        assert exc_info.value.status_code == 400
        assert "contato" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_create_subscription_invalid_plan(self, mock_user, mock_service):
        """Should reject invalid plan tier."""
        from api.routes.subscription import (CreateSubscriptionRequest,
                                             create_subscription)
        
        data = CreateSubscriptionRequest(plan_tier="invalid", billing_cycle="monthly")
        
        with pytest.raises(HTTPException) as exc_info:
            await create_subscription(
                data=data,
                current_user=mock_user,
                service=mock_service
            )
        
        assert exc_info.value.status_code == 400


class TestUpgradeSubscription:
    """Tests for POST /upgrade endpoint."""
    
    @pytest.mark.asyncio
    async def test_upgrade_invalid_plan(self, mock_user, mock_service):
        """Should reject invalid plan for upgrade."""
        from api.routes.subscription import (UpgradeRequest,
                                             upgrade_subscription)
        
        data = UpgradeRequest(plan="invalid_plan")
        
        with pytest.raises(HTTPException) as exc_info:
            await upgrade_subscription(
                data=data,
                current_user=mock_user,
                service=mock_service
            )
        
        assert exc_info.value.status_code == 400


class TestDowngradeSubscription:
    """Tests for POST /downgrade endpoint."""
    
    @pytest.mark.asyncio
    async def test_downgrade_invalid_plan(self, mock_user, mock_service):
        """Should reject invalid plan for downgrade."""
        from api.routes.subscription import (UpgradeRequest,
                                             downgrade_subscription)
        
        data = UpgradeRequest(plan="invalid_plan")
        
        with pytest.raises(HTTPException) as exc_info:
            await downgrade_subscription(
                data=data,
                current_user=mock_user,
                service=mock_service
            )
        
        assert exc_info.value.status_code == 400


# ============================================
# CHECKOUT RESPONSE TESTS
# ============================================

class TestCheckoutResponse:
    """Tests for checkout response schema."""
    
    def test_checkout_response_schema(self):
        """Should validate checkout response fields."""
        from api.routes.subscription import CheckoutResponse
        
        response = CheckoutResponse(
            checkout_url="https://mercadopago.com.br/checkout/123",
            preference_id="pref_12345"
        )
        
        assert response.checkout_url.startswith("https://")
        assert response.preference_id == "pref_12345"


# ============================================
# EDGE CASES TESTS
# ============================================

class TestEdgeCases:
    """Edge case tests for subscription routes."""
    
    @pytest.mark.asyncio
    async def test_usage_over_limit(self, mock_user, mock_service):
        """Should handle usage over limit correctly."""
        from api.routes.subscription import get_feature_usage
        
        mock_service.get_usage.return_value = 150
        mock_service.get_feature_limit.return_value = 100
        
        result = await get_feature_usage(
            feature="products",
            current_user=mock_user,
            service=mock_service
        )
        
        # Percentage should be capped at 100 in display
        assert result["percentage"] == 100.0
        assert result["can_use"] is False
    
    @pytest.mark.asyncio
    async def test_list_plans_empty(self, mock_service):
        """Should handle empty plan list."""
        from api.routes.subscription import list_plans
        
        mock_service.list_plans.return_value = []
        
        result = await list_plans(service=mock_service)
        
        assert len(result) == 0
    
    def test_plan_tier_enum_values(self):
        """Should verify plan tier enum values."""
        from modules.subscription import PlanTier
        
        assert PlanTier.FREE.value == "free"
        assert PlanTier.STARTER.value == "starter"
        assert PlanTier.BUSINESS.value == "business"
        assert PlanTier.ENTERPRISE.value == "enterprise"
    
    def test_billing_cycle_enum_values(self):
        """Should verify billing cycle enum values."""
        from modules.subscription import BillingCycle
        
        assert BillingCycle.MONTHLY.value == "monthly"
        assert BillingCycle.YEARLY.value == "yearly"
    
    def test_execution_mode_enum_values(self):
        """Should verify execution mode enum values."""
        from modules.subscription import ExecutionMode
        
        assert ExecutionMode.WEB_ONLY.value == "web_only"
        assert ExecutionMode.HYBRID.value == "hybrid"
        assert ExecutionMode.LOCAL_FIRST.value == "local_first"


# ============================================
# VALIDATION TESTS
# ============================================

class TestValidationRequest:
    """Tests for validation schemas."""
    
    def test_validate_subscription_request(self):
        """Should validate subscription request."""
        from api.routes.subscription import ValidateSubscriptionRequest
        
        request = ValidateSubscriptionRequest(
            hwid="test-hardware-id",
            app_version="1.0.0"
        )
        
        assert request.hwid == "test-hardware-id"
        assert request.app_version == "1.0.0"
    
    def test_set_execution_mode_request(self):
        """Should validate execution mode request."""
        from api.routes.subscription import SetExecutionModeRequest
        
        request = SetExecutionModeRequest(mode="hybrid")
        
        assert request.mode == "hybrid"


class TestSubscriptionResponseModels:
    """Tests for subscription response models."""
    
    def test_plan_info_v2(self):
        """Should create PlanInfoV2 correctly."""
        from api.routes.subscription import PlanInfoV2
        
        plan = PlanInfoV2(
            tier="starter",
            name="Starter",
            description="For starters",
            price_monthly=29.90,
            price_yearly=299.00,
            execution_modes=["web_only"],
            marketplaces=["shopee"],
            scraper_priority="normal",
            limits={"products": 100},
            features={"analytics": True},
            highlights=["Basic support"],
            offline_days=7
        )
        
        assert plan.tier == "starter"
        assert plan.price_monthly == 29.90
    
    def test_usage_stats_response(self):
        """Should create UsageStatsResponse correctly."""
        from api.routes.subscription import UsageStatsResponse
        
        stats = UsageStatsResponse(
            feature="products",
            current=50,
            limit=100,
            percentage=50.0,
            is_unlimited=False,
            resets_at=datetime.now(timezone.utc)
        )
        
        assert stats.feature == "products"
        assert stats.percentage == 50.0
