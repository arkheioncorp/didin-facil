"""
Integrations Routes
Endpoints para integrações n8n e Typebot
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any

from api.middleware.auth import get_current_user
from vendor.integrations.n8n import N8nClient, N8nConfig
from vendor.integrations.typebot import (
    TypebotClient, TypebotConfig
)
from shared.config import settings
from shared.redis import get_redis

router = APIRouter()


# ==================== SCHEMAS ====================

class N8nWorkflowTrigger(BaseModel):
    """Request para disparar workflow n8n."""
    workflow_id: str
    data: Dict[str, Any] = {}
    wait_for_result: bool = False


class N8nWebhookTrigger(BaseModel):
    """Request para disparar webhook n8n."""
    webhook_url: str
    data: Dict[str, Any] = {}


class TypebotStartChat(BaseModel):
    """Request para iniciar conversa com Typebot."""
    bot_id: str
    user_id: Optional[str] = None
    initial_variables: Dict[str, Any] = {}


class TypebotSendMessage(BaseModel):
    """Request para enviar mensagem ao Typebot."""
    session_id: str
    message: str


class TypebotSetVariable(BaseModel):
    """Request para definir variável no Typebot."""
    session_id: str
    variable_name: str
    value: Any


class IntegrationConfig(BaseModel):
    """Configuração de integração."""
    n8n_url: Optional[str] = None
    n8n_api_key: Optional[str] = None
    typebot_url: Optional[str] = None
    typebot_public_id: Optional[str] = None


# ==================== N8N ROUTES ====================

def get_n8n_client() -> N8nClient:
    """Retorna cliente n8n configurado."""
    if not settings.N8N_API_URL or not settings.N8N_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="n8n não configurado. Configure N8N_API_URL e N8N_API_KEY."
        )
    config = N8nConfig(
        api_url=settings.N8N_API_URL,
        api_key=settings.N8N_API_KEY
    )
    return N8nClient(config)


@router.get("/n8n/workflows")
async def list_n8n_workflows(
    active_only: bool = True,
    current_user=Depends(get_current_user)
):
    """
    Lista workflows disponíveis no n8n.
    
    Use para obter IDs de workflows que podem ser disparados.
    """
    client = get_n8n_client()
    try:
        async with client:
            workflows = await client.list_workflows(active_only=active_only)
            return {
                "workflows": workflows,
                "total": len(workflows)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/n8n/workflows/trigger")
async def trigger_n8n_workflow(
    data: N8nWorkflowTrigger,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user)
):
    """
    Dispara um workflow n8n.
    
    Se wait_for_result=True, aguarda a execução terminar.
    Caso contrário, retorna imediatamente o ID da execução.
    """
    client = get_n8n_client()
    try:
        async with client:
            execution = await client.execute_workflow(
                workflow_id=data.workflow_id,
                data=data.data,
                wait=data.wait_for_result
            )
            
            return {
                "execution_id": execution.id,
                "status": execution.status.value,
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "finished_at": execution.finished_at.isoformat() if execution.finished_at else None,
                "data": execution.data if data.wait_for_result else None
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/n8n/executions/{execution_id}")
async def get_n8n_execution(
    execution_id: str,
    current_user=Depends(get_current_user)
):
    """
    Obtém status de uma execução n8n.
    """
    client = get_n8n_client()
    try:
        async with client:
            execution = await client.get_execution(execution_id)
            return {
                "execution_id": execution.id,
                "workflow_id": execution.workflow_id,
                "status": execution.status.value,
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "finished_at": execution.finished_at.isoformat() if execution.finished_at else None,
                "data": execution.data,
                "error": execution.error
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/n8n/webhooks/trigger")
async def trigger_n8n_webhook(
    data: N8nWebhookTrigger,
    current_user=Depends(get_current_user)
):
    """
    Dispara um webhook n8n diretamente.
    
    Útil para workflows que não estão na mesma instância n8n.
    """
    client = get_n8n_client()
    try:
        async with client:
            result = await client.trigger_webhook(
                webhook_url=data.webhook_url,
                data=data.data
            )
            return {
                "success": True,
                "response": result
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TYPEBOT ROUTES ====================

def get_typebot_client() -> TypebotClient:
    """Retorna cliente Typebot configurado."""
    if not settings.TYPEBOT_API_URL:
        raise HTTPException(
            status_code=503,
            detail="Typebot não configurado. Configure TYPEBOT_API_URL."
        )
    config = TypebotConfig(
        api_url=settings.TYPEBOT_API_URL,
        public_id=settings.TYPEBOT_PUBLIC_ID
    )
    return TypebotClient(config)


@router.post("/typebot/chat/start")
async def start_typebot_chat(
    data: TypebotStartChat,
    current_user=Depends(get_current_user)
):
    """
    Inicia uma conversa com um bot Typebot.
    
    Retorna session_id para continuar a conversa.
    """
    client = get_typebot_client()
    try:
        async with client:
            session = await client.start_chat(
                bot_id=data.bot_id,
                initial_variables=data.initial_variables
            )
            
            # Salvar sessão no Redis
            redis = await get_redis()
            await redis.set(
                f"typebot:session:{session.session_id}",
                session.model_dump_json(),
                ex=3600  # 1 hora
            )
            
            return {
                "session_id": session.session_id,
                "messages": [
                    {
                        "type": msg.type.value,
                        "content": msg.content,
                        "rich_content": msg.rich_content
                    }
                    for msg in session.messages
                ],
                "input_request": {
                    "type": session.input_request.type.value,
                    "options": session.input_request.options,
                    "placeholder": session.input_request.placeholder
                } if session.input_request else None,
                "is_completed": session.is_completed
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/typebot/chat/send")
async def send_typebot_message(
    data: TypebotSendMessage,
    current_user=Depends(get_current_user)
):
    """
    Envia uma mensagem para a conversa Typebot.
    """
    client = get_typebot_client()
    try:
        async with client:
            session = await client.send_message(
                session_id=data.session_id,
                message=data.message
            )
            
            # Atualizar sessão no Redis
            redis = await get_redis()
            await redis.set(
                f"typebot:session:{session.session_id}",
                session.model_dump_json(),
                ex=3600
            )
            
            return {
                "session_id": session.session_id,
                "messages": [
                    {
                        "type": msg.type.value,
                        "content": msg.content,
                        "rich_content": msg.rich_content
                    }
                    for msg in session.messages
                ],
                "input_request": {
                    "type": session.input_request.type.value,
                    "options": session.input_request.options,
                    "placeholder": session.input_request.placeholder
                } if session.input_request else None,
                "is_completed": session.is_completed
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/typebot/variables/set")
async def set_typebot_variable(
    data: TypebotSetVariable,
    current_user=Depends(get_current_user)
):
    """
    Define uma variável na sessão Typebot.
    """
    client = get_typebot_client()
    try:
        async with client:
            success = await client.set_variable(
                session_id=data.session_id,
                variable_name=data.variable_name,
                value=data.value
            )
            return {
                "success": success,
                "variable": data.variable_name,
                "value": data.value
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/typebot/sessions/{session_id}")
async def get_typebot_session(
    session_id: str,
    current_user=Depends(get_current_user)
):
    """
    Obtém informações de uma sessão Typebot.
    """
    redis = await get_redis()
    session_data = await redis.get(f"typebot:session:{session_id}")
    
    if not session_data:
        raise HTTPException(
            status_code=404,
            detail="Sessão não encontrada ou expirada"
        )
    
    import json
    session = json.loads(session_data)
    return session


# ==================== CONFIGURATION ====================

@router.get("/config")
async def get_integration_config(
    current_user=Depends(get_current_user)
):
    """
    Retorna configuração atual das integrações.
    """
    return {
        "n8n": {
            "configured": bool(settings.N8N_API_URL),
            "url": settings.N8N_API_URL if settings.N8N_API_URL else None
        },
        "typebot": {
            "configured": bool(settings.TYPEBOT_API_URL),
            "url": settings.TYPEBOT_API_URL if settings.TYPEBOT_API_URL else None
        },
        "evolution_api": {
            "configured": bool(settings.EVOLUTION_API_URL),
            "url": settings.EVOLUTION_API_URL if settings.EVOLUTION_API_URL else None
        }
    }


@router.post("/config")
async def update_integration_config(
    data: IntegrationConfig,
    current_user=Depends(get_current_user)
):
    """
    Atualiza configurações de integração.
    
    Nota: Em produção, use variáveis de ambiente.
    Este endpoint é útil apenas para testes.
    """
    # Salvar no Redis para persistir entre reinícios
    redis = await get_redis()
    
    if data.n8n_url:
        await redis.set("config:n8n_url", data.n8n_url)
    if data.n8n_api_key:
        await redis.set("config:n8n_api_key", data.n8n_api_key)
    if data.typebot_url:
        await redis.set("config:typebot_url", data.typebot_url)
    if data.typebot_public_id:
        await redis.set("config:typebot_public_id", data.typebot_public_id)
    
    return {"status": "updated", "message": "Configurações salvas"}
