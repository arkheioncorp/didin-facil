"""
Email Service
=============
Serviço centralizado para envio de emails transacionais.

Suporta múltiplos providers:
- Resend (recomendado para produção)
- SMTP (fallback ou desenvolvimento)
- Console (desenvolvimento local)

Tipos de email:
- Verificação de conta
- Reset de senha
- Boas-vindas
- Alertas de preço
- Confirmação de compra
"""

import logging
import secrets
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from shared.config import settings

logger = logging.getLogger(__name__)


class EmailProvider(Enum):
    """Providers de email suportados."""
    RESEND = "resend"
    SMTP = "smtp"
    CONSOLE = "console"  # Para desenvolvimento


@dataclass
class EmailResult:
    """Resultado do envio de email."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    provider: str = ""


class EmailTemplates:
    """Templates HTML para emails transacionais."""
    
    BASE_STYLE = """
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .card { background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .logo { text-align: center; margin-bottom: 30px; }
        .logo h1 { color: #8B5CF6; margin: 0; font-size: 28px; }
        .content { color: #333; line-height: 1.6; }
        .button { display: inline-block; background: linear-gradient(135deg, #8B5CF6, #6366F1); color: white; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; margin: 20px 0; }
        .button:hover { opacity: 0.9; }
        .footer { text-align: center; color: #888; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }
        .code { background: #f5f5f5; padding: 15px 25px; border-radius: 8px; font-family: monospace; font-size: 24px; letter-spacing: 4px; text-align: center; margin: 20px 0; }
        .highlight { color: #8B5CF6; font-weight: 600; }
    </style>
    """
    
    @classmethod
    def verification_email(
        cls,
        name: str,
        verification_url: str,
        verification_code: str
    ) -> str:
        """Template de verificação de email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>{cls.BASE_STYLE}</head>
        <body>
            <div class="container">
                <div class="card">
                    <div class="logo">
                        <h1>📈 TikTrend</h1>
                    </div>
                    <div class="content">
                        <h2>Olá, {name}! 👋</h2>
                        <p>Obrigado por se cadastrar no <span class="highlight">TikTrend</span>!</p>
                        <p>Para ativar sua conta, clique no botão abaixo:</p>
                        
                        <div style="text-align: center;">
                            <a href="{verification_url}" class="button">✓ Verificar Email</a>
                        </div>
                        
                        <p>Ou use o código de verificação:</p>
                        <div class="code">{verification_code}</div>
                        
                        <p style="color: #888; font-size: 14px;">
                            Este link expira em <strong>24 horas</strong>.
                            Se você não criou esta conta, ignore este email.
                        </p>
                    </div>
                    <div class="footer">
                        <p>© 2025 TikTrend - Encontre Produtos Virais</p>
                        <p>
                            <a href="https://arkheion-tiktrend.com.br/terms">Termos</a> · 
                            <a href="https://arkheion-tiktrend.com.br/privacy">Privacidade</a>
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    @classmethod
    def password_reset(cls, name: str, reset_url: str, reset_code: str) -> str:
        """Template de reset de senha."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>{cls.BASE_STYLE}</head>
        <body>
            <div class="container">
                <div class="card">
                    <div class="logo">
                        <h1>🔐 TikTrend</h1>
                    </div>
                    <div class="content">
                        <h2>Olá, {name}!</h2>
                        <p>Recebemos um pedido para redefinir sua senha.</p>
                        <p>Clique no botão abaixo para criar uma nova senha:</p>
                        
                        <div style="text-align: center;">
                            <a href="{reset_url}" class="button">🔑 Redefinir Senha</a>
                        </div>
                        
                        <p>Ou use o código:</p>
                        <div class="code">{reset_code}</div>
                        
                        <p style="color: #888; font-size: 14px;">
                            Este link expira em <strong>1 hora</strong>.<br>
                            Se você não solicitou isso, ignore este email.
                            Sua senha permanecerá a mesma.
                        </p>
                    </div>
                    <div class="footer">
                        <p>© 2025 TikTrend</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    @classmethod
    def welcome(cls, name: str) -> str:
        """Template de boas-vindas após verificação."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>{cls.BASE_STYLE}</head>
        <body>
            <div class="container">
                <div class="card">
                    <div class="logo">
                        <h1>🎉 TikTrend</h1>
                    </div>
                    <div class="content">
                        <h2>Bem-vindo(a), {name}! 🚀</h2>
                        <p>Sua conta foi verificada com sucesso!</p>
                        
                        <p>Agora você pode:</p>
                        <ul>
                            <li>🔍 Encontrar produtos virais do TikTok</li>
                            <li>📈 Analisar tendências de mercado</li>
                            <li>❤️ Salvar produtos favoritos</li>
                            <li>💰 Descobrir oportunidades de lucro</li>
                        </ul>
                        
                        <div style="text-align: center;">
                            <a href="https://arkheion-tiktrend.com.br" class="button">
                                Começar a Explorar
                            </a>
                        </div>
                        
                        <p>Dúvidas? Responda este email ou acesse nosso suporte.</p>
                    </div>
                    <div class="footer">
                        <p>© 2025 TikTrend</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    @classmethod
    def purchase_confirmation(
        cls,
        name: str,
        package_name: str,
        credits: int,
        amount: str,
        transaction_id: str
    ) -> str:
        """Template de confirmação de compra."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>{cls.BASE_STYLE}</head>
        <body>
            <div class="container">
                <div class="card">
                    <div class="logo">
                        <h1>✅ Compra Confirmada</h1>
                    </div>
                    <div class="content">
                        <h2>Obrigado, {name}!</h2>
                        <p>Sua compra foi processada com sucesso.</p>
                        
                        <div style="background: #f0fdf4; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <p style="margin: 0;"><strong>Pacote:</strong> {package_name}</p>
                            <p style="margin: 8px 0;"><strong>Créditos:</strong> {credits}</p>
                            <p style="margin: 8px 0;"><strong>Valor:</strong> R$ {amount}</p>
                            <p style="margin: 0; color: #888; font-size: 12px;">
                                ID: {transaction_id}
                            </p>
                        </div>
                        
                        <p>Os créditos já estão disponíveis em sua conta!</p>
                        
                        <div style="text-align: center;">
                            <a href="https://arkheion-tiktrend.com.br/dashboard" class="button">
                                Acessar Dashboard
                            </a>
                        </div>
                    </div>
                    <div class="footer">
                        <p>© 2025 TikTrend</p>
                        <p>
                            Precisa de ajuda? <a href="mailto:suporte@arkheion-tiktrend.com.br">suporte@arkheion-tiktrend.com.br</a>
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """


class BaseEmailProvider(ABC):
    """Interface base para providers de email."""
    
    @abstractmethod
    async def send(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> EmailResult:
        """Envia um email."""
        pass


class ResendProvider(BaseEmailProvider):
    """Provider usando Resend.com API."""
    
    def __init__(self, api_key: str, from_email: str, from_name: str):
        self.api_key = api_key
        self.from_email = from_email
        self.from_name = from_name
        self.api_url = "https://api.resend.com/emails"
    
    async def send(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> EmailResult:
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "from": f"{self.from_name} <{self.from_email}>",
                    "to": [to],
                    "subject": subject,
                    "html": html,
                }
                
                if text:
                    payload["text"] = text
                if reply_to:
                    payload["reply_to"] = reply_to
                
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Email sent via Resend to {to}")
                    return EmailResult(
                        success=True,
                        message_id=data.get("id"),
                        provider="resend"
                    )
                else:
                    error = response.text
                    logger.error(f"Resend error: {error}")
                    return EmailResult(
                        success=False,
                        error=error,
                        provider="resend"
                    )
        except Exception as e:
            logger.error(f"Resend exception: {e}")
            return EmailResult(success=False, error=str(e), provider="resend")


class SMTPProvider(BaseEmailProvider):
    """Provider usando SMTP direto."""
    
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        from_email: str,
        from_name: str,
        use_tls: bool = True
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.from_email = from_email
        self.from_name = from_name
        self.use_tls = use_tls
    
    async def send(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> EmailResult:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to
            
            if reply_to:
                msg["Reply-To"] = reply_to
            
            if text:
                msg.attach(MIMEText(text, "plain", "utf-8"))
            
            msg.attach(MIMEText(html, "html", "utf-8"))
            
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent via SMTP to {to}")
            return EmailResult(success=True, provider="smtp")
            
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            return EmailResult(success=False, error=str(e), provider="smtp")


class ConsoleProvider(BaseEmailProvider):
    """Provider para desenvolvimento - imprime no console."""
    
    async def send(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> EmailResult:
        logger.info("=" * 60)
        logger.info(f"📧 EMAIL (Console Provider)")
        logger.info(f"To: {to}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Reply-To: {reply_to or 'N/A'}")
        logger.info("-" * 60)
        logger.info(text or "No text content")
        logger.info("=" * 60)
        
        return EmailResult(
            success=True,
            message_id=f"console-{secrets.token_hex(8)}",
            provider="console"
        )


class EmailService:
    """
    Serviço principal de envio de emails.
    
    Uso:
        email_service = EmailService()
        
        # Enviar verificação
        await email_service.send_verification_email(
            to="user@example.com",
            name="João",
            verification_token="abc123"
        )
        
        # Enviar reset de senha
        await email_service.send_password_reset(
            to="user@example.com", 
            name="João",
            reset_token="xyz789"
        )
    """
    
    def __init__(self):
        self.provider = self._get_provider()
        self.app_url = getattr(
            settings, 'APP_URL', 'https://arkheion-tiktrend.com.br'
        )
        self.support_email = getattr(
            settings, 'SUPPORT_EMAIL', 'suporte@arkheion-tiktrend.com.br'
        )
    
    def _get_provider(self) -> BaseEmailProvider:
        """Seleciona o provider baseado na configuração."""
        # Prioridade: Resend > SMTP > Console
        
        resend_key = getattr(settings, 'RESEND_API_KEY', None)
        if resend_key:
            return ResendProvider(
                api_key=resend_key,
                from_email=getattr(
                    settings, 'EMAIL_FROM', 'noreply@arkheion-tiktrend.com.br'
                ),
                from_name=getattr(settings, 'EMAIL_FROM_NAME', 'TikTrend')
            )
        
        smtp_host = getattr(settings, 'SMTP_HOST', None)
        if smtp_host:
            return SMTPProvider(
                host=smtp_host,
                port=getattr(settings, 'SMTP_PORT', 587),
                user=getattr(settings, 'SMTP_USER', ''),
                password=getattr(settings, 'SMTP_PASSWORD', ''),
                from_email=getattr(
                    settings, 'SMTP_FROM', 'noreply@arkheion-tiktrend.com.br'
                ),
                from_name=getattr(settings, 'EMAIL_FROM_NAME', 'TikTrend'),
                use_tls=getattr(settings, 'SMTP_TLS', True)
            )
        
        # Fallback para console em desenvolvimento
        logger.warning(
            "No email provider configured. Using console output. "
            "Set RESEND_API_KEY or SMTP_HOST for production."
        )
        return ConsoleProvider()
    
    def _generate_code(self, length: int = 6) -> str:
        """Gera código numérico para verificação."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])
    
    async def send_verification_email(
        self,
        to: str,
        name: str,
        verification_token: str
    ) -> EmailResult:
        """Envia email de verificação de conta."""
        verification_code = self._generate_code()
        verification_url = (
            f"{self.app_url}/verify-email?token={verification_token}"
        )
        
        html = EmailTemplates.verification_email(
            name=name,
            verification_url=verification_url,
            verification_code=verification_code
        )
        
        return await self.provider.send(
            to=to,
            subject="✓ Verifique seu email - TikTrend Finder",
            html=html,
            reply_to=self.support_email
        )
    
    async def send_password_reset(
        self,
        to: str,
        name: str,
        reset_token: str
    ) -> EmailResult:
        """Envia email de reset de senha."""
        reset_code = self._generate_code()
        reset_url = f"{self.app_url}/reset-password?token={reset_token}"
        
        html = EmailTemplates.password_reset(
            name=name,
            reset_url=reset_url,
            reset_code=reset_code
        )
        
        return await self.provider.send(
            to=to,
            subject="🔐 Redefinir senha - TikTrend Finder",
            html=html,
            reply_to=self.support_email
        )
    
    async def send_welcome(self, to: str, name: str) -> EmailResult:
        """Envia email de boas-vindas após verificação."""
        html = EmailTemplates.welcome(name=name)
        
        return await self.provider.send(
            to=to,
            subject="🎉 Bem-vindo ao TikTrend Finder!",
            html=html,
            reply_to=self.support_email
        )
    
    async def send_purchase_confirmation(
        self,
        to: str,
        name: str,
        package_name: str,
        credits: int,
        amount: str,
        transaction_id: str
    ) -> EmailResult:
        """Envia confirmação de compra."""
        html = EmailTemplates.purchase_confirmation(
            name=name,
            package_name=package_name,
            credits=credits,
            amount=amount,
            transaction_id=transaction_id
        )
        
        return await self.provider.send(
            to=to,
            subject="✅ Compra confirmada - TikTrend Finder",
            html=html,
            reply_to=self.support_email
        )
    
    async def send_custom(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None
    ) -> EmailResult:
        """Envia email customizado."""
        return await self.provider.send(
            to=to,
            subject=subject,
            html=html,
            text=text,
            reply_to=self.support_email
        )


# Singleton para uso global
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Retorna instância singleton do serviço de email."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
