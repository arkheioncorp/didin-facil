"""
Email Marketing Routes
======================
API endpoints para envio de emails e gestão de campanhas.

Funcionalidades:
- Envio de emails transacionais
- Templates de email
- Listas de contatos
- Tracking de métricas
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from api.middleware.auth import get_current_user
from api.database.models import User
from shared.redis import get_redis
from vendor.email import (
    EmailClient,
    EmailConfig,
    EmailMessage,
    EmailAddress,
    EmailStatus,
)

router = APIRouter()


# ==================== SCHEMAS ====================


class EmailProviderEnum(str, Enum):
    RESEND = "resend"
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    SES = "ses"


class EmailRecipient(BaseModel):
    """Destinatário de email."""

    email: EmailStr
    name: Optional[str] = None


class SendEmailRequest(BaseModel):
    """Request para envio de email."""

    to: List[EmailRecipient]
    subject: str = Field(..., min_length=1, max_length=200)
    html: Optional[str] = None
    text: Optional[str] = None
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    cc: Optional[List[EmailRecipient]] = None
    bcc: Optional[List[EmailRecipient]] = None
    reply_to: Optional[EmailRecipient] = None
    tags: Optional[List[str]] = None
    schedule_at: Optional[datetime] = None


class SendEmailResponse(BaseModel):
    """Resposta do envio de email."""

    success: bool
    message_id: Optional[str] = None
    status: str
    recipients_count: int
    scheduled_at: Optional[datetime] = None
    error: Optional[str] = None


class EmailTemplateCreate(BaseModel):
    """Criar template de email."""

    name: str = Field(..., min_length=1, max_length=100)
    subject: str = Field(..., min_length=1, max_length=200)
    html_content: str
    text_content: Optional[str] = None
    variables: Optional[List[str]] = None  # Lista de variáveis esperadas
    category: Optional[str] = None


class EmailTemplateResponse(BaseModel):
    """Template de email."""

    id: str
    name: str
    subject: str
    html_content: str
    text_content: Optional[str]
    variables: List[str]
    category: Optional[str]
    created_at: datetime
    updated_at: datetime
    usage_count: int


class EmailStatsResponse(BaseModel):
    """Estatísticas de email."""

    total_sent: int
    total_delivered: int
    total_opened: int
    total_clicked: int
    total_bounced: int
    total_complained: int
    open_rate: float
    click_rate: float
    bounce_rate: float
    period: str


class ContactCreate(BaseModel):
    """Criar contato para lista de email."""

    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    subscribed: bool = True


class ContactResponse(BaseModel):
    """Contato da lista."""

    id: str
    email: str
    name: Optional[str]
    phone: Optional[str]
    tags: List[str]
    custom_fields: Dict[str, Any]
    subscribed: bool
    created_at: datetime
    last_email_sent: Optional[datetime]
    open_count: int
    click_count: int


class ContactListCreate(BaseModel):
    """Criar lista de contatos."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class ContactListResponse(BaseModel):
    """Lista de contatos."""

    id: str
    name: str
    description: Optional[str]
    contacts_count: int
    created_at: datetime


# ==================== EMAIL SERVICE ====================


class EmailService:
    """Serviço de email marketing."""

    def __init__(self):
        self.config = EmailConfig()
        self.client = EmailClient(self.config)

    async def send_email(
        self, user_id: str, request: SendEmailRequest
    ) -> SendEmailResponse:
        """Envia email."""
        try:
            # Converter recipients
            to_addresses = [
                EmailAddress(email=r.email, name=r.name) for r in request.to
            ]

            # Processar template se especificado
            html_content = request.html
            text_content = request.text

            if request.template_id:
                template = await self._get_template(request.template_id)
                if template:
                    html_content = self._render_template(
                        template["html_content"], request.template_data or {}
                    )
                    if template.get("text_content"):
                        text_content = self._render_template(
                            template["text_content"], request.template_data or {}
                        )

            # Criar mensagem
            message = EmailMessage(
                to=to_addresses,
                subject=request.subject,
                html=html_content,
                text=text_content,
                cc=[
                    EmailAddress(email=r.email, name=r.name) for r in (request.cc or [])
                ],
                bcc=[
                    EmailAddress(email=r.email, name=r.name)
                    for r in (request.bcc or [])
                ],
                reply_to=(
                    EmailAddress(
                        email=request.reply_to.email, name=request.reply_to.name
                    )
                    if request.reply_to
                    else None
                ),
                tags=request.tags or [],
                metadata={"user_id": user_id},
            )

            # Agendar ou enviar
            if request.schedule_at:
                await self._schedule_email(user_id, message, request.schedule_at)
                return SendEmailResponse(
                    success=True,
                    status="scheduled",
                    recipients_count=len(request.to),
                    scheduled_at=request.schedule_at,
                )

            # Enviar imediatamente
            async with self.client as client:
                result = await client.send(message)

            # Registrar métricas
            await self._record_send(user_id, result)

            return SendEmailResponse(
                success=True,
                message_id=result.message_id,
                status=result.status.value,
                recipients_count=len(request.to),
            )

        except Exception as e:
            return SendEmailResponse(
                success=False,
                status="failed",
                recipients_count=len(request.to),
                error=str(e),
            )

    async def _get_template(self, template_id: str) -> Optional[Dict]:
        """Busca template por ID."""
        redis = await get_redis()
        data = await redis.hgetall(f"email:template:{template_id}")
        return data if data else None

    def _render_template(self, template: str, data: Dict) -> str:
        """Renderiza template com dados."""
        from jinja2 import Template

        return Template(template).render(**data)

    async def _schedule_email(
        self, user_id: str, message: EmailMessage, schedule_at: datetime
    ):
        """Agenda email para envio futuro."""
        redis = await get_redis()
        import json

        job_data = {
            "user_id": user_id,
            "message": {
                "to": [{"email": a.email, "name": a.name} for a in message.to],
                "subject": message.subject,
                "html": message.html,
                "text": message.text,
            },
            "schedule_at": schedule_at.isoformat(),
        }

        await redis.zadd(
            "email:scheduled", {json.dumps(job_data): schedule_at.timestamp()}
        )

    async def _record_send(self, user_id: str, result):
        """Registra envio para métricas."""
        redis = await get_redis()
        today = datetime.now().strftime("%Y-%m-%d")

        await redis.hincrby(f"email:stats:{user_id}:{today}", "sent", 1)
        if result.status == EmailStatus.DELIVERED:
            await redis.hincrby(f"email:stats:{user_id}:{today}", "delivered", 1)


email_service = EmailService()


# ==================== ENDPOINTS ====================


@router.post("/send", response_model=SendEmailResponse)
async def send_email(
    request: SendEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Envia um email.

    Pode usar template_id para usar um template pré-definido,
    ou enviar html/text diretamente.

    Use schedule_at para agendar envio futuro.
    """
    result = await email_service.send_email(str(current_user.id), request)

    if not result.success:
        raise HTTPException(
            status_code=500, detail=f"Erro ao enviar email: {result.error}"
        )

    return result


@router.post("/send/batch")
async def send_batch_emails(
    emails: List[SendEmailRequest],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Envia múltiplos emails em batch.

    Limite: 100 emails por request.
    """
    if len(emails) > 100:
        raise HTTPException(status_code=400, detail="Limite de 100 emails por batch")

    results = []
    for email_request in emails:
        result = await email_service.send_email(str(current_user.id), email_request)
        results.append(result)

    success_count = sum(1 for r in results if r.success)

    return {
        "total": len(emails),
        "success": success_count,
        "failed": len(emails) - success_count,
        "results": results,
    }


# ==================== TEMPLATES ====================


@router.post("/templates", response_model=EmailTemplateResponse)
async def create_template(
    template: EmailTemplateCreate, current_user: User = Depends(get_current_user)
):
    """Cria um novo template de email."""
    import uuid

    template_id = str(uuid.uuid4())
    now = datetime.now()

    redis = await get_redis()

    template_data = {
        "id": template_id,
        "name": template.name,
        "subject": template.subject,
        "html_content": template.html_content,
        "text_content": template.text_content or "",
        "variables": ",".join(template.variables or []),
        "category": template.category or "",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "usage_count": "0",
        "user_id": str(current_user.id),
    }

    await redis.hset(f"email:template:{template_id}", mapping=template_data)
    await redis.sadd(f"email:templates:{current_user.id}", template_id)

    return EmailTemplateResponse(
        id=template_id,
        name=template.name,
        subject=template.subject,
        html_content=template.html_content,
        text_content=template.text_content,
        variables=template.variables or [],
        category=template.category,
        created_at=now,
        updated_at=now,
        usage_count=0,
    )


@router.get("/templates", response_model=List[EmailTemplateResponse])
async def list_templates(
    category: Optional[str] = None, current_user: User = Depends(get_current_user)
):
    """Lista templates do usuário."""
    redis = await get_redis()

    template_ids = await redis.smembers(f"email:templates:{current_user.id}")
    templates = []

    for tid in template_ids:
        data = await redis.hgetall(f"email:template:{tid}")
        if data:
            if category and data.get("category") != category:
                continue
            templates.append(
                EmailTemplateResponse(
                    id=data["id"],
                    name=data["name"],
                    subject=data["subject"],
                    html_content=data["html_content"],
                    text_content=data.get("text_content"),
                    variables=(
                        data.get("variables", "").split(",")
                        if data.get("variables")
                        else []
                    ),
                    category=data.get("category"),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    updated_at=datetime.fromisoformat(data["updated_at"]),
                    usage_count=int(data.get("usage_count", 0)),
                )
            )

    return templates


@router.get("/templates/{template_id}", response_model=EmailTemplateResponse)
async def get_template(
    template_id: str, current_user: User = Depends(get_current_user)
):
    """Busca template por ID."""
    redis = await get_redis()
    data = await redis.hgetall(f"email:template:{template_id}")

    if not data or data.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=404, detail="Template não encontrado")

    return EmailTemplateResponse(
        id=data["id"],
        name=data["name"],
        subject=data["subject"],
        html_content=data["html_content"],
        text_content=data.get("text_content"),
        variables=data.get("variables", "").split(",") if data.get("variables") else [],
        category=data.get("category"),
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
        usage_count=int(data.get("usage_count", 0)),
    )


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str, current_user: User = Depends(get_current_user)
):
    """Remove template."""
    redis = await get_redis()
    data = await redis.hgetall(f"email:template:{template_id}")

    if not data or data.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=404, detail="Template não encontrado")

    await redis.delete(f"email:template:{template_id}")
    await redis.srem(f"email:templates:{current_user.id}", template_id)

    return {"status": "deleted", "template_id": template_id}


# ==================== CONTACT LISTS ====================


@router.post("/lists", response_model=ContactListResponse)
async def create_contact_list(
    data: ContactListCreate, current_user: User = Depends(get_current_user)
):
    """Cria uma nova lista de contatos."""
    import uuid

    list_id = str(uuid.uuid4())
    now = datetime.now()

    redis = await get_redis()

    list_data = {
        "id": list_id,
        "name": data.name,
        "description": data.description or "",
        "user_id": str(current_user.id),
        "created_at": now.isoformat(),
    }

    await redis.hset(f"email:list:{list_id}", mapping=list_data)
    await redis.sadd(f"email:lists:{current_user.id}", list_id)

    return ContactListResponse(
        id=list_id,
        name=data.name,
        description=data.description,
        contacts_count=0,
        created_at=now,
    )


@router.get("/lists", response_model=List[ContactListResponse])
async def list_contact_lists(current_user: User = Depends(get_current_user)):
    """Lista todas as listas de contatos."""
    redis = await get_redis()

    list_ids = await redis.smembers(f"email:lists:{current_user.id}")
    lists = []

    for lid in list_ids:
        data = await redis.hgetall(f"email:list:{lid}")
        if data:
            contacts_count = await redis.scard(f"email:list:{lid}:contacts")
            lists.append(
                ContactListResponse(
                    id=data["id"],
                    name=data["name"],
                    description=data.get("description"),
                    contacts_count=contacts_count,
                    created_at=datetime.fromisoformat(data["created_at"]),
                )
            )

    return lists


@router.post("/lists/{list_id}/contacts", response_model=ContactResponse)
async def add_contact_to_list(
    list_id: str, contact: ContactCreate, current_user: User = Depends(get_current_user)
):
    """Adiciona contato a uma lista."""
    import uuid

    redis = await get_redis()

    # Verificar se lista existe e pertence ao usuário
    list_data = await redis.hgetall(f"email:list:{list_id}")
    if not list_data or list_data.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=404, detail="Lista não encontrada")

    contact_id = str(uuid.uuid4())
    now = datetime.now()

    contact_data = {
        "id": contact_id,
        "email": contact.email,
        "name": contact.name or "",
        "phone": contact.phone or "",
        "tags": ",".join(contact.tags or []),
        "custom_fields": str(contact.custom_fields or {}),
        "subscribed": "1" if contact.subscribed else "0",
        "created_at": now.isoformat(),
        "open_count": "0",
        "click_count": "0",
    }

    await redis.hset(f"email:contact:{contact_id}", mapping=contact_data)
    await redis.sadd(f"email:list:{list_id}:contacts", contact_id)

    return ContactResponse(
        id=contact_id,
        email=contact.email,
        name=contact.name,
        phone=contact.phone,
        tags=contact.tags or [],
        custom_fields=contact.custom_fields or {},
        subscribed=contact.subscribed,
        created_at=now,
        last_email_sent=None,
        open_count=0,
        click_count=0,
    )


@router.get("/lists/{list_id}/contacts", response_model=List[ContactResponse])
async def list_contacts(
    list_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """Lista contatos de uma lista."""
    redis = await get_redis()

    # Verificar se lista existe
    list_data = await redis.hgetall(f"email:list:{list_id}")
    if not list_data or list_data.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=404, detail="Lista não encontrada")

    contact_ids = await redis.smembers(f"email:list:{list_id}:contacts")
    contacts = []

    # Paginar
    start = (page - 1) * per_page
    end = start + per_page
    paginated_ids = list(contact_ids)[start:end]

    for cid in paginated_ids:
        data = await redis.hgetall(f"email:contact:{cid}")
        if data:
            contacts.append(
                ContactResponse(
                    id=data["id"],
                    email=data["email"],
                    name=data.get("name") or None,
                    phone=data.get("phone") or None,
                    tags=data.get("tags", "").split(",") if data.get("tags") else [],
                    custom_fields=eval(data.get("custom_fields", "{}")),
                    subscribed=data.get("subscribed") == "1",
                    created_at=datetime.fromisoformat(data["created_at"]),
                    last_email_sent=(
                        datetime.fromisoformat(data["last_email_sent"])
                        if data.get("last_email_sent")
                        else None
                    ),
                    open_count=int(data.get("open_count", 0)),
                    click_count=int(data.get("click_count", 0)),
                )
            )

    return contacts


# ==================== STATISTICS ====================


@router.get("/stats", response_model=EmailStatsResponse)
async def get_email_stats(
    period: str = Query("7d", regex="^(1d|7d|30d|90d)$"),
    current_user: User = Depends(get_current_user),
):
    """Retorna estatísticas de email."""
    redis = await get_redis()

    from datetime import timedelta

    days_map = {"1d": 1, "7d": 7, "30d": 30, "90d": 90}
    days = days_map[period]

    total_sent = 0
    total_delivered = 0
    total_opened = 0
    total_clicked = 0
    total_bounced = 0
    total_complained = 0

    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        stats = await redis.hgetall(f"email:stats:{current_user.id}:{date}")

        if stats:
            total_sent += int(stats.get("sent", 0))
            total_delivered += int(stats.get("delivered", 0))
            total_opened += int(stats.get("opened", 0))
            total_clicked += int(stats.get("clicked", 0))
            total_bounced += int(stats.get("bounced", 0))
            total_complained += int(stats.get("complained", 0))

    open_rate = (total_opened / total_delivered * 100) if total_delivered > 0 else 0
    click_rate = (total_clicked / total_opened * 100) if total_opened > 0 else 0
    bounce_rate = (total_bounced / total_sent * 100) if total_sent > 0 else 0

    return EmailStatsResponse(
        total_sent=total_sent,
        total_delivered=total_delivered,
        total_opened=total_opened,
        total_clicked=total_clicked,
        total_bounced=total_bounced,
        total_complained=total_complained,
        open_rate=round(open_rate, 2),
        click_rate=round(click_rate, 2),
        bounce_rate=round(bounce_rate, 2),
        period=period,
    )


# ==================== WEBHOOKS ====================


@router.post("/webhooks/{provider}")
async def handle_email_webhook(provider: EmailProviderEnum, payload: Dict[str, Any]):
    """
    Recebe webhooks de provedores de email.

    Usado para tracking de opens, clicks, bounces, etc.
    """
    redis = await get_redis()

    # Processar webhook baseado no provider
    event_type = None
    email = None

    if provider == EmailProviderEnum.RESEND:
        event_type = payload.get("type")
        email = payload.get("data", {}).get("email")
    elif provider == EmailProviderEnum.SENDGRID:
        events = payload if isinstance(payload, list) else [payload]
        for event in events:
            event_type = event.get("event")
            email = event.get("email")

    # Atualizar métricas
    if event_type and email:
        # Buscar user_id pelo email (simplificado)
        today = datetime.now().strftime("%Y-%m-%d")

        metric_map = {
            "email.delivered": "delivered",
            "email.opened": "opened",
            "email.clicked": "clicked",
            "email.bounced": "bounced",
            "email.complained": "complained",
            "delivered": "delivered",
            "open": "opened",
            "click": "clicked",
            "bounce": "bounced",
            "spamreport": "complained",
        }

        metric_key = metric_map.get(event_type)
        if metric_key:
            # Incrementar métrica global (simplificado)
            await redis.hincrby(f"email:stats:global:{today}", metric_key, 1)

    return {"status": "received"}
