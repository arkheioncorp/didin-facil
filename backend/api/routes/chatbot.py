"""
Chatbot API Routes
==================
Endpoints para integração com Typebot e gerenciamento de chatbots.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from api.middleware.auth import get_current_user
from integrations.typebot import TypebotClient, TypebotWebhookHandler

router = APIRouter()
typebot_client = TypebotClient()
webhook_handler = TypebotWebhookHandler()


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class StartChatRequest(BaseModel):
    typebot_id: str
    variables: Optional[Dict[str, Any]] = None
    prefilled_variables: Optional[Dict[str, Any]] = None


class SendMessageRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]]
    input: Optional[Dict[str, Any]] = None


# ============================================
# CHAT ENDPOINTS
# ============================================

@router.post("/chat/start")
async def start_chat(
    data: StartChatRequest,
    current_user=Depends(get_current_user)
):
    """
    Inicia uma nova sessão de chat com um Typebot.
    
    Retorna as mensagens iniciais do fluxo.
    """
    try:
        session = await typebot_client.start_chat(
            typebot_id=data.typebot_id,
            user_id=str(current_user.id),
            variables=data.variables,
            prefilledVariables=data.prefilled_variables
        )
        
        return {
            "session_id": session.session_id,
            "status": session.status.value,
            "messages": [
                {
                    "id": msg.id,
                    "type": msg.type,
                    "content": msg.content
                }
                for msg in session.messages
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/message")
async def send_message(
    data: SendMessageRequest,
    current_user=Depends(get_current_user)
):
    """
    Envia uma mensagem para uma sessão de chat existente.
    """
    try:
        response = await typebot_client.send_message(
            session_id=data.session_id,
            message=data.message
        )
        
        return {
            "messages": [
                {
                    "id": msg.id,
                    "type": msg.type,
                    "content": msg.content
                }
                for msg in response.get("messages", [])
            ],
            "input": response.get("input"),
            "actions": response.get("clientSideActions", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/{session_id}")
async def get_chat_session(
    session_id: str,
    current_user=Depends(get_current_user)
):
    """
    Obtém informações de uma sessão de chat.
    """
    session = await typebot_client.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    return session


# ============================================
# TYPEBOT MANAGEMENT
# ============================================

@router.get("/typebots")
async def list_typebots(
    workspace_id: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """
    Lista todos os Typebots disponíveis.
    """
    try:
        typebots = await typebot_client.list_typebots(workspace_id)
        
        return {
            "typebots": [
                {
                    "id": tb.get("id"),
                    "name": tb.get("name"),
                    "publicId": tb.get("publicId"),
                    "createdAt": tb.get("createdAt"),
                    "updatedAt": tb.get("updatedAt")
                }
                for tb in typebots
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/typebots/{typebot_id}")
async def get_typebot(
    typebot_id: str,
    current_user=Depends(get_current_user)
):
    """
    Obtém detalhes de um Typebot específico.
    """
    typebot = await typebot_client.get_typebot(typebot_id)
    
    if not typebot:
        raise HTTPException(status_code=404, detail="Typebot não encontrado")
    
    return typebot


@router.get("/typebots/{typebot_id}/results")
async def get_typebot_results(
    typebot_id: str,
    limit: int = 50,
    cursor: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """
    Obtém resultados/respostas de um Typebot.
    """
    try:
        results = await typebot_client.get_results(
            typebot_id=typebot_id,
            limit=limit,
            cursor=cursor
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# TEMPLATES
# ============================================

@router.get("/templates")
async def list_chatbot_templates():
    """
    Lista templates de chatbot pré-definidos.
    """
    from integrations.typebot import DIDIN_TYPEBOT_TEMPLATES
    
    return {
        "templates": [
            {
                "id": key,
                "name": template["name"],
                "description": template["description"],
                "blocks_count": len(template.get("blocks", []))
            }
            for key, template in DIDIN_TYPEBOT_TEMPLATES.items()
        ]
    }


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """
    Obtém detalhes de um template de chatbot.
    """
    from integrations.typebot import DIDIN_TYPEBOT_TEMPLATES
    
    template = DIDIN_TYPEBOT_TEMPLATES.get(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    
    return template


# ============================================
# WEBHOOKS
# ============================================

@router.post("/webhooks/typebot")
async def typebot_webhook(request: Request):
    """
    Webhook para receber eventos do Typebot.
    """
    try:
        payload = await request.json()
        result = await webhook_handler.process_webhook(payload)
        return result
        
    except Exception as e:
        return {"error": str(e)}


# ============================================
# WEBHOOK HANDLERS
# ============================================

@webhook_handler.on("conversation.started")
async def on_conversation_started(payload: Dict[str, Any]):
    """Handler para início de conversa."""
    payload.get("sessionId")
    # TODO: Registrar no banco
    return {"status": "ok"}


@webhook_handler.on("conversation.completed")
async def on_conversation_completed(payload: Dict[str, Any]):
    """Handler para fim de conversa."""
    payload.get("sessionId")
    payload.get("variables", {})
    # TODO: Processar dados coletados
    return {"status": "ok"}
