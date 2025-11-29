"""
Chatwoot API Router
===================
Endpoints para integração com Chatwoot (suporte ao cliente).
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, EmailStr
import logging

from backend.vendor.integrations.chatwoot import (
    ChatwootClient,
    ChatwootConfig,
    ChatwootWebhookHandler,
    ConversationStatus,
    MessageType,
    create_support_ticket
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/support", tags=["Support"])

# Webhook handler global
webhook_handler = ChatwootWebhookHandler()


# ==================== Schemas ====================

class CreateTicketRequest(BaseModel):
    customer_name: str
    customer_email: EmailStr
    subject: str
    message: str
    priority: str = "normal"  # low, normal, high, urgent
    labels: List[str] = []


class SendMessageRequest(BaseModel):
    conversation_id: int
    content: str
    private: bool = False


class UpdateConversationRequest(BaseModel):
    status: Optional[str] = None
    assignee_id: Optional[int] = None
    labels: Optional[List[str]] = None


class CreateContactRequest(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    custom_attributes: Dict[str, Any] = {}


# ==================== Helper ====================

def get_chatwoot_config():
    """Obtém configuração do Chatwoot."""
    from backend.api.config import settings
    
    api_url = getattr(settings, 'CHATWOOT_API_URL', None)
    api_token = getattr(settings, 'CHATWOOT_API_TOKEN', None)
    account_id = getattr(settings, 'CHATWOOT_ACCOUNT_ID', None)
    
    if not all([api_url, api_token, account_id]):
        raise HTTPException(
            status_code=503,
            detail="Chatwoot não configurado. Configure CHATWOOT_API_URL, CHATWOOT_API_TOKEN e CHATWOOT_ACCOUNT_ID"
        )
    
    return ChatwootConfig(
        api_url=api_url,
        api_token=api_token,
        account_id=account_id
    )


# ==================== Tickets ====================

@router.post("/tickets")
async def create_ticket(request: CreateTicketRequest):
    """
    Cria um novo ticket de suporte.
    
    O ticket será criado no primeiro inbox do tipo API disponível.
    """
    config = get_chatwoot_config()
    
    async with ChatwootClient(config) as client:
        # Buscar inbox do tipo API
        inboxes = await client.list_inboxes()
        api_inbox = next(
            (i for i in inboxes if i["channel_type"] == "Channel::Api"),
            None
        )
        
        if not api_inbox:
            raise HTTPException(
                status_code=400,
                detail="Nenhum inbox do tipo API configurado no Chatwoot"
            )
        
        conversation = await create_support_ticket(
            client=client,
            inbox_id=api_inbox["id"],
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            subject=request.subject,
            message=request.message,
            priority=request.priority,
            labels=request.labels
        )
        
        return {
            "ticket_id": conversation.id,
            "status": conversation.status.value,
            "message": "Ticket criado com sucesso"
        }


@router.get("/tickets")
async def list_tickets(
    status: Optional[str] = None,
    assignee_id: Optional[int] = None,
    page: int = 1
):
    """Lista tickets/conversas."""
    config = get_chatwoot_config()
    
    async with ChatwootClient(config) as client:
        status_enum = ConversationStatus(status) if status else None
        
        conversations = await client.list_conversations(
            status=status_enum,
            assignee_id=assignee_id,
            page=page
        )
        
        return {
            "tickets": [
                {
                    "id": c.id,
                    "status": c.status.value,
                    "messages_count": c.messages_count,
                    "unread_count": c.unread_count,
                    "labels": c.labels
                }
                for c in conversations
            ],
            "page": page
        }


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: int):
    """Obtém detalhes de um ticket."""
    config = get_chatwoot_config()
    
    async with ChatwootClient(config) as client:
        conversation = await client.get_conversation(ticket_id)
        messages = await client.list_messages(ticket_id)
        
        return {
            "id": conversation.id,
            "status": conversation.status.value,
            "messages_count": conversation.messages_count,
            "unread_count": conversation.unread_count,
            "labels": conversation.labels,
            "assignee_id": conversation.assignee_id,
            "contact": {
                "id": conversation.contact.id,
                "name": conversation.contact.name,
                "email": conversation.contact.email,
                "phone": conversation.contact.phone_number
            } if conversation.contact else None,
            "messages": [
                {
                    "id": m.id,
                    "content": m.content,
                    "type": "outgoing" if m.message_type == MessageType.OUTGOING else "incoming",
                    "private": m.private
                }
                for m in messages
            ]
        }


@router.put("/tickets/{ticket_id}")
async def update_ticket(ticket_id: int, request: UpdateConversationRequest):
    """Atualiza um ticket."""
    config = get_chatwoot_config()
    
    async with ChatwootClient(config) as client:
        status_enum = ConversationStatus(request.status) if request.status else None
        
        conversation = await client.update_conversation(
            ticket_id,
            status=status_enum,
            assignee_id=request.assignee_id,
            labels=request.labels
        )
        
        return {
            "id": conversation.id,
            "status": conversation.status.value,
            "message": "Ticket atualizado"
        }


@router.post("/tickets/{ticket_id}/resolve")
async def resolve_ticket(ticket_id: int):
    """Marca um ticket como resolvido."""
    config = get_chatwoot_config()
    
    async with ChatwootClient(config) as client:
        conversation = await client.toggle_status(
            ticket_id,
            ConversationStatus.RESOLVED
        )
        
        return {
            "id": conversation.id,
            "status": conversation.status.value,
            "message": "Ticket resolvido"
        }


@router.post("/tickets/{ticket_id}/reopen")
async def reopen_ticket(ticket_id: int):
    """Reabre um ticket resolvido."""
    config = get_chatwoot_config()
    
    async with ChatwootClient(config) as client:
        conversation = await client.toggle_status(
            ticket_id,
            ConversationStatus.OPEN
        )
        
        return {
            "id": conversation.id,
            "status": conversation.status.value,
            "message": "Ticket reaberto"
        }


# ==================== Messages ====================

@router.post("/tickets/{ticket_id}/messages")
async def send_message(ticket_id: int, request: SendMessageRequest):
    """Envia mensagem em um ticket."""
    config = get_chatwoot_config()
    
    async with ChatwootClient(config) as client:
        message = await client.send_message(
            conversation_id=ticket_id,
            content=request.content,
            message_type=MessageType.OUTGOING,
            private=request.private
        )
        
        return {
            "message_id": message.id,
            "content": message.content,
            "private": message.private
        }


# ==================== Contacts ====================

@router.post("/contacts")
async def create_contact(request: CreateContactRequest):
    """Cria um novo contato."""
    config = get_chatwoot_config()
    
    async with ChatwootClient(config) as client:
        contact = await client.create_contact(
            name=request.name,
            email=request.email,
            phone=request.phone,
            custom_attributes=request.custom_attributes
        )
        
        return {
            "id": contact.id,
            "name": contact.name,
            "email": contact.email,
            "phone": contact.phone_number
        }


@router.get("/contacts/search")
async def search_contacts(q: str, page: int = 1):
    """Busca contatos."""
    config = get_chatwoot_config()
    
    async with ChatwootClient(config) as client:
        contacts = await client.search_contacts(q, page)
        
        return {
            "contacts": [
                {
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "phone": c.phone_number
                }
                for c in contacts
            ]
        }


# ==================== Agents & Teams ====================

@router.get("/agents")
async def list_agents():
    """Lista agentes de suporte."""
    config = get_chatwoot_config()
    
    async with ChatwootClient(config) as client:
        agents = await client.list_agents()
        return {"agents": agents}


@router.get("/teams")
async def list_teams():
    """Lista times de suporte."""
    config = get_chatwoot_config()
    
    async with ChatwootClient(config) as client:
        teams = await client.list_teams()
        return {"teams": teams}


@router.post("/tickets/{ticket_id}/assign")
async def assign_ticket(ticket_id: int, agent_id: int):
    """Atribui ticket a um agente."""
    config = get_chatwoot_config()
    
    async with ChatwootClient(config) as client:
        await client.assign_agent(ticket_id, agent_id)
        return {"message": f"Ticket #{ticket_id} atribuído ao agente #{agent_id}"}


# ==================== Labels ====================

@router.get("/labels")
async def list_labels():
    """Lista labels disponíveis."""
    config = get_chatwoot_config()
    
    async with ChatwootClient(config) as client:
        labels = await client.list_labels()
        return {"labels": labels}


@router.post("/tickets/{ticket_id}/labels")
async def add_labels(ticket_id: int, labels: List[str]):
    """Adiciona labels a um ticket."""
    config = get_chatwoot_config()
    
    async with ChatwootClient(config) as client:
        result = await client.add_labels(ticket_id, labels)
        return {"labels": result}


# ==================== Canned Responses ====================

@router.get("/canned-responses")
async def list_canned_responses():
    """Lista respostas prontas."""
    config = get_chatwoot_config()
    
    async with ChatwootClient(config) as client:
        responses = await client.list_canned_responses()
        return {"responses": responses}


# ==================== Reports ====================

@router.get("/reports/summary")
async def get_summary():
    """Obtém resumo de métricas de suporte."""
    config = get_chatwoot_config()
    
    async with ChatwootClient(config) as client:
        summary = await client.get_account_summary()
        return summary


# ==================== Inboxes ====================

@router.get("/inboxes")
async def list_inboxes():
    """Lista canais de suporte disponíveis."""
    config = get_chatwoot_config()
    
    async with ChatwootClient(config) as client:
        inboxes = await client.list_inboxes()
        return {"inboxes": inboxes}


# ==================== Webhooks ====================

@router.post("/webhook/chatwoot")
async def chatwoot_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Recebe webhooks do Chatwoot.
    
    Configure este URL no painel do Chatwoot:
    Settings > Integrations > Webhooks > Add Webhook
    """
    try:
        payload = await request.json()
        
        # Processar em background
        background_tasks.add_task(webhook_handler.process, payload)
        
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Status ====================

@router.get("/status")
async def get_support_status():
    """Verifica status da integração com Chatwoot."""
    try:
        config = get_chatwoot_config()
        
        async with ChatwootClient(config) as client:
            # Tenta listar inboxes para verificar conexão
            inboxes = await client.list_inboxes()
            agents = await client.list_agents()
            
            return {
                "status": "connected",
                "inboxes_count": len(inboxes),
                "agents_count": len(agents),
                "api_url": config.api_url
            }
    except HTTPException:
        raise
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# ==================== Webhook Handlers Registration ====================

# Registra handlers para eventos do Chatwoot

@webhook_handler.on("message_created")
async def on_message_created(payload: Dict):
    """Handler para nova mensagem."""
    message_type = payload.get("message_type")
    content = payload.get("content", "")
    conversation_id = payload.get("conversation", {}).get("id")
    
    # Apenas processa mensagens de entrada (clientes)
    if message_type == "incoming":
        logger.info(f"Nova mensagem de cliente em #{conversation_id}: {content[:100]}")
        
        # TODO: Implementar auto-resposta com IA
        # TODO: Notificar agentes via WhatsApp/Telegram
        # TODO: Criar alerta no dashboard


@webhook_handler.on("conversation_status_changed")
async def on_status_changed(payload: Dict):
    """Handler para mudança de status."""
    conversation_id = payload.get("id")
    status = payload.get("status")
    
    logger.info(f"Conversa #{conversation_id} mudou para status: {status}")
    
    # TODO: Atualizar métricas
    # TODO: Disparar automações (ex: pesquisa de satisfação)


@webhook_handler.on("conversation_created")
async def on_conversation_created(payload: Dict):
    """Handler para nova conversa."""
    conversation_id = payload.get("id")
    inbox_id = payload.get("inbox_id")
    
    logger.info(f"Nova conversa #{conversation_id} no inbox #{inbox_id}")
    
    # TODO: Atribuir automaticamente a agente disponível
    # TODO: Aplicar regras de roteamento
