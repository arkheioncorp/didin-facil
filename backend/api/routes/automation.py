"""
n8n Automation API Routes
=========================
Endpoints para integração com n8n e automações.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from api.middleware.auth import get_current_user
from integrations.n8n import N8nClient, WorkflowStatus, DIDIN_N8N_WORKFLOWS

router = APIRouter()
n8n_client = N8nClient()


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class TriggerWebhookRequest(BaseModel):
    webhook_path: str
    data: Dict[str, Any]


class ExecuteWorkflowRequest(BaseModel):
    workflow_id: str
    data: Optional[Dict[str, Any]] = None


# ============================================
# WORKFLOW MANAGEMENT
# ============================================

@router.get("/workflows")
async def list_workflows(
    active: Optional[bool] = None,
    limit: int = 50,
    current_user=Depends(get_current_user)
):
    """
    Lista todos os workflows do n8n.
    """
    try:
        workflows = await n8n_client.list_workflows(active, limit)
        
        return {
            "workflows": [
                {
                    "id": wf.id,
                    "name": wf.name,
                    "active": wf.active,
                    "created_at": wf.created_at.isoformat(),
                    "updated_at": wf.updated_at.isoformat()
                }
                for wf in workflows
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    current_user=Depends(get_current_user)
):
    """
    Obtém detalhes de um workflow específico.
    """
    workflow = await n8n_client.get_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow não encontrado")
    
    return {
        "id": workflow.id,
        "name": workflow.name,
        "active": workflow.active,
        "nodes_count": len(workflow.nodes) if workflow.nodes else 0,
        "created_at": workflow.created_at.isoformat(),
        "updated_at": workflow.updated_at.isoformat()
    }


@router.post("/workflows/{workflow_id}/activate")
async def activate_workflow(
    workflow_id: str,
    current_user=Depends(get_current_user)
):
    """
    Ativa um workflow.
    """
    success = await n8n_client.activate_workflow(workflow_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Falha ao ativar workflow")
    
    return {"status": "activated", "workflow_id": workflow_id}


@router.post("/workflows/{workflow_id}/deactivate")
async def deactivate_workflow(
    workflow_id: str,
    current_user=Depends(get_current_user)
):
    """
    Desativa um workflow.
    """
    success = await n8n_client.deactivate_workflow(workflow_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Falha ao desativar workflow")
    
    return {"status": "deactivated", "workflow_id": workflow_id}


# ============================================
# EXECUTION
# ============================================

@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    data: Optional[Dict[str, Any]] = None,
    current_user=Depends(get_current_user)
):
    """
    Executa um workflow manualmente.
    """
    try:
        execution = await n8n_client.trigger_workflow_by_id(
            workflow_id=workflow_id,
            data=data
        )
        
        return {
            "execution_id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status.value,
            "started_at": execution.started_at.isoformat(),
            "data": execution.data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/trigger")
async def trigger_webhook(
    data: TriggerWebhookRequest,
    current_user=Depends(get_current_user)
):
    """
    Dispara um webhook do n8n.
    """
    try:
        result = await n8n_client.trigger_webhook(
            webhook_path=data.webhook_path,
            data=data.data
        )
        
        return {"status": "triggered", "result": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# EXECUTIONS HISTORY
# ============================================

@router.get("/executions")
async def list_executions(
    workflow_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    current_user=Depends(get_current_user)
):
    """
    Lista histórico de execuções.
    """
    try:
        status_enum = WorkflowStatus(status) if status else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Status inválido")
    
    try:
        executions = await n8n_client.get_executions(
            workflow_id=workflow_id,
            status=status_enum,
            limit=limit
        )
        
        return {
            "executions": [
                {
                    "id": ex.id,
                    "workflow_id": ex.workflow_id,
                    "status": ex.status.value,
                    "started_at": ex.started_at.isoformat(),
                    "finished_at": ex.finished_at.isoformat() if ex.finished_at else None,
                    "error": ex.error
                }
                for ex in executions
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# PRE-DEFINED WORKFLOWS
# ============================================

@router.get("/templates")
async def list_workflow_templates():
    """
    Lista templates de workflows pré-definidos para Didin Fácil.
    """
    return {
        "templates": [
            {
                "id": key,
                "name": wf["name"],
                "description": wf["description"],
                "trigger": wf["trigger"].value,
                "webhook_path": wf.get("webhook_path"),
                "schedule": wf.get("schedule"),
                "actions": wf["actions"]
            }
            for key, wf in DIDIN_N8N_WORKFLOWS.items()
        ]
    }


@router.get("/templates/{template_id}")
async def get_workflow_template(template_id: str):
    """
    Obtém detalhes de um template de workflow.
    """
    template = DIDIN_N8N_WORKFLOWS.get(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    
    return {
        "id": template_id,
        "name": template["name"],
        "description": template["description"],
        "trigger": template["trigger"].value,
        "webhook_path": template.get("webhook_path"),
        "schedule": template.get("schedule"),
        "actions": template["actions"]
    }


# ============================================
# QUICK ACTIONS (WEBHOOKS PRÉ-CONFIGURADOS)
# ============================================

@router.post("/actions/price-drop")
async def trigger_price_drop_alert(
    product_name: str,
    old_price: float,
    new_price: float,
    product_url: str,
    current_user=Depends(get_current_user)
):
    """
    Dispara alerta de queda de preço.
    """
    try:
        result = await n8n_client.trigger_webhook(
            webhook_path="/didin/price-drop",
            data={
                "product_name": product_name,
                "old_price": old_price,
                "new_price": new_price,
                "discount_percent": round((1 - new_price/old_price) * 100, 1),
                "product_url": product_url,
                "user_id": str(current_user.id),
                "triggered_at": datetime.utcnow().isoformat()
            }
        )
        
        return {"status": "triggered", "result": result}
        
    except Exception:
        # Se webhook não estiver configurado, não falhar
        return {"status": "skipped", "message": "Webhook não configurado"}


@router.post("/actions/new-lead")
async def trigger_new_lead(
    name: str,
    phone: str,
    email: Optional[str] = None,
    source: str = "website",
    current_user=Depends(get_current_user)
):
    """
    Dispara automação para novo lead.
    """
    try:
        result = await n8n_client.trigger_webhook(
            webhook_path="/didin/new-lead",
            data={
                "name": name,
                "phone": phone,
                "email": email,
                "source": source,
                "user_id": str(current_user.id),
                "created_at": datetime.utcnow().isoformat()
            }
        )
        
        return {"status": "triggered", "result": result}
        
    except Exception:
        return {"status": "skipped", "message": "Webhook não configurado"}


@router.post("/actions/post-published")
async def trigger_post_published(
    platform: str,
    post_id: str,
    post_url: str,
    current_user=Depends(get_current_user)
):
    """
    Dispara automação quando post é publicado.
    """
    try:
        result = await n8n_client.trigger_webhook(
            webhook_path="/didin/post-published",
            data={
                "platform": platform,
                "post_id": post_id,
                "post_url": post_url,
                "user_id": str(current_user.id),
                "published_at": datetime.utcnow().isoformat()
            }
        )
        
        return {"status": "triggered", "result": result}
        
    except Exception:
        return {"status": "skipped", "message": "Webhook não configurado"}
