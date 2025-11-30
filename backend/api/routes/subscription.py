"""
Subscription API Routes
=======================
Endpoints para gerenciamento de assinaturas e planos.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

from api.middleware.auth import get_current_user
from modules.subscription.plans import (
    SubscriptionService,
    PlanTier,
    BillingCycle
)

router = APIRouter()
subscription_service = SubscriptionService()


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class PlanInfo(BaseModel):
    tier: str
    name: str
    description: str
    price_monthly: float
    price_yearly: float
    highlights: List[str]


class SubscriptionResponse(BaseModel):
    id: str
    plan: str
    status: str
    billing_cycle: str
    current_period_start: datetime
    current_period_end: datetime
    usage: Dict[str, int]


class UsageResponse(BaseModel):
    feature: str
    current: int
    limit: int
    remaining: int
    can_use: bool


class UpgradeRequest(BaseModel):
    plan: str
    billing_cycle: str = "monthly"


class CheckoutResponse(BaseModel):
    checkout_url: str
    preference_id: str


# ============================================
# PLANS ENDPOINTS
# ============================================

@router.get("/plans", response_model=List[PlanInfo])
async def list_plans():
    """
    Lista todos os planos disponíveis.
    
    Retorna informações de preço e features de cada plano.
    """
    return subscription_service.list_plans()


@router.get("/plans/{plan_tier}")
async def get_plan_details(plan_tier: str):
    """
    Obtém detalhes de um plano específico.
    
    Inclui todas as features e limites.
    """
    try:
        tier = PlanTier(plan_tier)
    except ValueError:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    
    plan_info = subscription_service.get_plan_info(tier)
    features = await subscription_service.get_plan_features(tier)
    
    return {
        "tier": tier.value,
        "name": plan_info["name"],
        "description": plan_info["description"],
        "price_monthly": float(plan_info["price_monthly"]),
        "price_yearly": float(plan_info["price_yearly"]),
        "highlights": plan_info["highlights"],
        "features": {
            name: {
                "description": feat.description,
                "limit": feat.limit,
                "unlimited": feat.limit == -1
            }
            for name, feat in features.features.items()
        }
    }


# ============================================
# SUBSCRIPTION ENDPOINTS
# ============================================

@router.get("/subscription", response_model=SubscriptionResponse)
async def get_my_subscription(current_user=Depends(get_current_user)):
    """
    Obtém assinatura atual do usuário.
    """
    subscription = await subscription_service.get_subscription(str(current_user.id))
    
    return SubscriptionResponse(
        id=subscription.id,
        plan=subscription.plan.value,
        status=subscription.status.value,
        billing_cycle=subscription.billing_cycle.value,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        usage=subscription.usage
    )


@router.get("/subscription/usage")
async def get_usage(current_user=Depends(get_current_user)):
    """
    Obtém uso atual de todas as features.
    """
    user_id = str(current_user.id)
    subscription = await subscription_service.get_subscription(user_id)
    plan_features = await subscription_service.get_plan_features(subscription.plan)
    
    usage_data = []
    for feature_name, feature in plan_features.features.items():
        current = await subscription_service.get_usage(user_id, feature_name)
        limit = feature.limit
        
        usage_data.append(UsageResponse(
            feature=feature_name,
            current=current,
            limit=limit,
            remaining=max(0, limit - current) if limit != -1 else -1,
            can_use=limit == -1 or current < limit
        ))
    
    return usage_data


@router.post("/subscription/check-feature")
async def check_feature_access(
    feature: str,
    current_user=Depends(get_current_user)
):
    """
    Verifica se usuário pode usar uma feature específica.
    """
    can_use = await subscription_service.can_use_feature(
        str(current_user.id),
        feature
    )
    
    return {"feature": feature, "can_use": can_use}


# ============================================
# UPGRADE ENDPOINTS
# ============================================

@router.post("/subscription/upgrade")
async def upgrade_subscription(
    data: UpgradeRequest,
    current_user=Depends(get_current_user)
):
    """
    Faz upgrade do plano.
    
    Redireciona para checkout do MercadoPago.
    """
    try:
        plan = PlanTier(data.plan)
        cycle = BillingCycle(data.billing_cycle)
    except ValueError:
        raise HTTPException(status_code=400, detail="Plano ou ciclo inválido")
    
    if plan == PlanTier.FREE:
        raise HTTPException(status_code=400, detail="Não é possível fazer upgrade para FREE")
    
    if plan == PlanTier.ENTERPRISE:
        raise HTTPException(
            status_code=400, 
            detail="Entre em contato para plano Enterprise"
        )
    
    # TODO: Criar preference no MercadoPago
    # Por enquanto, simula upgrade direto
    subscription = await subscription_service.upgrade_plan(
        str(current_user.id),
        plan,
        cycle
    )
    
    return {
        "status": "success",
        "message": f"Upgrade para {plan.value} realizado!",
        "subscription": {
            "plan": subscription.plan.value,
            "status": subscription.status.value,
            "current_period_end": subscription.current_period_end.isoformat()
        }
    }


@router.post("/subscription/cancel")
async def cancel_subscription(current_user=Depends(get_current_user)):
    """
    Cancela assinatura.
    
    Mantém acesso até o final do período pago.
    """
    subscription = await subscription_service.cancel_subscription(str(current_user.id))
    
    return {
        "status": "canceled",
        "message": "Assinatura cancelada",
        "access_until": subscription.current_period_end.isoformat()
    }


# ============================================
# WEBHOOK ENDPOINTS
# ============================================

@router.post("/webhooks/mercadopago")
async def mercadopago_webhook(payload: Dict[str, Any]):
    """
    Webhook do MercadoPago para eventos de pagamento.
    
    Eventos:
    - payment.created
    - payment.updated
    - subscription_preapproval.updated
    """
    event_type = payload.get("type")
    payload.get("data", {})
    
    # TODO: Processar eventos do MercadoPago
    # - Atualizar status da assinatura
    # - Enviar notificações
    
    return {"status": "received", "event": event_type}
