"""
Chatbot API Routes
==================
Endpoints para integração com Typebot e gerenciamento de chatbots.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from api.middleware.auth import get_current_user, get_current_user_optional
from fastapi import APIRouter, Depends, HTTPException, Request
from integrations.typebot import TypebotClient, TypebotWebhookHandler
from pydantic import BaseModel

router = APIRouter()
typebot_client = TypebotClient()
webhook_handler = TypebotWebhookHandler()

# In-memory storage for chatbots (will be replaced with database later)
chatbots_db: Dict[str, Dict[str, Any]] = {}


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


class CreateChatbotRequest(BaseModel):
    name: str
    description: str
    channels: List[str]


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
            user_id=str(current_user["id"]),
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
# CHATBOT MANAGEMENT (CRUD)
# ============================================

@router.get("/bots")
async def list_chatbots(
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Lista todos os chatbots do usuário.
    """
    # Return all chatbots from in-memory storage
    return list(chatbots_db.values())


@router.post("/bots")
async def create_chatbot(
    data: CreateChatbotRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Cria um novo chatbot.
    """
    chatbot_id = str(uuid.uuid4())
    typebot_id = str(uuid.uuid4())  # Mock typebot ID
    
    chatbot = {
        "id": chatbot_id,
        "name": data.name,
        "description": data.description,
        "typebot_id": typebot_id,
        "status": "draft",
        "channels": data.channels,
        "total_sessions": 0,
        "total_messages": 0,
        "completion_rate": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    chatbots_db[chatbot_id] = chatbot
    return chatbot


@router.post("/bots/{bot_id}/toggle")
async def toggle_chatbot(
    bot_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Alterna o status do chatbot (active/paused).
    """
    if bot_id not in chatbots_db:
        raise HTTPException(status_code=404, detail="Chatbot não encontrado")
    
    chatbot = chatbots_db[bot_id]
    
    # Toggle between active and paused
    if chatbot["status"] == "active":
        chatbot["status"] = "paused"
    else:
        chatbot["status"] = "active"
    
    chatbot["updated_at"] = datetime.utcnow().isoformat()
    return chatbot


@router.delete("/bots/{bot_id}")
async def delete_chatbot(
    bot_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Remove um chatbot.
    """
    if bot_id not in chatbots_db:
        raise HTTPException(status_code=404, detail="Chatbot não encontrado")
    
    del chatbots_db[bot_id]
    return {"status": "deleted", "id": bot_id}


@router.get("/stats")
async def get_chatbot_stats(
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Retorna estatísticas gerais dos chatbots.
    """
    total_chatbots = len(chatbots_db)
    active_chatbots = sum(1 for bot in chatbots_db.values() if bot["status"] == "active")
    
    # Calculate aggregated stats
    total_sessions_today = sum(bot.get("total_sessions", 0) for bot in chatbots_db.values())
    total_messages_today = sum(bot.get("total_messages", 0) for bot in chatbots_db.values())
    
    # Calculate average completion rate
    completion_rates = [bot.get("completion_rate", 0) for bot in chatbots_db.values()]
    avg_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else 0
    
    # Get popular flows (mock data for now)
    popular_flows = [
        {
            "name": bot["name"],
            "sessions": bot.get("total_sessions", 0),
            "completion_rate": bot.get("completion_rate", 0)
        }
        for bot in sorted(
            chatbots_db.values(),
            key=lambda x: x.get("total_sessions", 0),
            reverse=True
        )[:5]
    ]
    
    return {
        "total_chatbots": total_chatbots,
        "active_chatbots": active_chatbots,
        "total_sessions_today": total_sessions_today,
        "total_messages_today": total_messages_today,
        "avg_completion_rate": round(avg_completion_rate, 1),
        "popular_flows": popular_flows
    }


# ============================================
# TEMPLATES
# ============================================

@router.get("/templates")
async def list_chatbot_templates():
    """
    Lista templates de chatbot pré-definidos.
    """
    try:
        from integrations.typebot import DIDIN_TYPEBOT_TEMPLATES

        # Return array directly (not wrapped in {templates: []})
        return [
            {
                "id": key,
                "name": template.get("name", key),
                "description": template.get("description", ""),
                "category": template.get("category", "geral"),
                "preview_url": template.get("preview_url", ""),
                "tags": template.get("tags", [])
            }
            for key, template in DIDIN_TYPEBOT_TEMPLATES.items()
        ]
    except ImportError:
        # Return empty array if templates not available
        return []


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
