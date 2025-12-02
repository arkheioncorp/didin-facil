"""
Subscription Plans & Monetization - SaaS Híbrido
================================================
Sistema de planos e monetização do Didin Fácil.

Modelo: SaaS Híbrido (Local + Cloud)

Planos:
- FREE: Funcionalidades básicas gratuitas (Web Only)
- STARTER: R$ 97/mês - Para usuários individuais (Híbrido)
- BUSINESS: R$ 297/mês - Para empresas (Full Access)
- ENTERPRISE: Personalizado (On-premise + Custom)

Modos de Execução:
- WEB_ONLY: Apenas web, scrapers no cloud
- HYBRID: Tauri + Backend API, sync bidirecional
- LOCAL_FIRST: Tauri com cache offline completo

Integração com MercadoPago para pagamentos recorrentes.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ============================================
# ENUMS BASE
# ============================================

class PlanTier(str, Enum):
    """Níveis de plano."""
    FREE = "free"
    STARTER = "starter"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class BillingCycle(str, Enum):
    """Ciclo de cobrança."""
    MONTHLY = "monthly"
    YEARLY = "yearly"
    LIFETIME = "lifetime"  # Deprecado, mantido para compatibilidade


# ============================================
# NOVOS ENUMS - SAAS HÍBRIDO
# ============================================

class ExecutionMode(str, Enum):
    """
    Modo de execução do app.
    
    Determina onde o processamento ocorre e quais recursos estão disponíveis.
    """
    WEB_ONLY = "web_only"       # Apenas web, scrapers no cloud
    HYBRID = "hybrid"           # Tauri + Backend API, sync bidirecional
    LOCAL_FIRST = "local_first" # Tauri com cache offline completo


class MarketplaceAccess(str, Enum):
    """
    Acesso a marketplaces para scraping.
    
    Define quais marketplaces o usuário pode monitorar.
    """
    TIKTOK = "tiktok"
    SHOPEE = "shopee"
    AMAZON = "amazon"
    MERCADO_LIVRE = "mercado_livre"
    HOTMART = "hotmart"
    ALIEXPRESS = "aliexpress"


class ScraperPriority(str, Enum):
    """
    Prioridade no queue de scraping.
    
    Determina a ordem de processamento das requisições.
    """
    LOW = "low"           # FREE - última prioridade
    NORMAL = "normal"     # STARTER - prioridade normal
    HIGH = "high"         # BUSINESS - prioridade alta
    DEDICATED = "dedicated"  # ENTERPRISE - workers dedicados


class FeatureCategory(str, Enum):
    """Categorias de features."""
    COMPARISON = "comparison"      # Comparador de preços
    SOCIAL_MEDIA = "social_media"  # Redes sociais
    WHATSAPP = "whatsapp"          # WhatsApp
    CHATBOT = "chatbot"            # Chatbots
    CRM = "crm"                    # CRM/Leads
    ANALYTICS = "analytics"        # Analytics
    SUPPORT = "support"            # Suporte
    API = "api"                    # Acesso à API
    EXECUTION = "execution"        # Modos de execução


@dataclass
class FeatureLimit:
    """Limite de uma feature."""
    feature: str
    category: FeatureCategory
    limit: int  # -1 = ilimitado
    description: str


# ============================================
# NOVA ESTRUTURA - PLAN CONFIG (SaaS Híbrido)
# ============================================

@dataclass
class PlanConfig:
    """
    Configuração completa de um plano SaaS Híbrido.
    
    Esta estrutura substitui gradualmente o dict PLANS,
    oferecendo tipagem forte e suporte a novos recursos.
    """
    tier: PlanTier
    name: str
    description: str
    price_monthly: Decimal
    price_yearly: Decimal
    
    # Modos de execução permitidos
    execution_modes: List[ExecutionMode] = field(default_factory=list)
    
    # Marketplaces acessíveis
    marketplaces: List[MarketplaceAccess] = field(default_factory=list)
    
    # Prioridade no scraper queue
    scraper_priority: ScraperPriority = ScraperPriority.LOW
    
    # Limites numéricos (-1 = ilimitado)
    limits: Dict[str, int] = field(default_factory=dict)
    
    # Features booleanas (habilitado/desabilitado)
    features: Dict[str, bool] = field(default_factory=dict)
    
    # Destaques para exibição na UI
    highlights: List[str] = field(default_factory=list)
    
    # Dias de grace period após falha de pagamento
    grace_period_days: int = 3
    
    # Dias de funcionamento offline (modo híbrido)
    offline_days: int = 0
    
    def has_marketplace(self, marketplace: MarketplaceAccess) -> bool:
        """Verifica se plano tem acesso a marketplace."""
        return marketplace in self.marketplaces
    
    def has_execution_mode(self, mode: ExecutionMode) -> bool:
        """Verifica se plano suporta modo de execução."""
        return mode in self.execution_modes
    
    def get_limit(self, feature: str) -> int:
        """Retorna limite de uma feature (-1 = ilimitado)."""
        return self.limits.get(feature, 0)
    
    def has_feature(self, feature: str) -> bool:
        """Verifica se feature booleana está habilitada."""
        return self.features.get(feature, False)
    
    def can_use(self, feature: str, current_usage: int = 0) -> bool:
        """Verifica se pode usar uma feature baseado no limite."""
        limit = self.get_limit(feature)
        if limit == -1:
            return True
        return current_usage < limit


# ============================================
# PLANS V2 - NOVA DEFINIÇÃO (SaaS Híbrido)
# ============================================

PLANS_V2: Dict[PlanTier, PlanConfig] = {
    PlanTier.FREE: PlanConfig(
        tier=PlanTier.FREE,
        name="Free",
        description="Perfeito para começar a economizar",
        price_monthly=Decimal("0"),
        price_yearly=Decimal("0"),
        execution_modes=[ExecutionMode.WEB_ONLY],
        marketplaces=[MarketplaceAccess.TIKTOK],
        scraper_priority=ScraperPriority.LOW,
        limits={
            # Comparador
            "price_searches": 50,
            "price_alerts": 5,
            "favorites": 20,
            # Social Media
            "social_posts": 10,
            "social_accounts": 1,
            # WhatsApp
            "whatsapp_instances": 1,
            "whatsapp_messages": 100,
            # Chatbot
            "chatbot_flows": 0,
            # CRM
            "crm_leads": 0,
            # API
            "api_calls": 0,
        },
        features={
            "analytics_basic": True,
            "analytics_advanced": False,
            "analytics_export": False,
            "chatbot_ai": False,
            "crm_automation": False,
            "support_email": True,
            "support_priority": False,
            "support_phone": False,
            "api_access": False,
            "offline_mode": False,
            "hybrid_sync": False,
        },
        highlights=[
            "✓ Comparador de preços",
            "✓ 1 WhatsApp conectado",
            "✓ 10 posts/mês",
            "✓ 5 alertas de preço",
            "✓ TikTok Shop apenas",
            "✗ Chatbot",
            "✗ CRM"
        ],
        grace_period_days=0,
        offline_days=0,
    ),
    
    PlanTier.STARTER: PlanConfig(
        tier=PlanTier.STARTER,
        name="Starter",
        description="Para quem quer vender mais",
        price_monthly=Decimal("97.00"),
        price_yearly=Decimal("970.00"),  # 2 meses grátis
        execution_modes=[ExecutionMode.WEB_ONLY, ExecutionMode.HYBRID],
        marketplaces=[
            MarketplaceAccess.TIKTOK,
            MarketplaceAccess.SHOPEE,
            MarketplaceAccess.MERCADO_LIVRE,
        ],
        scraper_priority=ScraperPriority.NORMAL,
        limits={
            # Comparador
            "price_searches": 500,
            "price_alerts": 50,
            "favorites": 200,
            # Social Media
            "social_posts": 100,
            "social_accounts": 3,
            # WhatsApp
            "whatsapp_instances": 3,
            "whatsapp_messages": 1000,
            # Chatbot
            "chatbot_flows": 5,
            # CRM
            "crm_leads": 500,
            # API
            "api_calls": 1000,
        },
        features={
            "analytics_basic": True,
            "analytics_advanced": True,
            "analytics_export": False,
            "chatbot_ai": False,
            "crm_automation": False,
            "support_email": True,
            "support_priority": False,
            "support_phone": False,
            "api_access": True,
            "offline_mode": True,
            "hybrid_sync": True,
        },
        highlights=[
            "✓ Tudo do Free +",
            "✓ 3 WhatsApp conectados",
            "✓ 100 posts/mês",
            "✓ Chatbot básico (5 fluxos)",
            "✓ CRM com 500 leads",
            "✓ 3 marketplaces",
            "✓ Modo híbrido (Tauri)",
            "✓ Analytics avançado"
        ],
        grace_period_days=3,
        offline_days=3,
    ),
    
    PlanTier.BUSINESS: PlanConfig(
        tier=PlanTier.BUSINESS,
        name="Business",
        description="Para empresas que querem escalar",
        price_monthly=Decimal("297.00"),
        price_yearly=Decimal("2970.00"),  # 2 meses grátis
        execution_modes=[
            ExecutionMode.WEB_ONLY,
            ExecutionMode.HYBRID,
            ExecutionMode.LOCAL_FIRST,
        ],
        marketplaces=[
            MarketplaceAccess.TIKTOK,
            MarketplaceAccess.SHOPEE,
            MarketplaceAccess.AMAZON,
            MarketplaceAccess.MERCADO_LIVRE,
            MarketplaceAccess.HOTMART,
            MarketplaceAccess.ALIEXPRESS,
        ],
        scraper_priority=ScraperPriority.HIGH,
        limits={
            # Comparador - Ilimitado
            "price_searches": -1,
            "price_alerts": -1,
            "favorites": -1,
            # Social Media - Ilimitado
            "social_posts": -1,
            "social_accounts": -1,
            # WhatsApp - Ilimitado
            "whatsapp_instances": -1,
            "whatsapp_messages": -1,
            # Chatbot - Ilimitado
            "chatbot_flows": -1,
            # CRM - Ilimitado
            "crm_leads": -1,
            # API - Ilimitado
            "api_calls": -1,
        },
        features={
            "analytics_basic": True,
            "analytics_advanced": True,
            "analytics_export": True,
            "chatbot_ai": True,
            "crm_automation": True,
            "support_email": True,
            "support_priority": True,
            "support_phone": True,
            "api_access": True,
            "offline_mode": True,
            "hybrid_sync": True,
        },
        highlights=[
            "✓ Tudo do Starter +",
            "✓ TUDO ILIMITADO",
            "✓ Todos os 6 marketplaces",
            "✓ Chatbot com IA",
            "✓ Automação de vendas",
            "✓ Modo local-first",
            "✓ Exportar relatórios",
            "✓ Suporte prioritário + telefone"
        ],
        grace_period_days=7,
        offline_days=7,
    ),
    
    PlanTier.ENTERPRISE: PlanConfig(
        tier=PlanTier.ENTERPRISE,
        name="Enterprise",
        description="Solução personalizada para grandes empresas",
        price_monthly=Decimal("0"),  # Sob consulta
        price_yearly=Decimal("0"),
        execution_modes=[
            ExecutionMode.WEB_ONLY,
            ExecutionMode.HYBRID,
            ExecutionMode.LOCAL_FIRST,
        ],
        marketplaces=[
            MarketplaceAccess.TIKTOK,
            MarketplaceAccess.SHOPEE,
            MarketplaceAccess.AMAZON,
            MarketplaceAccess.MERCADO_LIVRE,
            MarketplaceAccess.HOTMART,
            MarketplaceAccess.ALIEXPRESS,
        ],
        scraper_priority=ScraperPriority.DEDICATED,
        limits={
            # Tudo ilimitado
            "price_searches": -1,
            "price_alerts": -1,
            "favorites": -1,
            "social_posts": -1,
            "social_accounts": -1,
            "whatsapp_instances": -1,
            "whatsapp_messages": -1,
            "chatbot_flows": -1,
            "crm_leads": -1,
            "api_calls": -1,
        },
        features={
            "analytics_basic": True,
            "analytics_advanced": True,
            "analytics_export": True,
            "chatbot_ai": True,
            "crm_automation": True,
            "support_email": True,
            "support_priority": True,
            "support_phone": True,
            "support_dedicated": True,
            "api_access": True,
            "api_dedicated": True,
            "offline_mode": True,
            "hybrid_sync": True,
            "on_premise": True,
            "sla_guaranteed": True,
            "custom_integrations": True,
        },
        highlights=[
            "✓ Tudo do Business +",
            "✓ SLA garantido",
            "✓ Gerente de conta dedicado",
            "✓ Customizações",
            "✓ API dedicada",
            "✓ Treinamento",
            "✓ On-premise disponível"
        ],
        grace_period_days=14,
        offline_days=30,
    ),
}


# ============================================
# LEGACY: PLAN FEATURES (Compatibilidade)
# ============================================

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
# LEGACY: DEFINIÇÃO DOS PLANOS (Compatibilidade)
# ============================================
# DEPRECATED: Use PLANS_V2 para novas funcionalidades.
# Este dict será removido em versões futuras.

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
    TRIALING = "trialing"  # Renomeado de TRIAL para consistência
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"
    
    # Alias para compatibilidade
    TRIAL = "trialing"


class SubscriptionV2(BaseModel):
    """
    Representa uma assinatura no modelo SaaS Híbrido.
    
    Nova estrutura com suporte a:
    - Modos de execução
    - Acesso a marketplaces
    - Grace period
    - Offline mode
    """
    id: str
    user_id: str
    plan: PlanTier
    status: SubscriptionStatus
    billing_cycle: BillingCycle
    execution_mode: ExecutionMode = ExecutionMode.WEB_ONLY
    
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
    
    # Metadata
    metadata: Dict[str, Any] = {}
    
    def is_active(self) -> bool:
        """Verifica se assinatura está ativa."""
        return self.status in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING
        ]
    
    def is_in_grace_period(self) -> bool:
        """Verifica se está em período de graça."""
        if self.status != SubscriptionStatus.PAST_DUE:
            return False
        plan_config = PLANS_V2.get(self.plan)
        if not plan_config:
            return False
        grace_end = self.current_period_end + timedelta(
            days=plan_config.grace_period_days
        )
        return datetime.utcnow() < grace_end
    
    def get_plan_config(self) -> PlanConfig:
        """Retorna configuração do plano."""
        return PLANS_V2.get(self.plan, PLANS_V2[PlanTier.FREE])
    
    class Config:
        use_enum_values = True


# LEGACY: Mantido para compatibilidade
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


class UsageStats(BaseModel):
    """Estatísticas de uso de uma feature."""
    feature: str
    current: int
    limit: int
    percentage: float
    is_unlimited: bool
    resets_at: datetime


# ============================================
# SERVICE
# ============================================

class SubscriptionService:
    """
    Serviço de gerenciamento de assinaturas SaaS Híbrido.
    
    Suporta:
    - Verificação de features por plano
    - Controle de acesso a marketplaces
    - Modos de execução (web, híbrido, local)
    - Metering e usage tracking
    - Grace period para falhas de pagamento
    
    Uso:
        service = SubscriptionService()
        
        # Verificar se pode usar feature
        can_use = await service.can_use_feature(user_id, "social_posts")
        
        # Verificar acesso a marketplace
        has_access = await service.has_marketplace_access(user_id, MarketplaceAccess.SHOPEE)
        
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
    
    async def get_subscription(self, user_id: str) -> Optional[SubscriptionV2]:
        """Obtém assinatura do usuário."""
        redis = await self._get_redis()
        
        # Tentar cache primeiro
        cached = await redis.get(f"subscription:{user_id}")
        if cached:
            import json
            data = json.loads(cached)
            return SubscriptionV2(**data)
        
        # Buscar no banco (implementar com SQLAlchemy)
        # TODO: Implementar query no banco
        
        # Se não encontrar, retornar plano FREE
        return SubscriptionV2(
            id=f"free_{user_id}",
            user_id=user_id,
            plan=PlanTier.FREE,
            status=SubscriptionStatus.ACTIVE,
            billing_cycle=BillingCycle.MONTHLY,
            execution_mode=ExecutionMode.WEB_ONLY,
            created_at=datetime.utcnow(),
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
            usage={}
        )
    
    async def get_subscription_with_plan(
        self,
        user_id: str
    ) -> tuple[SubscriptionV2, PlanConfig]:
        """Obtém assinatura e configuração do plano."""
        subscription = await self.get_subscription(user_id)
        plan_config = PLANS_V2.get(subscription.plan, PLANS_V2[PlanTier.FREE])
        return subscription, plan_config
    
    # ========================================
    # PLAN CONFIG HELPERS (NOVO)
    # ========================================
    
    def get_plan_config(self, plan: PlanTier) -> PlanConfig:
        """Obtém configuração completa do plano (PLANS_V2)."""
        return PLANS_V2.get(plan, PLANS_V2[PlanTier.FREE])
    
    async def get_plan_features(self, plan: PlanTier) -> PlanFeatures:
        """Obtém features de um plano (LEGACY)."""
        plan_data = PLANS.get(plan, PLANS[PlanTier.FREE])
        return PlanFeatures(
            tier=plan,
            features=plan_data.get("features", {})
        )
    
    # ========================================
    # MARKETPLACE ACCESS (NOVO)
    # ========================================
    
    async def has_marketplace_access(
        self,
        user_id: str,
        marketplace: MarketplaceAccess
    ) -> bool:
        """
        Verifica se usuário tem acesso a um marketplace.
        
        Args:
            user_id: ID do usuário
            marketplace: Marketplace a verificar
        
        Returns:
            True se tem acesso
        """
        subscription = await self.get_subscription(user_id)
        plan_config = self.get_plan_config(subscription.plan)
        return plan_config.has_marketplace(marketplace)
    
    async def get_accessible_marketplaces(
        self,
        user_id: str
    ) -> List[MarketplaceAccess]:
        """Retorna lista de marketplaces acessíveis."""
        subscription = await self.get_subscription(user_id)
        plan_config = self.get_plan_config(subscription.plan)
        return plan_config.marketplaces
    
    # ========================================
    # EXECUTION MODE (NOVO)
    # ========================================
    
    async def get_execution_mode(self, user_id: str) -> ExecutionMode:
        """Obtém modo de execução do usuário."""
        subscription = await self.get_subscription(user_id)
        return subscription.execution_mode
    
    async def can_use_execution_mode(
        self,
        user_id: str,
        mode: ExecutionMode
    ) -> bool:
        """Verifica se usuário pode usar um modo de execução."""
        subscription = await self.get_subscription(user_id)
        plan_config = self.get_plan_config(subscription.plan)
        return plan_config.has_execution_mode(mode)
    
    async def set_execution_mode(
        self,
        user_id: str,
        mode: ExecutionMode
    ) -> SubscriptionV2:
        """Define modo de execução (se permitido pelo plano)."""
        subscription = await self.get_subscription(user_id)
        plan_config = self.get_plan_config(subscription.plan)
        
        if not plan_config.has_execution_mode(mode):
            raise ValueError(
                f"Plano {subscription.plan.value} não suporta modo {mode.value}"
            )
        
        subscription.execution_mode = mode
        await self._cache_subscription(subscription)
        
        return subscription
    
    # ========================================
    # FEATURE ACCESS
    # ========================================
    
    async def can_use_feature(
        self,
        user_id: str,
        feature: str,
        increment: int = 0
    ) -> bool:
        """
        Verifica se usuário pode usar uma feature.
        
        Usa PLANS_V2 para limites numéricos e features booleanas.
        
        Args:
            user_id: ID do usuário
            feature: Nome da feature
            increment: Quantidade a incrementar (0 = apenas verificar)
        
        Returns:
            True se pode usar, False se atingiu limite
        """
        subscription = await self.get_subscription(user_id)
        plan_config = self.get_plan_config(subscription.plan)
        
        # Verificar se é feature booleana
        if feature in plan_config.features:
            return plan_config.features[feature]
        
        # Verificar limite numérico
        current_usage = await self.get_usage(user_id, feature)
        
        if not plan_config.can_use(feature, current_usage + increment):
            return False
        
        if increment > 0:
            await self.increment_usage(user_id, feature, increment)
        
        return True
    
    async def get_feature_limit(
        self,
        user_id: str,
        feature: str
    ) -> int:
        """Obtém limite de uma feature (-1 = ilimitado)."""
        subscription = await self.get_subscription(user_id)
        plan_config = self.get_plan_config(subscription.plan)
        return plan_config.get_limit(feature)
    
    # ========================================
    # USAGE TRACKING
    # ========================================
    
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
        plan_config = self.get_plan_config(subscription.plan)
        
        usage = {}
        for feature_name in plan_config.limits.keys():
            usage[feature_name] = await self.get_usage(user_id, feature_name)
        
        return usage
    
    async def get_usage_stats(self, user_id: str) -> List[UsageStats]:
        """
        Obtém estatísticas de uso de todas as features.
        
        Retorna dados formatados para exibição na UI.
        """
        subscription = await self.get_subscription(user_id)
        plan_config = self.get_plan_config(subscription.plan)
        
        # Calcular data de reset (primeiro dia do próximo mês)
        now = datetime.utcnow()
        if now.month == 12:
            resets_at = datetime(now.year + 1, 1, 1)
        else:
            resets_at = datetime(now.year, now.month + 1, 1)
        
        stats = []
        for feature_name, limit in plan_config.limits.items():
            current = await self.get_usage(user_id, feature_name)
            is_unlimited = limit == -1
            
            if is_unlimited:
                percentage = 0.0
            elif limit == 0:
                percentage = 100.0 if current > 0 else 0.0
            else:
                percentage = min(100.0, (current / limit) * 100)
            
            stats.append(UsageStats(
                feature=feature_name,
                current=current,
                limit=limit,
                percentage=percentage,
                is_unlimited=is_unlimited,
                resets_at=resets_at
            ))
        
        return stats
    
    # ========================================
    # PLAN MANAGEMENT
    # ========================================
    
    async def upgrade_plan(
        self,
        user_id: str,
        new_plan: PlanTier,
        billing_cycle: BillingCycle = BillingCycle.MONTHLY
    ) -> SubscriptionV2:
        """
        Faz upgrade do plano do usuário.
        
        Integra com MercadoPago para criar assinatura.
        """
        subscription = await self.get_subscription(user_id)
        new_config = self.get_plan_config(new_plan)
        
        # Atualizar subscription
        subscription.plan = new_plan
        subscription.billing_cycle = billing_cycle
        subscription.current_period_start = datetime.utcnow()
        subscription.status = SubscriptionStatus.ACTIVE
        
        # Definir modo de execução padrão do novo plano
        if new_config.execution_modes:
            subscription.execution_mode = new_config.execution_modes[0]
        
        if billing_cycle == BillingCycle.MONTHLY:
            subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
        else:
            subscription.current_period_end = datetime.utcnow() + timedelta(days=365)
        
        await self._cache_subscription(subscription)
        
        logger.info(f"User {user_id} upgraded to {new_plan.value}")
        return subscription
    
    async def downgrade_plan(
        self,
        user_id: str,
        new_plan: PlanTier
    ) -> SubscriptionV2:
        """
        Agenda downgrade para o final do período.
        
        O downgrade só acontece quando o período atual termina.
        """
        subscription = await self.get_subscription(user_id)
        
        # Marcar downgrade pendente no metadata
        subscription.metadata["pending_downgrade"] = new_plan.value
        subscription.metadata["downgrade_at"] = subscription.current_period_end.isoformat()
        
        await self._cache_subscription(subscription)
        
        logger.info(
            f"User {user_id} scheduled downgrade to {new_plan.value} "
            f"at {subscription.current_period_end}"
        )
        return subscription
    
    async def cancel_subscription(self, user_id: str) -> SubscriptionV2:
        """Cancela assinatura (mantém até o final do período)."""
        subscription = await self.get_subscription(user_id)
        subscription.status = SubscriptionStatus.CANCELED
        subscription.canceled_at = datetime.utcnow()
        
        await self._cache_subscription(subscription)
        
        logger.info(f"User {user_id} canceled subscription")
        return subscription
    
    # ========================================
    # CACHE HELPERS
    # ========================================
    
    async def _cache_subscription(
        self,
        subscription: SubscriptionV2,
        ttl: int = 3600
    ) -> None:
        """Salva subscription no cache Redis."""
        redis = await self._get_redis()
        import json
        await redis.set(
            f"subscription:{subscription.user_id}",
            json.dumps(subscription.dict(), default=str),
            ex=ttl
        )
    
    # ========================================
    # PRICING
    # ========================================
    
    def get_price(
        self,
        plan: PlanTier,
        billing_cycle: BillingCycle
    ) -> Decimal:
        """Obtém preço de um plano."""
        plan_config = self.get_plan_config(plan)
        
        if billing_cycle == BillingCycle.YEARLY:
            return plan_config.price_yearly
        return plan_config.price_monthly
    
    def get_plan_info(self, plan: PlanTier) -> Dict[str, Any]:
        """Obtém informações completas de um plano (LEGACY)."""
        return PLANS.get(plan, PLANS[PlanTier.FREE])
    
    def list_plans(self) -> List[Dict[str, Any]]:
        """Lista todos os planos disponíveis."""
        plans = []
        for tier in [PlanTier.FREE, PlanTier.STARTER, PlanTier.BUSINESS]:
            config = PLANS_V2[tier]
            plans.append({
                "tier": tier.value,
                "name": config.name,
                "description": config.description,
                "price_monthly": float(config.price_monthly),
                "price_yearly": float(config.price_yearly),
                "execution_modes": [m.value for m in config.execution_modes],
                "marketplaces": [m.value for m in config.marketplaces],
                "scraper_priority": config.scraper_priority.value,
                "limits": config.limits,
                "features": config.features,
                "highlights": config.highlights,
                "offline_days": config.offline_days,
            })
        return plans
    
    def list_plans_v2(self) -> List[PlanConfig]:
        """Lista todos os planos como PlanConfig."""
        return [
            PLANS_V2[PlanTier.FREE],
            PLANS_V2[PlanTier.STARTER],
            PLANS_V2[PlanTier.BUSINESS],
        ]
        return plans
