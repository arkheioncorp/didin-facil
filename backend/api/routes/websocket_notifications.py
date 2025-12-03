"""
WebSocket Notifications Endpoint
================================
Real-time notifications via WebSocket for:
- Post publication status
- Account connection events
- Scheduler updates
- Error alerts
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Set
from uuid import uuid4

from fastapi import (APIRouter, Depends, HTTPException, Query, WebSocket,
                     WebSocketDisconnect)
from pydantic import BaseModel
from shared.redis import get_redis

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


# ==================== Types ====================

class NotificationType:
    POST_PUBLISHED = "post_published"
    POST_FAILED = "post_failed"
    POST_SCHEDULED = "post_scheduled"
    ACCOUNT_CONNECTED = "account_connected"
    ACCOUNT_DISCONNECTED = "account_disconnected"
    ACCOUNT_EXPIRED = "account_expired"
    CHALLENGE_REQUIRED = "challenge_required"
    QUOTA_WARNING = "quota_warning"
    ERROR = "error"
    INFO = "info"
    # Bot automation notifications
    BOT_TASK_STARTED = "bot_task_started"
    BOT_TASK_COMPLETED = "bot_task_completed"
    BOT_TASK_FAILED = "bot_task_failed"
    BOT_TASK_PROGRESS = "bot_task_progress"
    BOT_STATS_UPDATE = "bot_stats_update"
    BOT_SCREENSHOT = "bot_screenshot"
    BOT_WORKER_STARTED = "bot_worker_started"
    BOT_WORKER_STOPPED = "bot_worker_stopped"


class WebSocketNotification(BaseModel):
    id: str
    type: str
    platform: Optional[str] = None
    title: str
    message: str
    timestamp: str
    data: Optional[dict] = None
    read: bool = False


class ConnectionManager:
    """Manages WebSocket connections for real-time notifications"""

    def __init__(self):
        # user_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Anonymous connections (no auth token)
        self.anonymous_connections: Set[WebSocket] = set()
        # Platform subscriptions: user_id -> Set of platforms
        self.platform_subscriptions: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        
        if user_id:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
            logger.info(f"WebSocket connected for user {user_id}")
        else:
            self.anonymous_connections.add(websocket)
            logger.info("Anonymous WebSocket connection established")

    def disconnect(self, websocket: WebSocket, user_id: Optional[str] = None):
        """Remove a WebSocket connection"""
        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                # Clean up subscriptions
                if user_id in self.platform_subscriptions:
                    del self.platform_subscriptions[user_id]
            logger.info(f"WebSocket disconnected for user {user_id}")
        else:
            self.anonymous_connections.discard(websocket)
            logger.info("Anonymous WebSocket disconnected")

    def subscribe_to_platform(self, user_id: str, platform: str):
        """Subscribe user to platform-specific notifications"""
        if user_id not in self.platform_subscriptions:
            self.platform_subscriptions[user_id] = set()
        self.platform_subscriptions[user_id].add(platform)

    def unsubscribe_from_platform(self, user_id: str, platform: str):
        """Unsubscribe user from platform-specific notifications"""
        if user_id in self.platform_subscriptions:
            self.platform_subscriptions[user_id].discard(platform)

    async def send_to_user(self, user_id: str, message: dict):
        """Send message to all connections for a specific user"""
        if user_id in self.active_connections:
            dead_connections = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
                    dead_connections.add(connection)
            
            # Clean up dead connections
            for conn in dead_connections:
                self.active_connections[user_id].discard(conn)

    async def broadcast(self, message: dict, platform: Optional[str] = None):
        """Broadcast message to all connected users (optionally filtered by platform)"""
        # Broadcast to authenticated users
        for user_id, connections in self.active_connections.items():
            # Check platform subscription if specified
            if platform:
                subscriptions = self.platform_subscriptions.get(user_id, set())
                if platform not in subscriptions and "all" not in subscriptions:
                    continue
            
            dead_connections = set()
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.add(connection)
            
            for conn in dead_connections:
                connections.discard(conn)

        # Broadcast to anonymous connections
        dead_connections = set()
        for connection in self.anonymous_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.add(connection)
        
        for conn in dead_connections:
            self.anonymous_connections.discard(conn)

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        authenticated = sum(len(conns) for conns in self.active_connections.values())
        return authenticated + len(self.anonymous_connections)


# Global connection manager
manager = ConnectionManager()


# ==================== Helper Functions ====================

def create_notification(
    notification_type: str,
    title: str,
    message: str,
    platform: Optional[str] = None,
    data: Optional[dict] = None,
) -> dict:
    """Create a notification payload"""
    return {
        "event": "notification",
        "data": {
            "id": str(uuid4()),
            "type": notification_type,
            "platform": platform,
            "title": title,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
            "read": False,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def publish_notification(
    notification_type: str,
    title: str,
    message: str,
    user_id: Optional[str] = None,
    platform: Optional[str] = None,
    data: Optional[dict] = None,
):
    """
    Publish a notification to WebSocket clients.
    If user_id is provided, sends only to that user.
    Otherwise broadcasts to all connected clients.
    """
    notification = create_notification(
        notification_type=notification_type,
        title=title,
        message=message,
        platform=platform,
        data=data,
    )

    if user_id:
        await manager.send_to_user(user_id, notification)
    else:
        await manager.broadcast(notification, platform=platform)

    # Also store in Redis for persistence
    try:
        redis = await get_redis()
        if redis:
            key = f"notifications:{user_id or 'broadcast'}"
            await redis.lpush(key, json.dumps(notification["data"]))
            await redis.ltrim(key, 0, 99)  # Keep last 100 notifications
            await redis.expire(key, 86400 * 7)  # 7 days TTL
    except Exception as e:
        logger.warning(f"Failed to store notification in Redis: {e}")


# ==================== WebSocket Endpoint ====================

@router.websocket("/ws/notifications")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for real-time notifications.
    
    Connect with optional token for authenticated access.
    
    Events received from server:
    - notification: New notification
    - post_update: Post status change
    - account_update: Account status change
    - scheduler_update: Scheduler events
    - ping: Heartbeat ping (respond with pong)
    
    Events to send to server:
    - pong: Heartbeat response
    - subscribe: Subscribe to platform (data: {platform: string})
    - unsubscribe: Unsubscribe from platform (data: {platform: string})
    - mark_read: Mark notification as read (data: {notificationId: string})
    - mark_all_read: Mark all notifications as read
    """
    # TODO: Validate token and get user_id
    # For now, extract user_id from token if provided
    user_id = None
    if token:
        # Simple token validation (replace with proper auth)
        # user_id = await validate_token(token)
        user_id = token  # Placeholder

    await manager.connect(websocket, user_id)

    try:
        # Send connection confirmation
        await websocket.send_json({
            "event": "connected",
            "data": {
                "userId": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Load recent notifications from Redis
        try:
            redis = await get_redis()
            if redis:
                key = f"notifications:{user_id or 'broadcast'}"
                notifications = await redis.lrange(key, 0, 19)  # Last 20
                for notif_json in reversed(notifications):
                    notif = json.loads(notif_json)
                    await websocket.send_json({
                        "event": "notification",
                        "data": notif,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
        except Exception as e:
            logger.warning(f"Failed to load notifications from Redis: {e}")

        # Message handling loop
        while True:
            data = await websocket.receive_json()
            event = data.get("event", "")

            if event == "pong":
                # Heartbeat response, ignore
                pass

            elif event == "ping":
                # Respond to client ping
                await websocket.send_json({
                    "event": "pong",
                    "data": {},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            elif event == "subscribe" and user_id:
                platform = data.get("data", {}).get("platform")
                if platform:
                    manager.subscribe_to_platform(user_id, platform)
                    await websocket.send_json({
                        "event": "subscribed",
                        "data": {"platform": platform},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })

            elif event == "unsubscribe" and user_id:
                platform = data.get("data", {}).get("platform")
                if platform:
                    manager.unsubscribe_from_platform(user_id, platform)
                    await websocket.send_json({
                        "event": "unsubscribed",
                        "data": {"platform": platform},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })

            elif event == "mark_read":
                notification_id = data.get("data", {}).get("notificationId")
                if notification_id:
                    # Update in Redis (simplified)
                    logger.info(f"Marking notification {notification_id} as read")

            elif event == "mark_all_read":
                # Mark all as read (simplified)
                logger.info(f"Marking all notifications as read for user {user_id}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)


# ==================== Notification API ====================

@router.get("/api/notifications", response_model=list)
async def get_notifications(
    user_id: Optional[str] = Query(None, description="User ID"),
    limit: int = Query(20, le=100, description="Max notifications to return"),
):
    """Get stored notifications for a user"""
    try:
        redis = await get_redis()
        if not redis:
            return []
        
        key = f"notifications:{user_id or 'broadcast'}"
        notifications_json = await redis.lrange(key, 0, limit - 1)
        return [json.loads(n) for n in notifications_json]
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}")
        return []


@router.post("/api/notifications/send")
async def send_notification(
    notification_type: str = Query(..., description="Notification type"),
    title: str = Query(..., description="Notification title"),
    message: str = Query(..., description="Notification message"),
    user_id: Optional[str] = Query(None, description="Target user ID (optional)"),
    platform: Optional[str] = Query(None, description="Platform filter (optional)"),
):
    """Send a notification via WebSocket (admin endpoint)"""
    await publish_notification(
        notification_type=notification_type,
        title=title,
        message=message,
        user_id=user_id,
        platform=platform,
    )
    return {"status": "sent", "connections": manager.get_connection_count()}


@router.get("/api/notifications/connections")
async def get_connection_stats():
    """Get WebSocket connection statistics"""
    return {
        "total_connections": manager.get_connection_count(),
        "authenticated_users": len(manager.active_connections),
        "anonymous_connections": len(manager.anonymous_connections),
    }


# ==================== Export for other modules ====================

__all__ = [
    "router",
    "manager",
    "publish_notification",
    "create_notification",
    "NotificationType",
]
