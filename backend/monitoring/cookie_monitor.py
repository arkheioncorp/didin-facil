"""
TikTok Cookie Monitoring and Alerting
Monitors cookie expiration and sends alerts via multiple channels
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum
import httpx

from shared.redis import get_redis
from shared.config import settings


logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Supported alert channels"""
    SLACK = "slack"
    DISCORD = "discord"
    EMAIL = "email"
    WEBHOOK = "webhook"


@dataclass
class CookieStatus:
    """Cookie health status"""
    session_id: str
    is_valid: bool
    expires_at: Optional[datetime]
    days_until_expiry: int
    last_check: datetime
    error: Optional[str] = None
    
    @property
    def severity(self) -> AlertSeverity:
        if not self.is_valid:
            return AlertSeverity.CRITICAL
        if self.days_until_expiry <= 3:
            return AlertSeverity.CRITICAL
        if self.days_until_expiry <= 7:
            return AlertSeverity.WARNING
        return AlertSeverity.INFO


@dataclass
class Alert:
    """Alert message"""
    title: str
    message: str
    severity: AlertSeverity
    timestamp: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class CookieMonitor:
    """
    Monitors TikTok cookies and sends alerts when they're about to expire.
    
    Features:
    - Periodic health checks
    - Multi-channel alerting (Slack, Discord, Email, Webhook)
    - Alert deduplication (don't spam)
    - Prometheus metrics export
    """
    
    REDIS_KEY_STATUS = "monitor:cookie:status"
    REDIS_KEY_ALERTS = "monitor:cookie:alerts"
    REDIS_KEY_LAST_ALERT = "monitor:cookie:last_alert"
    
    # Alert thresholds (days until expiry)
    THRESHOLD_CRITICAL = 3
    THRESHOLD_WARNING = 7
    THRESHOLD_INFO = 14
    
    # Minimum time between alerts for same issue (hours)
    ALERT_COOLDOWN_HOURS = 6
    
    def __init__(self):
        self._redis = None
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_redis(self):
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client
    
    async def check_cookies(self) -> CookieStatus:
        """
        Check TikTok cookie health.
        
        Returns:
            CookieStatus with current health info
        """
        from scraper.tiktok.api_scraper import TikTokAPIScraper
        
        try:
            scraper = TikTokAPIScraper()
            health = await scraper.health_check()
            
            # Parse expiration from cookies
            expires_at = None
            days_until_expiry = 0
            
            if health.get("expires"):
                try:
                    expires_at = datetime.fromisoformat(
                        health["expires"].replace("Z", "+00:00")
                    )
                    days_until_expiry = (expires_at - datetime.now(timezone.utc)).days
                except Exception:
                    pass
            
            status = CookieStatus(
                session_id=health.get("session_id", "unknown"),
                is_valid=health.get("cookies_valid", False),
                expires_at=expires_at,
                days_until_expiry=days_until_expiry,
                last_check=datetime.now(timezone.utc)
            )
            
            # Store status in Redis
            redis = await self._get_redis()
            await redis.set(
                self.REDIS_KEY_STATUS,
                json.dumps({
                    "session_id": status.session_id,
                    "is_valid": status.is_valid,
                    "expires_at": status.expires_at.isoformat() if status.expires_at else None,
                    "days_until_expiry": status.days_until_expiry,
                    "last_check": status.last_check.isoformat(),
                    "severity": status.severity.value
                }),
                ex=3600  # 1 hour TTL
            )
            
            return status
            
        except Exception as e:
            logger.error(f"Cookie check failed: {e}")
            return CookieStatus(
                session_id="unknown",
                is_valid=False,
                expires_at=None,
                days_until_expiry=0,
                last_check=datetime.now(timezone.utc),
                error=str(e)
            )
    
    async def should_send_alert(self, severity: AlertSeverity) -> bool:
        """
        Check if we should send an alert (avoid spam).
        
        Returns:
            True if enough time has passed since last alert
        """
        redis = await self._get_redis()
        key = f"{self.REDIS_KEY_LAST_ALERT}:{severity.value}"
        
        last_alert = await redis.get(key)
        if not last_alert:
            return True
        
        try:
            last_time = datetime.fromisoformat(last_alert)
            cooldown = timedelta(hours=self.ALERT_COOLDOWN_HOURS)
            
            # Critical alerts have shorter cooldown
            if severity == AlertSeverity.CRITICAL:
                cooldown = timedelta(hours=2)
            
            return datetime.now(timezone.utc) - last_time > cooldown
        except Exception:
            return True
    
    async def mark_alert_sent(self, severity: AlertSeverity):
        """Mark that an alert was sent"""
        redis = await self._get_redis()
        key = f"{self.REDIS_KEY_LAST_ALERT}:{severity.value}"
        
        await redis.set(
            key,
            datetime.now(timezone.utc).isoformat(),
            ex=86400  # 24 hours
        )
    
    async def send_alert(
        self,
        status: CookieStatus,
        channels: Optional[List[AlertChannel]] = None
    ):
        """
        Send alert to configured channels.
        
        Args:
            status: Current cookie status
            channels: List of channels to send to (defaults to all configured)
        """
        if not await self.should_send_alert(status.severity):
            logger.info(f"Alert suppressed (cooldown): {status.severity.value}")
            return
        
        alert = self._create_alert(status)
        
        if channels is None:
            channels = self._get_configured_channels()
        
        for channel in channels:
            try:
                if channel == AlertChannel.SLACK:
                    await self._send_slack_alert(alert)
                elif channel == AlertChannel.DISCORD:
                    await self._send_discord_alert(alert)
                elif channel == AlertChannel.WEBHOOK:
                    await self._send_webhook_alert(alert)
                elif channel == AlertChannel.EMAIL:
                    await self._send_email_alert(alert)
                    
                logger.info(f"Alert sent to {channel.value}: {alert.title}")
            except Exception as e:
                logger.error(f"Failed to send alert to {channel.value}: {e}")
        
        await self.mark_alert_sent(status.severity)
        
        # Store alert history
        await self._store_alert(alert)
    
    def _create_alert(self, status: CookieStatus) -> Alert:
        """Create alert from cookie status"""
        if not status.is_valid:
            title = "🚨 TikTok Cookies Inválidos"
            message = (
                "Os cookies do TikTok expiraram ou foram invalidados.\n"
                "O scraper não conseguirá coletar dados até que novos cookies sejam configurados.\n\n"
                "**Ação Necessária:** Atualizar cookies imediatamente."
            )
        elif status.days_until_expiry <= self.THRESHOLD_CRITICAL:
            title = f"⚠️ TikTok Cookies Expiram em {status.days_until_expiry} Dias"
            message = (
                f"Os cookies do TikTok expiram em **{status.days_until_expiry} dias**.\n"
                f"Data de expiração: {status.expires_at.strftime('%d/%m/%Y %H:%M') if status.expires_at else 'Desconhecida'}\n\n"
                "**Ação Recomendada:** Renovar cookies antes da expiração."
            )
        elif status.days_until_expiry <= self.THRESHOLD_WARNING:
            title = f"⏰ TikTok Cookies Expiram em {status.days_until_expiry} Dias"
            message = (
                f"Os cookies do TikTok expiram em **{status.days_until_expiry} dias**.\n"
                f"Data de expiração: {status.expires_at.strftime('%d/%m/%Y %H:%M') if status.expires_at else 'Desconhecida'}\n\n"
                "Considere renovar os cookies em breve."
            )
        else:
            title = "✅ TikTok Cookies OK"
            message = (
                f"Cookies válidos por mais **{status.days_until_expiry} dias**.\n"
                f"Data de expiração: {status.expires_at.strftime('%d/%m/%Y %H:%M') if status.expires_at else 'Desconhecida'}"
            )
        
        return Alert(
            title=title,
            message=message,
            severity=status.severity,
            timestamp=datetime.now(timezone.utc),
            metadata={
                "session_id": status.session_id,
                "days_until_expiry": status.days_until_expiry,
                "expires_at": status.expires_at.isoformat() if status.expires_at else None,
                "error": status.error
            }
        )
    
    def _get_configured_channels(self) -> List[AlertChannel]:
        """Get list of configured alert channels"""
        channels = []
        
        if getattr(settings, 'SLACK_WEBHOOK_URL', None):
            channels.append(AlertChannel.SLACK)
        if getattr(settings, 'DISCORD_WEBHOOK_URL', None):
            channels.append(AlertChannel.DISCORD)
        if getattr(settings, 'ALERT_WEBHOOK_URL', None):
            channels.append(AlertChannel.WEBHOOK)
        if getattr(settings, 'ALERT_EMAIL', None):
            channels.append(AlertChannel.EMAIL)
        
        return channels
    
    async def _send_slack_alert(self, alert: Alert):
        """Send alert to Slack"""
        webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', None)
        if not webhook_url:
            return
        
        color_map = {
            AlertSeverity.CRITICAL: "#ff0000",
            AlertSeverity.WARNING: "#ffaa00",
            AlertSeverity.INFO: "#00ff00"
        }
        
        payload = {
            "attachments": [{
                "color": color_map.get(alert.severity, "#808080"),
                "title": alert.title,
                "text": alert.message,
                "fields": [
                    {"title": "Severity", "value": alert.severity.value.upper(), "short": True},
                    {"title": "Time", "value": alert.timestamp.strftime("%Y-%m-%d %H:%M UTC"), "short": True}
                ],
                "footer": "Didin Fácil Cookie Monitor"
            }]
        }
        
        client = await self._get_http_client()
        await client.post(webhook_url, json=payload)
    
    async def _send_discord_alert(self, alert: Alert):
        """Send alert to Discord"""
        webhook_url = getattr(settings, 'DISCORD_WEBHOOK_URL', None)
        if not webhook_url:
            return
        
        color_map = {
            AlertSeverity.CRITICAL: 0xff0000,
            AlertSeverity.WARNING: 0xffaa00,
            AlertSeverity.INFO: 0x00ff00
        }
        
        payload = {
            "embeds": [{
                "title": alert.title,
                "description": alert.message,
                "color": color_map.get(alert.severity, 0x808080),
                "timestamp": alert.timestamp.isoformat(),
                "footer": {"text": "Didin Fácil Cookie Monitor"}
            }]
        }
        
        client = await self._get_http_client()
        await client.post(webhook_url, json=payload)
    
    async def _send_webhook_alert(self, alert: Alert):
        """Send alert to custom webhook"""
        webhook_url = getattr(settings, 'ALERT_WEBHOOK_URL', None)
        if not webhook_url:
            return
        
        client = await self._get_http_client()
        await client.post(webhook_url, json=alert.to_dict())
    
    async def _send_email_alert(self, alert: Alert):
        """Send alert via email (placeholder - implement with your email service)"""
        # TODO: Implement email sending (SendGrid, SES, etc.)
        logger.info(f"Email alert would be sent: {alert.title}")
    
    async def _store_alert(self, alert: Alert):
        """Store alert in history"""
        redis = await self._get_redis()
        
        await redis.lpush(
            self.REDIS_KEY_ALERTS,
            json.dumps(alert.to_dict())
        )
        
        # Keep only last 100 alerts
        await redis.ltrim(self.REDIS_KEY_ALERTS, 0, 99)
    
    async def get_alert_history(self, limit: int = 20) -> List[Dict]:
        """Get recent alert history"""
        redis = await self._get_redis()
        
        alerts = await redis.lrange(self.REDIS_KEY_ALERTS, 0, limit - 1)
        return [json.loads(a) for a in alerts]
    
    async def get_current_status(self) -> Optional[Dict]:
        """Get current cookie status from cache"""
        redis = await self._get_redis()
        
        status = await redis.get(self.REDIS_KEY_STATUS)
        if status:
            return json.loads(status)
        return None
    
    async def run_check_and_alert(self):
        """Run a single check and send alert if needed"""
        status = await self.check_cookies()
        
        # Only alert for warnings and critical
        if status.severity in [AlertSeverity.WARNING, AlertSeverity.CRITICAL]:
            await self.send_alert(status)
        
        return status
    
    async def start_monitoring(self, interval_minutes: int = 60):
        """
        Start continuous monitoring loop.
        
        Args:
            interval_minutes: Check interval in minutes
        """
        logger.info(f"Starting cookie monitoring (interval: {interval_minutes}m)")
        
        while True:
            try:
                status = await self.run_check_and_alert()
                logger.info(
                    f"Cookie check: valid={status.is_valid}, "
                    f"expires_in={status.days_until_expiry}d, "
                    f"severity={status.severity.value}"
                )
            except Exception as e:
                logger.error(f"Monitoring check failed: {e}")
            
            await asyncio.sleep(interval_minutes * 60)
    
    async def close(self):
        """Cleanup resources"""
        if self._http_client:
            await self._http_client.aclose()


# Prometheus metrics integration
def get_prometheus_metrics() -> str:
    """
    Generate Prometheus metrics for cookie monitoring.
    
    Returns:
        Prometheus metrics in text format
    """
    import asyncio
    
    async def _get_metrics():
        monitor = CookieMonitor()
        status = await monitor.get_current_status()
        
        if not status:
            return ""
        
        metrics = []
        
        # Cookie validity gauge (1 = valid, 0 = invalid)
        metrics.append(
            f'tiktok_cookies_valid{{session_id="{status.get("session_id", "unknown")}"}} '
            f'{1 if status.get("is_valid") else 0}'
        )
        
        # Days until expiry gauge
        metrics.append(
            f'tiktok_cookies_expiry_days{{session_id="{status.get("session_id", "unknown")}"}} '
            f'{status.get("days_until_expiry", 0)}'
        )
        
        # Last check timestamp
        try:
            last_check = datetime.fromisoformat(status.get("last_check", ""))
            metrics.append(
                f'tiktok_cookies_last_check_timestamp '
                f'{int(last_check.timestamp())}'
            )
        except Exception:
            pass
        
        return "\n".join(metrics)
    
    return asyncio.run(_get_metrics())


# CLI for testing
if __name__ == "__main__":
    async def main():
        monitor = CookieMonitor()
        
        print("Checking TikTok cookies...")
        status = await monitor.run_check_and_alert()
        
        print("\nStatus:")
        print(f"  Valid: {status.is_valid}")
        print(f"  Expires: {status.expires_at}")
        print(f"  Days until expiry: {status.days_until_expiry}")
        print(f"  Severity: {status.severity.value}")
        
        if status.error:
            print(f"  Error: {status.error}")
        
        await monitor.close()
    
    asyncio.run(main())
