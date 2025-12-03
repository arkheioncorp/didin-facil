"""
Webhooks Routes
Mercado Pago payment webhooks and other integrations
"""

import hashlib
import hmac
import json
from typing import Optional

from api.services.license import LicenseService
from api.services.mercadopago import MercadoPagoService
from fastapi import APIRouter, Header, HTTPException, Request, status
from modules.subscription import (BillingCycle, PlanTier, SubscriptionService,
                                  SubscriptionStatus)
from pydantic import BaseModel
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


class EvolutionWebhook(BaseModel):
    """Evolution API webhook payload"""
    event: str
    instance: str
    data: dict
    destination: Optional[str] = None
    date_time: Optional[str] = None
    sender: Optional[str] = None
    server_url: Optional[str] = None
    apikey: Optional[str] = None


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
    """Handle payment events for lifetime license and credits"""
    payment_id = data.get("id")

    if not payment_id:
        return

    # Get payment details from Mercado Pago
    payment = await mp_service.get_payment(payment_id)

    if action == "payment.created":
        # Log payment initiation
        await mp_service.log_event("payment_created", payment)

    elif action == "payment.approved":
        # Payment successful - activate license and/or add credits
        user_email = payment.get("payer", {}).get("email")
        metadata = payment.get("metadata", {})
        product_type = metadata.get("product_type", "credits")
        credits_amount = int(metadata.get("credits", 0))
        includes_license = metadata.get("includes_license", False)
        package_slug = metadata.get("package_slug", "")

        if user_email:
            # Add credits to user account
            if credits_amount > 0:
                await license_service.add_credits(
                    email=user_email,
                    amount=credits_amount,
                    payment_id=str(payment_id)
                )

            # Activate lifetime license if package includes it
            if includes_license:
                await license_service.activate_lifetime_license(
                    email=user_email,
                    payment_id=str(payment_id)
                )

            # Send confirmation email
            await mp_service.send_credits_email(
                user_email, credits_amount, includes_license
            )

        await mp_service.log_event("payment_approved", payment)

    elif action == "payment.cancelled":
        await mp_service.log_event("payment_cancelled", payment)

    elif action == "payment.refunded":
        # Refund - may deactivate license or deduct credits
        user_email = payment.get("payer", {}).get("email")
        product_type = payment.get("metadata", {}).get("product_type", "license")

        if user_email and product_type == "license":
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
    """
    Handle subscription events.
    Updates user subscription status based on MP events.
    """
    preapproval_id = data.get("id")

    if not preapproval_id:
        return

    subscription_mp = await mp_service.get_subscription(preapproval_id)
    external_reference = subscription_mp.get("external_reference")
    
    if not external_reference:
        return

    # Parse external_reference (user_id:plan:cycle)
    parts = external_reference.split(":")
    user_id = parts[0]
    plan_tier = None
    billing_cycle = None
    
    if len(parts) >= 3:
        try:
            plan_tier = PlanTier(parts[1])
            billing_cycle = BillingCycle(parts[2])
        except ValueError:
            pass

    status_mp = subscription_mp.get("status")
    
    subscription_service = SubscriptionService()
    
    # Map MP status to internal status
    status_map = {
        "authorized": SubscriptionStatus.ACTIVE,
        "paused": SubscriptionStatus.PAST_DUE,
        "cancelled": SubscriptionStatus.CANCELED,
        "pending": SubscriptionStatus.EXPIRED
    }
    
    new_status = status_map.get(status_mp, SubscriptionStatus.EXPIRED)
    
    try:
        subscription = await subscription_service.get_subscription(user_id)
        subscription.status = new_status
        
        if plan_tier:
            subscription.plan = plan_tier
        if billing_cycle:
            subscription.billing_cycle = billing_cycle
        
        if new_status == SubscriptionStatus.CANCELED:
            from datetime import datetime, timezone
            subscription.canceled_at = datetime.now(timezone.utc)
            
        await subscription_service._cache_subscription(subscription)
        await mp_service.log_event("subscription_updated", subscription_mp)
        
    except Exception as e:
        await mp_service.log_event(
            "subscription_update_error",
            {"error": str(e)}
        )


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
    
    payment = await mp_service.get_payment(payment_id)
    
    if action == "created" and payment.get("status") == "approved":
        # Recurring payment successful
        external_reference = payment.get("external_reference")
        
        if external_reference:
            user_id = external_reference
            subscription_service = SubscriptionService()
            
            try:
                subscription = await subscription_service.get_subscription(
                    user_id
                )
                
                # Extend subscription
                from datetime import datetime, timezone, timedelta, timezone
                
                now = datetime.now(timezone.utc)
                # If current period end is in the future, add to it.
                # Else start from now.
                start_date = max(now, subscription.current_period_end)
                subscription.current_period_end = (
                    start_date + timedelta(days=30)
                )
                subscription.status = SubscriptionStatus.ACTIVE
                
                await subscription_service._cache_subscription(subscription)
                await mp_service.log_event("subscription_renewed", payment)
                
            except Exception as e:
                await mp_service.log_event(
                    "subscription_renewal_error",
                    {"error": str(e)}
                )


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
        secret = settings.MERCADOPAGO_WEBHOOK_SECRET or "dev-secret"
        expected = hmac.new(
            secret.encode(),
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


@router.post("/evolution")
async def evolution_webhook(payload: EvolutionWebhook):
    """
    Handle Evolution API webhooks.
    
    Events handled:
    - MESSAGES_UPSERT: New message received
    - QRCODE_UPDATED: New QR Code generated
    - CONNECTION_UPDATE: Connection status changed
    """
    print(f"Received webhook: {payload.event} for instance {payload.instance}")
    
    if payload.event == "MESSAGES_UPSERT":
        # Handle new message
        message_data = payload.data
        # TODO: Process message (save to DB, trigger chatbot, etc.)
        print(f"New message: {message_data}")
        
    elif payload.event == "QRCODE_UPDATED":
        # Handle QR Code update
        qrcode_data = payload.data
        # TODO: Update QR Code in frontend (via WebSocket or polling)
        print(f"New QR Code: {qrcode_data.get('qrcode')}")
        
    elif payload.event == "CONNECTION_UPDATE":
        # Handle connection update
        connection_data = payload.data
        status = connection_data.get("status")
        reason = connection_data.get("reason")
        print(f"Connection update: {status} - {reason}")
        
    return {"status": "received"}


@router.get("/health")
async def webhooks_health():
    """Webhook endpoint health check"""
    return {
        "status": "healthy",
        "endpoints": [
            "/webhooks/mercadopago",
            "/webhooks/stripe",
            "/webhooks/evolution"
        ]
    }
