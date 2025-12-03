"""
n8n Webhooks - Backend Integration
===================================
Endpoints para receber eventos do n8n e inte grar bidirecionalmente.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import logging

from api.middleware.auth import get_current_user
from api.database.models import User
from integrations.n8n import get_n8n_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/n8n", tags=["n8n"])


# ==================== Request Models ====================


class ProductSearchRequest(BaseModel):
    """Request para busca de produtos via n8n."""

    query: str
    conversation_id: str
    limit: int = 5


class PriceAlertTriggeredRequest(BaseModel):
    """Evento de alerta de preço disparado."""

    user_id: str
    product_id: str
    old_price: float
    new_price: float
    discount_percentage: float


class WorkflowExecutionRequest(BaseModel):
    """Request para disparar workflow manualmente."""

    workflow_id: str
    data: Dict[str, Any]


class N8nEventRequest(BaseModel):
    """Evento genérico do n8n."""

    event_type: str
    conversation_id: Optional[str] = None
    data: Dict[str, Any]


# ==================== Response Models ====================


class ProductSearchResponse(BaseModel):
    """Resposta de busca de produtos."""

    products: List[Dict[str, Any]]
    total: int
    query: str


# ==================== Webhooks (n8n → Backend) ====================


@router.post("/webhook/product-search")
async def product_search_webhook(
    request: ProductSearchRequest, background_tasks: BackgroundTasks
):
    """
    Webhook chamado pelo n8n para buscar produtos.

    Fluxo:
    1. n8n recebe mensagem de WhatsApp
    2. Detecta intenção de busca
    3. Chama este endpoint
    4. Retorna produtos formatados
    """
    try:
        from api.services.scraper import ScraperOrchestrator

        orchestrator = ScraperOrchestrator()

        # Buscar produtos
        products = await orchestrator.search_products(
            query=request.query, limit=request.limit
        )

        # Registrar evento
        background_tasks.add_task(
            _log_product_search, request.conversation_id, request.query, len(products)
        )

        # Formatar resposta para WhatsApp
        formatted_products = []
        for p in products:
            formatted_products.append(
                {
                    "name": p.get("title", "Produto"),
                    "price": f"R$ {p.get('price', 0):.2f}",
                    "discount": p.get("discount_percentage", 0),
                    "store": p.get("store", "Loja"),
                    "url": p.get("url", "#"),
                }
            )

        return ProductSearchResponse(
            products=formatted_products,
            total=len(formatted_products),
            query=request.query,
        )

    except Exception as e:
        logger.error(f"Error in product search webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/price-alert")
async def price_alert_webhook(
    request: PriceAlertTriggeredRequest, background_tasks: BackgroundTasks
):
    """
    Webhook para registrar disparo de alerta de preço.

    Chamado quando n8n envia notificação de queda de preço.
    """
    try:
        # Registrar métrica
        background_tasks.add_task(
            _track_price_alert,
            request.user_id,
            request.product_id,
            request.old_price,
            request.new_price,
        )

        return {"success": True, "message": "Price alert logged"}

    except Exception as e:
        logger.error(f"Error in price alert webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/event")
async def generic_event_webhook(request: N8nEventRequest):
    """
    Webhook genérico para eventos do n8n.

    Permite extensibilidade sem criar novos endpoints.
    """
    try:
        logger.info(f"n8n event received: {request.event_type}")

        # Processar por tipo de evento
        if request.event_type == "user_interaction":
            await _track_interaction(request.conversation_id, request.data)

        elif request.event_type == "workflow_completed":
            await _track_workflow_completion(request.data)

        elif request.event_type == "error_occurred":
            logger.error(f"n8n workflow error: {request.data}")

        return {"success": True, "event_processed": request.event_type}

    except Exception as e:
        logger.error(f"Error processing n8n event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Triggers (Backend → n8n) ====================


@router.post("/trigger/new-user")
async def trigger_new_user_onboarding(user: User = Depends(get_current_user)):
    """
    Dispara workflow de onboarding para novo usuário.

    Chamado após registro bem-sucedido.
    """
    try:
        client = get_n8n_client()

        await client.trigger_webhook(
            webhook_path="/didin/new-user",
            data={
                "user_id": str(user.id),
                "email": user.email,
                "name": user.name,
                "created_at": user.created_at.isoformat(),
            },
        )

        return {"success": True, "message": "Onboarding triggered"}

    except Exception as e:
        logger.error(f"Error triggering onboarding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/price-drop")
async def trigger_price_drop_alert(
    product_id: str,
    old_price: float,
    new_price: float,
    user: User = Depends(get_current_user),
):
    """
    Dispara alerta de queda de preço.

    Chamado quando sistema detecta redução de preço.
    """
    try:
        client = get_n8n_client()

        await client.trigger_webhook(
            webhook_path="/didin/price-drop",
            data={
                "user_id": str(user.id),
                "product_id": product_id,
                "old_price": old_price,
                "new_price": new_price,
                "discount_percentage": round((1 - new_price / old_price) * 100, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        return {"success": True, "message": "Price alert triggered"}

    except Exception as e:
        logger.error(f"Error triggering price alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/workflow")
async def trigger_workflow_manually(
    request: WorkflowExecutionRequest, user: User = Depends(get_current_user)
):
    """
    Dispara workflow manualmente por ID.

    Útil para testes e disparos administrativos.
    """
    try:
        client = get_n8n_client()

        execution = await client.trigger_workflow_by_id(
            workflow_id=request.workflow_id, data=request.data
        )

        return {
            "success": True,
            "execution_id": execution.id,
            "status": execution.status.value,
        }

    except Exception as e:
        logger.error(f"Error triggering workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Admin Endpoints ====================


@router.get("/workflows")
async def list_workflows(user: User = Depends(get_current_user)):
    """Lista todos os workflows do n8n."""
    try:
        client = get_n8n_client()
        workflows = await client.list_workflows(limit=100)

        return {
            "workflows": [
                {
                    "id": wf.id,
                    "name": wf.name,
                    "active": wf.active,
                    "updated_at": wf.updated_at.isoformat(),
                }
                for wf in workflows
            ],
            "total": len(workflows),
        }

    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions")
async def list_executions(
    workflow_id: Optional[str] = None,
    limit: int = 20,
    user: User = Depends(get_current_user),
):
    """Lista execuções de workflows."""
    try:
        client = get_n8n_client()
        executions = await client.get_executions(workflow_id=workflow_id, limit=limit)

        return {
            "executions": [
                {
                    "id": ex.id,
                    "workflow_id": ex.workflow_id,
                    "status": ex.status.value,
                    "started_at": ex.started_at.isoformat(),
                    "finished_at": (
                        ex.finished_at.isoformat() if ex.finished_at else None
                    ),
                }
                for ex in executions
            ],
            "total": len(executions),
        }

    except Exception as e:
        logger.error(f"Error listing executions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Helper Functions ====================


async def _log_product_search(conversation_id: str, query: str, results_count: int):
    """Registra busca de produto em analytics."""
    logger.info(
        f"Product search: conv={conversation_id}, query={query}, results={results_count}"
    )
    # TODO: Salvar em analytics


async def _track_price_alert(
    user_id: str, product_id: str, old_price: float, new_price: float
):
    """Registra disparo de alerta de preço."""
    logger.info(
        f"Price alert: user={user_id}, product={product_id}, {old_price} → {new_price}"
    )
    # TODO: Salvar em analytics


async def _track_interaction(conversation_id: str, data: Dict):
    """Registra interação do usuário."""
    logger.info(f"User interaction: conv={conversation_id}, data={data}")
    # TODO: Salvar em analytics


async def _track_workflow_completion(data: Dict):
    """Registra conclusão de workflow."""
    logger.info(f"Workflow completed: {data}")
    # TODO: Salvar em métricas
