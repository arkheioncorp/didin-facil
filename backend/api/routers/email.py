"""
Email Marketing API Router
==========================
Endpoints para envio de emails e campanhas.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
import logging

from backend.vendor.email import (
    EmailMarketingService,
    EmailConfig,
    EmailProvider
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Email Marketing"])


# ==================== Schemas ====================

class SendEmailRequest(BaseModel):
    to: List[EmailStr]
    subject: str
    template: Optional[str] = None
    context: Dict[str, Any] = {}
    html: Optional[str] = None
    text: Optional[str] = None
    tags: List[str] = []


class SendCampaignRequest(BaseModel):
    recipients: List[Dict[str, Any]]  # [{"email": "x@x.com", "name": "X"}, ...]
    subject: str
    template: str
    context: Dict[str, Any] = {}
    tags: List[str] = []


class PriceAlertRequest(BaseModel):
    to: EmailStr
    product_name: str
    old_price: float
    new_price: float
    product_url: str
    product_image: str
    store_name: str


class WelcomeEmailRequest(BaseModel):
    to: EmailStr
    name: str
    cta_url: str = "https://didin.com.br"


class WeeklyDealsRequest(BaseModel):
    recipients: List[EmailStr]
    deals: List[Dict[str, Any]]


# ==================== Helper ====================

def get_email_config() -> EmailConfig:
    """Obtém configuração de email."""
    from backend.api.config import settings
    
    api_key = getattr(settings, 'EMAIL_API_KEY', None)
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Email não configurado. Configure EMAIL_API_KEY"
        )
    
    provider_str = getattr(settings, 'EMAIL_PROVIDER', 'resend').lower()
    provider = EmailProvider.RESEND
    if provider_str == 'sendgrid':
        provider = EmailProvider.SENDGRID
    
    return EmailConfig(
        provider=provider,
        api_key=api_key,
        from_email=getattr(settings, 'EMAIL_FROM', 'noreply@didin.com.br'),
        from_name=getattr(settings, 'EMAIL_FROM_NAME', 'Didin Fácil')
    )


# ==================== Endpoints ====================

@router.post("/send")
async def send_email(request: SendEmailRequest):
    """
    Envia um email.
    
    Templates disponíveis:
    - welcome: Email de boas-vindas
    - price_alert: Alerta de queda de preço
    - weekly_deals: Newsletter semanal
    - order_confirmation: Confirmação de pedido
    """
    config = get_email_config()
    
    async with EmailMarketingService(config) as service:
        result = await service.send(
            to=request.to,
            subject=request.subject,
            template=request.template,
            context=request.context,
            html=request.html,
            text=request.text,
            tags=request.tags
        )
        
        return {
            "message_id": result.message_id,
            "status": result.status.value,
            "sent_at": result.sent_at.isoformat()
        }


@router.post("/campaign")
async def send_campaign(
    request: SendCampaignRequest,
    background_tasks: BackgroundTasks
):
    """
    Envia campanha de email para múltiplos destinatários.
    
    Os emails são enviados em background.
    
    Formato de recipients:
    ```json
    [
        {"email": "user1@example.com", "name": "João"},
        {"email": "user2@example.com", "name": "Maria"}
    ]
    ```
    """
    config = get_email_config()
    
    async def send_campaign_task():
        async with EmailMarketingService(config) as service:
            await service.send_campaign(
                recipients=request.recipients,
                subject=request.subject,
                template=request.template,
                context=request.context,
                tags=request.tags
            )
    
    background_tasks.add_task(send_campaign_task)
    
    return {
        "status": "queued",
        "recipients_count": len(request.recipients),
        "message": "Campanha adicionada à fila de envio"
    }


@router.post("/price-alert")
async def send_price_alert(request: PriceAlertRequest):
    """Envia alerta de queda de preço."""
    config = get_email_config()
    
    async with EmailMarketingService(config) as service:
        result = await service.send_price_alert(
            to=request.to,
            product_name=request.product_name,
            old_price=request.old_price,
            new_price=request.new_price,
            product_url=request.product_url,
            product_image=request.product_image,
            store_name=request.store_name
        )
        
        return {
            "message_id": result.message_id,
            "status": result.status.value
        }


@router.post("/welcome")
async def send_welcome_email(request: WelcomeEmailRequest):
    """Envia email de boas-vindas."""
    config = get_email_config()
    
    async with EmailMarketingService(config) as service:
        result = await service.send_welcome(
            to=request.to,
            name=request.name,
            cta_url=request.cta_url
        )
        
        return {
            "message_id": result.message_id,
            "status": result.status.value
        }


@router.post("/weekly-deals")
async def send_weekly_deals(
    request: WeeklyDealsRequest,
    background_tasks: BackgroundTasks
):
    """
    Envia newsletter com ofertas da semana.
    
    Formato de deals:
    ```json
    [
        {
            "name": "Produto X",
            "price": "199.00",
            "discount": 20,
            "store": "Amazon",
            "image": "https://..."
        }
    ]
    ```
    """
    config = get_email_config()
    
    async def send_deals_task():
        async with EmailMarketingService(config) as service:
            await service.send_weekly_deals(
                recipients=request.recipients,
                deals=request.deals
            )
    
    background_tasks.add_task(send_deals_task)
    
    return {
        "status": "queued",
        "recipients_count": len(request.recipients),
        "deals_count": len(request.deals)
    }


# ==================== Templates ====================

@router.get("/templates")
async def list_templates():
    """Lista templates de email disponíveis."""
    from backend.vendor.email import EmailTemplateEngine
    
    list(EmailTemplateEngine.TEMPLATES.keys())
    
    return {
        "templates": [
            {
                "name": "welcome",
                "description": "Email de boas-vindas para novos usuários",
                "variables": ["name", "cta_url", "unsubscribe_url"]
            },
            {
                "name": "price_alert",
                "description": "Alerta de queda de preço de produto",
                "variables": [
                    "product_name", "old_price", "new_price", 
                    "discount", "product_url", "product_image", 
                    "store_name", "unsubscribe_url"
                ]
            },
            {
                "name": "weekly_deals",
                "description": "Newsletter com ofertas da semana",
                "variables": [
                    "deals (array)", "view_all_url", 
                    "unsubscribe_url", "preferences_url"
                ]
            },
            {
                "name": "order_confirmation",
                "description": "Confirmação de pedido",
                "variables": [
                    "customer_name", "order_id", "order_date",
                    "total", "payment_method", "support_url"
                ]
            }
        ]
    }


@router.post("/templates/preview")
async def preview_template(
    template: str,
    context: Dict[str, Any]
):
    """Pré-visualiza um template renderizado."""
    from backend.vendor.email import EmailTemplateEngine
    
    engine = EmailTemplateEngine()
    
    try:
        html = engine.render(template, context)
        return {"html": html}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao renderizar: {str(e)}")


# ==================== Status ====================

@router.get("/status")
async def get_email_status():
    """Verifica status da configuração de email."""
    try:
        config = get_email_config()
        
        return {
            "status": "configured",
            "provider": config.provider.value,
            "from_email": config.from_email,
            "from_name": config.from_name
        }
    except HTTPException:
        return {
            "status": "not_configured",
            "message": "Configure EMAIL_API_KEY para habilitar envio de emails"
        }
