"""
Webhooks Routes
Mercado Pago payment webhooks and other integrations
"""

import os
import hmac
import hashlib
import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, HTTPException, status, Header
from pydantic import BaseModel

from api.services.mercadopago import MercadoPagoService
from api.services.license import LicenseService
from shared.config import settings


router = APIRouter()


class MercadoPagoWebhook(BaseModel):
    """Mercado Pago webhook payload"""
    action: str
    api_version: str
    data: dict
    date_created: str
    id: int
    live_mode: bool
    type: str
    user_id: str


@router.post("/mercadopago")
async def mercadopago_webhook(
    request: Request,
    x_signature: str = Header(None),
    x_request_id: str = Header(None),
):
    """
    Handle Mercado Pago payment webhooks.
    
    Events handled:
    - payment.created: Payment initiated
    - payment.approved: Payment successful -> activate license
    - payment.cancelled: Payment cancelled
    - payment.refunded: Refund processed -> deactivate license
    - subscription.created: New subscription
    - subscription.updated: Subscription changed
    - subscription.cancelled: Subscription ended
    """
    # Verify webhook signature
    body = await request.body()
    
    if not verify_mercadopago_signature(body, x_signature, x_request_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )
    
    payload = json.loads(body)
    event_type = payload.get("type")
    action = payload.get("action")
    data = payload.get("data", {})
    
    mp_service = MercadoPagoService()
    license_service = LicenseService()
    
    # Handle different event types
    if event_type == "payment":
        await handle_payment_event(action, data, mp_service, license_service)
    elif event_type == "subscription_preapproval":
        await handle_subscription_event(action, data, mp_service, license_service)
    elif event_type == "subscription_authorized_payment":
        await handle_subscription_payment(action, data, mp_service, license_service)
    
    return {"status": "received"}


async def handle_payment_event(
    action: str,
    data: dict,
    mp_service: MercadoPagoService,
    license_service: LicenseService,
):
    """Handle payment events"""
    payment_id = data.get("id")
    
    if not payment_id:
        return
    
    # Get payment details from Mercado Pago
    payment = await mp_service.get_payment(payment_id)
    
    if action == "payment.created":
        # Log payment initiation
        await mp_service.log_event("payment_created", payment)
        
    elif action == "payment.approved":
        # Payment successful - activate or extend license
        user_email = payment.get("payer", {}).get("email")
        plan = payment.get("metadata", {}).get("plan", "starter")
        
        if user_email:
            # Check if user already has a license
            existing = await license_service.get_license_by_email(user_email)
            
            if existing:
                # Extend existing license
                await license_service.extend_license(
                    license_id=existing["id"],
                    days=30,  # Monthly subscription
                    payment_id=str(payment_id)
                )
            else:
                # Create new license
                license_key = await license_service.create_license(
                    email=user_email,
                    plan=plan,
                    duration_days=30,
                    payment_id=str(payment_id)
                )
                
                # Send license key via email
                await mp_service.send_license_email(user_email, license_key, plan)
        
        await mp_service.log_event("payment_approved", payment)
        
    elif action == "payment.cancelled":
        await mp_service.log_event("payment_cancelled", payment)
        
    elif action == "payment.refunded":
        # Refund - deactivate license
        user_email = payment.get("payer", {}).get("email")
        
        if user_email:
            license_info = await license_service.get_license_by_email(user_email)
            if license_info:
                await license_service.deactivate_license(
                    license_id=license_info["id"],
                    reason="refund"
                )
        
        await mp_service.log_event("payment_refunded", payment)


async def handle_subscription_event(
    action: str,
    data: dict,
    mp_service: MercadoPagoService,
    license_service: LicenseService,
):
    """Handle subscription events"""
    preapproval_id = data.get("id")
    
    if not preapproval_id:
        return
    
    subscription = await mp_service.get_subscription(preapproval_id)
    
    if action == "created":
        # New subscription created
        await mp_service.log_event("subscription_created", subscription)
        
    elif action == "updated":
        # Subscription updated (plan change, etc)
        status_value = subscription.get("status")
        
        if status_value == "authorized":
            # Subscription active
            user_email = subscription.get("payer_email")
            plan = subscription.get("reason", "starter")  # Plan name in reason field
            
            if user_email:
                existing = await license_service.get_license_by_email(user_email)
                
                if existing:
                    # Update plan if changed
                    if existing["plan"] != plan:
                        await license_service.update_plan(
                            license_id=existing["id"],
                            new_plan=plan
                        )
                    
                    # Extend license
                    await license_service.extend_license(
                        license_id=existing["id"],
                        days=30
                    )
        
        await mp_service.log_event("subscription_updated", subscription)
        
    elif action == "cancelled":
        # Subscription cancelled
        user_email = subscription.get("payer_email")
        
        if user_email:
            license_info = await license_service.get_license_by_email(user_email)
            if license_info:
                # Don't deactivate immediately, let current period expire
                await license_service.mark_for_expiration(license_info["id"])
        
        await mp_service.log_event("subscription_cancelled", subscription)


async def handle_subscription_payment(
    action: str,
    data: dict,
    mp_service: MercadoPagoService,
    license_service: LicenseService,
):
    """Handle recurring subscription payment events"""
    payment_id = data.get("id")
    
    if not payment_id:
        return
    
    payment = await mp_service.get_authorized_payment(payment_id)
    
    if action == "created" and payment.get("status") == "approved":
        # Recurring payment successful
        preapproval_id = payment.get("preapproval_id")
        subscription = await mp_service.get_subscription(preapproval_id)
        
        user_email = subscription.get("payer_email")
        
        if user_email:
            license_info = await license_service.get_license_by_email(user_email)
            if license_info:
                await license_service.extend_license(
                    license_id=license_info["id"],
                    days=30,
                    payment_id=str(payment_id)
                )
        
        await mp_service.log_event("subscription_payment", payment)


def verify_mercadopago_signature(
    body: bytes,
    signature: str,
    request_id: str
) -> bool:
    """
    Verify Mercado Pago webhook signature.
    """
    secret = settings.MERCADO_PAGO_WEBHOOK_SECRET
    if not signature or not secret:
        return False
    
    try:
        # Parse signature header
        parts = dict(p.split("=") for p in signature.split(","))
        ts = parts.get("ts")
        v1 = parts.get("v1")
        
        if not ts or not v1:
            return False
        
        # Build signed payload
        manifest = f"id:{request_id};request-id:{request_id};ts:{ts};"
        
        # Calculate expected signature
        expected = hmac.new(
            MP_WEBHOOK_SECRET.encode(),
            manifest.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, v1)
        
    except Exception:
        return False


@router.post("/stripe")
async def stripe_webhook(request: Request):
    """
    Stripe webhook handler (placeholder for future integration).
    """
    # TODO: Implement Stripe webhook handling
    return {"status": "not_implemented"}


@router.get("/health")
async def webhooks_health():
    """Webhook endpoint health check"""
    return {
        "status": "healthy",
        "endpoints": [
            "/webhooks/mercadopago",
            "/webhooks/stripe"
        ]
    }
