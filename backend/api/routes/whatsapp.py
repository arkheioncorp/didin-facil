"""
WhatsApp Routes (Legacy v1)
===========================
Rotas legadas usando WhatsApp Hub.

NOTA: Este módulo está em modo de compatibilidade.
Para novas implementações, use /api/v2/whatsapp/* (whatsapp_v2.py)

Migração:
- Todas as chamadas agora usam o Hub centralizado
- Backward compatible com chamadas antigas
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid
import logging

from shared.config import settings
from integrations.whatsapp_hub import get_whatsapp_hub, WhatsAppHub
from api.middleware.auth import get_current_user
from api.database.connection import database
from api.database.models import WhatsAppInstance, WhatsAppMessage

logger = logging.getLogger(__name__)

router = APIRouter()

# Hub singleton
_hub: Optional[WhatsAppHub] = None


def get_hub() -> WhatsAppHub:
    """Retorna o hub WhatsApp singleton."""
    global _hub
    if _hub is None:
        _hub = get_whatsapp_hub()
    return _hub


class WhatsAppInstanceCreate(BaseModel):
    instance_name: str
    webhook_url: Optional[str] = None


class WhatsAppMessageSend(BaseModel):
    instance_name: str
    to: str
    content: str


@router.post("/instances")
async def create_instance(
    data: WhatsAppInstanceCreate,
    current_user=Depends(get_current_user)
):
    """Create a new WhatsApp instance using Hub."""
    hub = get_hub()
    try:
        webhook_url = data.webhook_url or f"{settings.API_URL}/whatsapp/webhook"
        result = await hub.create_instance(
            instance_name=data.instance_name,
            webhook_url=webhook_url
        )

        # Save instance to DB
        query = WhatsAppInstance.__table__.insert().values(
            id=uuid.uuid4(),
            user_id=current_user.id,
            name=data.instance_name,
            status="created",
            webhook_url=webhook_url,
            created_at=datetime.now(timezone.utc)
        )
        await database.execute(query)

        return result
    except Exception as e:
        logger.error(f"Erro ao criar instância: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/instances/{instance_name}/qrcode")
async def get_qrcode(
    instance_name: str,
    current_user=Depends(get_current_user)
):
    """Get QR Code for instance using Hub."""
    hub = get_hub()
    try:
        qr_code = await hub.get_qr_code(instance_name=instance_name)
        return qr_code
    except Exception as e:
        logger.error(f"Erro ao obter QR code: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/messages/text")
async def send_message(
    data: WhatsAppMessageSend,
    current_user=Depends(get_current_user)
):
    """Send text message using Hub."""
    hub = get_hub()
    try:
        result = await hub.send_message(
            instance_name=data.instance_name,
            to=data.to,
            message=data.content
        )

        # Get instance ID
        instance_query = WhatsAppInstance.__table__.select().where(
            WhatsAppInstance.name == data.instance_name
        )
        instance = await database.fetch_one(instance_query)

        if instance:
            # Save message to DB
            msg_query = WhatsAppMessage.__table__.insert().values(
                id=uuid.uuid4(),
                instance_id=instance.id,
                remote_jid=data.to,
                from_me=True,
                content=data.content,
                message_type="text",
                status="sent",
                timestamp=datetime.now(timezone.utc)
            )
            await database.execute(msg_query)

        return result
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    Handle WhatsApp Webhooks from Evolution API.

    Processa eventos de conexão, QR Code e mensagens.
    """
    payload = await request.json()

    # Extract event info from Evolution API payload
    event_type = payload.get("event")
    instance_name = payload.get("instance")
    data = payload.get("data", {})

    if not instance_name:
        return {"status": "ignored", "reason": "no_instance"}

    # Find instance in DB
    instance_query = WhatsAppInstance.__table__.select().where(
        WhatsAppInstance.name == instance_name
    )
    instance = await database.fetch_one(instance_query)

    if not instance:
        return {"status": "ignored", "reason": "instance_not_found"}

    # Handle connection status updates
    if event_type == "connection.update":
        connection_state = data.get("state", "")

        # Map Evolution API states to our status
        status_map = {
            "open": "connected",
            "close": "disconnected",
            "connecting": "connecting",
            "refused": "error"
        }
        new_status = status_map.get(connection_state, "unknown")

        # Update instance status in DB
        update_query = WhatsAppInstance.__table__.update().where(
            WhatsAppInstance.id == instance.id
        ).values(
            status=new_status,
            updated_at=datetime.now(timezone.utc)
        )
        await database.execute(update_query)

        # If disconnected, try to reconnect automatically
        if new_status == "disconnected":
            await _schedule_reconnection(instance_name, str(instance.user_id))

        return {
            "status": "processed",
            "event": "connection.update",
            "new_status": new_status
        }

    # Handle QR code updates
    if event_type == "qrcode.updated":
        qr_code = data.get("qrcode", {})

        # Store QR code temporarily in Redis for frontend polling
        from shared.redis import get_redis
        redis = await get_redis()
        await redis.set(
            f"whatsapp:qrcode:{instance_name}",
            qr_code.get("base64", ""),
            ex=120  # QR codes expire in 2 minutes
        )

        # Update status to awaiting scan
        update_query = WhatsAppInstance.__table__.update().where(
            WhatsAppInstance.id == instance.id
        ).values(
            status="awaiting_scan",
            updated_at=datetime.now(timezone.utc)
        )
        await database.execute(update_query)

        return {"status": "processed", "event": "qrcode.updated"}

    # Handle messages
    if event_type == "messages.upsert":
        message_data = data.get("message", {})
        key = data.get("key", {})
        remote_jid = key.get("remoteJid")
        from_me = key.get("fromMe", False)

        # Extract content
        content = ""
        if "conversation" in message_data:
            content = message_data["conversation"]
        elif "extendedTextMessage" in message_data:
            content = message_data["extendedTextMessage"].get("text", "")

        if content:
            msg_query = WhatsAppMessage.__table__.insert().values(
                id=uuid.uuid4(),
                instance_id=instance.id,
                remote_jid=remote_jid,
                from_me=from_me,
                content=content,
                message_type="text",
                status="delivered",
                timestamp=datetime.now(timezone.utc),
                message_id=key.get("id")
            )
            await database.execute(msg_query)

    return {"status": "processed"}


async def _schedule_reconnection(instance_name: str, user_id: str):
    """
    Agenda tentativa de reconexão para instância desconectada.
    
    Usa exponential backoff para evitar sobrecarga.
    """
    from shared.redis import get_redis
    import json
    
    redis = await get_redis()
    
    # Verificar tentativas anteriores
    reconnect_key = f"whatsapp:reconnect:{instance_name}"
    reconnect_data = await redis.get(reconnect_key)
    
    if reconnect_data:
        data = json.loads(reconnect_data)
        attempts = data.get("attempts", 0)
        
        # Máximo 5 tentativas
        if attempts >= 5:
            return
        
        # Incrementar tentativas
        data["attempts"] = attempts + 1
    else:
        data = {"attempts": 1, "instance_name": instance_name}
    
    # Calcular delay (exponential backoff)
    delay = min(300, 30 * (2 ** (data["attempts"] - 1)))  # Max 5 min
    
    # Salvar estado
    await redis.set(reconnect_key, json.dumps(data), ex=3600)  # 1 hora
    
    # Agendar reconexão (via worker ou background task)
    await redis.zadd(
        "whatsapp:pending_reconnections",
        {instance_name: datetime.now(timezone.utc).timestamp() + delay}
    )


@router.get("/instances/{instance_name}/status")
async def get_instance_status(
    instance_name: str,
    current_user=Depends(get_current_user)
):
    """
    Get real-time status of a WhatsApp instance.
    
    Retorna status atual, QR code (se aguardando scan) e info de reconexão.
    """
    # Find instance
    instance_query = WhatsAppInstance.__table__.select().where(
        WhatsAppInstance.name == instance_name
    )
    instance = await database.fetch_one(instance_query)
    
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # Check ownership
    if instance.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    from shared.redis import get_redis
    import json
    
    redis = await get_redis()
    
    # Get QR code if available
    qr_code = await redis.get(f"whatsapp:qrcode:{instance_name}")
    
    # Get reconnection info
    reconnect_data = await redis.get(f"whatsapp:reconnect:{instance_name}")
    reconnect_info = json.loads(reconnect_data) if reconnect_data else None
    
    return {
        "instance_name": instance_name,
        "status": instance.status,
        "qr_code": qr_code if instance.status == "awaiting_scan" else None,
        "reconnection": reconnect_info,
        "updated_at": (
            instance.updated_at.isoformat()
            if hasattr(instance, 'updated_at') and instance.updated_at
            else None
        )
    }


@router.post("/instances/{instance_name}/reconnect")
async def force_reconnect(
    instance_name: str,
    current_user=Depends(get_current_user)
):
    """Force reconnection attempt for a disconnected instance using Hub."""
    hub = get_hub()
    
    # Find instance
    instance_query = WhatsAppInstance.__table__.select().where(
        WhatsAppInstance.name == instance_name
    )
    instance = await database.fetch_one(instance_query)

    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    if instance.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Try to reconnect via Hub
    try:
        result = await hub.get_qr_code(instance_name=instance_name)

        # Update status
        update_query = WhatsAppInstance.__table__.update().where(
            WhatsAppInstance.id == instance.id
        ).values(
            status="connecting",
            updated_at=datetime.now(timezone.utc)
        )
        await database.execute(update_query)

        return {
            "status": "reconnecting",
            "qr_code": result.get("base64") if result else None
        }
    except Exception as e:
        logger.error(f"Erro ao reconectar: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/messages/{instance_name}")
async def list_messages(
    instance_name: str,
    limit: int = 50,
    offset: int = 0,
    current_user=Depends(get_current_user)
):
    """List messages for an instance"""
    # Find instance
    instance_query = WhatsAppInstance.__table__.select().where(
        WhatsAppInstance.name == instance_name
    )
    instance = await database.fetch_one(instance_query)

    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    # Check ownership
    if instance.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Fetch messages
    query = WhatsAppMessage.__table__.select().where(
        WhatsAppMessage.instance_id == instance.id
    ).order_by(WhatsAppMessage.timestamp.desc()).limit(limit).offset(offset)
    
    messages = await database.fetch_all(query)
    return messages

