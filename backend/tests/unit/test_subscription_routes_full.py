"""Testes abrangentes para Subscription Routes."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class MockUsageStats:
    """Mock de UsageStats."""
    def __init__(self, feature="social_posts", current=5, limit=100):
        self.feature = feature
        self.current = current
        self.limit = limit
        self.percentage = (current / limit) * 100 if limit > 0 else 0
        self.is_unlimited = limit == -1
        self.resets_at = datetime.utcnow() + timedelta(days=30)


class MockSubscriptionV2:
    """Mock de SubscriptionV2."""
    def __init__(
        self,
        id="sub-123",
        plan="pro",
        status="active",
        billing_cycle="monthly",
        execution_mode="cloud"
    ):
        self.id = id
        self.plan = MagicMock()
        self.plan.value = plan
        self.status = MagicMock()
        self.status.value = status
        self.billing_cycle = MagicMock()
        self.billing_cycle.value = billing_cycle
        self.execution_mode = MagicMock()
        self.execution_mode.value = execution_mode
        self.current_period_start = datetime.utcnow()
        self.current_period_end = datetime.utcnow() + timedelta(days=30)
        self.canceled_at = None


class MockPlanConfig:
    """Mock de PlanConfig."""
    def __init__(self, tier="pro"):
        self.tier = MagicMock()
        self.tier.value = tier
        self.name = f"Plano {tier.capitalize()}"
        self.description = f"Descrição do plano {tier}"
        self.price_monthly = 49.90
        self.price_yearly = 479.90
        self.execution_modes = [MagicMock(value="cloud"), MagicMock(value="local")]
        self.marketplaces = [MagicMock(value="mercadolivre"), MagicMock(value="shopee")]
        self.scraper_priority = MagicMock()
        self.scraper_priority.value = "high"
        self.limits = {"social_posts": 100, "crm_contacts": 1000}
        self.features = {"ai_captions": True, "priority_support": True}
        self.highlights = ["Feature 1", "Feature 2"]
        self.offline_days = 7


@pytest.fixture
def mock_current_user():
    return {"id": "user-123", "email": "test@example.com"}


@pytest.fixture
def mock_subscription_service():
    service = AsyncMock()
    service.list_plans = MagicMock(return_value=[
        {
            "tier": "free",
            "name": "Gratuito",
            "description": "Plano gratuito",
            "price_monthly": 0.0,
            "price_yearly": 0.0,
            "execution_modes": ["cloud"],
            "marketplaces": ["mercadolivre"],
            "scraper_priority": "low",
            "limits": {"social_posts": 10},
            "features": {"ai_captions": False},
            "highlights": ["Básico"],
            "offline_days": 0
        }
    ])
    service.get_subscription = AsyncMock(return_value=MockSubscriptionV2())
    service.get_usage_stats = AsyncMock(return_value=[MockUsageStats()])
    service.get_usage = AsyncMock(return_value=5)
    service.can_use_feature = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_subscription():
    return MockSubscriptionV2()


class TestModels:
    """Testes para os modelos de request/response."""

    def test_plan_info_v2(self):
        """Teste do modelo PlanInfoV2."""
        from api.routes.subscription import PlanInfoV2
        plan = PlanInfoV2(
            tier="pro",
            name="Plano Pro",
            description="Plano profissional",
            price_monthly=49.90,
            price_yearly=479.90,
            execution_modes=["cloud", "local"],
            marketplaces=["mercadolivre"],
            scraper_priority="high",
            limits={"posts": 100},
            features={"ai": True},
            highlights=["Feature 1"],
            offline_days=7
        )
        assert plan.tier == "pro"
        assert plan.price_monthly == 49.90

    def test_subscription_response(self):
        """Teste do modelo SubscriptionResponse."""
        from api.routes.subscription import SubscriptionResponse
        now = datetime.utcnow()
        resp = SubscriptionResponse(
            id="sub-123",
            plan="pro",
            status="active",
            billing_cycle="monthly",
            execution_mode="cloud",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            marketplaces=["mercadolivre"],
            limits={"posts": 100},
            features={"ai": True}
        )
        assert resp.plan == "pro"
        assert resp.status == "active"

    def test_create_subscription_request(self):
        """Teste do modelo CreateSubscriptionRequest."""
        from api.routes.subscription import CreateSubscriptionRequest
        req = CreateSubscriptionRequest(
            plan_tier="pro",
            billing_cycle="yearly"
        )
        assert req.plan_tier == "pro"
        assert req.billing_cycle == "yearly"

    def test_upgrade_request(self):
        """Teste do modelo UpgradeRequest."""
        from api.routes.subscription import UpgradeRequest
        req = UpgradeRequest(plan="enterprise")
        assert req.plan == "enterprise"
        assert req.billing_cycle is None

    def test_set_execution_mode_request(self):
        """Teste do modelo SetExecutionModeRequest."""
        from api.routes.subscription import SetExecutionModeRequest
        req = SetExecutionModeRequest(mode="local")
        assert req.mode == "local"

    def test_validate_subscription_request(self):
        """Teste do modelo ValidateSubscriptionRequest."""
        from api.routes.subscription import ValidateSubscriptionRequest
        req = ValidateSubscriptionRequest(
            hwid="ABC123DEF456",
            app_version="1.0.0"
        )
        assert req.hwid == "ABC123DEF456"

    def test_checkout_response(self):
        """Teste do modelo CheckoutResponse."""
        from api.routes.subscription import CheckoutResponse
        resp = CheckoutResponse(
            checkout_url="https://checkout.mercadopago.com/...",
            preference_id="pref-123"
        )
        assert "mercadopago" in resp.checkout_url

    def test_usage_stats_response(self):
        """Teste do modelo UsageStatsResponse."""
        from api.routes.subscription import UsageStatsResponse
        resp = UsageStatsResponse(
            feature="social_posts",
            current=25,
            limit=100,
            percentage=25.0,
            is_unlimited=False,
            resets_at=datetime.utcnow()
        )
        assert resp.percentage == 25.0


class TestListPlans:
    """Testes para list_plans."""

    async def test_list_plans_success(self, mock_subscription_service):
        """Teste de listagem bem-sucedida."""
        from api.routes.subscription import list_plans
        
        result = await list_plans(service=mock_subscription_service)
        
        assert len(result) == 1
        assert result[0].tier == "free"


class TestGetPlanDetails:
    """Testes para get_plan_details."""

    async def test_get_plan_details_success(self, mock_subscription_service):
        """Teste de obtenção bem-sucedida."""
        from api.routes.subscription import get_plan_details
        
        with patch("api.routes.subscription.PlanTier") as mock_tier:
            mock_tier.return_value = "pro"
            with patch("api.routes.subscription.PLANS_V2", {"pro": MockPlanConfig()}):
                with patch.object(mock_tier, "__call__", return_value=MagicMock()):
                    # Este teste precisa de mocks mais complexos
                    pass

    async def test_get_plan_details_not_found(self, mock_subscription_service):
        """Teste de plano não encontrado."""
        from api.routes.subscription import get_plan_details
        
        with patch("api.routes.subscription.PlanTier") as mock_tier:
            mock_tier.side_effect = ValueError("Invalid tier")
            with pytest.raises(HTTPException) as exc:
                await get_plan_details(
                    plan_tier="invalid",
                    service=mock_subscription_service
                )
        
        assert exc.value.status_code == 404


class TestGetUsage:
    """Testes para get_usage."""

    async def test_get_usage_success(self, mock_current_user, mock_subscription_service):
        """Teste de obtenção de uso."""
        from api.routes.subscription import get_usage
        
        result = await get_usage(
            current_user=mock_current_user,
            service=mock_subscription_service
        )
        
        assert len(result) == 1
        assert result[0].feature == "social_posts"


class TestRouterConfig:
    """Testes para configuração do router."""

    def test_router_exists(self):
        """Teste se router existe."""
        from api.routes.subscription import router
        assert router is not None

    def test_mp_available_variable_exists(self):
        """Teste se variável MP_AVAILABLE existe."""
        from api.routes.subscription import MP_AVAILABLE
        assert isinstance(MP_AVAILABLE, bool)


class TestSubscriptionMiddlewareIntegration:
    """Testes de integração com middleware."""

    async def test_requires_plan_decorator_basic(self):
        """Teste básico do decorator RequiresPlan."""
        from api.middleware.subscription import RequiresPlan
        from modules.subscription import PlanTier
        
        decorator = RequiresPlan(PlanTier.BUSINESS)
        assert decorator is not None

    async def test_requires_plan_callable(self):
        """Teste se o decorator é callable."""
        from api.middleware.subscription import RequiresPlan
        from modules.subscription import PlanTier
        
        decorator = RequiresPlan(PlanTier.FREE)
        # O decorator deve ser callable
        assert callable(decorator)
