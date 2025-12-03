"""
Comprehensive tests for Subscription Middleware
Target: api/middleware/subscription.py (currently 40% coverage)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class TestRequiresPlan:
    """Tests for RequiresPlan dependency"""

    @pytest.mark.asyncio
    @patch('api.middleware.subscription.get_current_user')
    async def test_requires_plan_free_success(self, mock_get_user):
        """Test free plan access succeeds"""
        from api.middleware.subscription import RequiresPlan
        from modules.subscription import PlanTier, SubscriptionV2
        
        mock_user = {"id": "user123"}
        mock_subscription = MagicMock(spec=SubscriptionV2)
        mock_subscription.plan = PlanTier.FREE
        
        with patch.object(RequiresPlan, 'service') as mock_service:
            mock_service.get_subscription = AsyncMock(return_value=mock_subscription)
            
            requires = RequiresPlan(PlanTier.FREE)
            result = await requires(current_user=mock_user)
            
            assert result == mock_subscription

    @pytest.mark.asyncio
    @patch('api.middleware.subscription.get_current_user')
    async def test_requires_plan_starter_success(self, mock_get_user):
        """Test starter plan access succeeds for starter user"""
        from api.middleware.subscription import RequiresPlan
        from modules.subscription import PlanTier, SubscriptionV2
        
        mock_user = {"id": "user123"}
        mock_subscription = MagicMock(spec=SubscriptionV2)
        mock_subscription.plan = PlanTier.STARTER
        
        with patch.object(RequiresPlan, 'service') as mock_service:
            mock_service.get_subscription = AsyncMock(return_value=mock_subscription)
            
            requires = RequiresPlan(PlanTier.STARTER)
            result = await requires(current_user=mock_user)
            
            assert result == mock_subscription

    @pytest.mark.asyncio
    @patch('api.middleware.subscription.get_current_user')
    async def test_requires_plan_higher_tier_access(self, mock_get_user):
        """Test business plan can access starter features"""
        from api.middleware.subscription import RequiresPlan
        from modules.subscription import PlanTier, SubscriptionV2
        
        mock_user = {"id": "user123"}
        mock_subscription = MagicMock(spec=SubscriptionV2)
        mock_subscription.plan = PlanTier.BUSINESS
        
        with patch.object(RequiresPlan, 'service') as mock_service:
            mock_service.get_subscription = AsyncMock(return_value=mock_subscription)
            
            requires = RequiresPlan(PlanTier.STARTER)
            result = await requires(current_user=mock_user)
            
            assert result == mock_subscription

    @pytest.mark.asyncio
    @patch('api.middleware.subscription.get_current_user')
    async def test_requires_plan_denied(self, mock_get_user):
        """Test plan access denied for lower tier"""
        from api.middleware.subscription import RequiresPlan
        from modules.subscription import PlanTier, SubscriptionV2
        
        mock_user = {"id": "user123"}
        mock_subscription = MagicMock(spec=SubscriptionV2)
        mock_subscription.plan = PlanTier.FREE
        
        with patch.object(RequiresPlan, 'service') as mock_service:
            mock_service.get_subscription = AsyncMock(return_value=mock_subscription)
            
            requires = RequiresPlan(PlanTier.BUSINESS)
            
            with pytest.raises(HTTPException) as exc_info:
                await requires(current_user=mock_user)
            
            assert exc_info.value.status_code == 402
            assert "plan_required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch('api.middleware.subscription.get_current_user')
    async def test_requires_plan_enterprise(self, mock_get_user):
        """Test enterprise plan requirement"""
        from api.middleware.subscription import RequiresPlan
        from modules.subscription import PlanTier, SubscriptionV2
        
        mock_user = {"id": "user123"}
        mock_subscription = MagicMock(spec=SubscriptionV2)
        mock_subscription.plan = PlanTier.ENTERPRISE
        
        with patch.object(RequiresPlan, 'service') as mock_service:
            mock_service.get_subscription = AsyncMock(return_value=mock_subscription)
            
            requires = RequiresPlan(PlanTier.ENTERPRISE)
            result = await requires(current_user=mock_user)
            
            assert result == mock_subscription


class TestRequiresMarketplace:
    """Tests for RequiresMarketplace dependency"""

    @pytest.mark.asyncio
    @patch('api.middleware.subscription.get_current_user')
    async def test_requires_marketplace_success(self, mock_get_user):
        """Test marketplace access succeeds"""
        from api.middleware.subscription import RequiresMarketplace
        from modules.subscription import MarketplaceAccess
        
        mock_user = {"id": "user123"}
        mock_request = MagicMock()
        mock_request.path_params = {"marketplace": "shopee"}
        mock_request.query_params = {}
        
        with patch.object(RequiresMarketplace, 'service') as mock_service:
            mock_service.has_marketplace_access = AsyncMock(return_value=True)
            
            requires = RequiresMarketplace("marketplace")
            result = await requires(request=mock_request, current_user=mock_user)
            
            assert result is True

    @pytest.mark.asyncio
    @patch('api.middleware.subscription.get_current_user')
    async def test_requires_marketplace_enum_success(self, mock_get_user):
        """Test marketplace access with enum"""
        from api.middleware.subscription import RequiresMarketplace
        from modules.subscription import MarketplaceAccess
        
        mock_user = {"id": "user123"}
        mock_request = MagicMock()
        
        with patch.object(RequiresMarketplace, 'service') as mock_service:
            mock_service.has_marketplace_access = AsyncMock(return_value=True)
            
            requires = RequiresMarketplace(MarketplaceAccess.SHOPEE, from_param=False)
            result = await requires(request=mock_request, current_user=mock_user)
            
            assert result is True

    @pytest.mark.asyncio
    @patch('api.middleware.subscription.get_current_user')
    async def test_requires_marketplace_denied(self, mock_get_user):
        """Test marketplace access denied"""
        from api.middleware.subscription import RequiresMarketplace
        from modules.subscription import (MarketplaceAccess, PlanTier,
                                          SubscriptionV2)
        
        mock_user = {"id": "user123"}
        mock_request = MagicMock()
        mock_request.path_params = {"marketplace": "shopee"}
        mock_request.query_params = {}
        
        mock_subscription = MagicMock(spec=SubscriptionV2)
        mock_subscription.plan = PlanTier.FREE
        
        with patch.object(RequiresMarketplace, 'service') as mock_service:
            mock_service.has_marketplace_access = AsyncMock(return_value=False)
            mock_service.get_subscription = AsyncMock(return_value=mock_subscription)
            mock_service.get_accessible_marketplaces = AsyncMock(return_value=[])
            
            requires = RequiresMarketplace("marketplace")
            
            with pytest.raises(HTTPException) as exc_info:
                await requires(request=mock_request, current_user=mock_user)
            
            assert exc_info.value.status_code == 402

    @pytest.mark.asyncio
    @patch('api.middleware.subscription.get_current_user')
    async def test_requires_marketplace_invalid(self, mock_get_user):
        """Test invalid marketplace raises error"""
        from api.middleware.subscription import RequiresMarketplace
        
        mock_user = {"id": "user123"}
        mock_request = MagicMock()
        mock_request.path_params = {"marketplace": "invalid_marketplace"}
        mock_request.query_params = {}
        
        requires = RequiresMarketplace("marketplace")
        
        with pytest.raises(HTTPException) as exc_info:
            await requires(request=mock_request, current_user=mock_user)
        
        assert exc_info.value.status_code == 400
        assert "invalid_marketplace" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch('api.middleware.subscription.get_current_user')
    async def test_requires_marketplace_from_query(self, mock_get_user):
        """Test marketplace from query params"""
        from api.middleware.subscription import RequiresMarketplace
        from modules.subscription import MarketplaceAccess
        
        mock_user = {"id": "user123"}
        mock_request = MagicMock()
        mock_request.path_params = {}
        mock_request.query_params = {"marketplace": "shopee"}
        
        with patch.object(RequiresMarketplace, 'service') as mock_service:
            mock_service.has_marketplace_access = AsyncMock(return_value=True)
            
            requires = RequiresMarketplace("marketplace")
            result = await requires(request=mock_request, current_user=mock_user)
            
            assert result is True


class TestRequiresFeature:
    """Tests for RequiresFeature dependency"""

    @pytest.mark.asyncio
    @patch('api.middleware.subscription.get_current_user')
    async def test_requires_feature_success(self, mock_get_user):
        """Test feature access succeeds"""
        from api.middleware.subscription import RequiresFeature
        
        mock_user = {"id": "user123"}
        
        with patch.object(RequiresFeature, 'service') as mock_service:
            mock_service.can_use_feature = AsyncMock(return_value=True)
            
            requires = RequiresFeature("ai_copies")
            result = await requires(current_user=mock_user)
            
            assert result is True

    @pytest.mark.asyncio
    @patch('api.middleware.subscription.get_current_user')
    async def test_requires_feature_denied(self, mock_get_user):
        """Test feature access denied"""
        from api.middleware.subscription import RequiresFeature
        from modules.subscription import PlanTier, SubscriptionV2
        
        mock_user = {"id": "user123"}
        
        mock_subscription = MagicMock(spec=SubscriptionV2)
        mock_subscription.plan = PlanTier.FREE
        
        mock_service = AsyncMock()
        mock_service.can_use_feature = AsyncMock(return_value=False)
        mock_service.get_subscription = AsyncMock(return_value=mock_subscription)
        mock_service.get_usage = AsyncMock(return_value=100)
        
        requires = RequiresFeature("premium_feature")
        requires._service = mock_service
        
        with pytest.raises(HTTPException) as exc_info:
            await requires(current_user=mock_user)
        
        assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    @patch('api.middleware.subscription.get_current_user')
    async def test_requires_feature_with_usage_limit(self, mock_get_user):
        """Test feature with usage limit"""
        from api.middleware.subscription import RequiresFeature
        
        mock_user = {"id": "user123"}
        
        with patch.object(RequiresFeature, 'service') as mock_service:
            mock_service.can_use_feature = AsyncMock(return_value=True)
            
            requires = RequiresFeature("price_searches")
            result = await requires(current_user=mock_user)
            
            assert result is True


class TestRequiresExecutionMode:
    """Tests for RequiresExecutionMode dependency"""

    @pytest.mark.asyncio
    @patch('api.middleware.subscription.get_current_user')
    async def test_requires_hybrid_mode_success(self, mock_get_user):
        """Test hybrid execution mode access"""
        from api.middleware.subscription import RequiresExecutionMode
        from modules.subscription import (ExecutionMode, PlanTier,
                                          SubscriptionV2)
        
        mock_user = {"id": "user123"}
        mock_subscription = MagicMock(spec=SubscriptionV2)
        mock_subscription.plan = PlanTier.BUSINESS
        
        mock_service = AsyncMock()
        mock_service.can_use_execution_mode = AsyncMock(return_value=True)
        mock_service.get_subscription = AsyncMock(return_value=mock_subscription)
        
        requires = RequiresExecutionMode(ExecutionMode.HYBRID)
        requires._service = mock_service
        result = await requires(current_user=mock_user)
        
        assert result is True

    @pytest.mark.asyncio
    @patch('api.middleware.subscription.get_current_user')
    async def test_requires_web_only_mode(self, mock_get_user):
        """Test web only execution mode"""
        from api.middleware.subscription import RequiresExecutionMode
        from modules.subscription import (ExecutionMode, PlanTier,
                                          SubscriptionV2)
        
        mock_user = {"id": "user123"}
        mock_subscription = MagicMock(spec=SubscriptionV2)
        mock_subscription.plan = PlanTier.FREE
        
        mock_service = AsyncMock()
        mock_service.can_use_execution_mode = AsyncMock(return_value=True)
        mock_service.get_subscription = AsyncMock(return_value=mock_subscription)
        
        requires = RequiresExecutionMode(ExecutionMode.WEB_ONLY)
        requires._service = mock_service
        result = await requires(current_user=mock_user)
        
        assert result is True

    @pytest.mark.asyncio
    @patch('api.middleware.subscription.get_current_user')
    async def test_requires_execution_mode_denied(self, mock_get_user):
        """Test execution mode denied"""
        from api.middleware.subscription import RequiresExecutionMode
        from modules.subscription import (ExecutionMode, PlanTier,
                                          SubscriptionV2)
        
        mock_user = {"id": "user123"}
        mock_subscription = MagicMock(spec=SubscriptionV2)
        mock_subscription.plan = PlanTier.FREE
        
        mock_service = AsyncMock()
        mock_service.can_use_execution_mode = AsyncMock(return_value=False)
        mock_service.get_subscription = AsyncMock(return_value=mock_subscription)
        
        requires = RequiresExecutionMode(ExecutionMode.HYBRID)
        requires._service = mock_service
        
        with pytest.raises(HTTPException) as exc_info:
            await requires(current_user=mock_user)
        
        assert exc_info.value.status_code == 402


class TestDecoratorHelpers:
    """Tests for decorator functions"""

    def test_requires_plan_decorator_exists(self):
        """Test requires_plan decorator exists"""
        from api.middleware.subscription import requires_plan
        
        assert callable(requires_plan)

    def test_requires_feature_decorator_exists(self):
        """Test requires_feature decorator exists"""
        from api.middleware.subscription import requires_feature
        
        assert callable(requires_feature)

    def test_requires_marketplace_decorator_exists(self):
        """Test requires_marketplace decorator exists"""
        from api.middleware.subscription import requires_marketplace
        
        assert callable(requires_marketplace)


class TestPlanOrder:
    """Tests for plan order comparison"""

    def test_plan_order_free_lowest(self):
        """Test FREE is lowest plan"""
        from api.middleware.subscription import RequiresPlan
        from modules.subscription import PlanTier
        
        order = RequiresPlan.PLAN_ORDER
        assert order[0] == PlanTier.FREE

    def test_plan_order_enterprise_highest(self):
        """Test ENTERPRISE is highest plan"""
        from api.middleware.subscription import RequiresPlan
        from modules.subscription import PlanTier
        
        order = RequiresPlan.PLAN_ORDER
        assert order[-1] == PlanTier.ENTERPRISE

    def test_plan_order_progression(self):
        """Test plan order progression"""
        from api.middleware.subscription import RequiresPlan
        from modules.subscription import PlanTier
        
        order = RequiresPlan.PLAN_ORDER
        
        assert order.index(PlanTier.FREE) < order.index(PlanTier.STARTER)
        assert order.index(PlanTier.STARTER) < order.index(PlanTier.BUSINESS)
        assert order.index(PlanTier.BUSINESS) < order.index(PlanTier.ENTERPRISE)
