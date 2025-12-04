"""Contact & Support Routes
Handles contact form submissions and support information

Provides:
- Contact form submission
- Support information endpoint
- FAQ endpoint (future)
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from api.services.email import get_email_service
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, EmailStr, Field
from shared.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contact", tags=["contact"])


# ==========================================
# MODELS
# ==========================================

class ContactFormRequest(BaseModel):
    """Contact form submission"""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=5, max_length=200)
    message: str = Field(..., min_length=10, max_length=5000)
    category: Optional[str] = Field(
        default="general",
        pattern="^(general|support|billing|partnership|feedback)$"
    )


class ContactFormResponse(BaseModel):
    """Contact form response"""
    success: bool
    message: str
    ticket_id: Optional[str] = None


class SupportInfoResponse(BaseModel):
    """Support information response"""
    support_email: str
    contact_email: str
    company_name: str
    website: str
    business_hours: str
    response_time: str
    social_links: dict


# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/submit", response_model=ContactFormResponse)
async def submit_contact_form(
    request: ContactFormRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit contact form.
    
    Sends email to support team and confirmation to user.
    """
    # Generate ticket ID
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    ticket_id = f"TKT-{timestamp[-8:]}"
    
    # Send notification to support team
    async def send_to_support():
        try:
            email_service = get_email_service()
            await email_service.send_custom(
                to=settings.SUPPORT_EMAIL,
                subject=f"[{ticket_id}] {request.category.upper()}: "
                        f"{request.subject}",
                html=_build_support_notification(request, ticket_id)
            )
        except Exception as e:
            logger.error(f"Failed to send support notification: {e}")

    # Send confirmation to user
    async def send_confirmation():
        try:
            email_service = get_email_service()
            await email_service.send_custom(
                to=request.email,
                subject=f"Recebemos sua mensagem - {ticket_id}",
                html=_build_confirmation_email(request, ticket_id)
            )
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {e}")

    background_tasks.add_task(send_to_support)
    background_tasks.add_task(send_confirmation)

    return ContactFormResponse(
        success=True,
        message="Mensagem enviada com sucesso! "
                "Responderemos em até 24 horas.",
        ticket_id=ticket_id
    )


@router.get("/info", response_model=SupportInfoResponse)
async def get_support_info():
    """
    Get support and contact information.
    
    Returns company contact details and support policies.
    """
    return SupportInfoResponse(
        support_email=settings.SUPPORT_EMAIL,
        contact_email=settings.CONTACT_EMAIL,
        company_name=settings.COMPANY_NAME,
        website=settings.COMPANY_WEBSITE,
        business_hours="Segunda a Sexta, 9h às 18h (Horário de Brasília)",
        response_time="Até 24 horas úteis",
        social_links={
            "instagram": "https://instagram.com/tiktrendfinder",
            "twitter": "https://twitter.com/tiktrendfinder",
            "youtube": "https://youtube.com/@tiktrendfinder"
        }
    )


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def _build_support_notification(
    request: ContactFormRequest,
    ticket_id: str
) -> str:
    """Build HTML email for support team notification"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #f44336; color: white; padding: 20px; }}
            .content {{ padding: 20px; background: #f9f9f9; }}
            .field {{ margin-bottom: 15px; }}
            .label {{ font-weight: bold; color: #666; }}
            .value {{ margin-top: 5px; }}
            .message-box {{ 
                background: white; 
                padding: 15px; 
                border-left: 4px solid #f44336;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>📩 Nova Mensagem de Contato</h2>
                <p>Ticket: {ticket_id}</p>
            </div>
            <div class="content">
                <div class="field">
                    <div class="label">Categoria:</div>
                    <div class="value">{request.category.upper()}</div>
                </div>
                <div class="field">
                    <div class="label">Nome:</div>
                    <div class="value">{request.name}</div>
                </div>
                <div class="field">
                    <div class="label">Email:</div>
                    <div class="value">
                        <a href="mailto:{request.email}">{request.email}</a>
                    </div>
                </div>
                <div class="field">
                    <div class="label">Assunto:</div>
                    <div class="value">{request.subject}</div>
                </div>
                <div class="field">
                    <div class="label">Mensagem:</div>
                    <div class="message-box">{request.message}</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


def _build_confirmation_email(
    request: ContactFormRequest,
    ticket_id: str
) -> str:
    """Build HTML confirmation email for user"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                line-height: 1.6; 
                color: #333;
            }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
                padding: 30px; 
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .content {{ 
                padding: 30px; 
                background: #f9f9f9;
                border-radius: 0 0 10px 10px;
            }}
            .ticket-box {{
                background: white;
                padding: 20px;
                text-align: center;
                border-radius: 8px;
                margin: 20px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .ticket-id {{
                font-size: 24px;
                font-weight: bold;
                color: #667eea;
            }}
            .summary {{
                background: white;
                padding: 15px;
                border-radius: 8px;
                margin-top: 20px;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                color: #666;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✅ Recebemos sua mensagem!</h1>
                <p>Obrigado por entrar em contato conosco</p>
            </div>
            <div class="content">
                <p>Olá <strong>{request.name}</strong>,</p>
                
                <p>Recebemos sua mensagem e nossa equipe irá analisá-la 
                em breve. O tempo médio de resposta é de <strong>até 24 
                horas úteis</strong>.</p>
                
                <div class="ticket-box">
                    <p>Seu número de protocolo:</p>
                    <div class="ticket-id">{ticket_id}</div>
                    <p style="font-size: 12px; color: #666;">
                        Guarde este número para referência
                    </p>
                </div>
                
                <div class="summary">
                    <h3>Resumo da sua mensagem:</h3>
                    <p><strong>Assunto:</strong> {request.subject}</p>
                    <p><strong>Categoria:</strong> {request.category}</p>
                </div>
                
                <p style="margin-top: 20px;">
                    Se precisar adicionar informações, responda a este email 
                    citando o número do protocolo.
                </p>
            </div>
            <div class="footer">
                <p>
                    {settings.COMPANY_NAME}<br>
                    <a href="{settings.COMPANY_WEBSITE}">
                        {settings.COMPANY_WEBSITE}
                    </a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
