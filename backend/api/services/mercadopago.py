"""
Mercado Pago Service
Payment processing and subscription management
"""

import uuid

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
    
    async def get_subscription(self, preapproval_id: str) -> dict:
        """Get subscription (preapproval) details"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/preapproval/{preapproval_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_authorized_payment(self, payment_id: str) -> dict:
        """Get authorized payment details (for subscriptions)"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/authorized_payments/{payment_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def create_payment(
        self,
        title: str,
        price: float,
        user_email: str,
        external_reference: str
    ) -> dict:
        """Create a payment preference"""
        preference_data = {
            "items": [
                {
                    "title": title,
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
            "description": "TikTrend Finder - Licença Vitalícia"
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

    async def create_subscription(
        self,
        plan: str,
        user_email: str,
        user_id: str,
    ) -> dict:
        """
        Create recurring subscription.
        Note: Deprecated - using lifetime license + credits model now.
        Kept for legacy support.
        """

        # Legacy subscriptions not supported in new model
        # All purchases are now one-time (lifetime license or credit packs)
        raise NotImplementedError(
            "Subscriptions are deprecated. Use lifetime license + credits."
        )

    async def create_license_payment(
        self,
        user_email: str,
        user_id: str,
    ) -> dict:
        """Create payment for lifetime license (R$ 49,90)"""
        preference_data = {
            "items": [
                {
                    "title": "Didin Fácil - Licença Vitalícia",
                    "quantity": 1,
                    "unit_price": 49.90,
                    "currency_id": "BRL"
                }
            ],
            "payer": {
                "email": user_email
            },
            "metadata": {
                "product_type": "license",
                "user_id": user_id
            },
            "back_urls": {
                "success": f"{settings.FRONTEND_URL}/payment/success",
                "failure": f"{settings.FRONTEND_URL}/payment/failure",
                "pending": f"{settings.FRONTEND_URL}/payment/pending"
            },
            "auto_return": "approved",
            "external_reference": f"{user_id}:lifetime",
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

    async def create_credits_payment(
        self,
        user_email: str,
        user_id: str,
        pack: str,
    ) -> dict:
        """Create payment for credits pack"""
        credit_packs = {
            "starter": {"credits": 50, "price": 19.90},
            "pro": {"credits": 200, "price": 49.90},
            "ultra": {"credits": 500, "price": 99.90},
        }

        pack_info = credit_packs.get(pack, credit_packs["starter"])

        preference_data = {
            "items": [
                {
                    "title": f"Didin Fácil - {pack_info['credits']} Créditos IA",
                    "quantity": 1,
                    "unit_price": pack_info["price"],
                    "currency_id": "BRL"
                }
            ],
            "payer": {
                "email": user_email
            },
            "metadata": {
                "product_type": "credits",
                "credits": pack_info["credits"],
                "user_id": user_id
            },
            "back_urls": {
                "success": f"{settings.FRONTEND_URL}/payment/success",
                "failure": f"{settings.FRONTEND_URL}/payment/failure",
                "pending": f"{settings.FRONTEND_URL}/payment/pending"
            },
            "auto_return": "approved",
            "external_reference": f"{user_id}:credits:{pack}",
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

    async def cancel_subscription(self, preapproval_id: str) -> bool:
        """Cancel a subscription (legacy - deprecated)"""
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/preapproval/{preapproval_id}",
                headers=self.headers,
                json={"status": "cancelled"}
            )
            return response.status_code == 200

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

    async def send_license_email(
        self,
        email: str,
        license_key: str,
        plan: str
    ):
        """Send license key via email"""
        # TODO: Implement email sending (SendGrid, AWS SES, etc.)
        print(f"[EMAIL] Licença enviada para {email}: {license_key} ({plan})")

    async def send_credits_email(
        self,
        email: str,
        credits_amount: int
    ):
        """Send credits purchase confirmation via email"""
        # TODO: Implement email sending (SendGrid, AWS SES, etc.)
        print(f"[EMAIL] Créditos adicionados para {email}: {credits_amount}")

    async def get_payment_history(self, user_id: str) -> list:
        """Get user's payment history"""
        results = await self.db.fetch_all(
            """
            SELECT id, amount, status, payment_method, created_at
            FROM payments
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            """,
            {"user_id": user_id}
        )
        return [dict(r) for r in results]
