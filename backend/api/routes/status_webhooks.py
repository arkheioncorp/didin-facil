"""
Publication Status Webhooks
Notifies external services about post status changes
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from shared.redis import redis_client

router = APIRouter()
logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


class WebhookConfig(BaseModel):
    """Webhook configuration"""
    id: str
    url: HttpUrl
    events: List[str] = Field(
        default=["post.completed", "post.failed"],
        description="Events to notify: post.scheduled, post.processing, post.completed, post.failed"
    )
    secret: Optional[str] = None
    active: bool = True
    created_at: datetime = Field(default_factory=_utc_now)
    last_triggered: Optional[datetime] = None
    failure_count: int = 0


class WebhookEvent(BaseModel):
    """Webhook event payload"""
    event_type: str
    timestamp: datetime
    data: dict


class WebhookCreateRequest(BaseModel):
    """Request to create a webhook"""
    url: HttpUrl
    events: List[str] = ["post.completed", "post.failed"]
    secret: Optional[str] = None


class WebhookUpdateRequest(BaseModel):
    """Request to update a webhook"""
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    secret: Optional[str] = None
    active: Optional[bool] = None


# ============= Webhook Management Endpoints =============

@router.get("/webhooks")
async def list_webhooks() -> List[WebhookConfig]:
    """List all configured webhooks"""
    webhooks = []
    
    keys = await redis_client.keys("webhook:config:*")
    for key in keys:
        data = await redis_client.hgetall(key)
        if data:
            webhooks.append(WebhookConfig(
                id=data.get("id", key.split(":")[-1]),
                url=data.get("url"),
                events=json.loads(data.get("events", "[]")),
                secret=data.get("secret"),
                active=data.get("active", "true").lower() == "true",
                created_at=datetime.fromisoformat(data.get("created_at", datetime.now(timezone.utc).isoformat())),
                last_triggered=datetime.fromisoformat(data["last_triggered"]) if data.get("last_triggered") else None,
                failure_count=int(data.get("failure_count", 0))
            ))
    
    return webhooks


@router.post("/webhooks")
async def create_webhook(request: WebhookCreateRequest) -> WebhookConfig:
    """Create a new webhook"""
    import uuid
    
    webhook_id = str(uuid.uuid4())[:8]
    
    webhook = WebhookConfig(
        id=webhook_id,
        url=request.url,
        events=request.events,
        secret=request.secret
    )
    
    await redis_client.hset(
        f"webhook:config:{webhook_id}",
        mapping={
            "id": webhook_id,
            "url": str(webhook.url),
            "events": json.dumps(webhook.events),
            "secret": webhook.secret or "",
            "active": str(webhook.active).lower(),
            "created_at": webhook.created_at.isoformat(),
            "failure_count": "0"
        }
    )
    
    return webhook


@router.get("/webhooks/{webhook_id}")
async def get_webhook(webhook_id: str) -> WebhookConfig:
    """Get a specific webhook"""
    data = await redis_client.hgetall(f"webhook:config:{webhook_id}")
    
    if not data:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return WebhookConfig(
        id=webhook_id,
        url=data.get("url"),
        events=json.loads(data.get("events", "[]")),
        secret=data.get("secret") or None,
        active=data.get("active", "true").lower() == "true",
        created_at=datetime.fromisoformat(data.get("created_at", datetime.now(timezone.utc).isoformat())),
        last_triggered=datetime.fromisoformat(data["last_triggered"]) if data.get("last_triggered") else None,
        failure_count=int(data.get("failure_count", 0))
    )


@router.patch("/webhooks/{webhook_id}")
async def update_webhook(webhook_id: str, request: WebhookUpdateRequest) -> WebhookConfig:
    """Update a webhook"""
    key = f"webhook:config:{webhook_id}"
    
    exists = await redis_client.exists(key)
    if not exists:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    updates = {}
    if request.url:
        updates["url"] = str(request.url)
    if request.events is not None:
        updates["events"] = json.dumps(request.events)
    if request.secret is not None:
        updates["secret"] = request.secret
    if request.active is not None:
        updates["active"] = str(request.active).lower()
    
    if updates:
        await redis_client.hset(key, mapping=updates)
    
    return await get_webhook(webhook_id)


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str):
    """Delete a webhook"""
    key = f"webhook:config:{webhook_id}"
    
    deleted = await redis_client.delete(key)
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return {"success": True, "deleted": webhook_id}


@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(webhook_id: str, background_tasks: BackgroundTasks):
    """Send a test event to the webhook"""
    webhook = await get_webhook(webhook_id)
    
    test_event = WebhookEvent(
        event_type="test",
        timestamp=datetime.now(timezone.utc),
        data={
            "message": "This is a test webhook event from TikTrend Finder",
            "webhook_id": webhook_id
        }
    )
    
    background_tasks.add_task(send_webhook, webhook, test_event)
    
    return {"success": True, "message": "Test event queued"}


# ============= Webhook Event History =============

@router.get("/webhooks/{webhook_id}/history")
async def get_webhook_history(
    webhook_id: str,
    limit: int = 50
) -> List[dict]:
    """Get recent webhook deliveries"""
    history_key = f"webhook:history:{webhook_id}"
    
    entries = await redis_client.lrange(history_key, 0, limit - 1)
    
    return [json.loads(entry) for entry in entries]


# ============= Core Webhook Delivery =============

async def send_webhook(webhook: WebhookConfig, event: WebhookEvent):
    """Send a webhook notification"""
    payload = event.model_dump(mode="json")
    payload_bytes = json.dumps(payload).encode()
    
    headers = {
        "Content-Type": "application/json",
        "X-TikTrend-Event": event.event_type,
        "X-TikTrend-Delivery": datetime.now(timezone.utc).isoformat(),
    }
    
    # Add HMAC signature if secret is configured
    if webhook.secret:
        signature = hmac.new(
            webhook.secret.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        headers["X-TikTrend-Signature"] = f"sha256={signature}"
    
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event.event_type,
        "success": False,
        "status_code": None,
        "error": None
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                str(webhook.url),
                content=payload_bytes,
                headers=headers
            )
            
            result["status_code"] = response.status_code
            result["success"] = 200 <= response.status_code < 300
            
            if not result["success"]:
                result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
                
    except httpx.TimeoutException:
        result["error"] = "Request timed out"
    except httpx.RequestError as e:
        result["error"] = f"Request failed: {str(e)}"
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
    
    # Update webhook metadata
    key = f"webhook:config:{webhook.id}"
    await redis_client.hset(key, "last_triggered", datetime.now(timezone.utc).isoformat())
    
    if not result["success"]:
        await redis_client.hincrby(key, "failure_count", 1)
    else:
        await redis_client.hset(key, "failure_count", "0")
    
    # Store in history
    history_key = f"webhook:history:{webhook.id}"
    await redis_client.lpush(history_key, json.dumps(result))
    await redis_client.ltrim(history_key, 0, 99)  # Keep last 100
    
    logger.info(f"Webhook {webhook.id} delivery: {result}")


async def trigger_event(event_type: str, data: dict):
    """
    Trigger an event to all subscribed webhooks
    
    Usage:
        await trigger_event("post.completed", {
            "post_id": "123",
            "platform": "youtube",
            "url": "https://youtube.com/..."
        })
    """
    webhooks = await list_webhooks()
    
    event = WebhookEvent(
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        data=data
    )
    
    for webhook in webhooks:
        if not webhook.active:
            continue
        
        if event_type in webhook.events or "*" in webhook.events:
            # Don't await - fire and forget for performance
            import asyncio
            asyncio.create_task(send_webhook(webhook, event))


# ============= Event Types Documentation =============

@router.get("/webhooks/events/types")
async def list_event_types():
    """List all available webhook event types"""
    return {
        "events": [
            {
                "type": "post.scheduled",
                "description": "A new post was scheduled",
                "payload": {
                    "post_id": "string",
                    "platform": "string",
                    "scheduled_for": "datetime"
                }
            },
            {
                "type": "post.processing",
                "description": "A post started processing (upload in progress)",
                "payload": {
                    "post_id": "string",
                    "platform": "string",
                    "started_at": "datetime"
                }
            },
            {
                "type": "post.completed",
                "description": "A post was successfully published",
                "payload": {
                    "post_id": "string",
                    "platform": "string",
                    "url": "string",
                    "published_at": "datetime"
                }
            },
            {
                "type": "post.failed",
                "description": "A post failed to publish",
                "payload": {
                    "post_id": "string",
                    "platform": "string",
                    "error": "string",
                    "retry_count": "number",
                    "moved_to_dlq": "boolean"
                }
            },
            {
                "type": "quota.warning",
                "description": "YouTube quota approaching limit",
                "payload": {
                    "quota_used": "number",
                    "quota_limit": "number",
                    "percentage": "number"
                }
            },
            {
                "type": "session.expired",
                "description": "A platform session expired",
                "payload": {
                    "platform": "string",
                    "account_id": "string"
                }
            },
            {
                "type": "challenge.detected",
                "description": "Instagram security challenge detected",
                "payload": {
                    "account_id": "string",
                    "challenge_type": "string"
                }
            }
        ]
    }
