"""
Chatbot API Routes
==================
Endpoints para integração com Typebot e gerenciamento de chatbots.
"""

import uuid
from typing import Any, Dict, List, Optional

from api.database.connection import database
from api.middleware.auth import get_current_user, get_current_user_optional
from fastapi import APIRouter, Depends, HTTPException, Request
from integrations.typebot import TypebotClient, TypebotWebhookHandler
from pydantic import BaseModel

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
    Funciona em modo trial (sem autenticação).
    """
    # If not authenticated, return empty list (trial mode)
    if not current_user:
        return []
    
    rows = await database.fetch_all(
        """
        SELECT id, user_id, name, description, typebot_id, status, channels,
               total_sessions, total_messages, completion_rate,
               created_at, updated_at
        FROM chatbots
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        """,
        {"user_id": current_user["id"]}
    )
    return [dict(row) for row in rows]


@router.post("/bots")
async def create_chatbot(
    data: CreateChatbotRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Cria um novo chatbot.
    Requer autenticação em produção.
    """
    # Require authentication to create chatbots
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Faça login para criar chatbots"
        )
    
    chatbot_id = str(uuid.uuid4())

    # Insert into database
    await database.execute(
        """
        INSERT INTO chatbots (id, user_id, name, description, status, channels)
        VALUES (:id, :user_id, :name, :description, 'draft', :channels)
        """,
        {
            "id": chatbot_id,
            "user_id": current_user["id"],
            "name": data.name,
            "description": data.description,
            "channels": data.channels
        }
    )

    # Fetch and return created chatbot
    chatbot = await database.fetch_one(
        "SELECT * FROM chatbots WHERE id = :id",
        {"id": chatbot_id}
    )
    return dict(chatbot)


@router.post("/bots/{bot_id}/toggle")
async def toggle_chatbot(
    bot_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Alterna o status do chatbot (active/paused).
    Requer autenticação.
    """
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Faça login para alterar status de chatbots"
        )
    
    # Verify ownership
    chatbot = await database.fetch_one(
        "SELECT * FROM chatbots WHERE id = :id AND user_id = :user_id",
        {"id": bot_id, "user_id": current_user["id"]}
    )

    if not chatbot:
        raise HTTPException(
            status_code=404,
            detail="Chatbot não encontrado"
        )

    # Toggle status
    new_status = "paused" if chatbot["status"] == "active" else "active"

    await database.execute(
        "UPDATE chatbots SET status = :status WHERE id = :id",
        {"status": new_status, "id": bot_id}
    )

    # Return updated chatbot
    updated = await database.fetch_one(
        "SELECT * FROM chatbots WHERE id = :id",
        {"id": bot_id}
    )
    return dict(updated)


@router.delete("/bots/{bot_id}")
async def delete_chatbot(
    bot_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Remove um chatbot.
    Requer autenticação.
    """
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Faça login para remover chatbots"
        )
    
    # Verify ownership before delete
    chatbot = await database.fetch_one(
        "SELECT id FROM chatbots WHERE id = :id AND user_id = :user_id",
        {"id": bot_id, "user_id": current_user["id"]}
    )

    if not chatbot:
        raise HTTPException(
            status_code=404,
            detail="Chatbot não encontrado"
        )

    # Delete from database
    await database.execute(
        "DELETE FROM chatbots WHERE id = :id",
        {"id": bot_id}
    )

    return {"status": "deleted", "id": bot_id}


@router.get("/stats")
async def get_chatbot_stats(
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Retorna estatísticas gerais dos chatbots.
    Funciona em modo trial (sem autenticação).
    """
    # If not authenticated, return empty stats (trial mode)
    if not current_user:
        return {
            "total_chatbots": 0,
            "active_chatbots": 0,
            "total_sessions_today": 0,
            "total_messages_today": 0,
            "avg_completion_rate": 0,
            "popular_flows": []
        }
    
    # Get aggregate stats from database
    stats = await database.fetch_one(
        """
        SELECT
            COUNT(*) as total_chatbots,
            COUNT(*) FILTER (WHERE status = 'active') as active_chatbots,
            COALESCE(SUM(total_sessions), 0) as total_sessions_today,
            COALESCE(SUM(total_messages), 0) as total_messages_today,
            COALESCE(AVG(completion_rate), 0) as avg_completion_rate
        FROM chatbots
        WHERE user_id = :user_id
        """,
        {"user_id": current_user["id"]}
    )

    # Get popular flows (top 5 by sessions)
    popular_flows_rows = await database.fetch_all(
        """
        SELECT name, total_sessions as sessions, completion_rate
        FROM chatbots
        WHERE user_id = :user_id
        ORDER BY total_sessions DESC
        LIMIT 5
        """,
        {"user_id": current_user["id"]}
    )

    popular_flows = [dict(row) for row in popular_flows_rows]

    return {
        "total_chatbots": stats["total_chatbots"],
        "active_chatbots": stats["active_chatbots"],
        "total_sessions_today": stats["total_sessions_today"],
        "total_messages_today": stats["total_messages_today"],
        "avg_completion_rate": round(float(stats["avg_completion_rate"]), 1),
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
