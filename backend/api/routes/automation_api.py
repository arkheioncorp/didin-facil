"""
Automation API Routes
=====================
Endpoints REST para gerenciar automações n8n do Seller Bot.

Endpoints:
- POST /automation/trigger - Dispara uma automação
- GET /automation/stats - Estatísticas de automações
- GET /automation/list - Lista automações configuradas
- PUT /automation/{type}/config - Atualiza configuração
- POST /automation/process-pending - Processa eventos pendentes
"""

import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from modules.automation.n8n_orchestrator import (
    get_orchestrator,
    AutomationType,
    ChannelType,
    AutomationPriority,
    AutomationResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/automation", tags=["Seller Bot Automation"])


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class TriggerRequest(BaseModel):
    """Request para disparar automação."""
    automation_type: AutomationType
    user_id: str
    channel: ChannelType = ChannelType.WHATSAPP
    data: dict = Field(default_factory=dict)
    force: bool = False


class OnboardingRequest(BaseModel):
    """Request para onboarding de novo usuário."""
    user_id: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    channel: ChannelType = ChannelType.WHATSAPP


class CartAbandonedRequest(BaseModel):
    """Request para carrinho abandonado."""
    user_id: str
    name: str
    product_name: str
    product_url: str
    price: float
    channel: ChannelType = ChannelType.WHATSAPP


class PriceDropRequest(BaseModel):
    """Request para alerta de queda de preço."""
    user_id: str
    name: str
    product_name: str
    product_url: str
    old_price: float
    new_price: float
    channel: ChannelType = ChannelType.WHATSAPP


class PostPurchaseRequest(BaseModel):
    """Request para pós-compra."""
    user_id: str
    name: str
    order_id: str
    product_name: str
    total: float
    channel: ChannelType = ChannelType.WHATSAPP


class LeadQualifiedRequest(BaseModel):
    """Request para lead qualificado."""
    user_id: str
    name: str
    lead_score: int
    interested_products: List[str] = Field(default_factory=list)
    channel: ChannelType = ChannelType.WHATSAPP


class ReengagementRequest(BaseModel):
    """Request para reengajamento."""
    user_id: str
    name: str
    days_inactive: int
    last_product_viewed: Optional[str] = None
    channel: ChannelType = ChannelType.WHATSAPP


class UpdateConfigRequest(BaseModel):
    """Request para atualizar configuração."""
    enabled: Optional[bool] = None
    channels: Optional[List[ChannelType]] = None
    delay_minutes: Optional[int] = None
    priority: Optional[AutomationPriority] = None
    templates: Optional[dict] = None
    min_delay_between_triggers_hours: Optional[int] = None
    max_triggers_per_user_per_day: Optional[int] = None
    allowed_hours_start: Optional[int] = None
    allowed_hours_end: Optional[int] = None


class AutomationResponse(BaseModel):
    """Response padrão de automação."""
    success: bool
    event_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    scheduled_at: Optional[datetime] = None


# ============================================
# ENDPOINTS
# ============================================

@router.post("/trigger", response_model=AutomationResponse)
async def trigger_automation(request: TriggerRequest):
    """
    Dispara uma automação manualmente.
    
    Pode ser usado para testar ou forçar uma automação.
    """
    orchestrator = get_orchestrator()
    
    result = await orchestrator.trigger_automation(
        automation_type=request.automation_type,
        user_id=request.user_id,
        data=request.data,
        channel=request.channel,
        force=request.force
    )
    
    return AutomationResponse(
        success=result.success,
        event_id=result.event_id,
        message="Automação disparada com sucesso" if result.success else None,
        error=result.error
    )


@router.post("/onboarding", response_model=AutomationResponse)
async def trigger_onboarding(request: OnboardingRequest):
    """
    Dispara sequência de onboarding para novo usuário.
    
    Envia mensagem de boas-vindas e inicia nurturing.
    """
    orchestrator = get_orchestrator()
    
    result = await orchestrator.trigger_onboarding(
        user_id=request.user_id,
        name=request.name,
        channel=request.channel,
        phone=request.phone,
        email=request.email
    )
    
    return AutomationResponse(
        success=result.success,
        event_id=result.event_id,
        message="Onboarding iniciado" if result.success else None,
        error=result.error
    )


@router.post("/cart-abandoned", response_model=AutomationResponse)
async def trigger_cart_abandoned(request: CartAbandonedRequest):
    """
    Dispara recuperação de carrinho abandonado.
    
    Envia lembrete com produto e link para finalizar compra.
    """
    orchestrator = get_orchestrator()
    
    result = await orchestrator.trigger_cart_abandoned(
        user_id=request.user_id,
        name=request.name,
        product_name=request.product_name,
        product_url=request.product_url,
        price=request.price,
        channel=request.channel
    )
    
    return AutomationResponse(
        success=result.success,
        event_id=result.event_id,
        message="Recuperação de carrinho agendada" if result.success else None,
        error=result.error
    )


@router.post("/price-drop", response_model=AutomationResponse)
async def trigger_price_drop(request: PriceDropRequest):
    """
    Dispara alerta de queda de preço.
    
    Notifica usuário sobre produto que estava monitorando.
    """
    orchestrator = get_orchestrator()
    
    result = await orchestrator.trigger_price_drop(
        user_id=request.user_id,
        name=request.name,
        product_name=request.product_name,
        product_url=request.product_url,
        old_price=request.old_price,
        new_price=request.new_price,
        channel=request.channel
    )
    
    return AutomationResponse(
        success=result.success,
        event_id=result.event_id,
        message="Alerta de preço enviado" if result.success else None,
        error=result.error
    )


@router.post("/post-purchase", response_model=AutomationResponse)
async def trigger_post_purchase(request: PostPurchaseRequest):
    """
    Dispara agradecimento pós-compra.
    
    Envia confirmação e inicia sequência de follow-up.
    """
    orchestrator = get_orchestrator()
    
    result = await orchestrator.trigger_post_purchase(
        user_id=request.user_id,
        name=request.name,
        order_id=request.order_id,
        product_name=request.product_name,
        total=request.total,
        channel=request.channel
    )
    
    return AutomationResponse(
        success=result.success,
        event_id=result.event_id,
        message="Agradecimento enviado" if result.success else None,
        error=result.error
    )


@router.post("/lead-qualified", response_model=AutomationResponse)
async def trigger_lead_qualified(request: LeadQualifiedRequest):
    """
    Dispara automação para lead qualificado.
    
    Envia oferta especial quando lead atinge score alto.
    """
    orchestrator = get_orchestrator()
    
    result = await orchestrator.trigger_lead_qualified(
        user_id=request.user_id,
        name=request.name,
        lead_score=request.lead_score,
        interested_products=request.interested_products,
        channel=request.channel
    )
    
    return AutomationResponse(
        success=result.success,
        event_id=result.event_id,
        message="Oferta para lead qualificado enviada" if result.success else None,
        error=result.error
    )


@router.post("/reengagement", response_model=AutomationResponse)
async def trigger_reengagement(request: ReengagementRequest):
    """
    Dispara campanha de reengajamento.
    
    Tenta reativar usuário inativo com ofertas.
    """
    orchestrator = get_orchestrator()
    
    result = await orchestrator.trigger_reengagement(
        user_id=request.user_id,
        name=request.name,
        days_inactive=request.days_inactive,
        last_product_viewed=request.last_product_viewed,
        channel=request.channel
    )
    
    return AutomationResponse(
        success=result.success,
        event_id=result.event_id,
        message="Campanha de reengajamento iniciada" if result.success else None,
        error=result.error
    )


@router.get("/stats")
async def get_automation_stats():
    """
    Retorna estatísticas das automações.
    
    Inclui contagem de automações, eventos pendentes, etc.
    """
    orchestrator = get_orchestrator()
    return orchestrator.get_automation_stats()


@router.get("/list")
async def list_automations():
    """
    Lista todas as automações configuradas.
    
    Retorna tipo, status, configuração de cada automação.
    """
    orchestrator = get_orchestrator()
    
    automations = []
    for automation_type, config in orchestrator.automations.items():
        automations.append({
            "type": automation_type.value,
            "enabled": config.enabled,
            "priority": config.priority.value,
            "channels": [c.value for c in config.channels],
            "delay_minutes": config.delay_minutes,
            "webhook_path": config.webhook_path,
            "rate_limit": {
                "min_delay_hours": config.min_delay_between_triggers_hours,
                "max_per_day": config.max_triggers_per_user_per_day
            },
            "allowed_hours": {
                "start": config.allowed_hours_start,
                "end": config.allowed_hours_end
            }
        })
    
    return {"automations": automations}


@router.get("/pending")
async def list_pending_events():
    """Lista eventos pendentes de execução."""
    orchestrator = get_orchestrator()
    pending = orchestrator.get_pending_events()
    
    return {
        "count": len(pending),
        "events": [
            {
                "id": e.id,
                "type": e.automation_type.value,
                "user_id": e.user_id,
                "channel": e.channel.value,
                "scheduled_at": e.scheduled_at.isoformat(),
                "status": e.status
            }
            for e in pending
        ]
    }


@router.post("/process-pending")
async def process_pending_events(background_tasks: BackgroundTasks):
    """
    Processa eventos pendentes que já podem ser executados.
    
    Executa em background para não bloquear a resposta.
    """
    orchestrator = get_orchestrator()
    
    async def process():
        results = await orchestrator.process_pending_events()
        logger.info("Processados %d eventos pendentes", len(results))
    
    background_tasks.add_task(process)
    
    return {"message": "Processamento iniciado em background"}


@router.put("/{automation_type}/config")
async def update_automation_config(
    automation_type: AutomationType,
    request: UpdateConfigRequest
):
    """
    Atualiza configuração de uma automação.
    
    Permite habilitar/desabilitar, alterar canais, delays, etc.
    """
    orchestrator = get_orchestrator()
    
    if automation_type not in orchestrator.automations:
        raise HTTPException(
            status_code=404,
            detail=f"Automação {automation_type.value} não encontrada"
        )
    
    # Aplicar atualizações
    updates = request.model_dump(exclude_unset=True)
    orchestrator.update_automation_config(automation_type, **updates)
    
    return {
        "success": True,
        "message": f"Configuração de {automation_type.value} atualizada",
        "updates": updates
    }


@router.post("/{automation_type}/enable")
async def enable_automation(automation_type: AutomationType):
    """Habilita uma automação."""
    orchestrator = get_orchestrator()
    orchestrator.enable_automation(automation_type)
    return {"success": True, "message": f"{automation_type.value} habilitada"}


@router.post("/{automation_type}/disable")
async def disable_automation(automation_type: AutomationType):
    """Desabilita uma automação."""
    orchestrator = get_orchestrator()
    orchestrator.disable_automation(automation_type)
    return {"success": True, "message": f"{automation_type.value} desabilitada"}
