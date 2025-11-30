"""
Testes para o módulo de subscription/planos.
"""
import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timedelta
from decimal import Decimal

from modules.subscription.plans import (
    PlanTier,
    FeatureLimit,
    PlanFeatures,
    SubscriptionService,
    Subscription,
    UsageRecord,
)

# Alias para compatibilidade com testes existentes
PlanLimits = FeatureLimit
SubscriptionPlan = PlanFeatures
SubscriptionManager = SubscriptionService
UserSubscription = Subscription
FeatureUsage = UsageRecord


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
        # FREE < STARTER < BUSINESS < ENTERPRISE
        tier_order = [
            PlanTier.FREE,
            PlanTier.STARTER,
            PlanTier.BUSINESS,
            PlanTier.ENTERPRISE,
        ]
        
        for i, tier in enumerate(tier_order[:-1]):
            next_tier = tier_order[i + 1]
            assert tier.value != next_tier.value


class TestPlanLimits:
    """Testes para limites de plano."""
    
    def test_free_plan_limits(self):
        """Testa limites do plano FREE."""
        limits = PlanLimits(
            max_whatsapp_accounts=1,
            max_posts_per_month=10,
            max_leads=100,
            has_chatbot=False,
            has_ai_content=False,
            has_advanced_analytics=False,
            has_api_access=False,
            has_white_label=False,
            support_level="community",
        )
        
        assert limits.max_whatsapp_accounts == 1
        assert limits.max_posts_per_month == 10
        assert limits.has_chatbot is False
    
    def test_enterprise_plan_limits(self):
        """Testa limites do plano ENTERPRISE (ilimitado)."""
        limits = PlanLimits(
            max_whatsapp_accounts=-1,  # -1 = ilimitado
            max_posts_per_month=-1,
            max_leads=-1,
            has_chatbot=True,
            has_ai_content=True,
            has_advanced_analytics=True,
            has_api_access=True,
            has_white_label=True,
            support_level="dedicated",
        )
        
        assert limits.max_whatsapp_accounts == -1
        assert limits.has_white_label is True
        assert limits.support_level == "dedicated"


class TestSubscriptionPlan:
    """Testes para plano de assinatura."""
    
    @pytest.fixture
    def starter_plan(self):
        """Plano STARTER de exemplo."""
        return SubscriptionPlan(
            tier=PlanTier.STARTER,
            name="Starter",
            description="Plano para pequenos negócios",
            price_monthly=Decimal("97.00"),
            price_yearly=Decimal("970.00"),
            limits=PlanLimits(
                max_whatsapp_accounts=3,
                max_posts_per_month=100,
                max_leads=1000,
                has_chatbot=True,
                has_ai_content=False,
                has_advanced_analytics=False,
                has_api_access=False,
                has_white_label=False,
                support_level="email",
            ),
            features=[
                "3 contas WhatsApp",
                "100 posts/mês",
                "1.000 leads",
                "Chatbot básico",
            ],
        )
    
    def test_plan_creation(self, starter_plan):
        """Testa criação de plano."""
        assert starter_plan.tier == PlanTier.STARTER
        assert starter_plan.price_monthly == Decimal("97.00")
        assert len(starter_plan.features) == 4
    
    def test_yearly_discount(self, starter_plan):
        """Testa desconto anual."""
        monthly_total = starter_plan.price_monthly * 12
        yearly_price = starter_plan.price_yearly
        
        # Deve haver desconto
        assert yearly_price < monthly_total
        
        # Calcula desconto
        discount = ((monthly_total - yearly_price) / monthly_total) * 100
        assert discount > 0  # Tem desconto
    
    def test_plan_has_feature(self, starter_plan):
        """Testa verificação de feature."""
        assert starter_plan.limits.has_chatbot is True
        assert starter_plan.limits.has_ai_content is False


class TestSubscriptionManager:
    """Testes para gerenciador de assinaturas."""
    
    @pytest.fixture
    def manager(self):
        """Cria manager para testes."""
        return SubscriptionManager()
    
    @pytest.fixture
    def mock_db(self):
        """Mock do banco de dados."""
        return AsyncMock()
    
    def test_get_all_plans(self, manager):
        """Testa obtenção de todos os planos."""
        plans = manager.get_all_plans()
        
        assert len(plans) >= 3  # Pelo menos FREE, STARTER, BUSINESS
        assert any(p.tier == PlanTier.FREE for p in plans)
    
    def test_get_plan_by_tier(self, manager):
        """Testa obtenção de plano por tier."""
        plan = manager.get_plan(PlanTier.STARTER)
        
        assert plan is not None
        assert plan.tier == PlanTier.STARTER
    
    @pytest.mark.asyncio
    async def test_check_feature_access_allowed(self, manager):
        """Testa acesso a feature permitida."""
        subscription = UserSubscription(
            user_id="user-123",
            plan_tier=PlanTier.BUSINESS,
            status="active",
            started_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        
        # BUSINESS tem chatbot
        has_access = manager.check_feature_access(subscription, "chatbot")
        assert has_access is True
    
    @pytest.mark.asyncio
    async def test_check_feature_access_denied(self, manager):
        """Testa acesso a feature negada."""
        subscription = UserSubscription(
            user_id="user-123",
            plan_tier=PlanTier.FREE,
            status="active",
            started_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        
        # FREE não tem white_label
        has_access = manager.check_feature_access(subscription, "white_label")
        assert has_access is False
    
    @pytest.mark.asyncio
    async def test_check_limit_within_bounds(self, manager):
        """Testa verificação de limite dentro do permitido."""
        usage = FeatureUsage(
            feature="posts",
            current_usage=50,
            max_allowed=100,
        )
        
        within_limit = manager.check_limit(usage)
        assert within_limit is True
    
    @pytest.mark.asyncio
    async def test_check_limit_exceeded(self, manager):
        """Testa verificação de limite excedido."""
        usage = FeatureUsage(
            feature="posts",
            current_usage=100,
            max_allowed=100,
        )
        
        within_limit = manager.check_limit(usage)
        assert within_limit is False
    
    @pytest.mark.asyncio
    async def test_check_unlimited_resource(self, manager):
        """Testa verificação de recurso ilimitado."""
        usage = FeatureUsage(
            feature="posts",
            current_usage=999999,
            max_allowed=-1,  # Ilimitado
        )
        
        within_limit = manager.check_limit(usage)
        assert within_limit is True
    
    def test_compare_plans(self, manager):
        """Testa comparação entre planos."""
        free_plan = manager.get_plan(PlanTier.FREE)
        starter_plan = manager.get_plan(PlanTier.STARTER)
        
        comparison = manager.compare_plans(free_plan, starter_plan)
        
        assert "upgrades" in comparison
        assert len(comparison["upgrades"]) > 0
    
    def test_calculate_upgrade_price(self, manager):
        """Testa cálculo de preço de upgrade."""
        # Upgrade de FREE para STARTER
        price = manager.calculate_upgrade_price(
            current_tier=PlanTier.FREE,
            target_tier=PlanTier.STARTER,
            billing_cycle="monthly",
        )
        
        starter_plan = manager.get_plan(PlanTier.STARTER)
        assert price == starter_plan.price_monthly
    
    def test_calculate_prorated_upgrade(self, manager):
        """Testa cálculo de upgrade pro-rata."""
        # Usuário no meio do ciclo
        days_remaining = 15
        days_in_cycle = 30
        
        price = manager.calculate_prorated_upgrade(
            current_tier=PlanTier.STARTER,
            target_tier=PlanTier.BUSINESS,
            days_remaining=days_remaining,
            days_in_cycle=days_in_cycle,
        )
        
        # Deve ser proporcional
        assert price > 0
        
        business_plan = manager.get_plan(PlanTier.BUSINESS)
        starter_plan = manager.get_plan(PlanTier.STARTER)
        
        # Diferença de preço
        diff = business_plan.price_monthly - starter_plan.price_monthly
        prorated = diff * (days_remaining / days_in_cycle)
        
        assert abs(price - prorated) < Decimal("0.01")


class TestUserSubscription:
    """Testes para assinatura do usuário."""
    
    @pytest.fixture
    def active_subscription(self):
        """Assinatura ativa."""
        return UserSubscription(
            user_id="user-123",
            plan_tier=PlanTier.BUSINESS,
            status="active",
            started_at=datetime.utcnow() - timedelta(days=15),
            expires_at=datetime.utcnow() + timedelta(days=15),
            payment_method="credit_card",
            auto_renew=True,
        )
    
    @pytest.fixture
    def expired_subscription(self):
        """Assinatura expirada."""
        return UserSubscription(
            user_id="user-456",
            plan_tier=PlanTier.STARTER,
            status="expired",
            started_at=datetime.utcnow() - timedelta(days=45),
            expires_at=datetime.utcnow() - timedelta(days=15),
            payment_method="pix",
            auto_renew=False,
        )
    
    def test_subscription_is_active(self, active_subscription):
        """Testa verificação de assinatura ativa."""
        assert active_subscription.is_active() is True
    
    def test_subscription_is_expired(self, expired_subscription):
        """Testa verificação de assinatura expirada."""
        assert expired_subscription.is_active() is False
    
    def test_days_until_expiration(self, active_subscription):
        """Testa cálculo de dias até expiração."""
        days = active_subscription.days_until_expiration()
        
        assert days > 0
        assert days <= 15
    
    def test_days_until_expiration_expired(self, expired_subscription):
        """Testa dias até expiração para assinatura expirada."""
        days = expired_subscription.days_until_expiration()
        
        assert days < 0
    
    def test_subscription_needs_renewal(self, active_subscription, expired_subscription):
        """Testa verificação de necessidade de renovação."""
        # Com auto_renew = True e expirando em breve
        active_subscription.expires_at = datetime.utcnow() + timedelta(days=3)
        assert active_subscription.needs_renewal_reminder() is True
        
        # Já expirada
        assert expired_subscription.needs_renewal_reminder() is True


class TestFeatureUsage:
    """Testes para uso de features."""
    
    def test_usage_percentage(self):
        """Testa cálculo de porcentagem de uso."""
        usage = FeatureUsage(
            feature="posts",
            current_usage=50,
            max_allowed=100,
        )
        
        assert usage.usage_percentage() == 50.0
    
    def test_usage_percentage_exceeded(self):
        """Testa porcentagem quando excedido."""
        usage = FeatureUsage(
            feature="posts",
            current_usage=150,
            max_allowed=100,
        )
        
        assert usage.usage_percentage() == 150.0
    
    def test_remaining_usage(self):
        """Testa cálculo de uso restante."""
        usage = FeatureUsage(
            feature="leads",
            current_usage=700,
            max_allowed=1000,
        )
        
        assert usage.remaining() == 300
    
    def test_remaining_unlimited(self):
        """Testa uso restante para recurso ilimitado."""
        usage = FeatureUsage(
            feature="posts",
            current_usage=5000,
            max_allowed=-1,
        )
        
        assert usage.remaining() == float('inf')
    
    def test_is_near_limit(self):
        """Testa detecção de proximidade do limite."""
        usage = FeatureUsage(
            feature="leads",
            current_usage=850,
            max_allowed=1000,
        )
        
        # 85% - perto do limite (threshold padrão 80%)
        assert usage.is_near_limit() is True
    
    def test_is_not_near_limit(self):
        """Testa quando não está perto do limite."""
        usage = FeatureUsage(
            feature="leads",
            current_usage=500,
            max_allowed=1000,
        )
        
        assert usage.is_near_limit() is False


class TestBillingCalculations:
    """Testes para cálculos de billing."""
    
    @pytest.fixture
    def manager(self):
        return SubscriptionManager()
    
    def test_monthly_billing(self, manager):
        """Testa billing mensal."""
        plan = manager.get_plan(PlanTier.STARTER)
        
        total = manager.calculate_billing(
            plan=plan,
            billing_cycle="monthly",
            months=1,
        )
        
        assert total == plan.price_monthly
    
    def test_yearly_billing_with_discount(self, manager):
        """Testa billing anual com desconto."""
        plan = manager.get_plan(PlanTier.BUSINESS)
        
        total = manager.calculate_billing(
            plan=plan,
            billing_cycle="yearly",
            months=12,
        )
        
        # Anual deve ser menor que 12x mensal
        monthly_total = plan.price_monthly * 12
        assert total < monthly_total
    
    def test_trial_period(self, manager):
        """Testa período de trial."""
        trial = manager.create_trial(
            user_id="user-new",
            plan_tier=PlanTier.BUSINESS,
            trial_days=14,
        )
        
        assert trial.status == "trial"
        assert trial.plan_tier == PlanTier.BUSINESS
        
        # Trial expira em 14 dias
        days = trial.days_until_expiration()
        assert 13 <= days <= 14
