"""
Subscription Middleware - Feature Gating
=========================================

Middleware de controle de acesso baseado em subscription SaaS Híbrido.

Uso em routes:

    @router.get("/search")
    async def search_products(
        query: str,
        marketplace: str,
        _plan: SubscriptionV2 = Depends(RequiresPlan(PlanTier.FREE)),
        _marketplace: bool = Depends(RequiresMarketplace("marketplace")),
        _feature: bool = Depends(RequiresFeature("price_searches")),
    ):
        # Já validado pelo middleware
        ...

    # Ou usando decorators compostos
    @router.get("/premium-feature")
    @requires_plan(PlanTier.BUSINESS)
    @requires_feature("chatbot_ai")
    async def premium_feature(...):
        ...
"""

import logging
from functools import wraps
from typing import List, Optional, Union

from api.middleware.auth import get_current_user
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from modules.subscription import (PLANS_V2, ExecutionMode, MarketplaceAccess,
                                  PlanTier, SubscriptionService,
                                  SubscriptionV2)

logger = logging.getLogger(__name__)


# ============================================
# DEPENDENCY CLASSES
# ============================================

class RequiresPlan:
    """
    Dependency que verifica plano mínimo.
    
    Exemplo:
        @router.get("/analytics")
        async def get_analytics(
            _: SubscriptionV2 = Depends(RequiresPlan(PlanTier.STARTER))
        ):
            ...
    """
    
    # Ordem dos planos (do menor para o maior)
    PLAN_ORDER = [
        PlanTier.FREE,
        PlanTier.STARTER,
        PlanTier.BUSINESS,
        PlanTier.ENTERPRISE,
    ]
    
    def __init__(self, min_plan: PlanTier):
        self.min_plan = min_plan
        self._service = None
    
    @property
    def service(self) -> SubscriptionService:
        if self._service is None:
            self._service = SubscriptionService()
        return self._service
    
    async def __call__(
        self,
        current_user: dict = Depends(get_current_user)
    ) -> SubscriptionV2:
        user_id = str(current_user["id"])
        subscription = await self.service.get_subscription(user_id)
        
        # Comparar nível do plano
        current_idx = self.PLAN_ORDER.index(subscription.plan)
        required_idx = self.PLAN_ORDER.index(self.min_plan)
        
        if current_idx < required_idx:
            plan_config = PLANS_V2.get(self.min_plan)
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "plan_required",
                    "message": f"Esta funcionalidade requer o plano {plan_config.name} ou superior",
                    "current_plan": subscription.plan.value,
                    "required_plan": self.min_plan.value,
                    "upgrade_url": "/subscription/upgrade",
                }
            )
        
        return subscription


class RequiresMarketplace:
    """
    Dependency que verifica acesso a marketplace.
    
    Pode receber o marketplace como:
    - String literal: RequiresMarketplace("tiktok")
    - Enum: RequiresMarketplace(MarketplaceAccess.TIKTOK)
    - Nome do parâmetro: RequiresMarketplace("marketplace") -> pega do request
    
    Exemplo:
        @router.get("/products/{marketplace}")
        async def get_products(
            marketplace: str,
            _: bool = Depends(RequiresMarketplace("marketplace"))
        ):
            ...
    """
    
    def __init__(
        self,
        marketplace: Union[str, MarketplaceAccess],
        from_param: bool = True
    ):
        self.marketplace = marketplace
        self.from_param = from_param
        self._service = None
    
    @property
    def service(self) -> SubscriptionService:
        if self._service is None:
            self._service = SubscriptionService()
        return self._service
    
    async def __call__(
        self,
        request: Request,
        current_user: dict = Depends(get_current_user)
    ) -> bool:
        user_id = str(current_user["id"])
        
        # Determinar marketplace
        if self.from_param and isinstance(self.marketplace, str):
            # Tentar pegar do path params ou query params
            marketplace_str = (
                request.path_params.get(self.marketplace) or
                request.query_params.get(self.marketplace) or
                self.marketplace
            )
            try:
                marketplace = MarketplaceAccess(marketplace_str)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "invalid_marketplace",
                        "message": f"Marketplace inválido: {marketplace_str}",
                        "valid_marketplaces": [m.value for m in MarketplaceAccess],
                    }
                )
        elif isinstance(self.marketplace, MarketplaceAccess):
            marketplace = self.marketplace
        else:
            marketplace = MarketplaceAccess(self.marketplace)
        
        # Verificar acesso
        has_access = await self.service.has_marketplace_access(user_id, marketplace)
        
        if not has_access:
            subscription = await self.service.get_subscription(user_id)
            accessible = await self.service.get_accessible_marketplaces(user_id)
            
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "marketplace_not_accessible",
                    "message": f"Seu plano não inclui acesso ao {marketplace.value}",
                    "current_plan": subscription.plan.value,
                    "requested_marketplace": marketplace.value,
                    "accessible_marketplaces": [m.value for m in accessible],
                    "upgrade_url": "/subscription/upgrade",
                }
            )
        
        return True


class RequiresFeature:
    """
    Dependency que verifica limite de feature.
    
    Automaticamente incrementa o uso quando a request é bem-sucedida.
    
    Exemplo:
        @router.post("/search")
        async def search(
            _: bool = Depends(RequiresFeature("price_searches"))
        ):
            ...
        
        # Com incremento customizado
        @router.post("/bulk-import")
        async def bulk_import(
            items: List[Item],
            _: bool = Depends(RequiresFeature("crm_leads", increment=len(items)))
        ):
            ...
    """
    
    def __init__(
        self,
        feature: str,
        increment: int = 1,
        auto_increment: bool = True
    ):
        self.feature = feature
        self.increment = increment
        self.auto_increment = auto_increment
        self._service = None
    
    @property
    def service(self) -> SubscriptionService:
        if self._service is None:
            self._service = SubscriptionService()
        return self._service
    
    async def __call__(
        self,
        current_user: dict = Depends(get_current_user)
    ) -> bool:
        user_id = str(current_user["id"])
        
        # Verificar se pode usar (e incrementar se auto_increment)
        increment = self.increment if self.auto_increment else 0
        can_use = await self.service.can_use_feature(
            user_id,
            self.feature,
            increment=increment
        )
        
        if not can_use:
            subscription = await self.service.get_subscription(user_id)
            plan_config = PLANS_V2.get(subscription.plan)
            current_usage = await self.service.get_usage(user_id, self.feature)
            limit = plan_config.limits.get(self.feature, 0)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "feature_limit_exceeded",
                    "message": f"Você atingiu o limite de {self.feature}",
                    "feature": self.feature,
                    "current_usage": current_usage,
                    "limit": limit,
                    "current_plan": subscription.plan.value,
                    "upgrade_url": "/subscription/upgrade",
                }
            )
        
        return True


class RequiresExecutionMode:
    """
    Dependency que verifica modo de execução.
    
    Útil para endpoints que só funcionam em modo híbrido/local.
    
    Exemplo:
        @router.post("/sync")
        async def sync_data(
            _: bool = Depends(RequiresExecutionMode(ExecutionMode.HYBRID))
        ):
            ...
    """
    
    def __init__(self, mode: ExecutionMode):
        self.mode = mode
        self._service = None
    
    @property
    def service(self) -> SubscriptionService:
        if self._service is None:
            self._service = SubscriptionService()
        return self._service
    
    async def __call__(
        self,
        current_user: dict = Depends(get_current_user)
    ) -> bool:
        user_id = str(current_user["id"])
        
        can_use = await self.service.can_use_execution_mode(user_id, self.mode)
        
        if not can_use:
            subscription = await self.service.get_subscription(user_id)
            plan_config = PLANS_V2.get(subscription.plan)
            
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "execution_mode_not_available",
                    "message": f"Seu plano não suporta o modo {self.mode.value}",
                    "current_plan": subscription.plan.value,
                    "requested_mode": self.mode.value,
                    "available_modes": [m.value for m in plan_config.execution_modes],
                    "upgrade_url": "/subscription/upgrade",
                }
            )
        
        return True


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_subscription_service() -> SubscriptionService:
    """Factory para SubscriptionService (injeção de dependência)."""
    return SubscriptionService()


async def get_current_subscription(
    current_user: dict = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service)
) -> SubscriptionV2:
    """
    Dependency que retorna a subscription atual do usuário.
    
    Uso simples quando você só precisa da subscription sem validação.
    """
    user_id = str(current_user["id"])
    return await service.get_subscription(user_id)


async def get_current_user_with_subscription(
    current_user: dict = Depends(get_current_user),
    subscription: SubscriptionV2 = Depends(get_current_subscription)
) -> dict:
    """
    Combina user e subscription em um único objeto.
    
    Útil para ter acesso completo em um único Depends.
    """
    return {
        **current_user,
        "subscription": subscription,
        "plan_config": PLANS_V2.get(subscription.plan),
    }


# ============================================
# COMPOSITE DEPENDENCIES
# ============================================

def requires_plan(min_plan: PlanTier):
    """
    Cria dependency para plano mínimo.
    
    Versão funcional do RequiresPlan para uso mais limpo.
    """
    return Depends(RequiresPlan(min_plan))


def requires_feature(feature: str, increment: int = 1):
    """
    Cria dependency para feature.
    
    Versão funcional do RequiresFeature.
    """
    return Depends(RequiresFeature(feature, increment))


def requires_marketplace(marketplace: Union[str, MarketplaceAccess]):
    """
    Cria dependency para marketplace.
    
    Versão funcional do RequiresMarketplace.
    """
    return Depends(RequiresMarketplace(marketplace))


# ============================================
# CONVENIENCE SHORTCUTS
# ============================================

# Planos pré-definidos
require_starter = Depends(RequiresPlan(PlanTier.STARTER))
require_business = Depends(RequiresPlan(PlanTier.BUSINESS))
require_enterprise = Depends(RequiresPlan(PlanTier.ENTERPRISE))

# Modos de execução
require_hybrid = Depends(RequiresExecutionMode(ExecutionMode.HYBRID))
require_local_first = Depends(RequiresExecutionMode(ExecutionMode.LOCAL_FIRST))


# ============================================
# EXPORTS
# ============================================

__all__ = [
    # Classes
    "RequiresPlan",
    "RequiresMarketplace",
    "RequiresFeature",
    "RequiresExecutionMode",
    
    # Dependencies
    "get_subscription_service",
    "get_current_subscription",
    "get_current_user_with_subscription",
    
    # Factory functions
    "requires_plan",
    "requires_feature",
    "requires_marketplace",
    
    # Shortcuts
    "require_starter",
    "require_business",
    "require_enterprise",
    "require_hybrid",
    "require_local_first",
]
