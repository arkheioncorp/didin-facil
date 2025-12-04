"""
Testes para o módulo de subscription/planos.
Atualizado para os novos schemas (FeatureLimit, PlanFeatures, Subscription, UsageRecord).
"""
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from modules.subscription.plans import (PLANS, BillingCycle, FeatureCategory,
                                        FeatureLimit, PlanFeatures, PlanTier,
                                        Subscription, SubscriptionService,
                                        SubscriptionStatus, UsageRecord)


class TestPlanTier:
    """Testes para o enum PlanTier."""
    
    def test_plan_tier_values(self):
        """Testa valores dos tiers."""
        assert PlanTier.FREE.value == "free"
        assert PlanTier.STARTER.value == "starter"
        assert PlanTier.BUSINESS.value == "business"
        assert PlanTier.ENTERPRISE.value == "enterprise"
    
    def test_plan_tier_comparison(self):
        """Testa comparação entre tiers."""
        tier_order = [
            PlanTier.FREE,
            PlanTier.STARTER,
            PlanTier.BUSINESS,
            PlanTier.ENTERPRISE,
        ]
        
        for i, tier in enumerate(tier_order[:-1]):
            next_tier = tier_order[i + 1]
            assert tier.value != next_tier.value


class TestBillingCycle:
    """Testes para o enum BillingCycle."""
    
    def test_billing_cycle_values(self):
        """Testa valores dos ciclos de cobrança."""
        assert BillingCycle.MONTHLY.value == "monthly"
        assert BillingCycle.YEARLY.value == "yearly"
        assert BillingCycle.LIFETIME.value == "lifetime"


class TestFeatureCategory:
    """Testes para o enum FeatureCategory."""
    
    def test_feature_category_values(self):
        """Testa valores das categorias de features."""
        assert FeatureCategory.COMPARISON.value == "comparison"
        assert FeatureCategory.SOCIAL_MEDIA.value == "social_media"
        assert FeatureCategory.WHATSAPP.value == "whatsapp"
        assert FeatureCategory.CHATBOT.value == "chatbot"
        assert FeatureCategory.CRM.value == "crm"
        assert FeatureCategory.ANALYTICS.value == "analytics"
        assert FeatureCategory.SUPPORT.value == "support"


class TestFeatureLimit:
    """Testes para limites de features."""
    
    def test_feature_limit_creation(self):
        """Testa criação de FeatureLimit."""
        limit = FeatureLimit(
            feature="price_searches",
            category=FeatureCategory.COMPARISON,
            limit=50,
            description="Buscas de preço/mês",
        )
        
        assert limit.feature == "price_searches"
        assert limit.category == FeatureCategory.COMPARISON
        assert limit.limit == 50
        assert limit.description == "Buscas de preço/mês"
    
    def test_unlimited_feature(self):
        """Testa feature ilimitada (-1)."""
        limit = FeatureLimit(
            feature="price_searches",
            category=FeatureCategory.COMPARISON,
            limit=-1,
            description="Buscas ilimitadas",
        )
        
        assert limit.limit == -1


class TestPlanFeatures:
    """Testes para features de um plano."""
    
    @pytest.fixture
    def starter_features(self):
        """Features do plano STARTER."""
        return PlanFeatures(
            tier=PlanTier.STARTER,
            features={
                "price_searches": FeatureLimit(
                    "price_searches", FeatureCategory.COMPARISON, 500, "Buscas/mês"
                ),
                "social_posts": FeatureLimit(
                    "social_posts", FeatureCategory.SOCIAL_MEDIA, 100, "Posts/mês"
                ),
                "whatsapp_instances": FeatureLimit(
                    "whatsapp_instances", FeatureCategory.WHATSAPP, 3, "WhatsApp"
                ),
            }
        )
    
    @pytest.fixture
    def business_features(self):
        """Features do plano BUSINESS com recursos ilimitados."""
        return PlanFeatures(
            tier=PlanTier.BUSINESS,
            features={
                "price_searches": FeatureLimit(
                    "price_searches", FeatureCategory.COMPARISON, -1, "Ilimitado"
                ),
                "social_posts": FeatureLimit(
                    "social_posts", FeatureCategory.SOCIAL_MEDIA, -1, "Ilimitado"
                ),
            }
        )
    
    def test_get_limit(self, starter_features):
        """Testa obter limite de feature."""
        assert starter_features.get_limit("price_searches") == 500
        assert starter_features.get_limit("social_posts") == 100
        assert starter_features.get_limit("unknown_feature") == 0
    
    def test_can_use_within_limit(self, starter_features):
        """Testa verificação de uso dentro do limite."""
        assert starter_features.can_use("price_searches", 0) is True
        assert starter_features.can_use("price_searches", 499) is True
        assert starter_features.can_use("social_posts", 50) is True
    
    def test_can_use_at_limit(self, starter_features):
        """Testa verificação de uso no limite."""
        assert starter_features.can_use("price_searches", 500) is False
        assert starter_features.can_use("social_posts", 100) is False
    
    def test_can_use_unlimited(self, business_features):
        """Testa uso ilimitado (-1)."""
        assert business_features.can_use("price_searches", 999999) is True
        assert business_features.can_use("social_posts", 1000000) is True
    
    def test_can_use_unknown_feature(self, starter_features):
        """Testa uso de feature não existente (limite 0)."""
        assert starter_features.can_use("unknown_feature", 0) is False
        assert starter_features.can_use("unknown_feature", 1) is False


class TestPLANS:
    """Testes para a constante PLANS."""
    
    def test_plans_has_all_tiers(self):
        """Testa que todos os tiers estão definidos."""
        assert PlanTier.FREE in PLANS
        assert PlanTier.STARTER in PLANS
        assert PlanTier.BUSINESS in PLANS
        assert PlanTier.ENTERPRISE in PLANS
    
    def test_free_plan_structure(self):
        """Testa estrutura do plano FREE."""
        free = PLANS[PlanTier.FREE]
        
        assert free["name"] == "Free"
        assert free["price_monthly"] == Decimal("0")
        assert "features" in free
        assert "highlights" in free
    
    def test_starter_plan_pricing(self):
        """Testa preços do plano STARTER."""
        starter = PLANS[PlanTier.STARTER]
        
        assert starter["price_monthly"] == Decimal("97.00")
        assert starter["price_yearly"] == Decimal("970.00")
        # Desconto anual
        assert starter["price_yearly"] < starter["price_monthly"] * 12
    
    def test_business_plan_features(self):
        """Testa features do plano BUSINESS."""
        business = PLANS[PlanTier.BUSINESS]
        
        # BUSINESS tem tudo ilimitado
        assert business["features"]["price_searches"].limit == -1
        assert business["features"]["social_posts"].limit == -1


class TestSubscription:
    """Testes para modelo Subscription."""
    
    @pytest.fixture
    def active_subscription(self):
        """Subscription ativa."""
        return Subscription(
            id="sub-123",
            user_id="user-123",
            plan=PlanTier.BUSINESS,
            status=SubscriptionStatus.ACTIVE,
            billing_cycle=BillingCycle.MONTHLY,
            created_at=datetime.utcnow() - timedelta(days=15),
            current_period_start=datetime.utcnow() - timedelta(days=15),
            current_period_end=datetime.utcnow() + timedelta(days=15),
        )
    
    @pytest.fixture
    def trial_subscription(self):
        """Subscription em trial."""
        return Subscription(
            id="sub-456",
            user_id="user-456",
            plan=PlanTier.STARTER,
            status=SubscriptionStatus.TRIAL,
            billing_cycle=BillingCycle.MONTHLY,
            created_at=datetime.utcnow(),
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=14),
            trial_ends_at=datetime.utcnow() + timedelta(days=14),
        )
    
    def test_subscription_creation(self, active_subscription):
        """Testa criação de subscription."""
        assert active_subscription.id == "sub-123"
        assert active_subscription.user_id == "user-123"
        assert active_subscription.plan == PlanTier.BUSINESS
        assert active_subscription.status == SubscriptionStatus.ACTIVE
    
    def test_subscription_with_mercadopago(self):
        """Testa subscription com integração MercadoPago."""
        sub = Subscription(
            id="sub-789",
            user_id="user-789",
            plan=PlanTier.STARTER,
            status=SubscriptionStatus.ACTIVE,
            billing_cycle=BillingCycle.MONTHLY,
            created_at=datetime.utcnow(),
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
            mercadopago_subscription_id="MP-SUB-123456",
            last_payment_at=datetime.utcnow(),
            next_payment_at=datetime.utcnow() + timedelta(days=30),
        )
        
        assert sub.mercadopago_subscription_id == "MP-SUB-123456"
    
    def test_subscription_usage_tracking(self, active_subscription):
        """Testa rastreamento de uso na subscription."""
        active_subscription.usage = {
            "price_searches": 45,
            "social_posts": 12,
        }
        
        assert active_subscription.usage["price_searches"] == 45
        assert active_subscription.usage["social_posts"] == 12
    
    def test_subscription_statuses(self):
        """Testa todos os status de subscription."""
        assert SubscriptionStatus.ACTIVE.value == "active"
        assert SubscriptionStatus.TRIAL.value == "trialing"
        assert SubscriptionStatus.PAST_DUE.value == "past_due"
        assert SubscriptionStatus.CANCELED.value == "canceled"
        assert SubscriptionStatus.EXPIRED.value == "expired"


class TestUsageRecord:
    """Testes para modelo UsageRecord."""
    
    def test_usage_record_creation(self):
        """Testa criação de UsageRecord."""
        now = datetime.utcnow()
        record = UsageRecord(
            user_id="user-123",
            feature="price_searches",
            count=50,
            period_start=now - timedelta(days=15),
            period_end=now + timedelta(days=15),
        )
        
        assert record.user_id == "user-123"
        assert record.feature == "price_searches"
        assert record.count == 50
    
    def test_usage_record_multiple_features(self):
        """Testa múltiplos registros de uso."""
        now = datetime.utcnow()
        records = [
            UsageRecord(
                user_id="user-123",
                feature="price_searches",
                count=50,
                period_start=now,
                period_end=now + timedelta(days=30),
            ),
            UsageRecord(
                user_id="user-123",
                feature="social_posts",
                count=25,
                period_start=now,
                period_end=now + timedelta(days=30),
            ),
        ]
        
        assert len(records) == 2
        assert records[0].feature != records[1].feature


class TestSubscriptionService:
    """Testes para SubscriptionService."""
    
    @pytest.fixture
    def service(self):
        """Cria service para testes."""
        return SubscriptionService()
    
    @pytest.fixture
    def mock_redis(self):
        """Mock do Redis."""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.set = AsyncMock(return_value=True)
        redis.incrby = AsyncMock(return_value=1)
        redis.expire = AsyncMock(return_value=True)
        return redis
    
    @pytest.mark.asyncio
    async def test_get_subscription_default_free(self, service, mock_redis):
        """Testa que retorna FREE por padrão."""
        with patch.object(service, '_get_redis', return_value=mock_redis):
            subscription = await service.get_subscription("new-user")
            
            assert subscription.plan == PlanTier.FREE
            assert subscription.status == SubscriptionStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_get_subscription_from_cache(self, service, mock_redis):
        """Testa obter subscription do cache."""
        cached_data = json.dumps({
            "id": "sub-cached",
            "user_id": "user-cached",
            "plan": "starter",
            "status": "active",
            "billing_cycle": "monthly",
            "created_at": datetime.utcnow().isoformat(),
            "current_period_start": datetime.utcnow().isoformat(),
            "current_period_end": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "usage": {},
        })
        mock_redis.get = AsyncMock(return_value=cached_data)
        
        with patch.object(service, '_get_redis', return_value=mock_redis):
            subscription = await service.get_subscription("user-cached")
            
            assert subscription.id == "sub-cached"
            assert subscription.plan == PlanTier.STARTER
    
    @pytest.mark.asyncio
    async def test_get_plan_features(self, service):
        """Testa obter features de um plano."""
        features = await service.get_plan_features(PlanTier.STARTER)
        
        assert features.tier == PlanTier.STARTER
        assert "price_searches" in features.features
        assert "whatsapp_instances" in features.features
    
    @pytest.mark.asyncio
    async def test_get_plan_features_free(self, service):
        """Testa features do plano FREE."""
        features = await service.get_plan_features(PlanTier.FREE)
        
        assert features.tier == PlanTier.FREE
        # FREE tem limites menores
        assert features.get_limit("price_searches") == 50
    
    @pytest.mark.asyncio
    async def test_get_usage(self, service, mock_redis):
        """Testa obter uso atual."""
        mock_redis.get = AsyncMock(return_value="25")
        
        with patch.object(service, '_get_redis', return_value=mock_redis):
            usage = await service.get_usage("user-123", "price_searches")
            
            assert usage == 25
    
    @pytest.mark.asyncio
    async def test_get_usage_no_data(self, service, mock_redis):
        """Testa obter uso quando não há dados."""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch.object(service, '_get_redis', return_value=mock_redis):
            usage = await service.get_usage("user-123", "price_searches")
            
            assert usage == 0
    
    @pytest.mark.asyncio
    async def test_increment_usage(self, service, mock_redis):
        """Testa incrementar uso."""
        mock_redis.incrby = AsyncMock(return_value=26)
        
        with patch.object(service, '_get_redis', return_value=mock_redis):
            new_value = await service.increment_usage("user-123", "price_searches", 1)
            
            assert new_value == 26
            mock_redis.incrby.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_can_use_feature_allowed(self, service, mock_redis):
        """Testa verificação de feature permitida."""
        # Primeira chamada é subscription (None = FREE), segunda é usage
        mock_redis.get = AsyncMock(side_effect=[None, "10"])
        
        with patch.object(service, '_get_redis', return_value=mock_redis):
            can_use = await service.can_use_feature("user-123", "price_searches")
            
            # FREE tem limite de 50, uso é 10
            assert can_use is True
    
    @pytest.mark.asyncio
    async def test_can_use_feature_at_limit(self, service, mock_redis):
        """Testa verificação de feature no limite."""
        # Primeira chamada é subscription (None = FREE), segunda é usage
        mock_redis.get = AsyncMock(side_effect=[None, "50"])
        
        with patch.object(service, '_get_redis', return_value=mock_redis):
            can_use = await service.can_use_feature("user-123", "price_searches")
            
            # FREE tem limite de 50
            assert can_use is False
    
    @pytest.mark.asyncio
    async def test_can_use_feature_with_increment(self, service, mock_redis):
        """Testa verificação com incremento."""
        # Primeira chamada é subscription (None = FREE), segunda é usage
        mock_redis.get = AsyncMock(side_effect=[None, "10"])
        mock_redis.incrby = AsyncMock(return_value=11)
        
        with patch.object(service, '_get_redis', return_value=mock_redis):
            can_use = await service.can_use_feature(
                "user-123", "price_searches", increment=1
            )
            
            assert can_use is True
            mock_redis.incrby.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upgrade_plan(self, service, mock_redis):
        """Testa upgrade de plano."""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch.object(service, '_get_redis', return_value=mock_redis):
            subscription = await service.upgrade_plan(
                "user-123", PlanTier.STARTER, BillingCycle.MONTHLY
            )
            
            assert subscription.plan == PlanTier.STARTER
            assert subscription.billing_cycle == BillingCycle.MONTHLY
    
    @pytest.mark.asyncio
    async def test_upgrade_plan_yearly(self, service, mock_redis):
        """Testa upgrade de plano anual."""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch.object(service, '_get_redis', return_value=mock_redis):
            subscription = await service.upgrade_plan(
                "user-123", PlanTier.BUSINESS, BillingCycle.YEARLY
            )
            
            assert subscription.plan == PlanTier.BUSINESS
            assert subscription.billing_cycle == BillingCycle.YEARLY
            # Período de 365 dias
            days_diff = (subscription.current_period_end - subscription.current_period_start).days
            assert days_diff >= 364  # ~365 dias
    
    @pytest.mark.asyncio
    async def test_cancel_subscription(self, service, mock_redis):
        """Testa cancelamento de subscription."""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch.object(service, '_get_redis', return_value=mock_redis):
            subscription = await service.cancel_subscription("user-123")
            
            assert subscription.status == SubscriptionStatus.CANCELED
            assert subscription.canceled_at is not None
    
    def test_get_price_monthly(self, service):
        """Testa obter preço mensal."""
        price = service.get_price(PlanTier.STARTER, BillingCycle.MONTHLY)
        
        assert price == Decimal("97.00")
    
    def test_get_price_yearly(self, service):
        """Testa obter preço anual."""
        price = service.get_price(PlanTier.STARTER, BillingCycle.YEARLY)
        
        assert price == Decimal("970.00")
    
    def test_get_price_free(self, service):
        """Testa preço do plano FREE."""
        price = service.get_price(PlanTier.FREE, BillingCycle.MONTHLY)
        
        assert price == Decimal("0")
    
    def test_get_plan_info(self, service):
        """Testa obter informações do plano."""
        info = service.get_plan_info(PlanTier.BUSINESS)
        
        assert info["name"] == "Business"
        assert "features" in info
        assert "highlights" in info
    
    def test_list_plans(self, service):
        """Testa listar planos."""
        plans = service.list_plans()
        
        assert len(plans) >= 3
        tiers = [p["tier"] for p in plans]
        assert "free" in tiers
        assert "starter" in tiers
        assert "business" in tiers
    
    def test_list_plans_structure(self, service):
        """Testa estrutura da lista de planos."""
        plans = service.list_plans()
        
        for plan in plans:
            assert "tier" in plan
            assert "name" in plan
            assert "description" in plan
            assert "price_monthly" in plan
            assert "price_yearly" in plan
            assert "highlights" in plan


class TestPricingCalculations:
    """Testes para cálculos de preço."""
    
    @pytest.fixture
    def service(self):
        return SubscriptionService()
    
    def test_yearly_discount_starter(self, service):
        """Testa desconto anual no STARTER."""
        monthly = service.get_price(PlanTier.STARTER, BillingCycle.MONTHLY)
        yearly = service.get_price(PlanTier.STARTER, BillingCycle.YEARLY)
        
        # Anual deve ser menor que 12x mensal
        assert yearly < monthly * 12
        
        # ~2 meses grátis
        discount_months = (monthly * 12 - yearly) / monthly
        assert discount_months >= 1.5  # Pelo menos 1.5 meses de desconto
    
    def test_yearly_discount_business(self, service):
        """Testa desconto anual no BUSINESS."""
        monthly = service.get_price(PlanTier.BUSINESS, BillingCycle.MONTHLY)
        yearly = service.get_price(PlanTier.BUSINESS, BillingCycle.YEARLY)
        
        assert yearly < monthly * 12
    
    def test_price_progression(self, service):
        """Testa progressão de preços entre planos."""
        free = service.get_price(PlanTier.FREE, BillingCycle.MONTHLY)
        starter = service.get_price(PlanTier.STARTER, BillingCycle.MONTHLY)
        business = service.get_price(PlanTier.BUSINESS, BillingCycle.MONTHLY)
        
        assert free == Decimal("0")
        assert starter > free
        assert business > starter


class TestFeatureLimitsPerPlan:
    """Testes para limites de features por plano."""
    
    @pytest.fixture
    def service(self):
        return SubscriptionService()
    
    @pytest.mark.asyncio
    async def test_free_plan_limits(self, service):
        """Testa limites do plano FREE."""
        features = await service.get_plan_features(PlanTier.FREE)
        
        assert features.get_limit("price_searches") == 50
        assert features.get_limit("price_alerts") == 5
        assert features.get_limit("social_posts") == 10
        assert features.get_limit("whatsapp_instances") == 1
        assert features.get_limit("chatbot_flows") == 0  # FREE não tem chatbot
    
    @pytest.mark.asyncio
    async def test_starter_plan_limits(self, service):
        """Testa limites do plano STARTER."""
        features = await service.get_plan_features(PlanTier.STARTER)
        
        assert features.get_limit("price_searches") == 500
        assert features.get_limit("social_posts") == 100
        assert features.get_limit("whatsapp_instances") == 3
        assert features.get_limit("chatbot_flows") == 5
    
    @pytest.mark.asyncio
    async def test_business_plan_unlimited(self, service):
        """Testa recursos ilimitados do plano BUSINESS."""
        features = await service.get_plan_features(PlanTier.BUSINESS)
        
        # -1 significa ilimitado
        assert features.get_limit("price_searches") == -1
        assert features.get_limit("social_posts") == -1
        assert features.get_limit("whatsapp_instances") == -1
        assert features.get_limit("chatbot_flows") == -1
    
    @pytest.mark.asyncio
    async def test_feature_access_progression(self, service):
        """Testa progressão de acesso a features."""
        free = await service.get_plan_features(PlanTier.FREE)
        starter = await service.get_plan_features(PlanTier.STARTER)
        business = await service.get_plan_features(PlanTier.BUSINESS)
        
        # Cada plano deve ter mais que o anterior
        assert free.get_limit("price_searches") < starter.get_limit("price_searches")
        # Business é ilimitado, então só verificar que é diferente
        assert starter.get_limit("price_searches") != business.get_limit("price_searches")


class TestSubscriptionIntegration:
    """Testes de integração do sistema de subscription."""
    
    @pytest.fixture
    def service(self):
        return SubscriptionService()
    
    @pytest.fixture
    def mock_redis(self):
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.set = AsyncMock(return_value=True)
        redis.incrby = AsyncMock(side_effect=lambda k, v: v)
        redis.expire = AsyncMock(return_value=True)
        return redis
    
    @pytest.mark.asyncio
    async def test_new_user_flow(self, service, mock_redis):
        """Testa fluxo de novo usuário."""
        with patch.object(service, '_get_redis', return_value=mock_redis):
            # Novo usuário começa com FREE
            sub = await service.get_subscription("new-user")
            assert sub.plan == PlanTier.FREE
            
            # Pode usar features do FREE
            can_use = await service.can_use_feature("new-user", "price_searches")
            assert can_use is True
    
    @pytest.mark.asyncio
    async def test_upgrade_flow(self, service, mock_redis):
        """Testa fluxo de upgrade."""
        with patch.object(service, '_get_redis', return_value=mock_redis):
            # Upgrade para STARTER
            sub = await service.upgrade_plan("user-123", PlanTier.STARTER)
            
            assert sub.plan == PlanTier.STARTER
            assert sub.status != SubscriptionStatus.CANCELED
    
    @pytest.mark.asyncio
    async def test_cancellation_flow(self, service, mock_redis):
        """Testa fluxo de cancelamento."""
        with patch.object(service, '_get_redis', return_value=mock_redis):
            # Cancelar subscription
            sub = await service.cancel_subscription("user-123")
            
            assert sub.status == SubscriptionStatus.CANCELED
            assert sub.canceled_at is not None
