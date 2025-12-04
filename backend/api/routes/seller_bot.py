"""
Seller Bot API Routes
=====================
Endpoints REST para o Professional Seller Bot.

Features:
- Webhook receivers (WhatsApp, Instagram, Chatwoot)
- Conversation management
- Analytics
- Bot configuration
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from integrations.n8n import N8nClient
from modules.chatbot.channel_integrations import (ChannelRouter,
                                                  create_chatwoot_adapter,
                                                  create_evolution_adapter)
from modules.chatbot.professional_seller_bot import (ConversationStage,
                                                     IncomingMessage,
                                                     LeadTemperature,
                                                     MessageChannel,
                                                     ProfessionalSellerBot,
                                                     create_seller_bot)
from pydantic import BaseModel, Field
from shared.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/seller-bot", tags=["Seller Bot"])


# ============================================
# SINGLETON INSTANCES
# ============================================

_bot_instance: Optional[ProfessionalSellerBot] = None
_channel_router: Optional[ChannelRouter] = None


def get_bot() -> ProfessionalSellerBot:
    """Obtém instância do bot."""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = create_seller_bot(
            n8n_client=N8nClient() if settings.N8N_API_KEY else None,
        )
    return _bot_instance


def get_channel_router() -> ChannelRouter:
    """Obtém router de canais."""
    global _channel_router
    if _channel_router is None:
        _channel_router = ChannelRouter()
        
        # Registrar adaptadores baseado em configuração
        if settings.CHATWOOT_ACCESS_TOKEN:
            chatwoot = create_chatwoot_adapter(
                api_url=settings.CHATWOOT_API_URL,
                api_token=settings.CHATWOOT_ACCESS_TOKEN,
                account_id=settings.CHATWOOT_ACCOUNT_ID,
            )
            _channel_router.register_adapter(MessageChannel.WEBCHAT, chatwoot)
            _channel_router.register_adapter(MessageChannel.WHATSAPP, chatwoot)
        
        if settings.EVOLUTION_API_KEY:
            instance = getattr(settings, 'EVOLUTION_INSTANCE', 'tiktrend-bot')
            evolution = create_evolution_adapter(
                api_url=settings.EVOLUTION_API_URL,
                api_key=settings.EVOLUTION_API_KEY,
                instance_name=instance,
            )
            _channel_router.register_adapter(
                MessageChannel.WHATSAPP, evolution
            )
    
    return _channel_router


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class WebhookPayload(BaseModel):
    """Payload genérico de webhook."""
    event: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    # Campos comuns
    message: Optional[Dict[str, Any]] = None
    conversation: Optional[Dict[str, Any]] = None
    sender: Optional[Dict[str, Any]] = None
    # Evolution API fields
    key: Optional[Dict[str, Any]] = None
    pushName: Optional[str] = None
    instance: Optional[str] = None


class DirectMessageRequest(BaseModel):
    """Requisição de mensagem direta para testes."""
    channel: str = "webchat"
    sender_id: str
    sender_name: Optional[str] = None
    content: str
    media_url: Optional[str] = None


class ConversationResponse(BaseModel):
    """Resposta com dados da conversa."""
    conversation_id: str
    user_id: str
    channel: str
    stage: str
    lead_temperature: str
    lead_score: int
    message_count: int
    is_active: bool
    last_interaction: datetime
    interested_products: List[str]
    search_history: List[str]


class BotStatsResponse(BaseModel):
    """Estatísticas do bot."""
    total_conversations: int
    active_conversations: int
    messages_today: int
    handoffs_today: int
    avg_response_time_ms: float
    top_intents: List[Dict[str, Any]]
    lead_distribution: Dict[str, int]


class BotConfigRequest(BaseModel):
    """Configuração do bot."""
    greeting_message: Optional[str] = None
    fallback_message: Optional[str] = None
    handoff_threshold: Optional[int] = None  # Após N mensagens sem resolver
    enable_ai_responses: Optional[bool] = None
    typing_delay_ms: Optional[int] = None


# ============================================
# WEBHOOK ENDPOINTS
# ============================================

@router.post("/webhook/chatwoot")
async def chatwoot_webhook(
    payload: WebhookPayload,
    background_tasks: BackgroundTasks,
    bot: ProfessionalSellerBot = Depends(get_bot),
    router: ChannelRouter = Depends(get_channel_router),
):
    """
    Recebe webhooks do Chatwoot.
    
    Eventos processados:
    - message_created: Nova mensagem recebida
    - conversation_status_changed: Status alterado
    """
    try:
        # Log do evento
        event = payload.event or payload.data.get("event", "unknown")
        logger.info(f"Chatwoot webhook: {event}")
        
        # Só processar mensagens
        if event != "message_created":
            return {"status": "ignored", "event": event}
        
        # Parsear mensagem
        chatwoot_adapter = router.get_adapter(MessageChannel.WEBCHAT)
        if not chatwoot_adapter:
            raise HTTPException(500, "Chatwoot adapter não configurado")
        
        message = await chatwoot_adapter.parse_incoming(payload.model_dump())
        
        if not message:
            return {"status": "ignored", "reason": "not_incoming_message"}
        
        # Processar em background
        background_tasks.add_task(
            _process_message,
            bot,
            router,
            message,
            payload.model_dump()
        )
        
        return {"status": "processing", "message_id": message.id}
        
    except Exception as e:
        logger.exception(f"Erro no webhook Chatwoot: {e}")
        raise HTTPException(500, str(e))


@router.post("/webhook/evolution")
async def evolution_webhook(
    payload: WebhookPayload,
    background_tasks: BackgroundTasks,
    bot: ProfessionalSellerBot = Depends(get_bot),
    router: ChannelRouter = Depends(get_channel_router),
):
    """
    Recebe webhooks da Evolution API (WhatsApp).
    
    Eventos processados:
    - messages.upsert: Nova mensagem
    """
    try:
        event = payload.event or payload.data.get("event", "unknown")
        logger.info(f"Evolution webhook: {event}")
        
        if event not in ["messages.upsert", "message"]:
            return {"status": "ignored", "event": event}
        
        evolution_adapter = router.get_adapter(MessageChannel.WHATSAPP)
        if not evolution_adapter:
            raise HTTPException(500, "Evolution adapter não configurado")
        
        message = await evolution_adapter.parse_incoming(payload.model_dump())
        
        if not message:
            return {"status": "ignored", "reason": "not_processable"}
        
        background_tasks.add_task(
            _process_message,
            bot,
            router,
            message,
            payload.model_dump()
        )
        
        return {"status": "processing", "message_id": message.id}
        
    except Exception as e:
        logger.exception(f"Erro no webhook Evolution: {e}")
        raise HTTPException(500, str(e))


@router.post("/webhook/instagram")
async def instagram_webhook(request: Request):
    """
    Recebe webhooks do Instagram Messaging API.
    
    Inclui verificação de hub challenge e processamento de mensagens.
    
    Eventos suportados:
    - messages: Mensagens recebidas
    - messaging_postbacks: Cliques em botões
    - messaging_reactions: Reações a mensagens
    """
    # Hub verification (GET request transformado em POST)
    params = request.query_params
    if "hub.mode" in params:
        verify_token = getattr(
            settings, 'INSTAGRAM_VERIFY_TOKEN', 'default_token'
        )
        if params.get("hub.verify_token") == verify_token:
            return int(params.get("hub.challenge", 0))
        raise HTTPException(403, "Invalid verify token")
    
    # Processar webhook
    try:
        payload = await request.json()
        logger.info(f"Instagram webhook received: {payload}")
        
        # Validar estrutura do payload
        if "object" not in payload or payload["object"] != "instagram":
            logger.warning("Invalid Instagram webhook payload")
            return {"status": "ignored", "reason": "not_instagram"}
        
        entries = payload.get("entry", [])
        if not entries:
            return {"status": "ignored", "reason": "no_entries"}
        
        # Processar cada entrada
        for entry in entries:
            messaging = entry.get("messaging", [])
            
            for message_event in messaging:
                # Extrair dados do remetente
                sender_id = message_event.get("sender", {}).get("id")
                if not sender_id:
                    continue
                
                # Determinar tipo de evento
                if "message" in message_event:
                    # Mensagem de texto ou mídia
                    msg_data = message_event["message"]
                    
                    # Ignorar mensagens echo (enviadas por nós)
                    if msg_data.get("is_echo"):
                        continue
                    
                    # Extrair conteúdo
                    text = msg_data.get("text", "")
                    
                    # Verificar anexos (imagens, áudio, etc)
                    attachments = msg_data.get("attachments", [])
                    media_url = None
                    media_type = None
                    if attachments:
                        first_att = attachments[0]
                        media_type = first_att.get("type")
                        media_url = first_att.get("payload", {}).get("url")
                    
                    # Criar mensagem para o bot
                    incoming = IncomingMessage(
                        channel=MessageChannel.INSTAGRAM,
                        sender_id=sender_id,
                        content=text,
                        media_url=media_url,
                        media_type=media_type,
                        raw_payload=message_event,
                    )
                    
                    # Processar com o bot
                    bot = get_bot()
                    responses = await bot.process_message(incoming)
                    
                    # Enviar respostas via Instagram API
                    for response in responses:
                        await _send_instagram_message(
                            recipient_id=sender_id,
                            text=response.text,
                            quick_replies=response.quick_replies,
                        )
                
                elif "postback" in message_event:
                    # Clique em botão
                    postback = message_event["postback"]
                    payload_text = postback.get("payload", "")
                    
                    incoming = IncomingMessage(
                        channel=MessageChannel.INSTAGRAM,
                        sender_id=sender_id,
                        content=payload_text,
                        raw_payload=message_event,
                    )
                    
                    bot = get_bot()
                    responses = await bot.process_message(incoming)
                    
                    for response in responses:
                        await _send_instagram_message(
                            recipient_id=sender_id,
                            text=response.text,
                        )
                
                elif "reaction" in message_event:
                    # Reação - apenas logar
                    reaction = message_event["reaction"]
                    logger.info(
                        f"Instagram reaction from {sender_id}: "
                        f"{reaction.get('emoji', 'unknown')}"
                    )
        
        return {"status": "processed"}
        
    except Exception as e:
        logger.exception(f"Error processing Instagram webhook: {e}")
        # Retornar 200 para evitar reenvios
        return {"status": "error", "message": str(e)}


async def _send_instagram_message(
    recipient_id: str,
    text: str,
    quick_replies: list[str] | None = None,
):
    """
    Envia mensagem via Instagram Messaging API.
    
    Requer INSTAGRAM_ACCESS_TOKEN configurado.
    """
    import httpx
    
    access_token = getattr(settings, 'INSTAGRAM_ACCESS_TOKEN', None)
    if not access_token:
        logger.warning("INSTAGRAM_ACCESS_TOKEN not configured")
        return
    
    page_id = getattr(settings, 'INSTAGRAM_PAGE_ID', None)
    if not page_id:
        logger.warning("INSTAGRAM_PAGE_ID not configured")
        return
    
    url = f"https://graph.facebook.com/v18.0/{page_id}/messages"
    
    message_data: dict = {"text": text}
    
    # Adicionar quick replies se houver
    if quick_replies:
        message_data["quick_replies"] = [
            {"content_type": "text", "title": qr, "payload": qr}
            for qr in quick_replies[:13]  # Limite de 13 quick replies
        ]
    
    payload = {
        "recipient": {"id": recipient_id},
        "message": message_data,
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                params={"access_token": access_token},
                timeout=10.0,
            )
            
            if response.status_code != 200:
                logger.error(
                    f"Instagram send failed: {response.status_code} "
                    f"{response.text}"
                )
            else:
                logger.debug(f"Instagram message sent to {recipient_id}")
                
    except Exception as e:
        logger.error(f"Error sending Instagram message: {e}")


# ============================================
# DIRECT MESSAGE ENDPOINT (PARA TESTES)
# ============================================

@router.post("/message")
async def send_direct_message(
    request: DirectMessageRequest,
    bot: ProfessionalSellerBot = Depends(get_bot),
):
    """
    Endpoint direto para enviar mensagem ao bot.
    
    Útil para:
    - Testes
    - Integração com frontend
    - Debugging
    """
    try:
        # Mapear canal
        channel_map = {
            "whatsapp": MessageChannel.WHATSAPP,
            "instagram": MessageChannel.INSTAGRAM,
            "webchat": MessageChannel.WEBCHAT,
            "tiktok": MessageChannel.TIKTOK,
            "telegram": MessageChannel.TELEGRAM,
        }
        channel = channel_map.get(
            request.channel.lower(), MessageChannel.WEBCHAT
        )
        
        # Criar mensagem
        message = IncomingMessage(
            channel=channel,
            sender_id=request.sender_id,
            sender_name=request.sender_name,
            content=request.content,
            media_url=request.media_url,
        )
        
        # Processar
        responses = await bot.process_message(message)
        
        return {
            "status": "success",
            "responses": [
                {
                    "content": r.content,
                    "quick_replies": r.quick_replies,
                    "intent": (
                        r.intent_detected.value
                        if r.intent_detected else None
                    ),
                    "should_handoff": r.should_handoff,
                }
                for r in responses
            ]
        }
        
    except Exception as e:
        logger.exception(f"Erro ao processar mensagem: {e}")
        raise HTTPException(500, str(e))


# ============================================
# CONVERSATION MANAGEMENT
# ============================================

@router.get("/conversations")
async def list_conversations(
    active_only: bool = True,
    channel: Optional[str] = None,
    stage: Optional[str] = None,
    lead_temperature: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    bot: ProfessionalSellerBot = Depends(get_bot),
):
    """Lista conversas ativas."""
    try:
        conversations = []
        
        for key, ctx in bot._contexts.items():
            # Filtros
            if active_only and not ctx.is_active:
                continue
            if channel and ctx.channel.value != channel:
                continue
            if stage and ctx.stage.value != stage:
                continue
            if lead_temperature:
                if ctx.lead_temperature.value != lead_temperature:
                    continue
            
            conversations.append({
                "conversation_id": ctx.conversation_id,
                "user_id": ctx.user_id,
                "channel": ctx.channel.value,
                "stage": ctx.stage.value,
                "lead_temperature": ctx.lead_temperature.value,
                "lead_score": ctx.lead_score,
                "message_count": ctx.message_count,
                "is_active": ctx.is_active,
                "last_interaction": ctx.last_interaction.isoformat(),
                "user_name": ctx.user_name,
            })
        
        # Ordenar por última interação
        conversations.sort(key=lambda x: x["last_interaction"], reverse=True)
        
        # Paginação
        total = len(conversations)
        conversations = conversations[offset:offset + limit]
        
        return {
            "items": conversations,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
        
    except Exception as e:
        logger.exception(f"Erro ao listar conversas: {e}")
        raise HTTPException(500, str(e))


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    bot: ProfessionalSellerBot = Depends(get_bot),
):
    """Obtém detalhes de uma conversa."""
    for key, ctx in bot._contexts.items():
        if ctx.conversation_id == conversation_id:
            return ConversationResponse(
                conversation_id=ctx.conversation_id,
                user_id=ctx.user_id,
                channel=ctx.channel.value,
                stage=ctx.stage.value,
                lead_temperature=ctx.lead_temperature.value,
                lead_score=ctx.lead_score,
                message_count=ctx.message_count,
                is_active=ctx.is_active,
                last_interaction=ctx.last_interaction,
                interested_products=ctx.interested_products,
                search_history=ctx.search_history,
            )
    
    raise HTTPException(404, "Conversa não encontrada")


@router.post("/conversations/{conversation_id}/handoff")
async def handoff_conversation(
    conversation_id: str,
    reason: str = "manual",
    agent_id: Optional[int] = None,
    bot: ProfessionalSellerBot = Depends(get_bot),
    router: ChannelRouter = Depends(get_channel_router),
):
    """Escala conversa para atendimento humano."""
    for key, ctx in bot._contexts.items():
        if ctx.conversation_id == conversation_id:
            ctx.stage = ConversationStage.HUMAN_HANDOFF
            ctx.is_active = False
            
            # Se usando Chatwoot
            chatwoot = router.get_adapter(MessageChannel.WEBCHAT)
            if chatwoot and hasattr(chatwoot, 'handoff_to_human'):
                await chatwoot.handoff_to_human(
                    ctx.metadata.get("conversation_id", conversation_id),
                    reason
                )
            
            return {"status": "success", "reason": reason}
    
    raise HTTPException(404, "Conversa não encontrada")


@router.delete("/conversations/{conversation_id}")
async def close_conversation(
    conversation_id: str,
    bot: ProfessionalSellerBot = Depends(get_bot),
):
    """Fecha/encerra uma conversa."""
    for key, ctx in bot._contexts.items():
        if ctx.conversation_id == conversation_id:
            ctx.is_active = False
            return {"status": "closed"}
    
    raise HTTPException(404, "Conversa não encontrada")


# ============================================
# ANALYTICS
# ============================================

@router.get("/stats")
async def get_bot_stats(
    bot: ProfessionalSellerBot = Depends(get_bot),
) -> BotStatsResponse:
    """Retorna estatísticas do bot."""
    try:
        contexts = list(bot._contexts.values())
        
        # Calcular métricas
        total = len(contexts)
        active = sum(1 for c in contexts if c.is_active)
        
        # Distribuição de leads
        lead_dist = {}
        for temp in LeadTemperature:
            lead_dist[temp.value] = sum(
                1 for c in contexts if c.lead_temperature == temp
            )
        
        # Top intents (todos os históricos)
        intent_counts = {}
        for ctx in contexts:
            for intent in ctx.intents_detected:
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        top_intents = sorted(
            [{"intent": k, "count": v} for k, v in intent_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]

        # Calcular totais
        total_messages = sum(c.message_count for c in contexts)
        handoffs = sum(
            1 for c in contexts
            if c.stage == ConversationStage.HUMAN_HANDOFF
        )

        return BotStatsResponse(
            total_conversations=total,
            active_conversations=active,
            messages_today=total_messages,
            handoffs_today=handoffs,
            avg_response_time_ms=250.0,  # TODO: calcular real
            top_intents=top_intents,
            lead_distribution=lead_dist,
        )
        
    except Exception as e:
        logger.exception(f"Erro ao obter stats: {e}")
        raise HTTPException(500, str(e))


@router.get("/stats/intents")
async def get_intent_distribution(
    days: int = 7,
    bot: ProfessionalSellerBot = Depends(get_bot),
):
    """Distribuição de intenções no período."""
    # Agregar de todos os contextos
    intent_counts = {}
    for ctx in bot._contexts.values():
        for intent in ctx.intents_detected:
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    return {
        "period_days": days,
        "intents": sorted(
            [{"intent": k, "count": v} for k, v in intent_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )
    }


@router.get("/stats/funnel")
async def get_funnel_stats(
    bot: ProfessionalSellerBot = Depends(get_bot),
):
    """Estatísticas do funil de conversão."""
    stages = {}
    for stage in ConversationStage:
        stages[stage.value] = sum(
            1 for c in bot._contexts.values()
            if c.stage == stage
        )
    
    return {
        "stages": stages,
        "total": len(bot._contexts),
    }


# ============================================
# CONFIGURATION
# ============================================

@router.get("/config")
async def get_bot_config():
    """Retorna configuração atual do bot."""
    return {
        "greeting_enabled": True,
        "ai_responses_enabled": True,
        "typing_delay_ms": 1000,
        "handoff_after_unknown": 3,
        "channels": {
            "whatsapp": hasattr(settings, 'EVOLUTION_API_KEY'),
            "chatwoot": hasattr(settings, 'CHATWOOT_API_TOKEN'),
            "instagram": hasattr(settings, 'INSTAGRAM_ACCESS_TOKEN'),
        }
    }


@router.patch("/config")
async def update_bot_config(config: BotConfigRequest):
    """Atualiza configuração do bot."""
    # Em produção, salvar em banco/Redis
    logger.info(f"Config atualizada: {config.dict(exclude_none=True)}")
    return {"status": "updated", "config": config.dict(exclude_none=True)}


# ============================================
# HELPER FUNCTIONS
# ============================================

async def _process_message(
    bot: ProfessionalSellerBot,
    router: ChannelRouter,
    message: IncomingMessage,
    raw_payload: Dict[str, Any],
):
    """Processa mensagem em background."""
    try:
        # Processar com o bot
        responses = await bot.process_message(message)
        
        # Determinar recipient
        if message.channel == MessageChannel.WEBCHAT:
            # Para Chatwoot, usar conversation_id
            recipient = message.metadata.get(
                "conversation_id", message.sender_id
            )
        else:
            recipient = message.sender_id
        
        # Enviar respostas
        for response in responses:
            # Aguardar delay se configurado
            if response.delay_ms > 0:
                await router.send_typing(
                    message.channel, recipient, response.delay_ms
                )
            
            await router.send_response(message.channel, response, recipient)
            
            # Se deve escalar
            if response.should_handoff:
                adapter = router.get_adapter(message.channel)
                if hasattr(adapter, 'handoff_to_human'):
                    await adapter.handoff_to_human(
                        recipient,
                        response.handoff_reason or "bot_escalation"
                    )
        
    except Exception as e:
        logger.exception(f"Erro ao processar mensagem em background: {e}")


# ============================================
# HEALTH CHECK
# ============================================

@router.get("/health")
async def health_check():
    """Health check do seller bot."""
    adapters_count = (
        len(_channel_router._adapters) if _channel_router else 0
    )
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bot_active": _bot_instance is not None,
        "adapters_registered": adapters_count,
    }
