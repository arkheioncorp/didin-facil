"""
Hub Alert System
=================
Sistema de alertas para eventos dos Integration Hubs.

Este módulo fornece:
- AlertManager: Gerenciador centralizado de alertas
- AlertChannel: Interface para canais de notificação
- Implementações: Slack, Discord, Email, Webhook

Uso:
    from integrations.alerts import get_alert_manager, AlertSeverity

    # Disparar alerta manualmente
    await get_alert_manager().send_alert(
        severity=AlertSeverity.CRITICAL,
        title="Circuit Breaker Aberto",
        message="WhatsApp Hub circuit breaker abriu",
        hub="whatsapp"
    )

Autor: TikTrend Finder
Versão: 1.0.0
"""

import asyncio
import logging
import httpx
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from functools import wraps

logger = logging.getLogger(__name__)


# ============================================
# ENUMS & DATA CLASSES
# ============================================

class AlertSeverity(Enum):
    """Níveis de severidade de alertas."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    RECOVERY = "recovery"


class AlertType(Enum):
    """Tipos de alertas."""
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    CIRCUIT_BREAKER_HALF_OPEN = "circuit_breaker_half_open"
    CIRCUIT_BREAKER_CLOSED = "circuit_breaker_closed"
    HIGH_LATENCY = "high_latency"
    LOW_SUCCESS_RATE = "low_success_rate"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    HUB_UNHEALTHY = "hub_unhealthy"
    HUB_DEGRADED = "hub_degraded"
    HUB_RECOVERED = "hub_recovered"


@dataclass
class Alert:
    """Representa um alerta."""
    severity: AlertSeverity
    alert_type: AlertType
    title: str
    message: str
    hub: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "severity": self.severity.value,
            "alert_type": self.alert_type.value,
            "title": self.title,
            "message": self.message,
            "hub": self.hub,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    def get_emoji(self) -> str:
        """Retorna emoji baseado na severidade."""
        emojis = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.CRITICAL: "🔴",
            AlertSeverity.RECOVERY: "✅"
        }
        return emojis.get(self.severity, "📢")


# ============================================
# ALERT CHANNELS (INTERFACES)
# ============================================

class AlertChannel(ABC):
    """Interface para canais de alerta."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome do canal."""
        pass

    @abstractmethod
    async def send(self, alert: Alert) -> bool:
        """Envia alerta pelo canal."""
        pass


class SlackChannel(AlertChannel):
    """Canal de alertas via Slack."""

    def __init__(self, webhook_url: str, channel: str = "#alerts"):
        self.webhook_url = webhook_url
        self.channel = channel
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def name(self) -> str:
        return "slack"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def send(self, alert: Alert) -> bool:
        """Envia alerta para Slack."""
        try:
            color = {
                AlertSeverity.INFO: "#2196F3",
                AlertSeverity.WARNING: "#FFC107",
                AlertSeverity.CRITICAL: "#F44336",
                AlertSeverity.RECOVERY: "#4CAF50"
            }.get(alert.severity, "#9E9E9E")

            payload = {
                "channel": self.channel,
                "username": "TikTrend Hub Monitor",
                "icon_emoji": ":robot_face:",
                "attachments": [{
                    "color": color,
                    "title": f"{alert.get_emoji()} {alert.title}",
                    "text": alert.message,
                    "fields": [
                        {"title": "Hub", "value": alert.hub, "short": True},
                        {"title": "Severity", "value": alert.severity.value.upper(), "short": True},
                        {"title": "Type", "value": alert.alert_type.value, "short": True},
                        {"title": "Time", "value": alert.timestamp.strftime("%H:%M:%S UTC"), "short": True}
                    ],
                    "footer": "TikTrend Finder Hub Monitor",
                    "ts": int(alert.timestamp.timestamp())
                }]
            }

            client = await self._get_client()
            response = await client.post(self.webhook_url, json=payload)
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Erro ao enviar alerta Slack: {e}")
            return False


class DiscordChannel(AlertChannel):
    """Canal de alertas via Discord."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def name(self) -> str:
        return "discord"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def send(self, alert: Alert) -> bool:
        """Envia alerta para Discord."""
        try:
            color = {
                AlertSeverity.INFO: 0x2196F3,
                AlertSeverity.WARNING: 0xFFC107,
                AlertSeverity.CRITICAL: 0xF44336,
                AlertSeverity.RECOVERY: 0x4CAF50
            }.get(alert.severity, 0x9E9E9E)

            payload = {
                "username": "TikTrend Hub Monitor",
                "embeds": [{
                    "title": f"{alert.get_emoji()} {alert.title}",
                    "description": alert.message,
                    "color": color,
                    "fields": [
                        {"name": "Hub", "value": alert.hub, "inline": True},
                        {"name": "Severity", "value": alert.severity.value.upper(), "inline": True},
                        {"name": "Type", "value": alert.alert_type.value, "inline": True}
                    ],
                    "footer": {"text": "TikTrend Finder Hub Monitor"},
                    "timestamp": alert.timestamp.isoformat()
                }]
            }

            client = await self._get_client()
            response = await client.post(self.webhook_url, json=payload)
            return response.status_code in (200, 204)

        except Exception as e:
            logger.error(f"Erro ao enviar alerta Discord: {e}")
            return False


class WebhookChannel(AlertChannel):
    """Canal de alertas via Webhook genérico."""

    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None):
        self.url = url
        self.headers = headers or {}
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def name(self) -> str:
        return "webhook"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def send(self, alert: Alert) -> bool:
        """Envia alerta para webhook."""
        try:
            client = await self._get_client()
            response = await client.post(
                self.url,
                json=alert.to_dict(),
                headers=self.headers
            )
            return response.status_code in (200, 201, 202, 204)

        except Exception as e:
            logger.error(f"Erro ao enviar alerta Webhook: {e}")
            return False


class LogChannel(AlertChannel):
    """Canal de alertas via Log (sempre ativo)."""

    @property
    def name(self) -> str:
        return "log"

    async def send(self, alert: Alert) -> bool:
        """Loga o alerta."""
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.CRITICAL: logging.ERROR,
            AlertSeverity.RECOVERY: logging.INFO
        }.get(alert.severity, logging.INFO)

        logger.log(
            log_level,
            f"[ALERT] {alert.get_emoji()} [{alert.hub}] {alert.title}: {alert.message}"
        )
        return True


# ============================================
# ALERT MANAGER
# ============================================

class AlertManager:
    """
    Gerenciador centralizado de alertas.

    Features:
    - Múltiplos canais de notificação
    - Deduplicação de alertas
    - Rate limiting de alertas
    - Histórico em memória
    """

    def __init__(
        self,
        dedup_window_seconds: int = 300,
        max_alerts_per_minute: int = 10
    ):
        self.channels: List[AlertChannel] = []
        self.dedup_window = dedup_window_seconds
        self.max_alerts_per_minute = max_alerts_per_minute
        self._alert_history: List[Alert] = []
        self._last_alerts: Dict[str, datetime] = {}  # key -> timestamp
        self._alert_count_per_minute: int = 0
        self._last_minute: datetime = datetime.now(timezone.utc)

        # Sempre adiciona canal de log
        self.add_channel(LogChannel())

    def add_channel(self, channel: AlertChannel) -> None:
        """Adiciona um canal de alertas."""
        self.channels.append(channel)
        logger.info(f"Canal de alertas adicionado: {channel.name}")

    def remove_channel(self, channel_name: str) -> bool:
        """Remove um canal de alertas."""
        for i, channel in enumerate(self.channels):
            if channel.name == channel_name:
                self.channels.pop(i)
                logger.info(f"Canal de alertas removido: {channel_name}")
                return True
        return False

    def _get_dedup_key(self, alert: Alert) -> str:
        """Gera chave de deduplicação."""
        return f"{alert.hub}:{alert.alert_type.value}:{alert.severity.value}"

    def _is_duplicate(self, alert: Alert) -> bool:
        """Verifica se alerta é duplicado."""
        key = self._get_dedup_key(alert)
        last_time = self._last_alerts.get(key)

        if last_time:
            elapsed = (alert.timestamp - last_time).total_seconds()
            if elapsed < self.dedup_window:
                logger.debug(f"Alerta duplicado ignorado: {key}")
                return True

        return False

    def _is_rate_limited(self) -> bool:
        """Verifica rate limit de alertas."""
        now = datetime.now(timezone.utc)

        # Reset contador a cada minuto
        if (now - self._last_minute).total_seconds() >= 60:
            self._alert_count_per_minute = 0
            self._last_minute = now

        if self._alert_count_per_minute >= self.max_alerts_per_minute:
            logger.warning("Rate limit de alertas atingido")
            return True

        return False

    async def send_alert(
        self,
        severity: AlertSeverity,
        alert_type: AlertType,
        title: str,
        message: str,
        hub: str,
        metadata: Optional[Dict[str, Any]] = None,
        skip_dedup: bool = False
    ) -> bool:
        """
        Envia alerta para todos os canais configurados.

        Args:
            severity: Nível de severidade
            alert_type: Tipo do alerta
            title: Título do alerta
            message: Mensagem detalhada
            hub: Nome do hub (whatsapp, instagram, tiktok)
            metadata: Dados adicionais
            skip_dedup: Ignorar deduplicação

        Returns:
            True se pelo menos um canal recebeu o alerta
        """
        alert = Alert(
            severity=severity,
            alert_type=alert_type,
            title=title,
            message=message,
            hub=hub,
            metadata=metadata or {}
        )

        # Verificar deduplicação
        if not skip_dedup and self._is_duplicate(alert):
            return False

        # Verificar rate limit
        if self._is_rate_limited():
            return False

        # Atualizar tracking
        key = self._get_dedup_key(alert)
        self._last_alerts[key] = alert.timestamp
        self._alert_count_per_minute += 1
        self._alert_history.append(alert)

        # Limitar histórico
        if len(self._alert_history) > 1000:
            self._alert_history = self._alert_history[-500:]

        # Enviar para todos os canais
        results = await asyncio.gather(
            *[channel.send(alert) for channel in self.channels],
            return_exceptions=True
        )

        success_count = sum(1 for r in results if r is True)
        logger.debug(f"Alerta enviado para {success_count}/{len(self.channels)} canais")

        return success_count > 0

    async def send_circuit_breaker_open(
        self,
        hub: str,
        failure_count: int,
        threshold: int
    ) -> bool:
        """Alerta específico para circuit breaker aberto."""
        return await self.send_alert(
            severity=AlertSeverity.CRITICAL,
            alert_type=AlertType.CIRCUIT_BREAKER_OPEN,
            title=f"Circuit Breaker ABERTO - {hub.upper()}",
            message=(
                f"O circuit breaker do hub {hub} foi aberto após {failure_count} falhas consecutivas.\n"
                f"Threshold configurado: {threshold}\n\n"
                f"O hub está temporariamente indisponível. Requisições serão rejeitadas até "
                f"o circuit breaker entrar em half-open."
            ),
            hub=hub,
            metadata={"failure_count": failure_count, "threshold": threshold}
        )

    async def send_circuit_breaker_half_open(self, hub: str) -> bool:
        """Alerta para circuit breaker em half-open."""
        return await self.send_alert(
            severity=AlertSeverity.WARNING,
            alert_type=AlertType.CIRCUIT_BREAKER_HALF_OPEN,
            title=f"Circuit Breaker HALF-OPEN - {hub.upper()}",
            message=(
                f"O circuit breaker do hub {hub} está em modo half-open.\n"
                f"O sistema está testando se o serviço externo se recuperou."
            ),
            hub=hub
        )

    async def send_circuit_breaker_closed(self, hub: str) -> bool:
        """Alerta para circuit breaker fechado (recuperação)."""
        return await self.send_alert(
            severity=AlertSeverity.RECOVERY,
            alert_type=AlertType.CIRCUIT_BREAKER_CLOSED,
            title=f"Circuit Breaker FECHADO - {hub.upper()}",
            message=(
                f"O circuit breaker do hub {hub} foi fechado.\n"
                f"O serviço está operando normalmente novamente."
            ),
            hub=hub
        )

    async def send_high_latency_alert(
        self,
        hub: str,
        latency_ms: float,
        threshold_ms: float
    ) -> bool:
        """Alerta para latência alta."""
        return await self.send_alert(
            severity=AlertSeverity.WARNING,
            alert_type=AlertType.HIGH_LATENCY,
            title=f"Latência Alta - {hub.upper()}",
            message=(
                f"O hub {hub} está com latência elevada.\n"
                f"Latência atual: {latency_ms:.0f}ms\n"
                f"Threshold: {threshold_ms:.0f}ms"
            ),
            hub=hub,
            metadata={"latency_ms": latency_ms, "threshold_ms": threshold_ms}
        )

    async def send_low_success_rate_alert(
        self,
        hub: str,
        success_rate: float,
        threshold: float
    ) -> bool:
        """Alerta para taxa de sucesso baixa."""
        severity = AlertSeverity.CRITICAL if success_rate < 50 else AlertSeverity.WARNING

        return await self.send_alert(
            severity=severity,
            alert_type=AlertType.LOW_SUCCESS_RATE,
            title=f"Taxa de Sucesso Baixa - {hub.upper()}",
            message=(
                f"O hub {hub} está com taxa de sucesso abaixo do esperado.\n"
                f"Taxa atual: {success_rate:.1f}%\n"
                f"Threshold: {threshold:.1f}%"
            ),
            hub=hub,
            metadata={"success_rate": success_rate, "threshold": threshold}
        )

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retorna histórico de alertas."""
        return [a.to_dict() for a in self._alert_history[-limit:]]

    def clear_history(self) -> None:
        """Limpa histórico de alertas."""
        self._alert_history.clear()
        self._last_alerts.clear()


# ============================================
# SINGLETON & FACTORY
# ============================================

_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Retorna instância singleton do AlertManager."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


def configure_alert_manager(
    slack_webhook: Optional[str] = None,
    discord_webhook: Optional[str] = None,
    custom_webhook: Optional[str] = None,
    dedup_window: int = 300,
    max_per_minute: int = 10
) -> AlertManager:
    """
    Configura o AlertManager com canais de notificação.

    Args:
        slack_webhook: URL do webhook Slack
        discord_webhook: URL do webhook Discord
        custom_webhook: URL de webhook personalizado
        dedup_window: Janela de deduplicação em segundos
        max_per_minute: Máximo de alertas por minuto

    Returns:
        AlertManager configurado
    """
    global _alert_manager

    _alert_manager = AlertManager(
        dedup_window_seconds=dedup_window,
        max_alerts_per_minute=max_per_minute
    )

    if slack_webhook:
        _alert_manager.add_channel(SlackChannel(slack_webhook))

    if discord_webhook:
        _alert_manager.add_channel(DiscordChannel(discord_webhook))

    if custom_webhook:
        _alert_manager.add_channel(WebhookChannel(custom_webhook))

    return _alert_manager


# ============================================
# DECORATORS
# ============================================

def alert_on_circuit_breaker_change(hub_name: str):
    """
    Decorator que envia alertas quando circuit breaker muda de estado.

    Uso:
        @alert_on_circuit_breaker_change("whatsapp")
        async def my_method(self):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Obter estado antes
            cb = getattr(self, '_circuit_breaker', None)
            state_before = cb.state if cb else None

            # Executar função
            result = await func(self, *args, **kwargs)

            # Verificar mudança de estado
            if cb:
                state_after = cb.state
                if state_before != state_after:
                    manager = get_alert_manager()

                    if state_after.value == "open":
                        await manager.send_circuit_breaker_open(
                            hub=hub_name,
                            failure_count=cb.stats.failure_count,
                            threshold=cb.config.failure_threshold
                        )
                    elif state_after.value == "half_open":
                        await manager.send_circuit_breaker_half_open(hub_name)
                    elif state_after.value == "closed" and state_before.value != "closed":
                        await manager.send_circuit_breaker_closed(hub_name)

            return result
        return wrapper
    return decorator
