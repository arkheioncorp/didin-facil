"""
Subscription API Routes - SaaS Híbrido
======================================
Endpoints para gerenciamento de assinaturas e planos.

Modelo: SaaS Híbrido (Local + Cloud)

Endpoints:
- GET /plans - Lista planos disponíveis
- GET /plans/{tier} - Detalhes de um plano
- GET /current - Subscription atual do usuário
- POST /create - Criar nova subscription
- POST /upgrade - Upgrade de plano
- POST /downgrade - Agendar downgrade
- POST /cancel - Cancelar subscription
- GET /usage - Estatísticas de uso
- GET /usage/{feature} - Uso de feature específica
- POST /validate - Validar subscription (para Tauri)
- POST /set-mode - Definir modo de execução
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from api.middleware.auth import get_current_user
from api.middleware.subscription import (RequiresPlan,
                                         get_current_subscription,
                                         get_subscription_service)
from api.services.mercadopago import MercadoPagoService
from fastapi import APIRouter, Depends, HTTPException, Request
from modules.subscription import (PLANS_V2, BillingCycle, ExecutionMode,
                                  MarketplaceAccess, PlanConfig, PlanTier,
                                  SubscriptionService, SubscriptionV2,
                                  UsageStats)
from pydantic import BaseModel
from shared.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


# MercadoPago SDK
try:
    import mercadopago
    sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
    MP_AVAILABLE = True
except (ImportError, Exception):
    sdk = None
    MP_AVAILABLE = False
    logger.warning("MercadoPago SDK não disponível")


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class PlanInfoV2(BaseModel):
    """Informações completas de um plano SaaS."""
    tier: str
    name: str
    description: str
    price_monthly: float
    price_yearly: float
    execution_modes: List[str]
    marketplaces: List[str]
    scraper_priority: str
    limits: Dict[str, int]
    features: Dict[str, bool]
    highlights: List[str]
    offline_days: int


class SubscriptionResponse(BaseModel):
    """Resposta com dados da subscription."""
    id: str
    plan: str
    status: str
    billing_cycle: str
    execution_mode: str
    current_period_start: datetime
    current_period_end: datetime
    marketplaces: List[str]
    limits: Dict[str, int]
    features: Dict[str, bool]


class SubscriptionWithUsageResponse(BaseModel):
    """Subscription + uso atual."""
    subscription: SubscriptionResponse
    plan: PlanInfoV2
    usage: List[Dict[str, Any]]


class UsageStatsResponse(BaseModel):
    """Estatísticas de uso."""
    feature: str
    current: int
    limit: int
    percentage: float
    is_unlimited: bool
    resets_at: datetime


class CreateSubscriptionRequest(BaseModel):
    """Request para criar subscription."""
    plan_tier: str
    billing_cycle: str = "monthly"


class UpgradeRequest(BaseModel):
    """Request para upgrade/downgrade."""
    plan: str
    billing_cycle: Optional[str] = None


class SetExecutionModeRequest(BaseModel):
    """Request para definir modo de execução."""
    mode: str


class ValidateSubscriptionRequest(BaseModel):
    """Request para validar subscription (Tauri)."""
    hwid: str
    app_version: Optional[str] = None


class CheckoutResponse(BaseModel):
    """Resposta do checkout."""
    checkout_url: str
    preference_id: str


# ============================================
# PLANS ENDPOINTS
# ============================================

@router.get("/plans", response_model=List[PlanInfoV2])
async def list_plans(
    service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Lista todos os planos disponíveis.
    
    Retorna informações completas de cada plano incluindo:
    - Modos de execução suportados
    - Marketplaces acessíveis
    - Limites e features
    """
    plans = service.list_plans()
    return [PlanInfoV2(**p) for p in plans]


@router.get("/plans/{plan_tier}", response_model=PlanInfoV2)
async def get_plan_details(
    plan_tier: str,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Obtém detalhes de um plano específico.
    
    Inclui todas as features, limites e modos disponíveis.
    """
    try:
        tier = PlanTier(plan_tier)
    except ValueError:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    
    config = PLANS_V2.get(tier)
    if not config:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    
    return PlanInfoV2(
        tier=tier.value,
        name=config.name,
        description=config.description,
        price_monthly=float(config.price_monthly),
        price_yearly=float(config.price_yearly),
        execution_modes=[m.value for m in config.execution_modes],
        marketplaces=[m.value for m in config.marketplaces],
        scraper_priority=config.scraper_priority.value,
        limits=config.limits,
        features=config.features,
        highlights=config.highlights,
        offline_days=config.offline_days,
    )


# ============================================
# SUBSCRIPTION ENDPOINTS
# ============================================

@router.get("/current", response_model=SubscriptionWithUsageResponse)
async def get_current_subscription_full(
    current_user=Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Obtém subscription atual do usuário com informações do plano e uso.
    
    Retorna:
    - Dados da subscription
    - Configuração do plano
    - Estatísticas de uso de todas as features
    """
    user_id = str(current_user["id"])
    subscription = await service.get_subscription(user_id)
    plan_config = PLANS_V2.get(subscription.plan)
    usage_stats = await service.get_usage_stats(user_id)
    
    return SubscriptionWithUsageResponse(
        subscription=SubscriptionResponse(
            id=subscription.id,
            plan=subscription.plan.value,
            status=subscription.status.value,
            billing_cycle=subscription.billing_cycle.value,
            execution_mode=subscription.execution_mode.value,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            marketplaces=[m.value for m in plan_config.marketplaces],
            limits=plan_config.limits,
            features=plan_config.features,
        ),
        plan=PlanInfoV2(
            tier=plan_config.tier.value,
            name=plan_config.name,
            description=plan_config.description,
            price_monthly=float(plan_config.price_monthly),
            price_yearly=float(plan_config.price_yearly),
            execution_modes=[m.value for m in plan_config.execution_modes],
            marketplaces=[m.value for m in plan_config.marketplaces],
            scraper_priority=plan_config.scraper_priority.value,
            limits=plan_config.limits,
            features=plan_config.features,
            highlights=plan_config.highlights,
            offline_days=plan_config.offline_days,
        ),
        usage=[
            {
                "feature": s.feature,
                "current": s.current,
                "limit": s.limit,
                "percentage": s.percentage,
                "is_unlimited": s.is_unlimited,
                "resets_at": s.resets_at.isoformat(),
            }
            for s in usage_stats
        ]
    )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_my_subscription(
    subscription: SubscriptionV2 = Depends(get_current_subscription),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Obtém assinatura atual do usuário (compatibilidade).
    """
    plan_config = PLANS_V2.get(subscription.plan)
    
    return SubscriptionResponse(
        id=subscription.id,
        plan=subscription.plan.value,
        status=subscription.status.value,
        billing_cycle=subscription.billing_cycle.value,
        execution_mode=subscription.execution_mode.value,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        marketplaces=[m.value for m in plan_config.marketplaces],
        limits=plan_config.limits,
        features=plan_config.features,
    )


# ============================================
# USAGE ENDPOINTS
# ============================================

@router.get("/usage", response_model=List[UsageStatsResponse])
async def get_usage(
    current_user=Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Obtém uso atual de todas as features.
    """
    user_id = str(current_user["id"])
    usage_stats = await service.get_usage_stats(user_id)
    
    return [
        UsageStatsResponse(
            feature=s.feature,
            current=s.current,
            limit=s.limit,
            percentage=s.percentage,
            is_unlimited=s.is_unlimited,
            resets_at=s.resets_at,
        )
        for s in usage_stats
    ]


@router.get("/usage/{feature}")
async def get_feature_usage(
    feature: str,
    current_user=Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Obtém uso de uma feature específica.
    """
    user_id = str(current_user["id"])
    current = await service.get_usage(user_id, feature)
    limit = await service.get_feature_limit(user_id, feature)
    
    is_unlimited = limit == -1
    if is_unlimited:
        percentage = 0.0
    elif limit == 0:
        percentage = 100.0 if current > 0 else 0.0
    else:
        percentage = min(100.0, (current / limit) * 100)
    
    return {
        "feature": feature,
        "current": current,
        "limit": limit,
        "percentage": percentage,
        "is_unlimited": is_unlimited,
        "can_use": is_unlimited or current < limit,
    }


@router.post("/check-feature")
async def check_feature_access(
    feature: str,
    current_user=Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Verifica se usuário pode usar uma feature específica.
    """
    can_use = await service.can_use_feature(
        str(current_user["id"]),
        feature
    )
    
    return {"feature": feature, "can_use": can_use}


# ============================================
# CREATE/UPGRADE ENDPOINTS
# ============================================

@router.post("/create")
async def create_subscription(
    data: CreateSubscriptionRequest,
    current_user=Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Cria nova subscription.
    
    Redireciona para checkout do MercadoPago.
    """
    try:
        plan = PlanTier(data.plan_tier)
        cycle = BillingCycle(data.billing_cycle)
    except ValueError:
        raise HTTPException(status_code=400, detail="Plano ou ciclo inválido")
    
    if plan == PlanTier.FREE:
        raise HTTPException(
            status_code=400,
            detail="Não é possível assinar o plano FREE"
        )
    
    if plan == PlanTier.ENTERPRISE:
        raise HTTPException(
            status_code=400,
            detail="Entre em contato para plano Enterprise"
        )
    
    plan_config = PLANS_V2.get(plan)
    price = (
        plan_config.price_yearly 
        if cycle == BillingCycle.YEARLY 
        else plan_config.price_monthly
    )
    
    user_id = current_user["id"]
    
    # Criar preference no MercadoPago
    mp_service = MercadoPagoService()
    try:
        frequency = 1
        frequency_type = "months"
        if cycle == BillingCycle.YEARLY:
            frequency = 12
            
        response = await mp_service.create_subscription_preference(
            title=f"Didin Fácil - Plano {plan_config.name}",
            price=float(price),
            user_email=current_user.get("email"),
            external_reference=f"{user_id}:{plan.value}:{cycle.value}",
            frequency=frequency,
            frequency_type=frequency_type
        )
        
        return {
            "status": "redirect",
            "checkout_url": response.get("init_point"),
            "preference_id": response.get("id"),
            "plan": plan.value,
            "price": float(price),
        }
        
    except Exception as e:
        logger.error(f"Erro ao criar preference MP: {e}")
    
    # Fallback ou modo desenvolvimento
    subscription = await service.upgrade_plan(
        str(current_user["id"]),
        plan,
        cycle
    )
    
    return {
        "status": "success",
        "message": f"Subscription {plan.value} criada!",
        "subscription": {
            "plan": subscription.plan.value,
            "status": subscription.status.value,
            "current_period_end": subscription.current_period_end.isoformat()
        }
    }


@router.post("/upgrade")
async def upgrade_subscription(
    data: UpgradeRequest,
    current_user=Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Faz upgrade do plano.
    
    Redireciona para checkout do MercadoPago com pro-rata.
    """
    try:
        plan = PlanTier(data.plan)
    except ValueError:
        raise HTTPException(status_code=400, detail="Plano inválido")
    
    user_id = str(current_user["id"])
    current_sub = await service.get_subscription(user_id)
    
    # Verificar se é upgrade válido
    plan_order = [PlanTier.FREE, PlanTier.STARTER, PlanTier.BUSINESS]
    current_idx = plan_order.index(current_sub.plan)
    new_idx = plan_order.index(plan)
    
    if new_idx <= current_idx:
        raise HTTPException(
            status_code=400,
            detail="Use /downgrade para rebaixar o plano"
        )
    
    # Obter ciclo de billing
    cycle = (
        BillingCycle(data.billing_cycle)
        if data.billing_cycle
        else current_sub.billing_cycle
    )
    plan_config = PLANS_V2.get(plan)
    price = (
        plan_config.price_yearly
        if cycle == BillingCycle.YEARLY
        else plan_config.price_monthly
    )
    
    # TODO: Calcular pro-rata baseado no período restante
    
    # Criar checkout MercadoPago
    mp_service = MercadoPagoService()
    try:
        frequency = 1
        frequency_type = "months"
        if cycle == BillingCycle.YEARLY:
            frequency = 12
            
        response = await mp_service.create_subscription_preference(
            title=f"Upgrade para {plan_config.name}",
            price=float(price),
            user_email=current_user.get("email"),
            external_reference=f"{user_id}:{plan.value}:{cycle.value}",
            frequency=frequency,
            frequency_type=frequency_type
        )
        
        return {
            "status": "redirect",
            "checkout_url": response.get("init_point"),
            "preference_id": response.get("id"),
            "from_plan": current_sub.plan.value,
            "to_plan": plan.value,
            "price": float(price),
        }
        
    except Exception as e:
        logger.error(f"Erro ao criar preference MP: {e}")
    
    # Fallback: upgrade direto
    subscription = await service.upgrade_plan(user_id, plan, cycle)
    
    return {
        "status": "success",
        "message": f"Upgrade para {plan.value} realizado!",
        "subscription": {
            "plan": subscription.plan.value,
            "status": subscription.status.value,
            "current_period_end": subscription.current_period_end.isoformat()
        }
    }


@router.post("/downgrade")
async def downgrade_subscription(
    data: UpgradeRequest,
    current_user=Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Agenda downgrade para o final do período atual.
    
    O downgrade só acontece quando o período termina.
    """
    try:
        plan = PlanTier(data.plan)
    except ValueError:
        raise HTTPException(status_code=400, detail="Plano inválido")
    
    user_id = str(current_user["id"])
    current_sub = await service.get_subscription(user_id)
    
    # Verificar se é downgrade válido
    plan_order = [PlanTier.FREE, PlanTier.STARTER, PlanTier.BUSINESS]
    current_idx = plan_order.index(current_sub.plan)
    new_idx = plan_order.index(plan)
    
    if new_idx >= current_idx:
        raise HTTPException(
            status_code=400,
            detail="Use /upgrade para melhorar o plano"
        )
    
    subscription = await service.downgrade_plan(user_id, plan)
    
    return {
        "status": "scheduled",
        "message": f"Downgrade para {plan.value} agendado",
        "current_plan": current_sub.plan.value,
        "new_plan": plan.value,
        "effective_at": subscription.current_period_end.isoformat(),
    }


@router.post("/cancel")
async def cancel_subscription(
    current_user=Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Cancela assinatura.
    
    Mantém acesso até o final do período pago.
    """
    user_id = str(current_user["id"])
    subscription = await service.cancel_subscription(user_id)
    
    return {
        "status": "canceled",
        "message": "Assinatura cancelada",
        "access_until": subscription.current_period_end.isoformat()
    }


# ============================================
# EXECUTION MODE ENDPOINTS
# ============================================

@router.post("/set-mode")
async def set_execution_mode(
    data: SetExecutionModeRequest,
    current_user=Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Define modo de execução (se suportado pelo plano).
    """
    try:
        mode = ExecutionMode(data.mode)
    except ValueError:
        valid_modes = [m.value for m in ExecutionMode]
        raise HTTPException(
            status_code=400,
            detail=f"Modo inválido. Válidos: {valid_modes}"
        )
    
    user_id = str(current_user["id"])
    
    try:
        subscription = await service.set_execution_mode(user_id, mode)
    except ValueError as e:
        raise HTTPException(status_code=402, detail=str(e))
    
    return {
        "status": "success",
        "execution_mode": subscription.execution_mode.value,
    }


@router.get("/execution-mode")
async def get_execution_mode(
    current_user=Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Obtém modo de execução atual.
    """
    user_id = str(current_user["id"])
    mode = await service.get_execution_mode(user_id)
    subscription = await service.get_subscription(user_id)
    plan_config = PLANS_V2.get(subscription.plan)
    
    return {
        "current_mode": mode.value,
        "available_modes": [m.value for m in plan_config.execution_modes],
    }


# ============================================
# VALIDATION ENDPOINT (TAURI)
# ============================================

@router.post("/validate")
async def validate_subscription(
    data: ValidateSubscriptionRequest,
    current_user=Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Valida subscription para app Tauri.
    
    Retorna dados necessários para cache local e operação offline.
    """
    user_id = str(current_user["id"])
    subscription = await service.get_subscription(user_id)
    plan_config = PLANS_V2.get(subscription.plan)
    
    # Verificar status
    if not subscription.is_active() and not subscription.is_in_grace_period():
        return {
            "is_valid": False,
            "reason": "subscription_expired",
            "message": "Sua assinatura expirou. Renove para continuar.",
        }
    
    return {
        "is_valid": True,
        "plan_tier": subscription.plan.value,
        "execution_mode": subscription.execution_mode.value,
        "status": subscription.status.value,
        "marketplaces": [m.value for m in plan_config.marketplaces],
        "limits": plan_config.limits,
        "features": plan_config.features,
        "current_period_end": subscription.current_period_end.isoformat(),
        "offline_days": plan_config.offline_days,
        "grace_period_days": plan_config.grace_period_days,
        "cached_at": datetime.now(timezone.utc).isoformat(),
    }


# ============================================
# WEBHOOK ENDPOINTS
# ============================================

@router.post("/webhooks/mercadopago")
async def mercadopago_webhook(
    payload: Dict[str, Any],
    service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Webhook do MercadoPago para eventos de pagamento.
    
    Eventos:
    - payment.created
    - payment.updated
    - subscription_preapproval.updated
    """
    event_type = payload.get("type")
    data = payload.get("data", {})
    payment_id = data.get("id")
    
    logger.info(f"Webhook MP recebido: {event_type} - ID: {payment_id}")
    
    if not MP_AVAILABLE or not sdk:
        logger.warning("MercadoPago SDK não disponível para processar webhook")
        return {"status": "received", "event": event_type}
    
    try:
        if event_type in ["payment", "payment.created", "payment.updated"]:
            # Buscar detalhes do pagamento
            payment_response = sdk.payment().get(payment_id)
            payment = payment_response.get("response", {})
            
            status = payment.get("status")
            external_ref = payment.get("external_reference", "")
            metadata = payment.get("metadata", {})
            
            # Parse external_reference: "user_id:plan:cycle[:type]"
            parts = external_ref.split(":")
            if len(parts) >= 3:
                user_id = parts[0]
                plan_str = parts[1]
                cycle_str = parts[2]
                operation = parts[3] if len(parts) > 3 else "create"
            else:
                user_id = metadata.get("user_id")
                plan_str = metadata.get("plan")
                cycle_str = metadata.get("billing_cycle", "monthly")
                operation = metadata.get("type", "create")
            
            if status == "approved" and user_id and plan_str:
                # Ativar/atualizar assinatura
                try:
                    plan = PlanTier(plan_str)
                    cycle = BillingCycle(cycle_str)
                    await service.upgrade_plan(user_id, plan, cycle)
                    logger.info(
                        f"Subscription {operation}: {user_id} -> {plan.value}"
                    )
                except Exception as e:
                    logger.error(f"Erro ao processar subscription: {e}")
            
            elif status == "rejected":
                logger.warning(f"Pagamento rejeitado: {payment_id}")
            
            elif status == "pending":
                logger.info(f"Pagamento pendente: {payment_id}")
        
        elif event_type == "subscription_preapproval.updated":
            # Atualizar status de assinatura recorrente
            preapproval_id = data.get("id")
            preapproval_response = sdk.preapproval().get(preapproval_id)
            preapproval = preapproval_response.get("response", {})
            
            status = preapproval.get("status")
            # payer_email = preapproval.get("payer_email")
            
            logger.info(f"Preapproval {preapproval_id}: {status}")
            # TODO: Buscar usuário por email e atualizar status
            
    except Exception as e:
        logger.error(f"Erro ao processar webhook MP: {e}")
    
    return {"status": "received", "event": event_type}
