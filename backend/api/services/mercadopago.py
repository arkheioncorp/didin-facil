"""
Mercado Pago Service
Payment processing and subscription management
"""

import uuid
from datetime import datetime
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
    
    async def create_subscription(
        self,
        plan: str,
        user_email: str,
        user_id: str,
    ) -> dict:
        """Create recurring subscription"""
        
        plan_configs = {
            "starter": {
                "reason": "TikTrend Finder - Starter Mensal",
                "auto_recurring": {
                    "frequency": 1,
                    "frequency_type": "months",
                    "transaction_amount": 29.90,
                    "currency_id": "BRL"
                }
            },
            "pro": {
                "reason": "TikTrend Finder - Pro Mensal",
                "auto_recurring": {
                    "frequency": 1,
                    "frequency_type": "months",
                    "transaction_amount": 79.90,
                    "currency_id": "BRL"
                }
            },
            "enterprise": {
                "reason": "TikTrend Finder - Enterprise Mensal",
                "auto_recurring": {
                    "frequency": 1,
                    "frequency_type": "months",
                    "transaction_amount": 199.90,
                    "currency_id": "BRL"
                }
            }
        }
        
        config = plan_configs.get(plan, plan_configs["starter"])
        
        subscription_data = {
            "payer_email": user_email,
            "back_url": f"{settings.FRONTEND_URL}/subscription/callback",
            "external_reference": f"{user_id}:{plan}",
            **config
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/preapproval",
                headers=self.headers,
                json=subscription_data
            )
            response.raise_for_status()
            return response.json()
    
    async def cancel_subscription(self, preapproval_id: str) -> bool:
        """Cancel a subscription"""
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
        """Send license key via email (placeholder - implement with email service)"""
        # TODO: Implement email sending (SendGrid, AWS SES, etc.)
        # For now, just log
        print(f"[EMAIL] Sending license to {email}: {license_key} ({plan})")
    
    async def get_payment_history(self, user_id: str) -> list:
        """Get user's payment history"""
        results = await self.db.fetch_all(
            """
            SELECT id, amount, plan, status, payment_method, created_at
            FROM payments
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            """,
            {"user_id": user_id}
        )
        return [dict(r) for r in results]
        
        return [dict(r) for r in results]
