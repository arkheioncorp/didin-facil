"""
Subscription API Routes
=======================
Endpoints para gerenciamento de assinaturas e planos.
"""

import logging
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
from shared.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
subscription_service = SubscriptionService()


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
    subscription = await subscription_service.get_subscription(str(current_user["id"]))
    
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
    user_id = str(current_user["id"])
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
        str(current_user["id"]),
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
        raise HTTPException(
            status_code=400,
            detail="Não é possível fazer upgrade para FREE"
        )
    
    if plan == PlanTier.ENTERPRISE:
        raise HTTPException(
            status_code=400,
            detail="Entre em contato para plano Enterprise"
        )
    
    # Obter informações do plano
    plan_info = subscription_service.get_plan_info(plan)
    price = (
        plan_info["price_yearly"] 
        if cycle == BillingCycle.YEARLY 
        else plan_info["price_monthly"]
    )
    
    # Criar preference no MercadoPago
    user_id = current_user["id"]
    if MP_AVAILABLE and sdk:
        try:
            preference_data = {
                "items": [
                    {
                        "title": f"Didin Fácil - Plano {plan_info['name']}",
                        "description": plan_info["description"],
                        "quantity": 1,
                        "currency_id": "BRL",
                        "unit_price": float(price),
                    }
                ],
                "payer": {
                    "email": current_user.email,
                },
                "back_urls": {
                    "success": f"{settings.FRONTEND_URL}/subscription/success",
                    "failure": f"{settings.FRONTEND_URL}/subscription/error",
                    "pending": f"{settings.FRONTEND_URL}/subscription/pending",
                },
                "auto_return": "approved",
                "external_reference": f"{user_id}:{plan.value}:{cycle.value}",
                "notification_url": f"{settings.API_URL}/webhooks/mercadopago",
                "statement_descriptor": "DIDIN FACIL",
                "metadata": {
                    "user_id": str(user_id),
                    "plan": plan.value,
                    "billing_cycle": cycle.value,
                },
            }
            
            preference_response = sdk.preference().create(preference_data)
            preference = preference_response.get("response", {})
            
            return {
                "status": "redirect",
                "checkout_url": preference.get("init_point"),
                "preference_id": preference.get("id"),
                "plan": plan.value,
                "price": float(price),
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar preference MP: {e}")
            # Fallback: ativar plano direto (dev mode)
    
    # Fallback ou modo desenvolvimento: upgrade direto
    subscription = await subscription_service.upgrade_plan(
        str(current_user["id"]),
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
    user_id = str(current_user["id"])
    subscription = await subscription_service.cancel_subscription(user_id)
    
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
            
            # Parse external_reference: "user_id:plan:cycle"
            parts = external_ref.split(":")
            if len(parts) >= 3:
                user_id, plan_str, cycle_str = parts[0], parts[1], parts[2]
            else:
                user_id = metadata.get("user_id")
                plan_str = metadata.get("plan")
                cycle_str = metadata.get("billing_cycle", "monthly")
            
            if status == "approved" and user_id and plan_str:
                # Ativar/atualizar assinatura
                try:
                    plan = PlanTier(plan_str)
                    cycle = BillingCycle(cycle_str)
                    await subscription_service.upgrade_plan(user_id, plan, cycle)
                    logger.info(f"Assinatura ativada: {user_id} -> {plan.value}")
                except Exception as e:
                    logger.error(f"Erro ao ativar assinatura: {e}")
            
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
            payer_email = preapproval.get("payer_email")
            
            logger.info(f"Preapproval {preapproval_id}: {status}")
            # TODO: Buscar usuário por email e atualizar status
            
    except Exception as e:
        logger.error(f"Erro ao processar webhook MP: {e}")
    
    return {"status": "received", "event": event_type}
