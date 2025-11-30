"""
Subscription Plans & Monetization
=================================
Sistema de planos e monetização do Didin Fácil.

Planos:
- FREE: Funcionalidades básicas gratuitas
- STARTER: R$ 97/mês - Para usuários individuais
- BUSINESS: R$ 297/mês - Para empresas

Integração com MercadoPago para pagamentos recorrentes.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from decimal import Decimal
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class PlanTier(str, Enum):
    """Níveis de plano."""
    FREE = "free"
    STARTER = "starter"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"  # Personalizado


class BillingCycle(str, Enum):
    """Ciclo de cobrança."""
    MONTHLY = "monthly"
    YEARLY = "yearly"
    LIFETIME = "lifetime"


class FeatureCategory(str, Enum):
    """Categorias de features."""
    COMPARISON = "comparison"      # Comparador de preços
    SOCIAL_MEDIA = "social_media"  # Redes sociais
    WHATSAPP = "whatsapp"          # WhatsApp
    CHATBOT = "chatbot"            # Chatbots
    CRM = "crm"                    # CRM/Leads
    ANALYTICS = "analytics"        # Analytics
    SUPPORT = "support"            # Suporte


@dataclass
class FeatureLimit:
    """Limite de uma feature."""
    feature: str
    category: FeatureCategory
    limit: int  # -1 = ilimitado
    description: str


@dataclass
class PlanFeatures:
    """Features de um plano."""
    tier: PlanTier
    features: Dict[str, FeatureLimit] = field(default_factory=dict)
    
    def get_limit(self, feature: str) -> int:
        """Retorna limite de uma feature (-1 = ilimitado)."""
        if feature in self.features:
            return self.features[feature].limit
        return 0
    
    def can_use(self, feature: str, current_usage: int = 0) -> bool:
        """Verifica se pode usar uma feature."""
        limit = self.get_limit(feature)
        if limit == -1:
            return True
        return current_usage < limit


# ============================================
# DEFINIÇÃO DOS PLANOS
# ============================================

PLANS: Dict[PlanTier, Dict[str, Any]] = {
    PlanTier.FREE: {
        "name": "Free",
        "description": "Perfeito para começar a economizar",
        "price_monthly": Decimal("0"),
        "price_yearly": Decimal("0"),
        "features": {
            # Comparador
            "price_searches": FeatureLimit("price_searches", FeatureCategory.COMPARISON, 50, "Buscas de preço/mês"),
            "price_alerts": FeatureLimit("price_alerts", FeatureCategory.COMPARISON, 5, "Alertas de preço ativos"),
            "favorites": FeatureLimit("favorites", FeatureCategory.COMPARISON, 20, "Produtos favoritos"),
            
            # Social Media
            "social_posts": FeatureLimit("social_posts", FeatureCategory.SOCIAL_MEDIA, 10, "Posts agendados/mês"),
            "social_accounts": FeatureLimit("social_accounts", FeatureCategory.SOCIAL_MEDIA, 1, "Contas conectadas"),
            
            # WhatsApp
            "whatsapp_instances": FeatureLimit("whatsapp_instances", FeatureCategory.WHATSAPP, 1, "Instâncias WhatsApp"),
            "whatsapp_messages": FeatureLimit("whatsapp_messages", FeatureCategory.WHATSAPP, 100, "Mensagens/mês"),
            
            # Chatbot
            "chatbot_flows": FeatureLimit("chatbot_flows", FeatureCategory.CHATBOT, 0, "Fluxos de chatbot"),
            
            # CRM
            "crm_leads": FeatureLimit("crm_leads", FeatureCategory.CRM, 0, "Leads no CRM"),
            
            # Analytics
            "analytics_basic": FeatureLimit("analytics_basic", FeatureCategory.ANALYTICS, 1, "Analytics básico"),
            "analytics_advanced": FeatureLimit("analytics_advanced", FeatureCategory.ANALYTICS, 0, "Analytics avançado"),
            
            # Suporte
            "support_email": FeatureLimit("support_email", FeatureCategory.SUPPORT, 1, "Suporte por email"),
            "support_priority": FeatureLimit("support_priority", FeatureCategory.SUPPORT, 0, "Suporte prioritário"),
        },
        "highlights": [
            "✓ Comparador de preços",
            "✓ 1 WhatsApp conectado",
            "✓ 10 posts/mês",
            "✓ 5 alertas de preço",
            "✗ Chatbot",
            "✗ CRM"
        ]
    },
    
    PlanTier.STARTER: {
        "name": "Starter",
        "description": "Para quem quer vender mais",
        "price_monthly": Decimal("97.00"),
        "price_yearly": Decimal("970.00"),  # 2 meses grátis
        "features": {
            # Comparador
            "price_searches": FeatureLimit("price_searches", FeatureCategory.COMPARISON, 500, "Buscas de preço/mês"),
            "price_alerts": FeatureLimit("price_alerts", FeatureCategory.COMPARISON, 50, "Alertas de preço ativos"),
            "favorites": FeatureLimit("favorites", FeatureCategory.COMPARISON, 200, "Produtos favoritos"),
            
            # Social Media
            "social_posts": FeatureLimit("social_posts", FeatureCategory.SOCIAL_MEDIA, 100, "Posts agendados/mês"),
            "social_accounts": FeatureLimit("social_accounts", FeatureCategory.SOCIAL_MEDIA, 3, "Contas conectadas"),
            
            # WhatsApp
            "whatsapp_instances": FeatureLimit("whatsapp_instances", FeatureCategory.WHATSAPP, 3, "Instâncias WhatsApp"),
            "whatsapp_messages": FeatureLimit("whatsapp_messages", FeatureCategory.WHATSAPP, 1000, "Mensagens/mês"),
            
            # Chatbot
            "chatbot_flows": FeatureLimit("chatbot_flows", FeatureCategory.CHATBOT, 5, "Fluxos de chatbot"),
            
            # CRM
            "crm_leads": FeatureLimit("crm_leads", FeatureCategory.CRM, 500, "Leads no CRM"),
            
            # Analytics
            "analytics_basic": FeatureLimit("analytics_basic", FeatureCategory.ANALYTICS, 1, "Analytics básico"),
            "analytics_advanced": FeatureLimit("analytics_advanced", FeatureCategory.ANALYTICS, 1, "Analytics avançado"),
            
            # Suporte
            "support_email": FeatureLimit("support_email", FeatureCategory.SUPPORT, 1, "Suporte por email"),
            "support_priority": FeatureLimit("support_priority", FeatureCategory.SUPPORT, 0, "Suporte prioritário"),
        },
        "highlights": [
            "✓ Tudo do Free +",
            "✓ 3 WhatsApp conectados",
            "✓ 100 posts/mês",
            "✓ Chatbot básico",
            "✓ CRM com 500 leads",
            "✓ Analytics avançado"
        ]
    },
    
    PlanTier.BUSINESS: {
        "name": "Business",
        "description": "Para empresas que querem escalar",
        "price_monthly": Decimal("297.00"),
        "price_yearly": Decimal("2970.00"),  # 2 meses grátis
        "features": {
            # Comparador
            "price_searches": FeatureLimit("price_searches", FeatureCategory.COMPARISON, -1, "Buscas ilimitadas"),
            "price_alerts": FeatureLimit("price_alerts", FeatureCategory.COMPARISON, -1, "Alertas ilimitados"),
            "favorites": FeatureLimit("favorites", FeatureCategory.COMPARISON, -1, "Favoritos ilimitados"),
            
            # Social Media
            "social_posts": FeatureLimit("social_posts", FeatureCategory.SOCIAL_MEDIA, -1, "Posts ilimitados"),
            "social_accounts": FeatureLimit("social_accounts", FeatureCategory.SOCIAL_MEDIA, -1, "Contas ilimitadas"),
            
            # WhatsApp
            "whatsapp_instances": FeatureLimit("whatsapp_instances", FeatureCategory.WHATSAPP, -1, "WhatsApp ilimitado"),
            "whatsapp_messages": FeatureLimit("whatsapp_messages", FeatureCategory.WHATSAPP, -1, "Mensagens ilimitadas"),
            
            # Chatbot
            "chatbot_flows": FeatureLimit("chatbot_flows", FeatureCategory.CHATBOT, -1, "Fluxos ilimitados"),
            "chatbot_ai": FeatureLimit("chatbot_ai", FeatureCategory.CHATBOT, 1, "Chatbot com IA"),
            
            # CRM
            "crm_leads": FeatureLimit("crm_leads", FeatureCategory.CRM, -1, "Leads ilimitados"),
            "crm_automation": FeatureLimit("crm_automation", FeatureCategory.CRM, 1, "Automação de vendas"),
            
            # Analytics
            "analytics_basic": FeatureLimit("analytics_basic", FeatureCategory.ANALYTICS, 1, "Analytics básico"),
            "analytics_advanced": FeatureLimit("analytics_advanced", FeatureCategory.ANALYTICS, 1, "Analytics avançado"),
            "analytics_export": FeatureLimit("analytics_export", FeatureCategory.ANALYTICS, 1, "Exportar relatórios"),
            
            # Suporte
            "support_email": FeatureLimit("support_email", FeatureCategory.SUPPORT, 1, "Suporte por email"),
            "support_priority": FeatureLimit("support_priority", FeatureCategory.SUPPORT, 1, "Suporte prioritário"),
            "support_phone": FeatureLimit("support_phone", FeatureCategory.SUPPORT, 1, "Suporte por telefone"),
        },
        "highlights": [
            "✓ Tudo do Starter +",
            "✓ TUDO ILIMITADO",
            "✓ Chatbot com IA",
            "✓ Automação de vendas",
            "✓ Exportar relatórios",
            "✓ Suporte prioritário"
        ]
    },
    
    PlanTier.ENTERPRISE: {
        "name": "Enterprise",
        "description": "Solução personalizada para grandes empresas",
        "price_monthly": Decimal("0"),  # Sob consulta
        "price_yearly": Decimal("0"),
        "features": {},  # Personalizado
        "highlights": [
            "✓ Tudo do Business +",
            "✓ SLA garantido",
            "✓ Gerente de conta dedicado",
            "✓ Customizações",
            "✓ API dedicada",
            "✓ Treinamento"
        ]
    }
}


# ============================================
# MODELS
# ============================================

class SubscriptionStatus(str, Enum):
    """Status da assinatura."""
    ACTIVE = "active"
    TRIAL = "trial"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"


class Subscription(BaseModel):
    """Representa uma assinatura."""
    id: str
    user_id: str
    plan: PlanTier
    status: SubscriptionStatus
    billing_cycle: BillingCycle
    
    # Datas
    created_at: datetime
    current_period_start: datetime
    current_period_end: datetime
    canceled_at: Optional[datetime] = None
    
    # Pagamento
    mercadopago_subscription_id: Optional[str] = None
    last_payment_at: Optional[datetime] = None
    next_payment_at: Optional[datetime] = None
    
    # Trial
    trial_ends_at: Optional[datetime] = None
    
    # Uso
    usage: Dict[str, int] = {}


class UsageRecord(BaseModel):
    """Registro de uso de feature."""
    user_id: str
    feature: str
    count: int
    period_start: datetime
    period_end: datetime


# ============================================
# SERVICE
# ============================================

class SubscriptionService:
    """
    Serviço de gerenciamento de assinaturas.
    
    Uso:
        service = SubscriptionService()
        
        # Verificar se pode usar feature
        can_use = await service.can_use_feature(user_id, "social_posts")
        
        # Criar assinatura
        subscription = await service.create_subscription(
            user_id, PlanTier.STARTER, BillingCycle.MONTHLY
        )
    """
    
    def __init__(self):
        self._redis = None
        self._db = None
    
    async def _get_redis(self):
        if self._redis is None:
            from shared.redis import get_redis
            self._redis = await get_redis()
        return self._redis
    
    # ========================================
    # SUBSCRIPTION MANAGEMENT
    # ========================================
    
    async def get_subscription(self, user_id: str) -> Optional[Subscription]:
        """Obtém assinatura do usuário."""
        redis = await self._get_redis()
        
        # Tentar cache primeiro
        cached = await redis.get(f"subscription:{user_id}")
        if cached:
            import json
            return Subscription(**json.loads(cached))
        
        # Buscar no banco (implementar com SQLAlchemy)
        # TODO: Implementar query no banco
        
        # Se não encontrar, retornar plano FREE
        return Subscription(
            id=f"free_{user_id}",
            user_id=user_id,
            plan=PlanTier.FREE,
            status=SubscriptionStatus.ACTIVE,
            billing_cycle=BillingCycle.MONTHLY,
            created_at=datetime.utcnow(),
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
            usage={}
        )
    
    async def get_plan_features(self, plan: PlanTier) -> PlanFeatures:
        """Obtém features de um plano."""
        plan_data = PLANS.get(plan, PLANS[PlanTier.FREE])
        return PlanFeatures(
            tier=plan,
            features=plan_data.get("features", {})
        )
    
    async def can_use_feature(
        self,
        user_id: str,
        feature: str,
        increment: int = 0
    ) -> bool:
        """
        Verifica se usuário pode usar uma feature.
        
        Args:
            user_id: ID do usuário
            feature: Nome da feature
            increment: Quantidade a incrementar (0 = apenas verificar)
        
        Returns:
            True se pode usar, False se atingiu limite
        """
        subscription = await self.get_subscription(user_id)
        plan_features = await self.get_plan_features(subscription.plan)
        
        current_usage = await self.get_usage(user_id, feature)
        
        if not plan_features.can_use(feature, current_usage + increment):
            return False
        
        if increment > 0:
            await self.increment_usage(user_id, feature, increment)
        
        return True
    
    async def get_usage(self, user_id: str, feature: str) -> int:
        """Obtém uso atual de uma feature."""
        redis = await self._get_redis()
        
        # Key com período mensal
        now = datetime.utcnow()
        key = f"usage:{user_id}:{feature}:{now.year}:{now.month}"
        
        usage = await redis.get(key)
        return int(usage) if usage else 0
    
    async def increment_usage(
        self,
        user_id: str,
        feature: str,
        amount: int = 1
    ) -> int:
        """Incrementa uso de uma feature."""
        redis = await self._get_redis()
        
        now = datetime.utcnow()
        key = f"usage:{user_id}:{feature}:{now.year}:{now.month}"
        
        new_value = await redis.incrby(key, amount)
        
        # Expirar no final do mês
        days_until_end = 32 - now.day
        await redis.expire(key, days_until_end * 24 * 60 * 60)
        
        return new_value
    
    async def get_all_usage(self, user_id: str) -> Dict[str, int]:
        """Obtém uso de todas as features."""
        subscription = await self.get_subscription(user_id)
        plan_features = await self.get_plan_features(subscription.plan)
        
        usage = {}
        for feature_name in plan_features.features.keys():
            usage[feature_name] = await self.get_usage(user_id, feature_name)
        
        return usage
    
    # ========================================
    # PLAN MANAGEMENT
    # ========================================
    
    async def upgrade_plan(
        self,
        user_id: str,
        new_plan: PlanTier,
        billing_cycle: BillingCycle = BillingCycle.MONTHLY
    ) -> Subscription:
        """
        Faz upgrade do plano do usuário.
        
        Integra com MercadoPago para criar assinatura.
        """
        # TODO: Implementar integração com MercadoPago
        # 1. Criar assinatura no MercadoPago
        # 2. Salvar no banco
        # 3. Atualizar cache
        
        subscription = await self.get_subscription(user_id)
        subscription.plan = new_plan
        subscription.billing_cycle = billing_cycle
        subscription.current_period_start = datetime.utcnow()
        
        if billing_cycle == BillingCycle.MONTHLY:
            subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
        else:
            subscription.current_period_end = datetime.utcnow() + timedelta(days=365)
        
        # Salvar no cache
        redis = await self._get_redis()
        import json
        await redis.set(
            f"subscription:{user_id}",
            json.dumps(subscription.dict(), default=str),
            ex=3600
        )
        
        logger.info(f"User {user_id} upgraded to {new_plan.value}")
        return subscription
    
    async def cancel_subscription(self, user_id: str) -> Subscription:
        """Cancela assinatura (mantém até o final do período)."""
        subscription = await self.get_subscription(user_id)
        subscription.status = SubscriptionStatus.CANCELED
        subscription.canceled_at = datetime.utcnow()
        
        # TODO: Cancelar no MercadoPago
        
        logger.info(f"User {user_id} canceled subscription")
        return subscription
    
    # ========================================
    # PRICING
    # ========================================
    
    def get_price(
        self,
        plan: PlanTier,
        billing_cycle: BillingCycle
    ) -> Decimal:
        """Obtém preço de um plano."""
        plan_data = PLANS.get(plan)
        if not plan_data:
            return Decimal("0")
        
        if billing_cycle == BillingCycle.YEARLY:
            return plan_data["price_yearly"]
        return plan_data["price_monthly"]
    
    def get_plan_info(self, plan: PlanTier) -> Dict[str, Any]:
        """Obtém informações completas de um plano."""
        return PLANS.get(plan, PLANS[PlanTier.FREE])
    
    def list_plans(self) -> List[Dict[str, Any]]:
        """Lista todos os planos disponíveis."""
        plans = []
        for tier in [PlanTier.FREE, PlanTier.STARTER, PlanTier.BUSINESS]:
            plan_data = PLANS[tier]
            plans.append({
                "tier": tier.value,
                "name": plan_data["name"],
                "description": plan_data["description"],
                "price_monthly": float(plan_data["price_monthly"]),
                "price_yearly": float(plan_data["price_yearly"]),
                "highlights": plan_data["highlights"]
            })
        return plans
