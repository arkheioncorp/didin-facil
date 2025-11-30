"""
Testes para Subscription Routes - api/routes/subscription.py
Cobertura: list_plans, get_plan_details, get_my_subscription, get_usage,
           check_feature_access, upgrade_subscription, cancel_subscription, webhook
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from fastapi import HTTPException


# ============================================
# MOCKS & FIXTURES
# ============================================

@pytest.fixture
def mock_user():
    """Mock de usuário autenticado"""
    user = MagicMock()
    user.id = "user-123"
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_subscription():
    """Mock de assinatura"""
    sub = MagicMock()
    sub.id = "sub-123"
    sub.plan.value = "pro"
    sub.status.value = "active"
    sub.billing_cycle.value = "monthly"
    sub.current_period_start = datetime(2024, 1, 1)
    sub.current_period_end = datetime(2024, 2, 1)
    sub.usage = {"videos": 50, "downloads": 100}
    return sub


@pytest.fixture
def mock_plan_features():
    """Mock de features do plano"""
    features = MagicMock()
    features.features = {
        "videos": MagicMock(description="Vídeos por mês", limit=100),
        "downloads": MagicMock(description="Downloads por mês", limit=500)
    }
    return features


@pytest.fixture
def mock_subscription_service(mock_subscription, mock_plan_features):
    """Mock do SubscriptionService"""
    service = MagicMock()
    service.list_plans.return_value = [
        {
            "tier": "free",
            "name": "Free",
            "description": "Plano gratuito",
            "price_monthly": 0,
            "price_yearly": 0,
            "highlights": ["Feature 1"]
        },
        {
            "tier": "pro",
            "name": "Pro",
            "description": "Plano profissional",
            "price_monthly": 29.90,
            "price_yearly": 299.00,
            "highlights": ["Feature 1", "Feature 2"]
        }
    ]
    service.get_plan_info.return_value = {
        "name": "Pro",
        "description": "Plano profissional",
        "price_monthly": 29.90,
        "price_yearly": 299.00,
        "highlights": ["Feature 1"]
    }
    # Métodos async precisam de AsyncMock
    service.get_plan_features = AsyncMock(return_value=mock_plan_features)
    service.get_subscription = AsyncMock(return_value=mock_subscription)
    service.get_usage = AsyncMock(return_value=50)
    service.can_use_feature = AsyncMock(return_value=True)
    service.upgrade_plan = AsyncMock(return_value=mock_subscription)
    service.cancel_subscription = AsyncMock(return_value=mock_subscription)
    return service


# ============================================
# TESTS: List Plans
# ============================================

class TestListPlans:
    """Testes do endpoint list_plans"""
    
    @pytest.mark.asyncio
    async def test_list_plans_success(self, mock_subscription_service):
        """Deve listar todos os planos"""
        with patch("api.routes.subscription.subscription_service", mock_subscription_service):
            from api.routes.subscription import list_plans
            
            response = await list_plans()
            
            assert len(response) == 2
            assert response[0]["tier"] == "free"
            assert response[1]["tier"] == "pro"


# ============================================
# TESTS: Get Plan Details
# ============================================

class TestGetPlanDetails:
    """Testes do endpoint get_plan_details"""
    
    @pytest.mark.asyncio
    async def test_get_plan_details_success(self, mock_subscription_service):
        """Deve retornar detalhes do plano"""
        # Mock PlanTier enum
        mock_plan_tier = MagicMock()
        mock_plan_tier.value = "pro"
        
        with patch("api.routes.subscription.subscription_service", mock_subscription_service):
            with patch("api.routes.subscription.PlanTier", return_value=mock_plan_tier):
                from api.routes.subscription import get_plan_details
                
                response = await get_plan_details("pro")
                
                assert response["tier"] == "pro"
                assert response["name"] == "Pro"
                assert "features" in response
    
    @pytest.mark.asyncio
    async def test_get_plan_details_invalid_tier(self):
        """Deve retornar 404 para plano inválido"""
        with patch("api.routes.subscription.PlanTier") as mock_tier:
            mock_tier.side_effect = ValueError("Invalid tier")
            
            from api.routes.subscription import get_plan_details
            
            with pytest.raises(HTTPException) as exc_info:
                await get_plan_details("invalid_tier")
            
            assert exc_info.value.status_code == 404


# ============================================
# TESTS: Get My Subscription
# ============================================

class TestGetMySubscription:
    """Testes do endpoint get_my_subscription"""
    
    @pytest.mark.asyncio
    async def test_get_subscription_success(self, mock_user, mock_subscription_service):
        """Deve retornar assinatura do usuário"""
        with patch("api.routes.subscription.subscription_service", mock_subscription_service):
            from api.routes.subscription import get_my_subscription
            
            response = await get_my_subscription(current_user=mock_user)
            
            assert response.id == "sub-123"
            assert response.plan == "pro"
            assert response.status == "active"


# ============================================
# TESTS: Get Usage
# ============================================

class TestGetUsage:
    """Testes do endpoint get_usage"""
    
    @pytest.mark.asyncio
    async def test_get_usage_success(self, mock_user, mock_subscription_service, mock_subscription):
        """Deve retornar uso atual de features"""
        mock_subscription.plan = MagicMock()
        mock_subscription.plan.value = "pro"
        mock_subscription_service.get_subscription.return_value = mock_subscription
        
        with patch("api.routes.subscription.subscription_service", mock_subscription_service):
            from api.routes.subscription import get_usage
            
            response = await get_usage(current_user=mock_user)
            
            assert len(response) == 2
            # Verifica que retornou UsageResponse para cada feature


# ============================================
# TESTS: Check Feature Access
# ============================================

class TestCheckFeatureAccess:
    """Testes do endpoint check_feature_access"""
    
    @pytest.mark.asyncio
    async def test_check_feature_can_use(self, mock_user, mock_subscription_service):
        """Deve retornar True quando pode usar feature"""
        mock_subscription_service.can_use_feature.return_value = True
        
        with patch("api.routes.subscription.subscription_service", mock_subscription_service):
            from api.routes.subscription import check_feature_access
            
            response = await check_feature_access(
                feature="videos",
                current_user=mock_user
            )
            
            assert response["feature"] == "videos"
            assert response["can_use"] is True
    
    @pytest.mark.asyncio
    async def test_check_feature_cannot_use(self, mock_user, mock_subscription_service):
        """Deve retornar False quando não pode usar feature"""
        mock_subscription_service.can_use_feature.return_value = False
        
        with patch("api.routes.subscription.subscription_service", mock_subscription_service):
            from api.routes.subscription import check_feature_access
            
            response = await check_feature_access(
                feature="premium_feature",
                current_user=mock_user
            )
            
            assert response["can_use"] is False


# ============================================
# TESTS: Upgrade Subscription
# ============================================

class TestUpgradeSubscription:
    """Testes do endpoint upgrade_subscription"""
    
    @pytest.mark.asyncio
    async def test_upgrade_success(self, mock_user, mock_subscription_service):
        """Deve fazer upgrade com sucesso"""
        mock_plan_tier = MagicMock()
        mock_plan_tier.value = "pro"
        mock_plan_tier.FREE = MagicMock()
        mock_plan_tier.ENTERPRISE = MagicMock()
        
        mock_billing_cycle = MagicMock()
        mock_billing_cycle.value = "monthly"
        
        with patch("api.routes.subscription.subscription_service", mock_subscription_service):
            with patch("api.routes.subscription.PlanTier") as PlanTierMock:
                PlanTierMock.return_value = mock_plan_tier
                PlanTierMock.FREE = MagicMock()
                PlanTierMock.ENTERPRISE = MagicMock()
                
                with patch("api.routes.subscription.BillingCycle", return_value=mock_billing_cycle):
                    from api.routes.subscription import upgrade_subscription, UpgradeRequest
                    
                    request = UpgradeRequest(plan="pro", billing_cycle="monthly")
                    
                    response = await upgrade_subscription(
                        data=request,
                        current_user=mock_user
                    )
                    
                    assert response["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_upgrade_invalid_plan(self, mock_user):
        """Deve retornar 400 para plano inválido"""
        with patch("api.routes.subscription.PlanTier") as PlanTierMock:
            PlanTierMock.side_effect = ValueError("Invalid plan")
            
            from api.routes.subscription import upgrade_subscription, UpgradeRequest
            
            request = UpgradeRequest(plan="invalid", billing_cycle="monthly")
            
            with pytest.raises(HTTPException) as exc_info:
                await upgrade_subscription(data=request, current_user=mock_user)
            
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_upgrade_to_free_not_allowed(self, mock_user, mock_subscription_service):
        """Não deve permitir upgrade para FREE"""
        mock_free_tier = MagicMock()
        mock_free_tier.value = "free"
        
        with patch("api.routes.subscription.subscription_service", mock_subscription_service):
            with patch("api.routes.subscription.PlanTier") as PlanTierMock:
                PlanTierMock.return_value = mock_free_tier
                PlanTierMock.FREE = mock_free_tier
                PlanTierMock.ENTERPRISE = MagicMock()
                
                with patch("api.routes.subscription.BillingCycle"):
                    from api.routes.subscription import upgrade_subscription, UpgradeRequest
                    
                    request = UpgradeRequest(plan="free", billing_cycle="monthly")
                    
                    with pytest.raises(HTTPException) as exc_info:
                        await upgrade_subscription(data=request, current_user=mock_user)
                    
                    assert exc_info.value.status_code == 400
                    assert "FREE" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_upgrade_to_enterprise_requires_contact(self, mock_user, mock_subscription_service):
        """Deve exigir contato para plano Enterprise"""
        mock_enterprise_tier = MagicMock()
        mock_enterprise_tier.value = "enterprise"
        
        with patch("api.routes.subscription.subscription_service", mock_subscription_service):
            with patch("api.routes.subscription.PlanTier") as PlanTierMock:
                PlanTierMock.return_value = mock_enterprise_tier
                PlanTierMock.FREE = MagicMock()
                PlanTierMock.ENTERPRISE = mock_enterprise_tier
                
                with patch("api.routes.subscription.BillingCycle"):
                    from api.routes.subscription import upgrade_subscription, UpgradeRequest
                    
                    request = UpgradeRequest(plan="enterprise", billing_cycle="monthly")
                    
                    with pytest.raises(HTTPException) as exc_info:
                        await upgrade_subscription(data=request, current_user=mock_user)
                    
                    assert exc_info.value.status_code == 400
                    assert "Enterprise" in str(exc_info.value.detail)


# ============================================
# TESTS: Cancel Subscription
# ============================================

class TestCancelSubscription:
    """Testes do endpoint cancel_subscription"""
    
    @pytest.mark.asyncio
    async def test_cancel_success(self, mock_user, mock_subscription_service):
        """Deve cancelar assinatura com sucesso"""
        with patch("api.routes.subscription.subscription_service", mock_subscription_service):
            from api.routes.subscription import cancel_subscription
            
            response = await cancel_subscription(current_user=mock_user)
            
            assert response["status"] == "canceled"
            assert "access_until" in response


# ============================================
# TESTS: MercadoPago Webhook
# ============================================

class TestMercadoPagoWebhook:
    """Testes do webhook do MercadoPago"""
    
    @pytest.mark.asyncio
    async def test_webhook_payment_created(self):
        """Deve processar evento payment.created"""
        from api.routes.subscription import mercadopago_webhook
        
        payload = {
            "type": "payment.created",
            "data": {"id": "pay-123"}
        }
        
        response = await mercadopago_webhook(payload)
        
        assert response["status"] == "received"
        assert response["event"] == "payment.created"
    
    @pytest.mark.asyncio
    async def test_webhook_payment_updated(self):
        """Deve processar evento payment.updated"""
        from api.routes.subscription import mercadopago_webhook
        
        payload = {
            "type": "payment.updated",
            "data": {"id": "pay-123", "status": "approved"}
        }
        
        response = await mercadopago_webhook(payload)
        
        assert response["status"] == "received"
        assert response["event"] == "payment.updated"
    
    @pytest.mark.asyncio
    async def test_webhook_subscription_preapproval(self):
        """Deve processar evento subscription_preapproval.updated"""
        from api.routes.subscription import mercadopago_webhook
        
        payload = {
            "type": "subscription_preapproval.updated",
            "data": {"id": "preapproval-123"}
        }
        
        response = await mercadopago_webhook(payload)
        
        assert response["status"] == "received"
        assert response["event"] == "subscription_preapproval.updated"


# ============================================
# TESTS: Models
# ============================================

class TestSubscriptionModels:
    """Testes dos modelos Pydantic"""
    
    def test_plan_info_model(self):
        """Deve criar PlanInfo corretamente"""
        from api.routes.subscription import PlanInfo
        
        plan = PlanInfo(
            tier="pro",
            name="Pro",
            description="Plano profissional",
            price_monthly=29.90,
            price_yearly=299.00,
            highlights=["Feature 1", "Feature 2"]
        )
        
        assert plan.tier == "pro"
        assert plan.price_monthly == 29.90
    
    def test_subscription_response_model(self):
        """Deve criar SubscriptionResponse corretamente"""
        from api.routes.subscription import SubscriptionResponse
        
        sub = SubscriptionResponse(
            id="sub-123",
            plan="pro",
            status="active",
            billing_cycle="monthly",
            current_period_start=datetime(2024, 1, 1),
            current_period_end=datetime(2024, 2, 1),
            usage={"videos": 50}
        )
        
        assert sub.id == "sub-123"
        assert sub.plan == "pro"
    
    def test_usage_response_model(self):
        """Deve criar UsageResponse corretamente"""
        from api.routes.subscription import UsageResponse
        
        usage = UsageResponse(
            feature="videos",
            current=50,
            limit=100,
            remaining=50,
            can_use=True
        )
        
        assert usage.feature == "videos"
        assert usage.remaining == 50
    
    def test_upgrade_request_model(self):
        """Deve criar UpgradeRequest corretamente"""
        from api.routes.subscription import UpgradeRequest
        
        req = UpgradeRequest(plan="pro")
        
        assert req.plan == "pro"
        assert req.billing_cycle == "monthly"  # default
    
    def test_checkout_response_model(self):
        """Deve criar CheckoutResponse corretamente"""
        from api.routes.subscription import CheckoutResponse
        
        checkout = CheckoutResponse(
            checkout_url="https://mp.com/checkout",
            preference_id="pref-123"
        )
        
        assert checkout.preference_id == "pref-123"
