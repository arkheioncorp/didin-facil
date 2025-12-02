"""
Subscription Module - SaaS Híbrido
===================================

Sistema de assinaturas com suporte a:
- Múltiplos modos de execução (web, híbrido, local)
- Acesso granular a marketplaces
- Feature gating e usage metering
- Grace period e offline mode
"""

from .plans import PLANS  # Legacy
from .plans import PLANS_V2  # Novo - SaaS Híbrido
from .plans import (  # Enums; Dataclasses; Models; Service; Plan definitions
    BillingCycle, ExecutionMode, FeatureCategory, FeatureLimit,
    MarketplaceAccess, PlanConfig, PlanFeatures, PlanTier, ScraperPriority,
    Subscription, SubscriptionService, SubscriptionStatus, SubscriptionV2,
    UsageRecord, UsageStats)

__all__ = [
    # Enums
    "PlanTier",
    "BillingCycle",
    "FeatureCategory",
    "ExecutionMode",
    "MarketplaceAccess",
    "ScraperPriority",
    "SubscriptionStatus",
    
    # Dataclasses
    "FeatureLimit",
    "PlanFeatures",
    "PlanConfig",
    
    # Models
    "Subscription",
    "SubscriptionV2",
    "UsageRecord",
    "UsageStats",
    
    # Service
    "SubscriptionService",
    
    # Plan definitions
    "PLANS",
    "PLANS_V2",
]
