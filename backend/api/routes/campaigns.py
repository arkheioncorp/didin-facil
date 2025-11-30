"""
Email Campaigns Routes
======================
API endpoints para campanhas de email marketing.

Funcionalidades:
- Criação de campanhas
- Segmentação de audiência
- A/B Testing
- Agendamento
- Analytics de campanha
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json

from api.middleware.auth import get_current_user
from api.database.models import User
from shared.redis import get_redis

router = APIRouter()


# ==================== ENUMS ====================


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class CampaignType(str, Enum):
    REGULAR = "regular"
    AUTOMATED = "automated"
    AB_TEST = "ab_test"
    TRANSACTIONAL = "transactional"


class TriggerType(str, Enum):
    IMMEDIATE = "immediate"
    SCHEDULED = "scheduled"
    EVENT_BASED = "event_based"
    RECURRING = "recurring"


# ==================== SCHEMAS ====================


class CampaignCreate(BaseModel):
    """Criar nova campanha."""

    name: str = Field(..., min_length=1, max_length=200)
    subject: str = Field(..., min_length=1, max_length=200)
    preview_text: Optional[str] = Field(None, max_length=150)
    template_id: Optional[str] = None
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    list_ids: List[str] = Field(..., min_items=1)
    type: CampaignType = CampaignType.REGULAR
    trigger: TriggerType = TriggerType.IMMEDIATE
    schedule_at: Optional[datetime] = None

    # Segmentação
    segment_rules: Optional[Dict[str, Any]] = None

    # A/B Test
    ab_test: Optional[Dict[str, Any]] = (
        None  # {"variants": [...], "split_percentage": 50}
    )

    # Tracking
    track_opens: bool = True
    track_clicks: bool = True

    # Reply
    reply_to_email: Optional[EmailStr] = None
    reply_to_name: Optional[str] = None


class CampaignUpdate(BaseModel):
    """Atualizar campanha."""

    name: Optional[str] = None
    subject: Optional[str] = None
    preview_text: Optional[str] = None
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    schedule_at: Optional[datetime] = None


class CampaignResponse(BaseModel):
    """Resposta de campanha."""

    id: str
    name: str
    subject: str
    preview_text: Optional[str]
    status: CampaignStatus
    type: CampaignType
    trigger: TriggerType
    list_ids: List[str]
    recipients_count: int
    schedule_at: Optional[datetime]
    sent_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # Métricas (quando enviada)
    stats: Optional[Dict[str, Any]] = None


class CampaignStats(BaseModel):
    """Estatísticas detalhadas da campanha."""

    campaign_id: str
    total_recipients: int
    total_sent: int
    total_delivered: int
    total_opened: int
    unique_opens: int
    total_clicked: int
    unique_clicks: int
    total_bounced: int
    total_unsubscribed: int
    total_complained: int

    # Taxas
    delivery_rate: float
    open_rate: float
    click_rate: float
    click_to_open_rate: float
    bounce_rate: float
    unsubscribe_rate: float

    # Tempo
    first_open_at: Optional[datetime]
    last_open_at: Optional[datetime]
    avg_open_time_seconds: Optional[int]

    # Links mais clicados
    top_links: List[Dict[str, Any]]

    # Dispositivos
    device_breakdown: Dict[str, int]

    # Localização
    location_breakdown: Dict[str, int]


class ABTestVariant(BaseModel):
    """Variante de teste A/B."""

    id: str
    name: str
    subject: Optional[str] = None
    html_content: Optional[str] = None
    percentage: int = 50

    # Resultados
    sent: int = 0
    opened: int = 0
    clicked: int = 0
    winner: bool = False


class AutomationCreate(BaseModel):
    """Criar automação de email."""

    name: str
    description: Optional[str] = None
    trigger_event: str  # "signup", "purchase", "abandoned_cart", "custom"
    trigger_conditions: Optional[Dict[str, Any]] = None
    delay_minutes: int = 0
    emails: List[Dict[str, Any]]  # Lista de emails na sequência
    active: bool = True


class AutomationResponse(BaseModel):
    """Resposta de automação."""

    id: str
    name: str
    description: Optional[str]
    trigger_event: str
    trigger_conditions: Optional[Dict[str, Any]]
    delay_minutes: int
    emails_count: int
    active: bool
    total_triggered: int
    total_completed: int
    created_at: datetime


# ==================== SERVICE ====================


class CampaignService:
    """Serviço de campanhas."""

    async def create_campaign(
        self, user_id: str, data: CampaignCreate
    ) -> CampaignResponse:
        """Cria nova campanha."""
        redis = await get_redis()

        campaign_id = str(uuid.uuid4())
        now = datetime.now()

        # Calcular total de recipients
        recipients_count = 0
        for list_id in data.list_ids:
            count = await redis.scard(f"email:list:{list_id}:contacts")
            recipients_count += count

        campaign_data = {
            "id": campaign_id,
            "user_id": user_id,
            "name": data.name,
            "subject": data.subject,
            "preview_text": data.preview_text or "",
            "template_id": data.template_id or "",
            "html_content": data.html_content or "",
            "text_content": data.text_content or "",
            "list_ids": json.dumps(data.list_ids),
            "type": data.type.value,
            "trigger": data.trigger.value,
            "status": CampaignStatus.DRAFT.value,
            "schedule_at": data.schedule_at.isoformat() if data.schedule_at else "",
            "recipients_count": str(recipients_count),
            "segment_rules": (
                json.dumps(data.segment_rules) if data.segment_rules else ""
            ),
            "ab_test": json.dumps(data.ab_test) if data.ab_test else "",
            "track_opens": "1" if data.track_opens else "0",
            "track_clicks": "1" if data.track_clicks else "0",
            "reply_to_email": data.reply_to_email or "",
            "reply_to_name": data.reply_to_name or "",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        await redis.hset(f"campaign:{campaign_id}", mapping=campaign_data)
        await redis.sadd(f"campaigns:{user_id}", campaign_id)

        return CampaignResponse(
            id=campaign_id,
            name=data.name,
            subject=data.subject,
            preview_text=data.preview_text,
            status=CampaignStatus.DRAFT,
            type=data.type,
            trigger=data.trigger,
            list_ids=data.list_ids,
            recipients_count=recipients_count,
            schedule_at=data.schedule_at,
            sent_at=None,
            created_at=now,
            updated_at=now,
        )

    async def get_campaign(
        self, user_id: str, campaign_id: str
    ) -> Optional[CampaignResponse]:
        """Busca campanha por ID."""
        redis = await get_redis()
        data = await redis.hgetall(f"campaign:{campaign_id}")

        if not data or data.get("user_id") != user_id:
            return None

        return self._parse_campaign(data)

    async def list_campaigns(
        self,
        user_id: str,
        status: Optional[CampaignStatus] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> List[CampaignResponse]:
        """Lista campanhas do usuário."""
        redis = await get_redis()

        campaign_ids = await redis.smembers(f"campaigns:{user_id}")
        campaigns = []

        for cid in campaign_ids:
            data = await redis.hgetall(f"campaign:{cid}")
            if data:
                if status and data.get("status") != status.value:
                    continue
                campaigns.append(self._parse_campaign(data))

        # Ordenar por data de criação (mais recente primeiro)
        campaigns.sort(key=lambda c: c.created_at, reverse=True)

        # Paginar
        start = (page - 1) * per_page
        return campaigns[start : start + per_page]

    async def update_campaign(
        self, user_id: str, campaign_id: str, data: CampaignUpdate
    ) -> Optional[CampaignResponse]:
        """Atualiza campanha."""
        redis = await get_redis()

        existing = await redis.hgetall(f"campaign:{campaign_id}")
        if not existing or existing.get("user_id") != user_id:
            return None

        # Só permite editar se estiver em DRAFT
        if existing.get("status") != CampaignStatus.DRAFT.value:
            raise HTTPException(
                status_code=400, detail="Só é possível editar campanhas em rascunho"
            )

        updates = {}
        if data.name:
            updates["name"] = data.name
        if data.subject:
            updates["subject"] = data.subject
        if data.preview_text is not None:
            updates["preview_text"] = data.preview_text
        if data.html_content:
            updates["html_content"] = data.html_content
        if data.text_content:
            updates["text_content"] = data.text_content
        if data.schedule_at:
            updates["schedule_at"] = data.schedule_at.isoformat()

        updates["updated_at"] = datetime.now().isoformat()

        await redis.hset(f"campaign:{campaign_id}", mapping=updates)

        return await self.get_campaign(user_id, campaign_id)

    async def send_campaign(
        self, user_id: str, campaign_id: str, background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """Inicia envio da campanha."""
        redis = await get_redis()

        campaign = await redis.hgetall(f"campaign:{campaign_id}")
        if not campaign or campaign.get("user_id") != user_id:
            raise HTTPException(status_code=404, detail="Campanha não encontrada")

        if campaign.get("status") not in [
            CampaignStatus.DRAFT.value,
            CampaignStatus.SCHEDULED.value,
        ]:
            raise HTTPException(
                status_code=400, detail="Campanha já foi enviada ou está em envio"
            )

        # Atualizar status
        await redis.hset(
            f"campaign:{campaign_id}", "status", CampaignStatus.SENDING.value
        )

        # Adicionar job de envio na fila
        job = {
            "campaign_id": campaign_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
        }
        await redis.lpush("campaign:queue", json.dumps(job))

        return {
            "status": "sending",
            "campaign_id": campaign_id,
            "message": "Campanha adicionada à fila de envio",
        }

    async def schedule_campaign(
        self, user_id: str, campaign_id: str, schedule_at: datetime
    ) -> Dict[str, Any]:
        """Agenda campanha para envio futuro."""
        redis = await get_redis()

        campaign = await redis.hgetall(f"campaign:{campaign_id}")
        if not campaign or campaign.get("user_id") != user_id:
            raise HTTPException(status_code=404, detail="Campanha não encontrada")

        if campaign.get("status") != CampaignStatus.DRAFT.value:
            raise HTTPException(
                status_code=400, detail="Só é possível agendar campanhas em rascunho"
            )

        if schedule_at <= datetime.now():
            raise HTTPException(
                status_code=400, detail="Data de agendamento deve ser no futuro"
            )

        await redis.hset(
            f"campaign:{campaign_id}",
            mapping={
                "status": CampaignStatus.SCHEDULED.value,
                "schedule_at": schedule_at.isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
        )

        # Adicionar ao sorted set de agendamentos
        await redis.zadd("campaign:scheduled", {campaign_id: schedule_at.timestamp()})

        return {
            "status": "scheduled",
            "campaign_id": campaign_id,
            "schedule_at": schedule_at.isoformat(),
        }

    async def get_campaign_stats(
        self, user_id: str, campaign_id: str
    ) -> Optional[CampaignStats]:
        """Retorna estatísticas detalhadas da campanha."""
        redis = await get_redis()

        campaign = await redis.hgetall(f"campaign:{campaign_id}")
        if not campaign or campaign.get("user_id") != user_id:
            return None

        stats = await redis.hgetall(f"campaign:{campaign_id}:stats")
        if not stats:
            return None

        total_recipients = int(stats.get("total_recipients", 0))
        total_sent = int(stats.get("total_sent", 0))
        total_delivered = int(stats.get("total_delivered", 0))
        total_opened = int(stats.get("total_opened", 0))
        unique_opens = int(stats.get("unique_opens", 0))
        total_clicked = int(stats.get("total_clicked", 0))
        unique_clicks = int(stats.get("unique_clicks", 0))
        total_bounced = int(stats.get("total_bounced", 0))
        total_unsubscribed = int(stats.get("total_unsubscribed", 0))
        total_complained = int(stats.get("total_complained", 0))

        return CampaignStats(
            campaign_id=campaign_id,
            total_recipients=total_recipients,
            total_sent=total_sent,
            total_delivered=total_delivered,
            total_opened=total_opened,
            unique_opens=unique_opens,
            total_clicked=total_clicked,
            unique_clicks=unique_clicks,
            total_bounced=total_bounced,
            total_unsubscribed=total_unsubscribed,
            total_complained=total_complained,
            delivery_rate=(total_delivered / total_sent * 100) if total_sent > 0 else 0,
            open_rate=(
                (unique_opens / total_delivered * 100) if total_delivered > 0 else 0
            ),
            click_rate=(
                (unique_clicks / total_delivered * 100) if total_delivered > 0 else 0
            ),
            click_to_open_rate=(
                (unique_clicks / unique_opens * 100) if unique_opens > 0 else 0
            ),
            bounce_rate=(total_bounced / total_sent * 100) if total_sent > 0 else 0,
            unsubscribe_rate=(
                (total_unsubscribed / total_delivered * 100)
                if total_delivered > 0
                else 0
            ),
            first_open_at=(
                datetime.fromisoformat(stats["first_open_at"])
                if stats.get("first_open_at")
                else None
            ),
            last_open_at=(
                datetime.fromisoformat(stats["last_open_at"])
                if stats.get("last_open_at")
                else None
            ),
            avg_open_time_seconds=(
                int(stats.get("avg_open_time_seconds"))
                if stats.get("avg_open_time_seconds")
                else None
            ),
            top_links=json.loads(stats.get("top_links", "[]")),
            device_breakdown=json.loads(stats.get("device_breakdown", "{}")),
            location_breakdown=json.loads(stats.get("location_breakdown", "{}")),
        )

    def _parse_campaign(self, data: Dict) -> CampaignResponse:
        """Converte dados do Redis para CampaignResponse."""
        stats = None
        if data.get("status") == CampaignStatus.SENT.value:
            # Incluir estatísticas básicas
            stats = {
                "sent": int(data.get("sent_count", 0)),
                "opened": int(data.get("open_count", 0)),
                "clicked": int(data.get("click_count", 0)),
            }

        return CampaignResponse(
            id=data["id"],
            name=data["name"],
            subject=data["subject"],
            preview_text=data.get("preview_text") or None,
            status=CampaignStatus(data["status"]),
            type=CampaignType(data["type"]),
            trigger=TriggerType(data["trigger"]),
            list_ids=json.loads(data.get("list_ids", "[]")),
            recipients_count=int(data.get("recipients_count", 0)),
            schedule_at=(
                datetime.fromisoformat(data["schedule_at"])
                if data.get("schedule_at")
                else None
            ),
            sent_at=(
                datetime.fromisoformat(data["sent_at"]) if data.get("sent_at") else None
            ),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            stats=stats,
        )


campaign_service = CampaignService()


# ==================== ENDPOINTS ====================


@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    data: CampaignCreate, current_user: User = Depends(get_current_user)
):
    """Cria uma nova campanha de email."""
    return await campaign_service.create_campaign(str(current_user.id), data)


@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(
    status: Optional[CampaignStatus] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """Lista todas as campanhas do usuário."""
    return await campaign_service.list_campaigns(
        str(current_user.id), status=status, page=page, per_page=per_page
    )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str, current_user: User = Depends(get_current_user)
):
    """Busca campanha por ID."""
    campaign = await campaign_service.get_campaign(str(current_user.id), campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    data: CampaignUpdate,
    current_user: User = Depends(get_current_user),
):
    """Atualiza uma campanha."""
    campaign = await campaign_service.update_campaign(
        str(current_user.id), campaign_id, data
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return campaign


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str, current_user: User = Depends(get_current_user)
):
    """Remove uma campanha."""
    redis = await get_redis()

    campaign = await redis.hgetall(f"campaign:{campaign_id}")
    if not campaign or campaign.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=404, detail="Campanha não encontrada")

    # Só permite deletar se não estiver enviando
    if campaign.get("status") == CampaignStatus.SENDING.value:
        raise HTTPException(
            status_code=400, detail="Não é possível deletar campanha em envio"
        )

    await redis.delete(f"campaign:{campaign_id}")
    await redis.srem(f"campaigns:{current_user.id}", campaign_id)

    return {"status": "deleted", "campaign_id": campaign_id}


@router.post("/{campaign_id}/send")
async def send_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Inicia o envio da campanha."""
    return await campaign_service.send_campaign(
        str(current_user.id), campaign_id, background_tasks
    )


@router.post("/{campaign_id}/schedule")
async def schedule_campaign(
    campaign_id: str,
    schedule_at: datetime,
    current_user: User = Depends(get_current_user),
):
    """Agenda campanha para envio futuro."""
    return await campaign_service.schedule_campaign(
        str(current_user.id), campaign_id, schedule_at
    )


@router.post("/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: str, current_user: User = Depends(get_current_user)
):
    """Pausa uma campanha em envio."""
    redis = await get_redis()

    campaign = await redis.hgetall(f"campaign:{campaign_id}")
    if not campaign or campaign.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=404, detail="Campanha não encontrada")

    if campaign.get("status") != CampaignStatus.SENDING.value:
        raise HTTPException(
            status_code=400, detail="Só é possível pausar campanhas em envio"
        )

    await redis.hset(f"campaign:{campaign_id}", "status", CampaignStatus.PAUSED.value)

    return {"status": "paused", "campaign_id": campaign_id}


@router.post("/{campaign_id}/resume")
async def resume_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Retoma uma campanha pausada."""
    redis = await get_redis()

    campaign = await redis.hgetall(f"campaign:{campaign_id}")
    if not campaign or campaign.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=404, detail="Campanha não encontrada")

    if campaign.get("status") != CampaignStatus.PAUSED.value:
        raise HTTPException(
            status_code=400, detail="Só é possível retomar campanhas pausadas"
        )

    await redis.hset(f"campaign:{campaign_id}", "status", CampaignStatus.SENDING.value)

    # Re-adicionar à fila
    job = {
        "campaign_id": campaign_id,
        "user_id": str(current_user.id),
        "resume": True,
        "created_at": datetime.now().isoformat(),
    }
    await redis.lpush("campaign:queue", json.dumps(job))

    return {"status": "resumed", "campaign_id": campaign_id}


@router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(
    campaign_id: str, current_user: User = Depends(get_current_user)
):
    """Retorna estatísticas detalhadas da campanha."""
    stats = await campaign_service.get_campaign_stats(str(current_user.id), campaign_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Estatísticas não disponíveis")
    return stats


@router.post("/{campaign_id}/duplicate", response_model=CampaignResponse)
async def duplicate_campaign(
    campaign_id: str, current_user: User = Depends(get_current_user)
):
    """Duplica uma campanha existente."""
    redis = await get_redis()

    original = await redis.hgetall(f"campaign:{campaign_id}")
    if not original or original.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=404, detail="Campanha não encontrada")

    # Criar nova campanha baseada na original
    new_campaign = CampaignCreate(
        name=f"{original['name']} (Cópia)",
        subject=original["subject"],
        preview_text=original.get("preview_text") or None,
        html_content=original.get("html_content") or None,
        text_content=original.get("text_content") or None,
        list_ids=json.loads(original.get("list_ids", "[]")),
        type=CampaignType(original["type"]),
        trigger=TriggerType(original["trigger"]),
        track_opens=original.get("track_opens") == "1",
        track_clicks=original.get("track_clicks") == "1",
    )

    return await campaign_service.create_campaign(str(current_user.id), new_campaign)


# ==================== AUTOMATIONS ====================


@router.post("/automations", response_model=AutomationResponse)
async def create_automation(
    data: AutomationCreate, current_user: User = Depends(get_current_user)
):
    """Cria uma automação de email."""
    redis = await get_redis()

    automation_id = str(uuid.uuid4())
    now = datetime.now()

    automation_data = {
        "id": automation_id,
        "user_id": str(current_user.id),
        "name": data.name,
        "description": data.description or "",
        "trigger_event": data.trigger_event,
        "trigger_conditions": (
            json.dumps(data.trigger_conditions) if data.trigger_conditions else ""
        ),
        "delay_minutes": str(data.delay_minutes),
        "emails": json.dumps(data.emails),
        "active": "1" if data.active else "0",
        "total_triggered": "0",
        "total_completed": "0",
        "created_at": now.isoformat(),
    }

    await redis.hset(f"automation:{automation_id}", mapping=automation_data)
    await redis.sadd(f"automations:{current_user.id}", automation_id)

    if data.active:
        await redis.sadd("automations:active", automation_id)

    return AutomationResponse(
        id=automation_id,
        name=data.name,
        description=data.description,
        trigger_event=data.trigger_event,
        trigger_conditions=data.trigger_conditions,
        delay_minutes=data.delay_minutes,
        emails_count=len(data.emails),
        active=data.active,
        total_triggered=0,
        total_completed=0,
        created_at=now,
    )


@router.get("/automations", response_model=List[AutomationResponse])
async def list_automations(current_user: User = Depends(get_current_user)):
    """Lista automações do usuário."""
    redis = await get_redis()

    automation_ids = await redis.smembers(f"automations:{current_user.id}")
    automations = []

    for aid in automation_ids:
        data = await redis.hgetall(f"automation:{aid}")
        if data:
            automations.append(
                AutomationResponse(
                    id=data["id"],
                    name=data["name"],
                    description=data.get("description") or None,
                    trigger_event=data["trigger_event"],
                    trigger_conditions=(
                        json.loads(data["trigger_conditions"])
                        if data.get("trigger_conditions")
                        else None
                    ),
                    delay_minutes=int(data.get("delay_minutes", 0)),
                    emails_count=len(json.loads(data.get("emails", "[]"))),
                    active=data.get("active") == "1",
                    total_triggered=int(data.get("total_triggered", 0)),
                    total_completed=int(data.get("total_completed", 0)),
                    created_at=datetime.fromisoformat(data["created_at"]),
                )
            )

    return automations


@router.put("/automations/{automation_id}/toggle")
async def toggle_automation(
    automation_id: str, current_user: User = Depends(get_current_user)
):
    """Ativa/desativa automação."""
    redis = await get_redis()

    automation = await redis.hgetall(f"automation:{automation_id}")
    if not automation or automation.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=404, detail="Automação não encontrada")

    is_active = automation.get("active") == "1"
    new_status = "0" if is_active else "1"

    await redis.hset(f"automation:{automation_id}", "active", new_status)

    if new_status == "1":
        await redis.sadd("automations:active", automation_id)
    else:
        await redis.srem("automations:active", automation_id)

    return {"automation_id": automation_id, "active": new_status == "1"}


@router.delete("/automations/{automation_id}")
async def delete_automation(
    automation_id: str, current_user: User = Depends(get_current_user)
):
    """Remove automação."""
    redis = await get_redis()

    automation = await redis.hgetall(f"automation:{automation_id}")
    if not automation or automation.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=404, detail="Automação não encontrada")

    await redis.delete(f"automation:{automation_id}")
    await redis.srem(f"automations:{current_user.id}", automation_id)
    await redis.srem("automations:active", automation_id)

    return {"status": "deleted", "automation_id": automation_id}
