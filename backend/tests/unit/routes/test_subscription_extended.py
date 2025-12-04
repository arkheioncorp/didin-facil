"""
Testes extensivos para api/routes/subscription.py
Foco nas linhas não cobertas: 46-47, 171, 400, 411, 456-517, 544-560, 579-582, 602-618, 632-637, 658-670, 702-768
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# ==================== TESTES DE SCHEMAS ====================

class TestSubscriptionSchemas:
    """Testes para schemas de subscription."""
    
    def test_plan_info_v2_schema(self):
        """Test PlanInfoV2 schema."""
        from api.routes.subscription import PlanInfoV2
        
        plan = PlanInfoV2(
            tier="business",
            name="Business",
            description="Plano business",
            price_monthly=99.90,
            price_yearly=999.00,
            execution_modes=["cloud", "local"],
            marketplaces=["tiktok", "mercadolibre"],
            scraper_priority="high",
            limits={"products": 1000},
            features={"analytics": True},
            highlights=["Suporte prioritário"],
            offline_days=7
        )
        
        assert plan.tier == "business"
        assert plan.price_monthly == 99.90
    
    def test_subscription_response_schema(self):
        """Test SubscriptionResponse schema."""
        from api.routes.subscription import SubscriptionResponse
        
        response = SubscriptionResponse(
            id="sub123",
            plan="starter",
            status="active",
            billing_cycle="monthly",
            execution_mode="cloud",
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
            marketplaces=["tiktok"],
            limits={"products": 100},
            features={"basic": True}
        )
        
        assert response.id == "sub123"
        assert response.plan == "starter"
    
    def test_usage_stats_response_schema(self):
        """Test UsageStatsResponse schema."""
        from api.routes.subscription import UsageStatsResponse
        
        stats = UsageStatsResponse(
            feature="price_searches",
            current=50,
            limit=100,
            percentage=50.0,
            is_unlimited=False,
            resets_at=datetime.now(timezone.utc)
        )
        
        assert stats.current == 50
        assert stats.percentage == 50.0
    
    def test_create_subscription_request(self):
        """Test CreateSubscriptionRequest schema."""
        from api.routes.subscription import CreateSubscriptionRequest
        
        request = CreateSubscriptionRequest(
            plan_tier="starter",
            billing_cycle="monthly"
        )
        
        assert request.plan_tier == "starter"
        assert request.billing_cycle == "monthly"
    
    def test_upgrade_request_schema(self):
        """Test UpgradeRequest schema."""
        from api.routes.subscription import UpgradeRequest
        
        request = UpgradeRequest(
            plan="business",
            billing_cycle="yearly"
        )
        
        assert request.plan == "business"
    
    def test_set_execution_mode_request(self):
        """Test SetExecutionModeRequest schema."""
        from api.routes.subscription import SetExecutionModeRequest
        
        request = SetExecutionModeRequest(mode="local")
        assert request.mode == "local"
    
    def test_validate_subscription_request(self):
        """Test ValidateSubscriptionRequest schema."""
        from api.routes.subscription import ValidateSubscriptionRequest
        
        request = ValidateSubscriptionRequest(
            hwid="hardware123",
            app_version="1.0.0"
        )
        
        assert request.hwid == "hardware123"
    
    def test_checkout_response_schema(self):
        """Test CheckoutResponse schema."""
        from api.routes.subscription import CheckoutResponse
        
        response = CheckoutResponse(
            checkout_url="https://checkout.mp.com/...",
            preference_id="pref123"
        )
        
        assert response.preference_id == "pref123"


# ==================== TESTES DE ENDPOINTS: PLANS ====================

class TestPlansEndpoints:
    """Testes para endpoints de planos."""
    
    @pytest.mark.asyncio
    async def test_list_plans(self):
        """Test listing all plans."""
        from api.routes.subscription import list_plans
        
        mock_service = MagicMock()
        mock_service.list_plans.return_value = [
            {
                "tier": "free",
                "name": "Free",
                "description": "Plano gratuito",
                "price_monthly": 0.0,
                "price_yearly": 0.0,
                "execution_modes": ["cloud"],
                "marketplaces": [],
                "scraper_priority": "low",
                "limits": {},
                "features": {},
                "highlights": [],
                "offline_days": 0
            }
        ]
        
        result = await list_plans(mock_service)
        
        assert len(result) >= 1
    
    @pytest.mark.asyncio
    async def test_get_plan_details_success(self):
        """Test getting plan details successfully."""
        from api.routes.subscription import get_plan_details
        
        mock_service = MagicMock()
        
        with patch('api.routes.subscription.PlanTier') as mock_tier:
            mock_tier.return_value = MagicMock(value="starter")
            
            with patch('api.routes.subscription.PLANS_V2') as mock_plans:
                mock_config = MagicMock()
                mock_config.tier.value = "starter"
                mock_config.name = "Starter"
                mock_config.description = "Plano starter"
                mock_config.price_monthly = Decimal("49.90")
                mock_config.price_yearly = Decimal("499.00")
                mock_config.execution_modes = []
                mock_config.marketplaces = []
                mock_config.scraper_priority.value = "medium"
                mock_config.limits = {}
                mock_config.features = {}
                mock_config.highlights = []
                mock_config.offline_days = 3
                
                mock_plans.get.return_value = mock_config
                
                result = await get_plan_details("starter", mock_service)
                
                assert result.tier == "starter"
    
    @pytest.mark.asyncio
    async def test_get_plan_details_not_found(self):
        """Test getting plan details for non-existent plan."""
        from api.routes.subscription import get_plan_details
        
        mock_service = MagicMock()
        
        with pytest.raises(HTTPException) as exc:
            await get_plan_details("invalid_plan", mock_service)
        
        assert exc.value.status_code == 404


# ==================== TESTES DE ENDPOINTS: SUBSCRIPTION ====================

class TestSubscriptionEndpoints:
    """Testes para endpoints de subscription."""
    
    @pytest.mark.asyncio
    async def test_get_current_subscription_full(self):
        """Test getting current subscription with full info."""
        from api.routes.subscription import get_current_subscription_full
        
        mock_user = {"id": 123}
        mock_service = AsyncMock()
        
        mock_subscription = MagicMock()
        mock_subscription.id = "sub123"
        mock_subscription.plan.value = "starter"
        mock_subscription.status.value = "active"
        mock_subscription.billing_cycle.value = "monthly"
        mock_subscription.execution_mode.value = "cloud"
        mock_subscription.current_period_start = datetime.now(timezone.utc)
        mock_subscription.current_period_end = datetime.now(timezone.utc) + timedelta(days=30)
        
        mock_service.get_subscription.return_value = mock_subscription
        mock_service.get_usage_stats.return_value = []
        
        with patch('api.routes.subscription.PLANS_V2') as mock_plans:
            mock_config = MagicMock()
            mock_config.tier.value = "starter"
            mock_config.name = "Starter"
            mock_config.description = "Starter plan"
            mock_config.price_monthly = Decimal("49.90")
            mock_config.price_yearly = Decimal("499.00")
            mock_config.execution_modes = []
            mock_config.marketplaces = []
            mock_config.scraper_priority.value = "medium"
            mock_config.limits = {}
            mock_config.features = {}
            mock_config.highlights = []
            mock_config.offline_days = 3
            
            mock_plans.get.return_value = mock_config
            
            result = await get_current_subscription_full(mock_user, mock_service)
            
            assert result.subscription.id == "sub123"


# ==================== TESTES DE ENDPOINTS: USAGE ====================

class TestUsageEndpoints:
    """Testes para endpoints de uso."""
    
    @pytest.mark.asyncio
    async def test_get_usage(self):
        """Test getting usage stats."""
        from api.routes.subscription import get_usage
        
        mock_user = {"id": 123}
        mock_service = AsyncMock()
        
        mock_stats = MagicMock()
        mock_stats.feature = "price_searches"
        mock_stats.current = 50
        mock_stats.limit = 100
        mock_stats.percentage = 50.0
        mock_stats.is_unlimited = False
        mock_stats.resets_at = datetime.now(timezone.utc)
        
        mock_service.get_usage_stats.return_value = [mock_stats]
        
        result = await get_usage(mock_user, mock_service)
        
        assert len(result) == 1
        assert result[0].feature == "price_searches"
    
    @pytest.mark.asyncio
    async def test_get_feature_usage(self):
        """Test getting feature-specific usage."""
        from api.routes.subscription import get_feature_usage
        
        mock_user = {"id": 123}
        mock_service = AsyncMock()
        mock_service.get_usage.return_value = 50
        mock_service.get_feature_limit.return_value = 100
        
        result = await get_feature_usage("price_searches", mock_user, mock_service)
        
        assert result["current"] == 50
        assert result["limit"] == 100
        assert result["percentage"] == 50.0
        assert result["can_use"] is True
    
    @pytest.mark.asyncio
    async def test_get_feature_usage_unlimited(self):
        """Test getting feature usage for unlimited feature."""
        from api.routes.subscription import get_feature_usage
        
        mock_user = {"id": 123}
        mock_service = AsyncMock()
        mock_service.get_usage.return_value = 1000
        mock_service.get_feature_limit.return_value = -1  # unlimited
        
        result = await get_feature_usage("unlimited_feature", mock_user, mock_service)
        
        assert result["is_unlimited"] is True
        assert result["percentage"] == 0.0
        assert result["can_use"] is True
    
    @pytest.mark.asyncio
    async def test_get_feature_usage_at_limit(self):
        """Test getting feature usage when at limit."""
        from api.routes.subscription import get_feature_usage
        
        mock_user = {"id": 123}
        mock_service = AsyncMock()
        mock_service.get_usage.return_value = 100
        mock_service.get_feature_limit.return_value = 100
        
        result = await get_feature_usage("limited_feature", mock_user, mock_service)
        
        assert result["percentage"] == 100.0
        assert result["can_use"] is False
    
    @pytest.mark.asyncio
    async def test_check_feature_access(self):
        """Test checking feature access."""
        from api.routes.subscription import check_feature_access
        
        mock_user = {"id": 123}
        mock_service = AsyncMock()
        mock_service.can_use_feature.return_value = True
        
        result = await check_feature_access("analytics", mock_user, mock_service)
        
        assert result["feature"] == "analytics"
        assert result["can_use"] is True


# ==================== TESTES DE ENDPOINTS: CREATE/UPGRADE ====================

class TestCreateUpgradeEndpoints:
    """Testes para endpoints de criação e upgrade."""
    
    @pytest.mark.asyncio
    async def test_create_subscription_invalid_plan(self):
        """Test creating subscription with invalid plan."""
        from api.routes.subscription import (CreateSubscriptionRequest,
                                             create_subscription)
        
        mock_user = {"id": 123}
        mock_service = AsyncMock()
        request = CreateSubscriptionRequest(plan_tier="invalid", billing_cycle="monthly")
        
        with pytest.raises(HTTPException) as exc:
            await create_subscription(request, mock_user, mock_service)
        
        assert exc.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_create_subscription_free_plan(self):
        """Test creating subscription for FREE plan."""
        from api.routes.subscription import (CreateSubscriptionRequest,
                                             create_subscription)
        
        mock_user = {"id": 123}
        mock_service = AsyncMock()
        request = CreateSubscriptionRequest(plan_tier="free", billing_cycle="monthly")
        
        with pytest.raises(HTTPException) as exc:
            await create_subscription(request, mock_user, mock_service)
        
        assert exc.value.status_code == 400
        assert "FREE" in exc.value.detail
    
    @pytest.mark.asyncio
    async def test_create_subscription_enterprise_plan(self):
        """Test creating subscription for ENTERPRISE plan."""
        from api.routes.subscription import (CreateSubscriptionRequest,
                                             create_subscription)
        
        mock_user = {"id": 123}
        mock_service = AsyncMock()
        request = CreateSubscriptionRequest(plan_tier="enterprise", billing_cycle="monthly")
        
        with pytest.raises(HTTPException) as exc:
            await create_subscription(request, mock_user, mock_service)
        
        assert exc.value.status_code == 400
        assert "Enterprise" in exc.value.detail
    
    @pytest.mark.asyncio
    async def test_upgrade_subscription_invalid_plan(self):
        """Test upgrading subscription with invalid plan."""
        from api.routes.subscription import (UpgradeRequest,
                                             upgrade_subscription)
        
        mock_user = {"id": 123}
        mock_service = AsyncMock()
        request = UpgradeRequest(plan="invalid")
        
        with pytest.raises(HTTPException) as exc:
            await upgrade_subscription(request, mock_user, mock_service)
        
        assert exc.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_downgrade_subscription_invalid_plan(self):
        """Test downgrading subscription with invalid plan."""
        from api.routes.subscription import (UpgradeRequest,
                                             downgrade_subscription)
        
        mock_user = {"id": 123}
        mock_service = AsyncMock()
        request = UpgradeRequest(plan="invalid")
        
        with pytest.raises(HTTPException) as exc:
            await downgrade_subscription(request, mock_user, mock_service)
        
        assert exc.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_cancel_subscription(self):
        """Test canceling subscription."""
        from api.routes.subscription import cancel_subscription
        
        mock_user = {"id": 123}
        mock_service = AsyncMock()
        
        mock_subscription = MagicMock()
        mock_subscription.current_period_end = datetime.now(timezone.utc) + timedelta(days=15)
        mock_service.cancel_subscription.return_value = mock_subscription
        
        result = await cancel_subscription(mock_user, mock_service)
        
        assert result["status"] == "canceled"


# ==================== TESTES DE ENDPOINTS: EXECUTION MODE ====================

class TestExecutionModeEndpoints:
    """Testes para endpoints de modo de execução."""
    
    @pytest.mark.asyncio
    async def test_set_execution_mode_invalid(self):
        """Test setting invalid execution mode."""
        from api.routes.subscription import (SetExecutionModeRequest,
                                             set_execution_mode)
        
        mock_user = {"id": 123}
        mock_service = AsyncMock()
        request = SetExecutionModeRequest(mode="invalid_mode")
        
        with pytest.raises(HTTPException) as exc:
            await set_execution_mode(request, mock_user, mock_service)
        
        assert exc.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_set_execution_mode_not_supported(self):
        """Test setting execution mode not supported by plan."""
        from api.routes.subscription import (SetExecutionModeRequest,
                                             set_execution_mode)
        
        mock_user = {"id": 123}
        mock_service = AsyncMock()
        mock_service.set_execution_mode.side_effect = ValueError("Mode not supported")
        request = SetExecutionModeRequest(mode="local_first")
        
        with pytest.raises(HTTPException) as exc:
            await set_execution_mode(request, mock_user, mock_service)
        
        assert exc.value.status_code == 402
    
    @pytest.mark.asyncio
    async def test_get_execution_mode(self):
        """Test getting current execution mode."""
        from api.routes.subscription import get_execution_mode
        from modules.subscription import ExecutionMode
        
        mock_user = {"id": 123}
        mock_service = AsyncMock()
        # ExecutionMode usa valores: 'web_only', 'hybrid', 'local_first'
        mock_service.get_execution_mode.return_value = ExecutionMode.WEB_ONLY
        
        mock_subscription = MagicMock()
        mock_subscription.plan = MagicMock()
        mock_service.get_subscription.return_value = mock_subscription
        
        with patch('api.routes.subscription.PLANS_V2') as mock_plans:
            mock_config = MagicMock()
            mock_config.execution_modes = [ExecutionMode.WEB_ONLY]
            mock_plans.get.return_value = mock_config
            
            result = await get_execution_mode(mock_user, mock_service)
            
            assert result["current_mode"] == "web_only"


# ==================== TESTES DE ENDPOINTS: VALIDATE ====================

class TestValidateEndpoints:
    """Testes para endpoints de validação."""
    
    @pytest.mark.asyncio
    async def test_validate_subscription_valid(self):
        """Test validating a valid subscription."""
        from api.routes.subscription import (ValidateSubscriptionRequest,
                                             validate_subscription)
        
        mock_user = {"id": 123}
        mock_service = AsyncMock()
        request = ValidateSubscriptionRequest(hwid="hw123")
        
        mock_subscription = MagicMock()
        mock_subscription.plan.value = "starter"
        mock_subscription.execution_mode.value = "cloud"
        mock_subscription.status.value = "active"
        mock_subscription.current_period_end = datetime.now(timezone.utc) + timedelta(days=15)
        mock_subscription.is_active.return_value = True
        mock_subscription.is_in_grace_period.return_value = False
        mock_service.get_subscription.return_value = mock_subscription
        
        with patch('api.routes.subscription.PLANS_V2') as mock_plans:
            mock_config = MagicMock()
            mock_config.marketplaces = []
            mock_config.limits = {}
            mock_config.features = {}
            mock_config.offline_days = 3
            mock_config.grace_period_days = 7
            mock_plans.get.return_value = mock_config
            
            result = await validate_subscription(request, mock_user, mock_service)
            
            assert result["is_valid"] is True
            assert result["plan_tier"] == "starter"
    
    @pytest.mark.asyncio
    async def test_validate_subscription_expired(self):
        """Test validating an expired subscription."""
        from api.routes.subscription import (ValidateSubscriptionRequest,
                                             validate_subscription)
        
        mock_user = {"id": 123}
        mock_service = AsyncMock()
        request = ValidateSubscriptionRequest(hwid="hw123")
        
        mock_subscription = MagicMock()
        mock_subscription.is_active.return_value = False
        mock_subscription.is_in_grace_period.return_value = False
        mock_service.get_subscription.return_value = mock_subscription
        
        with patch('api.routes.subscription.PLANS_V2') as mock_plans:
            mock_plans.get.return_value = MagicMock()
            
            result = await validate_subscription(request, mock_user, mock_service)
            
            assert result["is_valid"] is False
            assert result["reason"] == "subscription_expired"


# ==================== TESTES DE WEBHOOKS ====================

class TestWebhookEndpoints:
    """Testes para endpoints de webhook."""
    
    @pytest.mark.asyncio
    async def test_mercadopago_webhook_no_sdk(self):
        """Test MP webhook when SDK not available."""
        from api.routes.subscription import mercadopago_webhook
        
        mock_service = AsyncMock()
        payload = {"type": "payment", "data": {"id": "123"}}
        
        with patch('api.routes.subscription.MP_AVAILABLE', False):
            result = await mercadopago_webhook(payload, mock_service)
            
            assert result["status"] == "received"
    
    @pytest.mark.asyncio
    async def test_mercadopago_webhook_payment_created(self):
        """Test MP webhook for payment created."""
        from api.routes.subscription import mercadopago_webhook
        
        mock_service = AsyncMock()
        payload = {
            "type": "payment.created",
            "data": {"id": "payment123"}
        }
        
        with patch('api.routes.subscription.MP_AVAILABLE', True):
            with patch('api.routes.subscription.sdk') as mock_sdk:
                mock_payment_response = {
                    "response": {
                        "status": "approved",
                        "external_reference": "user123:starter:monthly",
                        "metadata": {}
                    }
                }
                mock_sdk.payment.return_value.get.return_value = mock_payment_response
                
                result = await mercadopago_webhook(payload, mock_service)
                
                assert result["status"] == "received"
    
    @pytest.mark.asyncio
    async def test_mercadopago_webhook_payment_rejected(self):
        """Test MP webhook for rejected payment."""
        from api.routes.subscription import mercadopago_webhook
        
        mock_service = AsyncMock()
        payload = {
            "type": "payment",
            "data": {"id": "payment123"}
        }
        
        with patch('api.routes.subscription.MP_AVAILABLE', True):
            with patch('api.routes.subscription.sdk') as mock_sdk:
                mock_payment_response = {
                    "response": {
                        "status": "rejected",
                        "external_reference": "user123:starter:monthly"
                    }
                }
                mock_sdk.payment.return_value.get.return_value = mock_payment_response
                
                result = await mercadopago_webhook(payload, mock_service)
                
                assert result["status"] == "received"
    
    @pytest.mark.asyncio
    async def test_mercadopago_webhook_preapproval(self):
        """Test MP webhook for subscription preapproval."""
        from api.routes.subscription import mercadopago_webhook
        
        mock_service = AsyncMock()
        payload = {
            "type": "subscription_preapproval.updated",
            "data": {"id": "preapproval123"}
        }
        
        with patch('api.routes.subscription.MP_AVAILABLE', True):
            with patch('api.routes.subscription.sdk') as mock_sdk:
                mock_preapproval_response = {
                    "response": {
                        "status": "authorized",
                        "payer_email": "test@test.com"
                    }
                }
                mock_sdk.preapproval.return_value.get.return_value = mock_preapproval_response
                
                result = await mercadopago_webhook(payload, mock_service)
                
                assert result["status"] == "received"


# ==================== TESTES DE ROUTER ====================

class TestRouterConfiguration:
    """Testes para configuração do router."""
    
    def test_router_exists(self):
        """Test that router exists."""
        from api.routes.subscription import router
        assert router is not None
    
    def test_router_has_routes(self):
        """Test that router has expected routes."""
        from api.routes.subscription import router
        routes = [r.path for r in router.routes if hasattr(r, 'path')]
        
        assert "/plans" in routes
        assert "/current" in routes
        assert "/usage" in routes


# ==================== TESTES DE MP_AVAILABLE ====================

class TestMercadoPagoAvailability:
    """Testes para disponibilidade do MercadoPago."""
    
    def test_mp_sdk_import(self):
        """Test MercadoPago SDK availability flag."""
        # Just check the module loads without error
        from api.routes.subscription import MP_AVAILABLE

        # MP_AVAILABLE is either True or False, both are valid
        assert isinstance(MP_AVAILABLE, bool)
