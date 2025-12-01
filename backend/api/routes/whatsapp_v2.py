"""
WhatsApp Routes V2
=================
Rotas unificadas usando o WhatsApp Hub centralizado.

Este módulo substitui as rotas antigas em whatsapp.py,
usando o hub unificado em integrations/whatsapp_hub.py.

Migração:
- /api/v1/whatsapp/* -> /api/v2/whatsapp/*
- Backward compatible com v1 durante período de transição
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid
import logging

from integrations.whatsapp_hub import (
    WhatsAppHub,
    WhatsAppMessage,
    InstanceInfo,
    MessageType,
    ConnectionState,
    get_whatsapp_hub,
)
from api.middleware.auth import get_current_user
from api.database.connection import database
from api.database.models import WhatsAppInstance, WhatsAppMessage as DBWhatsAppMessage
from shared.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2/whatsapp", tags=["WhatsApp Hub"])


# ============================================
# SCHEMAS
# ============================================

class InstanceCreate(BaseModel):
    """Schema para criar instância."""
    instance_name: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-z0-9-]+$")
    webhook_url: Optional[str] = None
    auto_configure_webhook: bool = True


class InstanceResponse(BaseModel):
    """Response de instância."""
    name: str
    state: str
    phone_connected: Optional[str] = None
    webhook_url: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class WebhookConfigRequest(BaseModel):
    """Request para configurar webhook."""
    url: str
    events: Optional[List[str]] = None


class SendTextRequest(BaseModel):
    """Request para enviar texto."""
    to: str = Field(..., description="Número do destinatário")
    text: str = Field(..., min_length=1, max_length=4096)
    instance_name: Optional[str] = None
    delay_ms: int = Field(default=0, ge=0, le=5000)


class SendMediaRequest(BaseModel):
    """Request para enviar mídia."""
    to: str
    media_url: str
    caption: Optional[str] = None
    instance_name: Optional[str] = None


class SendLocationRequest(BaseModel):
    """Request para enviar localização."""
    to: str
    latitude: float
    longitude: float
    name: Optional[str] = None
    address: Optional[str] = None
    instance_name: Optional[str] = None


class SendButtonsRequest(BaseModel):
    """Request para enviar botões."""
    to: str
    title: str
    description: str
    buttons: List[Dict[str, Any]]
    footer: Optional[str] = None
    instance_name: Optional[str] = None


class SendListRequest(BaseModel):
    """Request para enviar lista."""
    to: str
    title: str
    description: str
    button_text: str
    sections: List[Dict[str, Any]]
    footer: Optional[str] = None
    instance_name: Optional[str] = None


class MessageResponse(BaseModel):
    """Response de envio de mensagem."""
    success: bool
    message_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class CheckNumberRequest(BaseModel):
    """Request para verificar número."""
    phone: str
    instance_name: Optional[str] = None


class CheckNumberResponse(BaseModel):
    """Response de verificação de número."""
    phone: str
    exists: bool
    formatted: Optional[str] = None


# ============================================
# INSTANCE MANAGEMENT ROUTES
# ============================================

@router.post("/instances", response_model=InstanceResponse)
async def create_instance(
    data: InstanceCreate,
    current_user=Depends(get_current_user)
):
    """
    Cria uma nova instância do WhatsApp.
    
    - **instance_name**: Nome único (apenas letras minúsculas, números e hífens)
    - **webhook_url**: URL opcional para webhooks
    - **auto_configure_webhook**: Se True, configura webhook automaticamente
    """
    hub = get_whatsapp_hub()
    
    try:
        # Configura webhook URL
        webhook_url = data.webhook_url
        if data.auto_configure_webhook and not webhook_url:
            webhook_url = f"{settings.API_URL}/api/v2/whatsapp/webhook"
        
        instance = await hub.create_instance(
            instance_name=data.instance_name,
            webhook_url=webhook_url
        )
        
        # Salva no banco
        query = WhatsAppInstance.__table__.insert().values(
            id=uuid.uuid4(),
            user_id=current_user["id"],
            name=data.instance_name,
            status="created",
            webhook_url=webhook_url,
            created_at=datetime.now(timezone.utc)
        )
        await database.execute(query)
        
        return InstanceResponse(
            name=instance.name,
            state=instance.state.value,
            webhook_url=webhook_url,
            created_at=instance.created_at
        )
        
    except Exception as e:
        logger.error(f"Erro ao criar instância: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/instances", response_model=List[InstanceResponse])
async def list_instances(
    current_user=Depends(get_current_user)
):
    """Lista todas as instâncias do usuário."""
    hub = get_whatsapp_hub()
    
    try:
        instances = await hub.list_instances()
        
        # Filtra por usuário (opcional - admin vê todas)
        if not getattr(current_user, 'is_admin', False):
            user_instances = await database.fetch_all(
                WhatsAppInstance.__table__.select().where(
                    WhatsAppInstance.user_id == current_user["id"]
                )
            )
            user_instance_names = {inst.name for inst in user_instances}
            instances = [i for i in instances if i.name in user_instance_names]
        
        return [
            InstanceResponse(
                name=inst.name,
                state=inst.state.value,
                phone_connected=inst.phone_connected
            )
            for inst in instances
        ]
        
    except Exception as e:
        logger.error(f"Erro ao listar instâncias: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instances/{instance_name}", response_model=InstanceResponse)
async def get_instance(
    instance_name: str,
    current_user=Depends(get_current_user)
):
    """Retorna status detalhado de uma instância."""
    hub = get_whatsapp_hub()
    
    # Verifica permissão
    db_instance = await database.fetch_one(
        WhatsAppInstance.__table__.select().where(
            WhatsAppInstance.name == instance_name
        )
    )
    
    if not db_instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada")
    
    if db_instance.user_id != current_user["id"] and not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        instance = await hub.get_instance_status(instance_name)
        return InstanceResponse(
            name=instance.name,
            state=instance.state.value,
            phone_connected=instance.phone_connected,
            webhook_url=db_instance.webhook_url
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/instances/{instance_name}/qrcode")
async def get_qr_code(
    instance_name: str,
    current_user=Depends(get_current_user)
):
    """
    Retorna QR Code para conectar a instância.
    
    O QR Code é retornado em base64 e como código texto.
    """
    hub = get_whatsapp_hub()
    
    # Verifica permissão
    await _verify_instance_access(instance_name, current_user)
    
    try:
        qr_data = await hub.get_qr_code(instance_name)
        return {
            "instance_name": instance_name,
            "qr_code": qr_data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/instances/{instance_name}")
async def delete_instance(
    instance_name: str,
    current_user=Depends(get_current_user)
):
    """Remove uma instância do WhatsApp."""
    hub = get_whatsapp_hub()
    
    # Verifica permissão
    db_instance = await _verify_instance_access(instance_name, current_user)
    
    try:
        success = await hub.delete_instance(instance_name)
        
        if success:
            # Remove do banco
            await database.execute(
                WhatsAppInstance.__table__.delete().where(
                    WhatsAppInstance.id == db_instance.id
                )
            )
        
        return {"success": success, "instance_name": instance_name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/instances/{instance_name}/disconnect")
async def disconnect_instance(
    instance_name: str,
    current_user=Depends(get_current_user)
):
    """Desconecta uma instância (logout do WhatsApp)."""
    hub = get_whatsapp_hub()
    
    await _verify_instance_access(instance_name, current_user)
    
    try:
        success = await hub.disconnect_instance(instance_name)
        return {"success": success, "instance_name": instance_name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# WEBHOOK CONFIGURATION
# ============================================

@router.post("/instances/{instance_name}/webhook")
async def configure_webhook(
    instance_name: str,
    data: WebhookConfigRequest,
    current_user=Depends(get_current_user)
):
    """Configura webhook para uma instância."""
    hub = get_whatsapp_hub()
    
    await _verify_instance_access(instance_name, current_user)
    
    try:
        success = await hub.configure_webhook(
            webhook_url=data.url,
            instance_name=instance_name,
            events=data.events
        )
        
        if success:
            # Atualiza no banco
            await database.execute(
                WhatsAppInstance.__table__.update().where(
                    WhatsAppInstance.name == instance_name
                ).values(
                    webhook_url=data.url,
                    updated_at=datetime.now(timezone.utc)
                )
            )
        
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/instances/{instance_name}/webhook")
async def get_webhook_config(
    instance_name: str,
    current_user=Depends(get_current_user)
):
    """Retorna configuração atual do webhook."""
    hub = get_whatsapp_hub()
    
    await _verify_instance_access(instance_name, current_user)
    
    try:
        config = await hub.get_webhook_config(instance_name)
        return config
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# MESSAGING ROUTES
# ============================================

@router.post("/send/text", response_model=MessageResponse)
async def send_text_message(
    data: SendTextRequest,
    current_user=Depends(get_current_user)
):
    """
    Envia mensagem de texto.
    
    - **to**: Número no formato 5511999999999
    - **text**: Texto da mensagem (máx 4096 caracteres)
    - **delay_ms**: Delay antes de enviar (simula digitação)
    """
    hub = get_whatsapp_hub()
    
    instance_name = data.instance_name or settings.EVOLUTION_INSTANCE
    
    try:
        result = await hub.send_text(
            to=data.to,
            text=data.text,
            instance_name=instance_name,
            delay_ms=data.delay_ms
        )
        
        # Log da mensagem
        await _log_outgoing_message(
            instance_name=instance_name,
            to=data.to,
            content=data.text,
            message_type="text"
        )
        
        return MessageResponse(
            success=True,
            message_id=result.get("key", {}).get("id"),
            details=result
        )
    except Exception as e:
        logger.error(f"Erro ao enviar texto: {e}")
        return MessageResponse(success=False, details={"error": str(e)})


@router.post("/send/image", response_model=MessageResponse)
async def send_image(
    data: SendMediaRequest,
    current_user=Depends(get_current_user)
):
    """Envia imagem."""
    hub = get_whatsapp_hub()
    
    instance_name = data.instance_name or settings.EVOLUTION_INSTANCE
    
    try:
        result = await hub.send_image(
            to=data.to,
            image_url=data.media_url,
            caption=data.caption,
            instance_name=instance_name
        )
        
        await _log_outgoing_message(
            instance_name=instance_name,
            to=data.to,
            content=data.caption or "[IMAGE]",
            message_type="image"
        )
        
        return MessageResponse(
            success=True,
            message_id=result.get("key", {}).get("id"),
            details=result
        )
    except Exception as e:
        logger.error(f"Erro ao enviar imagem: {e}")
        return MessageResponse(success=False, details={"error": str(e)})


@router.post("/send/video", response_model=MessageResponse)
async def send_video(
    data: SendMediaRequest,
    current_user=Depends(get_current_user)
):
    """Envia vídeo."""
    hub = get_whatsapp_hub()
    
    instance_name = data.instance_name or settings.EVOLUTION_INSTANCE
    
    try:
        result = await hub.send_video(
            to=data.to,
            video_url=data.media_url,
            caption=data.caption,
            instance_name=instance_name
        )
        
        await _log_outgoing_message(
            instance_name=instance_name,
            to=data.to,
            content=data.caption or "[VIDEO]",
            message_type="video"
        )
        
        return MessageResponse(
            success=True,
            message_id=result.get("key", {}).get("id"),
            details=result
        )
    except Exception as e:
        logger.error(f"Erro ao enviar vídeo: {e}")
        return MessageResponse(success=False, details={"error": str(e)})


@router.post("/send/audio", response_model=MessageResponse)
async def send_audio(
    to: str,
    audio_url: str,
    as_voice: bool = True,
    instance_name: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """
    Envia áudio.
    
    - **as_voice**: Se True, envia como mensagem de voz (bolinha)
    """
    hub = get_whatsapp_hub()
    
    inst = instance_name or settings.EVOLUTION_INSTANCE
    
    try:
        result = await hub.send_audio(
            to=to,
            audio_url=audio_url,
            as_voice_message=as_voice,
            instance_name=inst
        )
        
        return MessageResponse(
            success=True,
            message_id=result.get("key", {}).get("id"),
            details=result
        )
    except Exception as e:
        return MessageResponse(success=False, details={"error": str(e)})


@router.post("/send/document", response_model=MessageResponse)
async def send_document(
    to: str,
    document_url: str,
    filename: str,
    caption: Optional[str] = None,
    instance_name: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """Envia documento."""
    hub = get_whatsapp_hub()
    
    inst = instance_name or settings.EVOLUTION_INSTANCE
    
    try:
        result = await hub.send_document(
            to=to,
            document_url=document_url,
            filename=filename,
            caption=caption,
            instance_name=inst
        )
        
        return MessageResponse(
            success=True,
            message_id=result.get("key", {}).get("id"),
            details=result
        )
    except Exception as e:
        return MessageResponse(success=False, details={"error": str(e)})


@router.post("/send/location", response_model=MessageResponse)
async def send_location(
    data: SendLocationRequest,
    current_user=Depends(get_current_user)
):
    """Envia localização."""
    hub = get_whatsapp_hub()
    
    instance_name = data.instance_name or settings.EVOLUTION_INSTANCE
    
    try:
        result = await hub.send_location(
            to=data.to,
            latitude=data.latitude,
            longitude=data.longitude,
            name=data.name,
            address=data.address,
            instance_name=instance_name
        )
        
        return MessageResponse(
            success=True,
            message_id=result.get("key", {}).get("id"),
            details=result
        )
    except Exception as e:
        return MessageResponse(success=False, details={"error": str(e)})


@router.post("/send/buttons", response_model=MessageResponse)
async def send_buttons(
    data: SendButtonsRequest,
    current_user=Depends(get_current_user)
):
    """
    Envia mensagem com botões interativos.
    
    Exemplo de buttons:
    ```json
    [
        {"buttonId": "1", "buttonText": {"displayText": "Opção 1"}},
        {"buttonId": "2", "buttonText": {"displayText": "Opção 2"}}
    ]
    ```
    """
    hub = get_whatsapp_hub()
    
    instance_name = data.instance_name or settings.EVOLUTION_INSTANCE
    
    try:
        result = await hub.send_buttons(
            to=data.to,
            title=data.title,
            description=data.description,
            buttons=data.buttons,
            footer=data.footer,
            instance_name=instance_name
        )
        
        return MessageResponse(
            success=True,
            message_id=result.get("key", {}).get("id"),
            details=result
        )
    except Exception as e:
        return MessageResponse(success=False, details={"error": str(e)})


@router.post("/send/list", response_model=MessageResponse)
async def send_list(
    data: SendListRequest,
    current_user=Depends(get_current_user)
):
    """
    Envia mensagem com lista interativa.
    
    Exemplo de sections:
    ```json
    [
        {
            "title": "Categoria 1",
            "rows": [
                {"rowId": "1", "title": "Item 1", "description": "Descrição"},
                {"rowId": "2", "title": "Item 2", "description": "Descrição"}
            ]
        }
    ]
    ```
    """
    hub = get_whatsapp_hub()
    
    instance_name = data.instance_name or settings.EVOLUTION_INSTANCE
    
    try:
        result = await hub.send_list(
            to=data.to,
            title=data.title,
            description=data.description,
            button_text=data.button_text,
            sections=data.sections,
            footer=data.footer,
            instance_name=instance_name
        )
        
        return MessageResponse(
            success=True,
            message_id=result.get("key", {}).get("id"),
            details=result
        )
    except Exception as e:
        return MessageResponse(success=False, details={"error": str(e)})


# ============================================
# UTILITIES
# ============================================

@router.post("/check-number", response_model=CheckNumberResponse)
async def check_number(
    data: CheckNumberRequest,
    current_user=Depends(get_current_user)
):
    """Verifica se um número tem WhatsApp."""
    hub = get_whatsapp_hub()
    
    instance_name = data.instance_name or settings.EVOLUTION_INSTANCE
    
    try:
        exists = await hub.check_number(data.phone, instance_name)
        formatted = hub._format_phone(data.phone)
        
        return CheckNumberResponse(
            phone=data.phone,
            exists=exists,
            formatted=formatted
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/profile-picture/{phone}")
async def get_profile_picture(
    phone: str,
    instance_name: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """Obtém foto de perfil de um contato."""
    hub = get_whatsapp_hub()
    
    inst = instance_name or settings.EVOLUTION_INSTANCE
    
    try:
        url = await hub.get_profile_picture(phone, inst)
        return {"phone": phone, "profile_picture_url": url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# WEBHOOK HANDLER
# ============================================

@router.post("/webhook")
async def webhook_handler(request: Request):
    """
    Handler centralizado de webhooks do WhatsApp.
    
    Este endpoint recebe todos os eventos da Evolution API e:
    1. Processa através do WhatsApp Hub
    2. Dispara handlers registrados
    3. Salva mensagens no banco
    4. Encaminha para Seller Bot se necessário
    """
    hub = get_whatsapp_hub()
    
    try:
        payload = await request.json()
        event = payload.get("event", "")
        instance_name = payload.get("instance", "")
        
        logger.info(f"Webhook recebido: {event} para {instance_name}")
        
        # Processa pelo hub
        result = await hub.process_webhook(payload)
        
        # Salva mensagem recebida no banco
        if event in ("MESSAGES_UPSERT", "messages.upsert"):
            message = hub.parse_webhook(payload)
            if message and not message.from_me:
                await _save_incoming_message(instance_name, message)
                
                # Encaminha para Seller Bot
                await _forward_to_seller_bot(instance_name, message)
        
        # Atualiza status de conexão no banco
        if event in ("CONNECTION_UPDATE", "connection.update"):
            conn_result = hub.parse_connection_update(payload)
            if conn_result:
                inst_name, state = conn_result
                await _update_instance_status(inst_name, state)
        
        return result
        
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        return {"status": "error", "message": str(e)}


# ============================================
# HELPER FUNCTIONS
# ============================================

async def _verify_instance_access(instance_name: str, current_user) -> Any:
    """Verifica se usuário tem acesso à instância."""
    db_instance = await database.fetch_one(
        WhatsAppInstance.__table__.select().where(
            WhatsAppInstance.name == instance_name
        )
    )
    
    if not db_instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada")
    
    if db_instance.user_id != current_user["id"] and not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    return db_instance


async def _log_outgoing_message(
    instance_name: str,
    to: str,
    content: str,
    message_type: str
):
    """Salva mensagem enviada no banco."""
    try:
        # Busca instância
        instance = await database.fetch_one(
            WhatsAppInstance.__table__.select().where(
                WhatsAppInstance.name == instance_name
            )
        )
        
        if not instance:
            return
        
        # Salva mensagem
        query = DBWhatsAppMessage.__table__.insert().values(
            id=uuid.uuid4(),
            instance_id=instance.id,
            remote_jid=to,
            from_me=True,
            content=content,
            message_type=message_type,
            status="sent",
            timestamp=datetime.now(timezone.utc)
        )
        await database.execute(query)
    except Exception as e:
        logger.error(f"Erro ao salvar mensagem enviada: {e}")


async def _save_incoming_message(instance_name: str, message: WhatsAppMessage):
    """Salva mensagem recebida no banco."""
    try:
        instance = await database.fetch_one(
            WhatsAppInstance.__table__.select().where(
                WhatsAppInstance.name == instance_name
            )
        )
        
        if not instance:
            return
        
        query = DBWhatsAppMessage.__table__.insert().values(
            id=uuid.uuid4(),
            instance_id=instance.id,
            remote_jid=message.remote_jid,
            from_me=False,
            content=message.content,
            message_type=message.message_type.value,
            status="delivered",
            timestamp=message.timestamp,
            message_id=message.message_id
        )
        await database.execute(query)
    except Exception as e:
        logger.error(f"Erro ao salvar mensagem recebida: {e}")


async def _update_instance_status(instance_name: str, state: ConnectionState):
    """Atualiza status da instância no banco."""
    try:
        status_map = {
            ConnectionState.CONNECTED: "connected",
            ConnectionState.DISCONNECTED: "disconnected",
            ConnectionState.CONNECTING: "connecting",
            ConnectionState.AWAITING_SCAN: "awaiting_scan",
            ConnectionState.ERROR: "error",
        }
        
        await database.execute(
            WhatsAppInstance.__table__.update().where(
                WhatsAppInstance.name == instance_name
            ).values(
                status=status_map.get(state, "unknown"),
                updated_at=datetime.now(timezone.utc)
            )
        )
    except Exception as e:
        logger.error(f"Erro ao atualizar status da instância: {e}")


async def _forward_to_seller_bot(instance_name: str, message: WhatsAppMessage):
    """Encaminha mensagem para o Seller Bot."""
    try:
        from modules.chatbot.whatsapp_adapter import WhatsAppHubAdapter
        from modules.chatbot.bot import get_seller_bot
        
        # Obtém o hub
        hub = get_whatsapp_hub()
        
        # Cria adapter com a instância
        adapter = WhatsAppHubAdapter(hub, instance_name)
        
        # Obtém bot
        bot = await get_seller_bot()
        
        # Processa mensagem
        # O adapter espera um payload bruto ou WhatsAppMessage no parse_incoming
        # Mas aqui já temos a mensagem processada.
        # O bot.handle_message espera que o adapter faça o parse.
        # Vamos passar a mensagem diretamente para o adapter converter
        
        incoming_msg = await adapter.parse_incoming(message)
        
        if incoming_msg:
            await bot.process_message(incoming_msg, adapter)
            
    except ImportError:
        # Seller Bot não disponível
        logger.debug("Seller Bot não disponível para processar mensagem")
    except Exception as e:
        logger.error(f"Erro ao encaminhar para Seller Bot: {e}")
