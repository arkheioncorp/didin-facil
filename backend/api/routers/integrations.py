"""
Integrations API Router
=======================
Endpoints para integrações com serviços externos (Typebot, n8n).
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from backend.vendor.integrations.typebot import TypebotClient, TypebotConfig
from backend.vendor.integrations.n8n import N8nClient, N8nConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/integrations", tags=["Integrations"])


# ==================== Schemas ====================

class TypebotChatRequest(BaseModel):
    typebot_id: str
    message: Optional[str] = None
    session_id: Optional[str] = None
    variables: Dict[str, Any] = {}


class N8nWebhookRequest(BaseModel):
    webhook_path: str
    data: Dict[str, Any]


class N8nExecuteRequest(BaseModel):
    workflow_id: str
    data: Dict[str, Any] = {}


# ==================== Typebot Endpoints ====================

@router.post("/typebot/start")
async def start_typebot_chat(request: TypebotChatRequest):
    """
    Inicia uma conversa com um bot do Typebot.
    
    Requer variáveis de ambiente:
    - TYPEBOT_API_URL
    - TYPEBOT_API_TOKEN (opcional)
    """
    from backend.api.config import settings
    
    typebot_url = getattr(settings, 'TYPEBOT_API_URL', None)
    if not typebot_url:
        raise HTTPException(status_code=503, detail="Typebot não configurado")
    
    config = TypebotConfig(
        api_url=typebot_url,
        api_token=getattr(settings, 'TYPEBOT_API_TOKEN', None),
        public_id=request.typebot_id
    )
    
    async with TypebotClient(config) as client:
        session = await client.start_chat(
            typebot_id=request.typebot_id,
            prefilted_variables=request.variables
        )
        
        return {
            "session_id": session.session_id,
            "messages": session.messages,
            "input": session.current_input,
            "is_completed": session.is_completed
        }


@router.post("/typebot/message")
async def send_typebot_message(request: TypebotChatRequest):
    """Envia mensagem para conversa existente."""
    from backend.api.config import settings
    
    typebot_url = getattr(settings, 'TYPEBOT_API_URL', None)
    if not typebot_url:
        raise HTTPException(status_code=503, detail="Typebot não configurado")
    
    if not request.session_id:
        raise HTTPException(status_code=400, detail="session_id é obrigatório")
    
    if not request.message:
        raise HTTPException(status_code=400, detail="message é obrigatório")
    
    config = TypebotConfig(api_url=typebot_url)
    
    async with TypebotClient(config) as client:
        session = await client.send_message(
            request.session_id,
            request.message
        )
        
        return {
            "session_id": session.session_id,
            "messages": session.messages,
            "input": session.current_input,
            "is_completed": session.is_completed
        }


# ==================== n8n Endpoints ====================

@router.post("/n8n/webhook")
async def trigger_n8n_webhook(request: N8nWebhookRequest):
    """
    Dispara um webhook do n8n.
    
    Requer variáveis de ambiente:
    - N8N_API_URL
    - N8N_API_KEY
    """
    from backend.api.config import settings
    
    n8n_url = getattr(settings, 'N8N_API_URL', None)
    n8n_key = getattr(settings, 'N8N_API_KEY', None)
    
    if not n8n_url:
        raise HTTPException(status_code=503, detail="n8n não configurado")
    
    config = N8nConfig(api_url=n8n_url, api_key=n8n_key or "")
    
    async with N8nClient(config) as client:
        result = await client.trigger_webhook(
            request.webhook_path,
            request.data
        )
        
        return {"status": "triggered", "response": result}


@router.post("/n8n/execute")
async def execute_n8n_workflow(request: N8nExecuteRequest):
    """Executa um workflow do n8n."""
    from backend.api.config import settings
    
    n8n_url = getattr(settings, 'N8N_API_URL', None)
    n8n_key = getattr(settings, 'N8N_API_KEY', None)
    
    if not n8n_url or not n8n_key:
        raise HTTPException(status_code=503, detail="n8n não configurado")
    
    config = N8nConfig(api_url=n8n_url, api_key=n8n_key)
    
    async with N8nClient(config) as client:
        execution = await client.execute_workflow(
            request.workflow_id,
            request.data
        )
        
        return {
            "execution_id": execution.execution_id,
            "status": execution.status.value,
            "data": execution.data
        }


@router.get("/n8n/workflows")
async def list_n8n_workflows(active_only: bool = False):
    """Lista workflows do n8n."""
    from backend.api.config import settings
    
    n8n_url = getattr(settings, 'N8N_API_URL', None)
    n8n_key = getattr(settings, 'N8N_API_KEY', None)
    
    if not n8n_url or not n8n_key:
        raise HTTPException(status_code=503, detail="n8n não configurado")
    
    config = N8nConfig(api_url=n8n_url, api_key=n8n_key)
    
    async with N8nClient(config) as client:
        workflows = await client.list_workflows(active_only=active_only)
        return {"workflows": workflows}


@router.get("/n8n/executions/{execution_id}")
async def get_n8n_execution(execution_id: str):
    """Obtém status de uma execução."""
    from backend.api.config import settings
    
    n8n_url = getattr(settings, 'N8N_API_URL', None)
    n8n_key = getattr(settings, 'N8N_API_KEY', None)
    
    if not n8n_url or not n8n_key:
        raise HTTPException(status_code=503, detail="n8n não configurado")
    
    config = N8nConfig(api_url=n8n_url, api_key=n8n_key)
    
    async with N8nClient(config) as client:
        execution = await client.get_execution(execution_id)
        
        return {
            "execution_id": execution.execution_id,
            "status": execution.status.value,
            "started_at": execution.started_at,
            "finished_at": execution.finished_at,
            "error": execution.error
        }


# ==================== Status ====================

@router.get("/status")
async def get_integrations_status():
    """Verifica status das integrações configuradas."""
    from backend.api.config import settings
    
    status = {
        "typebot": {
            "configured": bool(getattr(settings, 'TYPEBOT_API_URL', None)),
            "url": getattr(settings, 'TYPEBOT_API_URL', None)
        },
        "n8n": {
            "configured": bool(getattr(settings, 'N8N_API_URL', None)),
            "url": getattr(settings, 'N8N_API_URL', None)
        }
    }
    
    return status
