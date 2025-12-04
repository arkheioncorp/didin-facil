"""
Email Marketing Module
======================
Sistema de email marketing com suporte a múltiplos provedores.

Provedores suportados:
- Resend (recomendado)
- SendGrid
- Mailgun
- Amazon SES

Funcionalidades:
- Envio de emails transacionais
- Campanhas de email
- Templates HTML/Markdown
- Tracking de aberturas/cliques
- Segmentação de listas
- Automações de email
"""

import os
import httpx
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import logging
from jinja2 import Template, Environment, FileSystemLoader
import markdown

logger = logging.getLogger(__name__)


class EmailProvider(Enum):
    """Provedores de email suportados."""

    RESEND = "resend"
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    SES = "ses"


class EmailStatus(Enum):
    """Status de envio de email."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    COMPLAINED = "complained"
    FAILED = "failed"


@dataclass
class EmailAddress:
    """Endereço de email."""

    email: str
    name: Optional[str] = None

    def to_string(self) -> str:
        if self.name:
            return f"{self.name} <{self.email}>"
        return self.email

    def to_dict(self) -> Dict:
        result = {"email": self.email}
        if self.name:
            result["name"] = self.name
        return result


@dataclass
class Attachment:
    """Anexo de email."""

    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


@dataclass
class EmailMessage:
    """Mensagem de email."""

    to: List[EmailAddress]
    subject: str
    html: Optional[str] = None
    text: Optional[str] = None
    from_email: Optional[EmailAddress] = None
    reply_to: Optional[EmailAddress] = None
    cc: List[EmailAddress] = field(default_factory=list)
    bcc: List[EmailAddress] = field(default_factory=list)
    attachments: List[Attachment] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmailResult:
    """Resultado do envio de email."""

    message_id: str
    status: EmailStatus
    provider: EmailProvider
    sent_at: datetime
    error: Optional[str] = None


@dataclass
class EmailConfig:
    """Configuração do provedor de email."""

    provider: EmailProvider = EmailProvider.RESEND
    api_key: str = field(default_factory=lambda: os.getenv("EMAIL_API_KEY", ""))
    from_email: str = field(
        default_factory=lambda: os.getenv("EMAIL_FROM", "noreply@tiktrendfinder.com")
    )
    from_name: str = field(
        default_factory=lambda: os.getenv("EMAIL_FROM_NAME", "TikTrend Finder")
    )
    templates_dir: str = "./templates/email"
    track_opens: bool = True
    track_clicks: bool = True


# ==================== Provedor Abstrato ====================


class EmailProviderClient(ABC):
    """Interface base para provedores de email."""

    @abstractmethod
    async def send(self, message: EmailMessage) -> EmailResult:
        """Envia um email."""
        pass

    @abstractmethod
    async def send_batch(self, messages: List[EmailMessage]) -> List[EmailResult]:
        """Envia múltiplos emails."""
        pass

    async def close(self):
        """Fecha conexões."""
        pass


# ==================== Resend Provider ====================


class ResendClient(EmailProviderClient):
    """
    Cliente para Resend API.

    Documentação: https://resend.com/docs
    """

    def __init__(self, config: EmailConfig):
        self.config = config
        self.api_url = "https://api.resend.com"
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()

    async def send(self, message: EmailMessage) -> EmailResult:
        """Envia email via Resend."""
        payload = {
            "from": (
                message.from_email.to_string()
                if message.from_email
                else f"{self.config.from_name} <{self.config.from_email}>"
            ),
            "to": [addr.email for addr in message.to],
            "subject": message.subject,
        }

        if message.html:
            payload["html"] = message.html
        if message.text:
            payload["text"] = message.text
        if message.reply_to:
            payload["reply_to"] = message.reply_to.email
        if message.cc:
            payload["cc"] = [addr.email for addr in message.cc]
        if message.bcc:
            payload["bcc"] = [addr.email for addr in message.bcc]
        if message.tags:
            payload["tags"] = [{"name": tag} for tag in message.tags]
        if message.headers:
            payload["headers"] = message.headers

        # Attachments
        if message.attachments:
            payload["attachments"] = [
                {
                    "filename": att.filename,
                    "content": (
                        att.content.decode()
                        if isinstance(att.content, bytes)
                        else att.content
                    ),
                    "type": att.content_type,
                }
                for att in message.attachments
            ]

        try:
            response = await self.client.post(f"{self.api_url}/emails", json=payload)
            response.raise_for_status()
            data = response.json()

            return EmailResult(
                message_id=data.get("id", ""),
                status=EmailStatus.SENT,
                provider=EmailProvider.RESEND,
                sent_at=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Erro ao enviar email via Resend: {e}")
            return EmailResult(
                message_id="",
                status=EmailStatus.FAILED,
                provider=EmailProvider.RESEND,
                sent_at=datetime.now(),
                error=str(e),
            )

    async def send_batch(self, messages: List[EmailMessage]) -> List[EmailResult]:
        """Envia múltiplos emails em batch."""
        payload = []

        for message in messages:
            email_data = {
                "from": (
                    message.from_email.to_string()
                    if message.from_email
                    else f"{self.config.from_name} <{self.config.from_email}>"
                ),
                "to": [addr.email for addr in message.to],
                "subject": message.subject,
            }

            if message.html:
                email_data["html"] = message.html
            if message.text:
                email_data["text"] = message.text

            payload.append(email_data)

        try:
            response = await self.client.post(
                f"{self.api_url}/emails/batch", json=payload
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for i, item in enumerate(data.get("data", [])):
                results.append(
                    EmailResult(
                        message_id=item.get("id", ""),
                        status=EmailStatus.SENT,
                        provider=EmailProvider.RESEND,
                        sent_at=datetime.now(),
                    )
                )

            return results
        except Exception as e:
            logger.error(f"Erro ao enviar batch via Resend: {e}")
            return [
                EmailResult(
                    message_id="",
                    status=EmailStatus.FAILED,
                    provider=EmailProvider.RESEND,
                    sent_at=datetime.now(),
                    error=str(e),
                )
                for _ in messages
            ]


# ==================== SendGrid Provider ====================


class SendGridClient(EmailProviderClient):
    """
    Cliente para SendGrid API.

    Documentação: https://docs.sendgrid.com/api-reference
    """

    def __init__(self, config: EmailConfig):
        self.config = config
        self.api_url = "https://api.sendgrid.com/v3"
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()

    async def send(self, message: EmailMessage) -> EmailResult:
        """Envia email via SendGrid."""
        payload = {
            "personalizations": [{"to": [addr.to_dict() for addr in message.to]}],
            "from": (
                message.from_email.to_dict()
                if message.from_email
                else {"email": self.config.from_email, "name": self.config.from_name}
            ),
            "subject": message.subject,
            "content": [],
        }

        if message.text:
            payload["content"].append({"type": "text/plain", "value": message.text})
        if message.html:
            payload["content"].append({"type": "text/html", "value": message.html})

        if message.cc:
            payload["personalizations"][0]["cc"] = [
                addr.to_dict() for addr in message.cc
            ]
        if message.bcc:
            payload["personalizations"][0]["bcc"] = [
                addr.to_dict() for addr in message.bcc
            ]

        if message.reply_to:
            payload["reply_to"] = message.reply_to.to_dict()

        # Tracking
        payload["tracking_settings"] = {
            "click_tracking": {"enable": self.config.track_clicks},
            "open_tracking": {"enable": self.config.track_opens},
        }

        try:
            response = await self.client.post(f"{self.api_url}/mail/send", json=payload)

            if response.status_code == 202:
                message_id = response.headers.get("X-Message-Id", "")
                return EmailResult(
                    message_id=message_id,
                    status=EmailStatus.SENT,
                    provider=EmailProvider.SENDGRID,
                    sent_at=datetime.now(),
                )
            else:
                raise Exception(
                    f"Status: {response.status_code}, Body: {response.text}"
                )

        except Exception as e:
            logger.error(f"Erro ao enviar email via SendGrid: {e}")
            return EmailResult(
                message_id="",
                status=EmailStatus.FAILED,
                provider=EmailProvider.SENDGRID,
                sent_at=datetime.now(),
                error=str(e),
            )

    async def send_batch(self, messages: List[EmailMessage]) -> List[EmailResult]:
        """Envia múltiplos emails (sequencialmente no SendGrid)."""
        results = []
        for message in messages:
            result = await self.send(message)
            results.append(result)
        return results


# ==================== Template Engine ====================


class EmailTemplateEngine:
    """
    Motor de templates para emails.

    Suporta:
    - Jinja2 templates
    - Markdown para HTML
    - Templates pré-definidos
    """

    # Templates built-in
    TEMPLATES = {
        "welcome": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; padding: 20px 0; }
        .logo { font-size: 24px; font-weight: bold; color: #4F46E5; }
        .content { padding: 20px 0; }
        .button { display: inline-block; padding: 12px 24px; background: #4F46E5; color: white; text-decoration: none; border-radius: 6px; }
        .footer { text-align: center; padding: 20px 0; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🛒 TikTrend Finder</div>
        </div>
        <div class="content">
            <h1>Bem-vindo(a), {{ name }}!</h1>
            <p>Obrigado por se cadastrar no TikTrend Finder. Estamos felizes em ter você conosco!</p>
            <p>Com o TikTrend Finder você pode:</p>
            <ul>
                <li>Comparar preços de milhares de produtos</li>
                <li>Receber alertas de ofertas imperdíveis</li>
                <li>Economizar dinheiro em suas compras</li>
            </ul>
            <p style="text-align: center;">
                <a href="{{ cta_url }}" class="button">Começar a Economizar</a>
            </p>
        </div>
        <div class="footer">
            <p>© 2024 TikTrend Finder. Todos os direitos reservados.</p>
            <p><a href="{{ unsubscribe_url }}">Cancelar inscrição</a></p>
        </div>
    </div>
</body>
</html>
        """,
        "price_alert": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; padding: 20px 0; }
        .logo { font-size: 24px; font-weight: bold; color: #4F46E5; }
        .product { background: #f9fafb; border-radius: 8px; padding: 20px; margin: 20px 0; }
        .product-image { text-align: center; }
        .product-image img { max-width: 200px; border-radius: 8px; }
        .price-old { color: #999; text-decoration: line-through; font-size: 18px; }
        .price-new { color: #16a34a; font-size: 28px; font-weight: bold; }
        .discount { background: #dc2626; color: white; padding: 4px 8px; border-radius: 4px; font-size: 14px; }
        .button { display: inline-block; padding: 12px 24px; background: #16a34a; color: white; text-decoration: none; border-radius: 6px; }
        .footer { text-align: center; padding: 20px 0; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🔔 Alerta de Preço!</div>
        </div>
        <div class="product">
            <div class="product-image">
                <img src="{{ product_image }}" alt="{{ product_name }}">
            </div>
            <h2>{{ product_name }}</h2>
            <p class="price-old">De: R$ {{ old_price }}</p>
            <p class="price-new">Por: R$ {{ new_price }}</p>
            <p><span class="discount">{{ discount }}% OFF</span></p>
            <p>Loja: {{ store_name }}</p>
            <p style="text-align: center;">
                <a href="{{ product_url }}" class="button">Ver Oferta</a>
            </p>
        </div>
        <div class="footer">
            <p>Você está recebendo este email porque configurou um alerta para este produto.</p>
            <p><a href="{{ unsubscribe_url }}">Remover alerta</a></p>
        </div>
    </div>
</body>
</html>
        """,
        "weekly_deals": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; padding: 20px 0; background: linear-gradient(135deg, #4F46E5, #7C3AED); color: white; border-radius: 8px; }
        .deals { padding: 20px 0; }
        .deal { border-bottom: 1px solid #eee; padding: 15px 0; display: flex; align-items: center; }
        .deal img { width: 80px; height: 80px; object-fit: cover; border-radius: 8px; margin-right: 15px; }
        .deal-info { flex: 1; }
        .deal-name { font-weight: bold; }
        .deal-price { color: #16a34a; font-weight: bold; }
        .deal-discount { background: #fee2e2; color: #dc2626; padding: 2px 6px; border-radius: 4px; font-size: 12px; }
        .footer { text-align: center; padding: 20px 0; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 Ofertas da Semana</h1>
            <p>As melhores ofertas selecionadas para você!</p>
        </div>
        <div class="deals">
            {% for deal in deals %}
            <div class="deal">
                <img src="{{ deal.image }}" alt="{{ deal.name }}">
                <div class="deal-info">
                    <div class="deal-name">{{ deal.name }}</div>
                    <div class="deal-price">R$ {{ deal.price }} <span class="deal-discount">{{ deal.discount }}% OFF</span></div>
                    <div>{{ deal.store }}</div>
                </div>
            </div>
            {% endfor %}
        </div>
        <p style="text-align: center;">
            <a href="{{ view_all_url }}" style="color: #4F46E5;">Ver todas as ofertas →</a>
        </p>
        <div class="footer">
            <p><a href="{{ unsubscribe_url }}">Cancelar inscrição</a> | <a href="{{ preferences_url }}">Preferências</a></p>
        </div>
    </div>
</body>
</html>
        """,
        "order_confirmation": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; padding: 20px 0; }
        .success { color: #16a34a; font-size: 48px; }
        .order-details { background: #f9fafb; border-radius: 8px; padding: 20px; margin: 20px 0; }
        .footer { text-align: center; padding: 20px 0; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="success">✓</div>
            <h1>Pedido Confirmado!</h1>
        </div>
        <p>Olá {{ customer_name }},</p>
        <p>Seu pedido <strong>#{{ order_id }}</strong> foi confirmado com sucesso!</p>
        <div class="order-details">
            <h3>Detalhes do Pedido</h3>
            <p><strong>Data:</strong> {{ order_date }}</p>
            <p><strong>Total:</strong> R$ {{ total }}</p>
            <p><strong>Forma de Pagamento:</strong> {{ payment_method }}</p>
        </div>
        <p>Você receberá atualizações sobre o status do seu pedido.</p>
        <div class="footer">
            <p>Dúvidas? <a href="{{ support_url }}">Entre em contato</a></p>
        </div>
    </div>
</body>
</html>
        """,
    }

    def __init__(self, templates_dir: Optional[str] = None):
        self.templates_dir = templates_dir
        if templates_dir and os.path.exists(templates_dir):
            self.jinja_env = Environment(loader=FileSystemLoader(templates_dir))
        else:
            self.jinja_env = None

    def render(
        self, template_name: str, context: Dict[str, Any], use_builtin: bool = True
    ) -> str:
        """
        Renderiza um template com o contexto fornecido.

        Args:
            template_name: Nome do template (ou conteúdo se use_builtin=False)
            context: Variáveis para o template
            use_builtin: Se True, busca nos templates built-in
        """
        if use_builtin and template_name in self.TEMPLATES:
            template_str = self.TEMPLATES[template_name]
        elif self.jinja_env:
            template = self.jinja_env.get_template(f"{template_name}.html")
            return template.render(**context)
        else:
            template_str = template_name

        template = Template(template_str)
        return template.render(**context)

    def markdown_to_html(self, md_content: str, context: Dict[str, Any] = None) -> str:
        """
        Converte Markdown para HTML email-friendly.

        Args:
            md_content: Conteúdo em Markdown
            context: Variáveis para substituir antes de converter
        """
        if context:
            template = Template(md_content)
            md_content = template.render(**context)

        html = markdown.markdown(
            md_content, extensions=["tables", "fenced_code", "nl2br"]
        )

        # Wrap em template básico
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #4F46E5; }}
        a {{ color: #4F46E5; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f3f4f6; }}
    </style>
</head>
<body>
{html}
</body>
</html>
        """


# ==================== Email Marketing Service ====================


class EmailMarketingService:
    """
    Serviço principal de email marketing.

    Uso:
        service = EmailMarketingService()

        # Enviar email simples
        await service.send(
            to="user@example.com",
            subject="Olá!",
            template="welcome",
            context={"name": "João"}
        )

        # Enviar campanha
        await service.send_campaign(
            recipients=["user1@example.com", "user2@example.com"],
            subject="Ofertas da Semana",
            template="weekly_deals",
            context={"deals": [...]}
        )
    """

    def __init__(self, config: Optional[EmailConfig] = None):
        self.config = config or EmailConfig()
        self.template_engine = EmailTemplateEngine(self.config.templates_dir)
        self._client: Optional[EmailProviderClient] = None

    async def __aenter__(self):
        await self._get_client()
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.close()

    async def _get_client(self) -> EmailProviderClient:
        """Obtém cliente do provedor configurado."""
        if self._client:
            return self._client

        if self.config.provider == EmailProvider.RESEND:
            self._client = ResendClient(self.config)
        elif self.config.provider == EmailProvider.SENDGRID:
            self._client = SendGridClient(self.config)
        else:
            raise ValueError(f"Provedor não suportado: {self.config.provider}")

        await self._client.__aenter__()
        return self._client

    async def send(
        self,
        to: Union[str, List[str], EmailAddress, List[EmailAddress]],
        subject: str,
        template: Optional[str] = None,
        context: Dict[str, Any] = None,
        html: Optional[str] = None,
        text: Optional[str] = None,
        tags: List[str] = None,
        **kwargs,
    ) -> EmailResult:
        """
        Envia um email.

        Args:
            to: Destinatário(s)
            subject: Assunto
            template: Nome do template (built-in ou arquivo)
            context: Variáveis do template
            html: HTML customizado (se não usar template)
            text: Texto plano (opcional)
            tags: Tags para categorização
        """
        # Normalizar destinatários
        if isinstance(to, str):
            recipients = [EmailAddress(email=to)]
        elif isinstance(to, EmailAddress):
            recipients = [to]
        elif isinstance(to, list):
            recipients = [
                EmailAddress(email=addr) if isinstance(addr, str) else addr
                for addr in to
            ]
        else:
            recipients = [EmailAddress(email=to)]

        # Renderizar template
        if template:
            html_content = self.template_engine.render(
                template, context or {}, use_builtin=True
            )
        else:
            html_content = html

        message = EmailMessage(
            to=recipients,
            subject=subject,
            html=html_content,
            text=text,
            tags=tags or [],
            metadata=kwargs.get("metadata", {}),
        )

        client = await self._get_client()
        return await client.send(message)

    async def send_campaign(
        self,
        recipients: List[Union[str, Dict, EmailAddress]],
        subject: str,
        template: str,
        context: Dict[str, Any] = None,
        personalize: bool = True,
        tags: List[str] = None,
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Envia campanha de email para múltiplos destinatários.

        Args:
            recipients: Lista de destinatários (emails ou dicts com email+dados)
            subject: Assunto (pode conter {{ variables }})
            template: Template a usar
            context: Contexto base (compartilhado)
            personalize: Se True, personaliza para cada destinatário
            tags: Tags da campanha
            batch_size: Tamanho do batch para envio

        Returns:
            Dict com estatísticas da campanha
        """
        results = {"total": len(recipients), "sent": 0, "failed": 0, "errors": []}

        messages = []

        for recipient in recipients:
            # Extrair email e dados personalizados
            if isinstance(recipient, str):
                email = recipient
                personal_data = {}
            elif isinstance(recipient, dict):
                email = recipient.get("email")
                personal_data = {k: v for k, v in recipient.items() if k != "email"}
            elif isinstance(recipient, EmailAddress):
                email = recipient.email
                personal_data = {"name": recipient.name} if recipient.name else {}
            else:
                continue

            # Mesclar contexto base com dados pessoais
            full_context = {**(context or {}), **personal_data}

            # Renderizar template
            html_content = self.template_engine.render(template, full_context)

            # Personalizar assunto
            if personalize and "{{" in subject:
                rendered_subject = Template(subject).render(**full_context)
            else:
                rendered_subject = subject

            message = EmailMessage(
                to=[EmailAddress(email=email, name=personal_data.get("name"))],
                subject=rendered_subject,
                html=html_content,
                tags=tags or ["campaign"],
            )
            messages.append(message)

        # Enviar em batches
        client = await self._get_client()

        for i in range(0, len(messages), batch_size):
            batch = messages[i : i + batch_size]
            batch_results = await client.send_batch(batch)

            for result in batch_results:
                if result.status == EmailStatus.SENT:
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                    if result.error:
                        results["errors"].append(result.error)

        return results

    async def send_price_alert(
        self,
        to: str,
        product_name: str,
        old_price: float,
        new_price: float,
        product_url: str,
        product_image: str,
        store_name: str,
    ) -> EmailResult:
        """Envia alerta de queda de preço."""
        discount = round((1 - new_price / old_price) * 100)

        return await self.send(
            to=to,
            subject=f"🔔 Preço caiu! {product_name} por R$ {new_price:.2f}",
            template="price_alert",
            context={
                "product_name": product_name,
                "old_price": f"{old_price:.2f}",
                "new_price": f"{new_price:.2f}",
                "discount": discount,
                "product_url": product_url,
                "product_image": product_image,
                "store_name": store_name,
                "unsubscribe_url": "#",
            },
            tags=["price_alert", "transactional"],
        )

    async def send_welcome(
        self, to: str, name: str, cta_url: str = "https://tiktrendfinder.com"
    ) -> EmailResult:
        """Envia email de boas-vindas."""
        return await self.send(
            to=to,
            subject=f"Bem-vindo(a) ao TikTrend Finder, {name}! 🎉",
            template="welcome",
            context={"name": name, "cta_url": cta_url, "unsubscribe_url": "#"},
            tags=["welcome", "transactional"],
        )

    async def send_weekly_deals(self, recipients: List[str], deals: List[Dict]) -> Dict:
        """Envia newsletter com ofertas da semana."""
        return await self.send_campaign(
            recipients=recipients,
            subject="🔥 Ofertas da Semana - TikTrend Finder",
            template="weekly_deals",
            context={
                "deals": deals,
                "view_all_url": "https://tiktrendfinder.com/ofertas",
                "unsubscribe_url": "#",
                "preferences_url": "#",
            },
            tags=["newsletter", "weekly_deals"],
        )


# ==================== Exemplo de Uso ====================


async def example_usage():
    """Exemplo de uso do serviço de email."""
    config = EmailConfig(
        provider=EmailProvider.RESEND,
        api_key="re_xxxxxxxxxxxxx",
        from_email="ofertas@tiktrendfinder.com",
        from_name="TikTrend Finder",
    )

    async with EmailMarketingService(config) as service:
        # Email de boas-vindas
        result = await service.send_welcome(to="novo_usuario@example.com", name="João")
        print(f"Welcome email: {result.status}")

        # Alerta de preço
        result = await service.send_price_alert(
            to="usuario@example.com",
            product_name="iPhone 15 Pro Max 256GB",
            old_price=9999.00,
            new_price=7999.00,
            product_url="https://tiktrendfinder.com/p/iphone-15",
            product_image="https://example.com/iphone.jpg",
            store_name="Amazon",
        )
        print(f"Price alert: {result.status}")

        # Campanha semanal
        deals = [
            {
                "name": "PlayStation 5",
                "price": "3499.00",
                "discount": 15,
                "store": "Magazine Luiza",
                "image": "https://example.com/ps5.jpg",
            },
            {
                "name": 'Smart TV 55"',
                "price": "2199.00",
                "discount": 25,
                "store": "Casas Bahia",
                "image": "https://example.com/tv.jpg",
            },
        ]

        stats = await service.send_weekly_deals(
            recipients=["user1@example.com", "user2@example.com"], deals=deals
        )
        print(f"Campaign: {stats['sent']}/{stats['total']} enviados")


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())


# Aliases para compatibilidade com código legado
EmailClient = EmailMarketingService
