"""
Extended tests for subscription.py
===================================
Tests for subscription routes to increase coverage.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# ==================== FIXTURES ====================


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {
        "id": "user123",
        "email": "test@example.com",
        "name": "Test User",
    }


@pytest.fixture
def mock_subscription():
    """Mock subscription object."""
    sub = MagicMock()
    sub.id = "sub123"
    sub.plan = MagicMock()
    sub.plan.value = "pro"
    sub.status = MagicMock()
    sub.status.value = "active"
    sub.billing_cycle = MagicMock()
    sub.billing_cycle.value = "monthly"
    sub.execution_mode = MagicMock()
    sub.execution_mode.value = "cloud"
    sub.current_period_start = datetime.now(timezone.utc)
    sub.current_period_end = datetime.now(timezone.utc) + timedelta(days=30)
    return sub


@pytest.fixture
def mock_service():
    """Mock subscription service."""
    service = MagicMock()
    service.list_plans = MagicMock(return_value=[])
    service.get_subscription = AsyncMock()
    service.get_usage_stats = AsyncMock(return_value=[])
    service.get_usage = AsyncMock(return_value=5)
    service.get_feature_limit = AsyncMock(return_value=100)
    service.can_use_feature = AsyncMock(return_value=True)
    service.upgrade_plan = AsyncMock()
    service.validate_subscription = AsyncMock()
    service.set_execution_mode = AsyncMock()
    return service


@pytest.fixture
def mock_plan_config():
    """Mock plan configuration."""
    config = MagicMock()
    config.tier = MagicMock()
    config.tier.value = "pro"
    config.name = "Pro"
    config.description = "Plano Pro"
    config.price_monthly = 49.90
    config.price_yearly = 499.00
    config.execution_modes = []
    config.marketplaces = []
    config.scraper_priority = MagicMock()
    config.scraper_priority.value = "high"
    config.limits = {"searches": 1000}
    config.features = {"ai": True}
    config.highlights = ["Feature 1"]
    config.offline_days = 7
    return config


# ==================== SCHEMA TESTS ====================


class TestSchemas:
    """Test Pydantic schemas."""
    
    def test_plan_info_v2_schema(self):
        """Test PlanInfoV2 schema."""
        from api.routes.subscription import PlanInfoV2
        
        plan = PlanInfoV2(
            tier="pro",
            name="Pro",
            description="Plano Pro",
            price_monthly=49.90,
            price_yearly=499.00,
            execution_modes=["cloud", "local"],
            marketplaces=["amazon", "mercadolivre"],
            scraper_priority="high",
            limits={"searches": 1000},
            features={"ai": True},
            highlights=["Feature 1"],
            offline_days=7,
        )
        assert plan.tier == "pro"
        assert plan.price_monthly == 49.90
    
    def test_subscription_response_schema(self):
        """Test SubscriptionResponse schema."""
        from api.routes.subscription import SubscriptionResponse
        
        now = datetime.now(timezone.utc)
        resp = SubscriptionResponse(
            id="sub123",
            plan="pro",
            status="active",
            billing_cycle="monthly",
            execution_mode="cloud",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            marketplaces=["amazon"],
            limits={"searches": 1000},
            features={"ai": True},
        )
        assert resp.plan == "pro"
        assert resp.status == "active"
    
    def test_create_subscription_request(self):
        """Test CreateSubscriptionRequest schema."""
        from api.routes.subscription import CreateSubscriptionRequest
        
        req = CreateSubscriptionRequest(
            plan_tier="pro",
            billing_cycle="yearly",
        )
        assert req.plan_tier == "pro"
        assert req.billing_cycle == "yearly"
    
    def test_create_subscription_request_default(self):
        """Test CreateSubscriptionRequest with default cycle."""
        from api.routes.subscription import CreateSubscriptionRequest
        
        req = CreateSubscriptionRequest(plan_tier="starter")
        assert req.billing_cycle == "monthly"
    
    def test_upgrade_request(self):
        """Test UpgradeRequest schema."""
        from api.routes.subscription import UpgradeRequest
        
        req = UpgradeRequest(plan="pro")
        assert req.plan == "pro"
        assert req.billing_cycle is None
    
    def test_set_execution_mode_request(self):
        """Test SetExecutionModeRequest schema."""
        from api.routes.subscription import SetExecutionModeRequest
        
        req = SetExecutionModeRequest(mode="local")
        assert req.mode == "local"
    
    def test_validate_subscription_request(self):
        """Test ValidateSubscriptionRequest schema."""
        from api.routes.subscription import ValidateSubscriptionRequest
        
        req = ValidateSubscriptionRequest(
            hwid="ABC123",
            app_version="1.0.0",
        )
        assert req.hwid == "ABC123"
        assert req.app_version == "1.0.0"
    
    def test_usage_stats_response(self):
        """Test UsageStatsResponse schema."""
        from api.routes.subscription import UsageStatsResponse
        
        now = datetime.now(timezone.utc)
        resp = UsageStatsResponse(
            feature="searches",
            current=50,
            limit=100,
            percentage=50.0,
            is_unlimited=False,
            resets_at=now,
        )
        assert resp.feature == "searches"
        assert resp.percentage == 50.0
    
    def test_checkout_response(self):
        """Test CheckoutResponse schema."""
        from api.routes.subscription import CheckoutResponse
        
        resp = CheckoutResponse(
            checkout_url="https://mercadopago.com/checkout/123",
            preference_id="pref123",
        )
        assert resp.preference_id == "pref123"


# ==================== PLANS ENDPOINT TESTS ====================


class TestPlansEndpoints:
    """Test plans endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_plans(self, mock_service):
        """Test list plans endpoint."""
        from api.routes.subscription import list_plans
        
        mock_service.list_plans.return_value = [
            {
                "tier": "free",
                "name": "Free",
                "description": "Plano grátis",
                "price_monthly": 0.0,
                "price_yearly": 0.0,
                "execution_modes": ["cloud"],
                "marketplaces": [],
                "scraper_priority": "low",
                "limits": {"searches": 10},
                "features": {},
                "highlights": [],
                "offline_days": 0,
            }
        ]
        
        result = await list_plans(mock_service)
        
        assert len(result) == 1
        assert result[0].tier == "free"
    
    @pytest.mark.asyncio
    async def test_get_plan_details_success(self, mock_service):
        """Test get plan details success."""
        from api.routes.subscription import get_plan_details
        from modules.subscription import PLANS_V2, PlanTier

        # Use a real tier that exists in PLANS_V2
        if PlanTier.FREE in PLANS_V2:
            result = await get_plan_details("free", mock_service)
            assert result.tier == "free"
    
    @pytest.mark.asyncio
    async def test_get_plan_details_invalid_tier(self, mock_service):
        """Test get plan details with invalid tier."""
        from api.routes.subscription import get_plan_details
        
        with pytest.raises(HTTPException) as exc:
            await get_plan_details("invalid_tier", mock_service)
        
        assert exc.value.status_code == 404


# ==================== USAGE ENDPOINT TESTS ====================


class TestUsageEndpoints:
    """Test usage endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_usage(self, mock_user, mock_service):
        """Test get usage endpoint."""
        from api.routes.subscription import get_usage
        
        mock_stat = MagicMock()
        mock_stat.feature = "searches"
        mock_stat.current = 50
        mock_stat.limit = 100
        mock_stat.percentage = 50.0
        mock_stat.is_unlimited = False
        mock_stat.resets_at = datetime.now(timezone.utc)
        
        mock_service.get_usage_stats.return_value = [mock_stat]
        
        result = await get_usage(mock_user, mock_service)
        
        assert len(result) == 1
        assert result[0].feature == "searches"
    
    @pytest.mark.asyncio
    async def test_get_feature_usage(self, mock_user, mock_service):
        """Test get feature usage endpoint."""
        from api.routes.subscription import get_feature_usage
        
        mock_service.get_usage.return_value = 50
        mock_service.get_feature_limit.return_value = 100
        
        result = await get_feature_usage("searches", mock_user, mock_service)
        
        assert result["feature"] == "searches"
        assert result["current"] == 50
        assert result["limit"] == 100
        assert result["percentage"] == 50.0
        assert result["can_use"] is True
    
    @pytest.mark.asyncio
    async def test_get_feature_usage_unlimited(self, mock_user, mock_service):
        """Test get feature usage with unlimited limit."""
        from api.routes.subscription import get_feature_usage
        
        mock_service.get_usage.return_value = 500
        mock_service.get_feature_limit.return_value = -1  # Unlimited
        
        result = await get_feature_usage("searches", mock_user, mock_service)
        
        assert result["is_unlimited"] is True
        assert result["percentage"] == 0.0
        assert result["can_use"] is True
    
    @pytest.mark.asyncio
    async def test_get_feature_usage_zero_limit(self, mock_user, mock_service):
        """Test get feature usage with zero limit."""
        from api.routes.subscription import get_feature_usage
        
        mock_service.get_usage.return_value = 5
        mock_service.get_feature_limit.return_value = 0
        
        result = await get_feature_usage("ai_requests", mock_user, mock_service)
        
        assert result["percentage"] == 100.0
        assert result["can_use"] is False
    
    @pytest.mark.asyncio
    async def test_get_feature_usage_no_usage(self, mock_user, mock_service):
        """Test get feature usage with no current usage."""
        from api.routes.subscription import get_feature_usage
        
        mock_service.get_usage.return_value = 0
        mock_service.get_feature_limit.return_value = 0
        
        result = await get_feature_usage("ai_requests", mock_user, mock_service)
        
        assert result["percentage"] == 0.0
    
    @pytest.mark.asyncio
    async def test_check_feature_access(self, mock_user, mock_service):
        """Test check feature access endpoint."""
        from api.routes.subscription import check_feature_access
        
        mock_service.can_use_feature.return_value = True
        
        result = await check_feature_access("ai_generation", mock_user, mock_service)
        
        assert result["feature"] == "ai_generation"
        assert result["can_use"] is True


# ==================== CREATE/UPGRADE ENDPOINT TESTS ====================


class TestCreateUpgradeEndpoints:
    """Test create and upgrade endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_subscription_invalid_plan(self, mock_user, mock_service):
        """Test create subscription with invalid plan."""
        from api.routes.subscription import (CreateSubscriptionRequest,
                                             create_subscription)
        
        req = CreateSubscriptionRequest(plan_tier="invalid")
        
        with pytest.raises(HTTPException) as exc:
            await create_subscription(req, mock_user, mock_service)
        
        assert exc.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_create_subscription_free_plan(self, mock_user, mock_service):
        """Test create subscription with free plan."""
        from api.routes.subscription import (CreateSubscriptionRequest,
                                             create_subscription)
        
        req = CreateSubscriptionRequest(plan_tier="free")
        
        with pytest.raises(HTTPException) as exc:
            await create_subscription(req, mock_user, mock_service)
        
        assert exc.value.status_code == 400
        assert "FREE" in exc.value.detail
    
    @pytest.mark.asyncio
    async def test_create_subscription_enterprise_plan(
        self, mock_user, mock_service
    ):
        """Test create subscription with enterprise plan."""
        from api.routes.subscription import (CreateSubscriptionRequest,
                                             create_subscription)
        
        req = CreateSubscriptionRequest(plan_tier="enterprise")
        
        with pytest.raises(HTTPException) as exc:
            await create_subscription(req, mock_user, mock_service)
        
        assert exc.value.status_code == 400
        assert "Enterprise" in exc.value.detail
    
    @pytest.mark.asyncio
    async def test_create_subscription_fallback(self, mock_user, mock_service):
        """Test create subscription with MP failure (fallback)."""
        from api.routes.subscription import (CreateSubscriptionRequest,
                                             create_subscription)
        
        req = CreateSubscriptionRequest(
            plan_tier="starter", billing_cycle="monthly"
        )
        
        # Mock the subscription result
        mock_sub = MagicMock()
        mock_sub.plan = MagicMock()
        mock_sub.plan.value = "starter"
        mock_sub.status = MagicMock()
        mock_sub.status.value = "active"
        mock_sub.current_period_end = datetime.now(timezone.utc)
        mock_service.upgrade_plan.return_value = mock_sub
        
        with patch('api.routes.subscription.MercadoPagoService') as mock_mp:
            mock_mp_instance = MagicMock()
            mock_mp_instance.create_subscription_preference = AsyncMock(
                side_effect=Exception("MP Error")
            )
            mock_mp.return_value = mock_mp_instance
            
            result = await create_subscription(req, mock_user, mock_service)
            
            assert result["status"] == "success"
            assert result["subscription"]["plan"] == "starter"


# ==================== GET SUBSCRIPTION TESTS ====================


class TestGetSubscription:
    """Test get subscription endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_my_subscription(
        self, mock_subscription, mock_service, mock_plan_config
    ):
        """Test get my subscription endpoint."""
        from api.routes.subscription import get_my_subscription
        
        with patch(
            'api.routes.subscription.PLANS_V2',
            {mock_subscription.plan: mock_plan_config}
        ):
            result = await get_my_subscription(mock_subscription, mock_service)
            
            assert result.id == "sub123"
            assert result.plan == "pro"


# ==================== SUBSCRIPTION WITH USAGE TESTS ====================


class TestSubscriptionWithUsage:
    """Test subscription with usage endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_current_subscription_full(
        self, mock_user, mock_subscription, mock_service, mock_plan_config
    ):
        """Test get current subscription full endpoint."""
        from api.routes.subscription import get_current_subscription_full
        
        mock_service.get_subscription.return_value = mock_subscription
        mock_service.get_usage_stats.return_value = []
        
        with patch(
            'api.routes.subscription.PLANS_V2',
            {mock_subscription.plan: mock_plan_config}
        ):
            result = await get_current_subscription_full(
                mock_user, mock_service
            )
            
            assert result.subscription.id == "sub123"
            assert result.plan.tier == "pro"
