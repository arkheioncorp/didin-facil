"""
Mercado Pago Service
Payment processing and subscription management
"""

import uuid
from typing import Optional

import httpx
from api.database.connection import database
from shared.config import settings


class MercadoPagoService:
    """Mercado Pago payment integration"""
    
    def __init__(self, use_sandbox: bool | None = None):
        # Determine if should use sandbox (explicit param > env config)
        self.is_sandbox = (
            use_sandbox if use_sandbox is not None
            else settings.MERCADOPAGO_USE_SANDBOX
        )
        
        # Select appropriate token based on environment
        if self.is_sandbox and settings.MERCADOPAGO_SANDBOX_TOKEN:
            self.access_token = settings.MERCADOPAGO_SANDBOX_TOKEN
        else:
            # Support both naming conventions
            self.access_token = (
                settings.MERCADO_PAGO_ACCESS_TOKEN or 
                settings.MERCADOPAGO_ACCESS_TOKEN
            )
        
        self.base_url = "https://api.mercadopago.com"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        self.db = database
    
    async def get_payment(self, payment_id: str) -> dict:
        """Get payment details from Mercado Pago"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/payments/{payment_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def create_payment(
        self,
        title: str,
        price: float,
        user_email: str,
        external_reference: str,
        description: Optional[str] = None
    ) -> dict:
        """Create a payment preference (Card, Boleto, etc)"""
        preference_data = {
            "items": [
                {
                    "title": title,
                    "description": description or title,
                    "quantity": 1,
                    "unit_price": float(price),
                    "currency_id": "BRL"
                }
            ],
            "payer": {
                "email": user_email
            },
            "back_urls": {
                "success": f"{settings.FRONTEND_URL}/payment/success",
                "failure": f"{settings.FRONTEND_URL}/payment/failure",
                "pending": f"{settings.FRONTEND_URL}/payment/pending"
            },
            "auto_return": "approved",
            "external_reference": external_reference,
            "notification_url": f"{settings.API_URL}/webhooks/mercadopago"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/checkout/preferences",
                headers=self.headers,
                json=preference_data
            )
            response.raise_for_status()
            return response.json()
    
    async def create_pix_payment(
        self,
        amount: float,
        email: str,
        cpf: str,
        name: str,
        external_reference: str,
        description: str = "TikTrend Finder - Créditos"
    ) -> dict:
        """
        Create a PIX payment with QR code.
        Returns QR code for immediate payment.
        """
        payment_data = {
            "transaction_amount": amount,
            "payment_method_id": "pix",
            "payer": {
                "email": email,
                "first_name": name.split()[0] if name else "Cliente",
                "last_name": " ".join(name.split()[1:]) if len(name.split()) > 1 else "",
                "identification": {
                    "type": "CPF",
                    "number": cpf
                }
            },
            "external_reference": external_reference,
            "notification_url": f"{settings.API_URL}/webhooks/mercadopago",
            "description": description
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/payments",
                headers=self.headers,
                json=payment_data
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract PIX payment data
            point_of_interaction = data.get("point_of_interaction", {})
            transaction_data = point_of_interaction.get("transaction_data", {})
            
            return {
                "payment_id": data.get("id"),
                "status": data.get("status"),
                "qr_code": transaction_data.get("qr_code"),
                "qr_code_base64": transaction_data.get("qr_code_base64"),
                "copy_paste": transaction_data.get("qr_code"),
                "date_of_expiration": data.get("date_of_expiration"),
                "ticket_url": transaction_data.get("ticket_url")
            }

    async def create_subscription_preference(
        self,
        title: str,
        price: float,
        user_email: str,
        external_reference: str,
        frequency: int = 1,
        frequency_type: str = "months"
    ) -> dict:
        """Create a subscription preference (preapproval)"""
        data = {
            "reason": title,
            "auto_recurring": {
                "frequency": frequency,
                "frequency_type": frequency_type,
                "transaction_amount": price,
                "currency_id": "BRL"
            },
            "payer_email": user_email,
            "back_url": f"{settings.FRONTEND_URL}/subscription/success",
            "external_reference": external_reference,
            "status": "pending"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/preapproval",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()

    async def get_subscription(self, preapproval_id: str) -> dict:
        """Get subscription details"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/preapproval/{preapproval_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def cancel_subscription(self, preapproval_id: str) -> dict:
        """Cancel a subscription"""
        data = {"status": "cancelled"}
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/preapproval/{preapproval_id}",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()

    async def log_event(self, event_type: str, data: dict):
        """Log payment event to database"""
        await self.db.execute(
            """
            INSERT INTO payment_events (id, event_type, data, created_at)
            VALUES (:id, :event_type, :data, NOW())
            """,
            {
                "id": str(uuid.uuid4()),
                "event_type": event_type,
                "data": str(data)  # JSON serialization
            }
        )

    async def send_credits_email(
        self,
        email: str,
        credits_amount: int,
        includes_license: bool = False
    ):
        """Send credits purchase confirmation via email"""
        import logging
        logger = logging.getLogger(__name__)
        
        license_msg = ""
        if includes_license:
            license_msg = """
                <p style='background: #10b981; color: white; padding: 12px; 
                   border-radius: 8px; text-align: center;'>
                    🎫 <strong>Licença Vitalícia ATIVADA!</strong><br>
                    Você agora tem acesso ilimitado à plataforma.
                </p>
            """
        
        # Tentar enviar email via serviço configurado
        try:
            # Verificar se há serviço de email configurado
            if hasattr(settings, 'SMTP_HOST') and settings.SMTP_HOST:
                # Envio via SMTP
                import smtplib
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText
                
                subject = f'🎉 {credits_amount} créditos adicionados!'
                if includes_license:
                    subject = f'🎉 Licença + {credits_amount} créditos!'
                
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = settings.SMTP_FROM or 'noreply@tiktrendfinder.com'
                msg['To'] = email
                
                html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2>Seus créditos foram adicionados! 🚀</h2>
                    {license_msg}
                    <p>Olá!</p>
                    <p>Confirmamos a adição de 
                       <strong>{credits_amount} créditos</strong> 
                       à sua conta TikTrend Finder.</p>
                    <p>Você já pode usar para:</p>
                    <ul>
                        <li>Gerar copies com IA</li>
                        <li>Analisar produtos</li>
                        <li>Criar automações</li>
                    </ul>
                    <p>Boas vendas!</p>
                    <p><small>Equipe TikTrend Finder</small></p>
                </body>
                </html>
                """
                
                msg.attach(MIMEText(html, 'html'))
                
                with smtplib.SMTP(
                    settings.SMTP_HOST, 
                    getattr(settings, 'SMTP_PORT', 587)
                ) as server:
                    if getattr(settings, 'SMTP_TLS', True):
                        server.starttls()
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(
                            settings.SMTP_USER,
                            settings.SMTP_PASSWORD
                        )
                    server.send_message(msg)
                
                logger.info(f"Email de créditos enviado para {email}")
                
            elif (hasattr(settings, 'RESEND_API_KEY') and
                  settings.RESEND_API_KEY):
                # Envio via Resend (alternativa moderna)
                async with httpx.AsyncClient() as client:
                    await client.post(
                        "https://api.resend.com/emails",
                        headers={
                            "Authorization": (
                                f"Bearer {settings.RESEND_API_KEY}"
                            ),
                            "Content-Type": "application/json",
                        },
                        json={
                            "from": "TikTrend Finder <noreply@tiktrendfinder.com>",
                            "to": [email],
                            "subject": (
                                f"🎉 {credits_amount} créditos adicionados!"
                            ),
                            "html": f"""
                            <h2>Seus créditos foram adicionados! 🚀</h2>
                            <p>
                                {credits_amount} créditos disponíveis.
                            </p>
                            """,
                        },
                    )
                logger.info(f"Email enviado via Resend para {email}")
            else:
                # Log apenas se não houver serviço configurado
                logger.info(
                    f"[EMAIL SIM] Créditos: {email} +{credits_amount}"
                )
                
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            # Não falhar a operação principal por erro de email
