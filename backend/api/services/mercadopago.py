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
    
    def __init__(self):
        self.access_token = settings.MERCADO_PAGO_ACCESS_TOKEN
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
        description: str = "Didin Fácil - Créditos"
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
        credits_amount: int
    ):
        """Send credits purchase confirmation via email"""
        # TODO: Implement email sending (SendGrid, AWS SES, etc.)
        print(f"[EMAIL] Créditos adicionados para {email}: {credits_amount}")
