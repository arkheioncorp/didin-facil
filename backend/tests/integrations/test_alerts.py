"""
Testes para o módulo de alertas.
================================

Testa:
- AlertManager: Envio, deduplicação, rate limiting
- Canais: Slack, Discord, Webhook, Log
- Alertas específicos: Circuit Breaker, Latência, Success Rate

Autor: Didin Fácil
Versão: 1.0.0
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from integrations.alerts import (
    AlertManager,
    AlertSeverity,
    AlertType,
    Alert,
    SlackChannel,
    DiscordChannel,
    WebhookChannel,
    LogChannel,
    get_alert_manager,
    configure_alert_manager,
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def alert_manager():
    """AlertManager limpo para cada teste."""
    return AlertManager(dedup_window_seconds=60, max_alerts_per_minute=5)


@pytest.fixture
def sample_alert():
    """Alerta de exemplo."""
    return Alert(
        severity=AlertSeverity.CRITICAL,
        alert_type=AlertType.CIRCUIT_BREAKER_OPEN,
        title="Test Alert",
        message="This is a test alert",
        hub="whatsapp"
    )


# ============================================
# TESTES - ALERT DATA CLASS
# ============================================

class TestAlert:
    """Testes para a classe Alert."""

    def test_alert_creation(self):
        """Testa criação de alerta."""
        alert = Alert(
            severity=AlertSeverity.WARNING,
            alert_type=AlertType.HIGH_LATENCY,
            title="High Latency",
            message="Latency is high",
            hub="instagram"
        )

        assert alert.severity == AlertSeverity.WARNING
        assert alert.alert_type == AlertType.HIGH_LATENCY
        assert alert.hub == "instagram"
        assert alert.timestamp is not None

    def test_alert_to_dict(self):
        """Testa conversão para dicionário."""
        alert = Alert(
            severity=AlertSeverity.CRITICAL,
            alert_type=AlertType.CIRCUIT_BREAKER_OPEN,
            title="CB Open",
            message="Circuit breaker opened",
            hub="tiktok",
            metadata={"failure_count": 5}
        )

        data = alert.to_dict()

        assert data["severity"] == "critical"
        assert data["alert_type"] == "circuit_breaker_open"
        assert data["hub"] == "tiktok"
        assert data["metadata"]["failure_count"] == 5
        assert "timestamp" in data

    def test_alert_emoji(self):
        """Testa emojis por severidade."""
        assert Alert(
            severity=AlertSeverity.INFO,
            alert_type=AlertType.HUB_RECOVERED,
            title="", message="", hub=""
        ).get_emoji() == "ℹ️"

        assert Alert(
            severity=AlertSeverity.WARNING,
            alert_type=AlertType.HIGH_LATENCY,
            title="", message="", hub=""
        ).get_emoji() == "⚠️"

        assert Alert(
            severity=AlertSeverity.CRITICAL,
            alert_type=AlertType.CIRCUIT_BREAKER_OPEN,
            title="", message="", hub=""
        ).get_emoji() == "🔴"

        assert Alert(
            severity=AlertSeverity.RECOVERY,
            alert_type=AlertType.CIRCUIT_BREAKER_CLOSED,
            title="", message="", hub=""
        ).get_emoji() == "✅"


# ============================================
# TESTES - LOG CHANNEL
# ============================================

class TestLogChannel:
    """Testes para LogChannel."""

    @pytest.mark.asyncio
    async def test_log_channel_always_succeeds(self, sample_alert):
        """LogChannel deve sempre retornar True."""
        channel = LogChannel()
        result = await channel.send(sample_alert)
        assert result is True

    def test_log_channel_name(self):
        """Testa nome do canal."""
        channel = LogChannel()
        assert channel.name == "log"


# ============================================
# TESTES - SLACK CHANNEL
# ============================================

class TestSlackChannel:
    """Testes para SlackChannel."""

    @pytest.mark.asyncio
    async def test_slack_send_success(self, sample_alert):
        """Testa envio bem-sucedido para Slack."""
        channel = SlackChannel(
            webhook_url="https://hooks.slack.com/services/xxx",
            channel="#alerts"
        )

        with patch.object(channel, '_get_client') as mock_get:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=MagicMock(status_code=200))
            mock_get.return_value = mock_client

            result = await channel.send(sample_alert)

            assert result is True
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_slack_send_failure(self, sample_alert):
        """Testa falha no envio para Slack."""
        channel = SlackChannel(webhook_url="https://invalid")

        with patch.object(channel, '_get_client') as mock_get:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=MagicMock(status_code=500))
            mock_get.return_value = mock_client

            result = await channel.send(sample_alert)

            assert result is False

    @pytest.mark.asyncio
    async def test_slack_handles_exception(self, sample_alert):
        """Testa tratamento de exceção."""
        channel = SlackChannel(webhook_url="https://invalid")

        with patch.object(channel, '_get_client') as mock_get:
            mock_get.side_effect = Exception("Connection error")

            result = await channel.send(sample_alert)

            assert result is False


# ============================================
# TESTES - DISCORD CHANNEL
# ============================================

class TestDiscordChannel:
    """Testes para DiscordChannel."""

    @pytest.mark.asyncio
    async def test_discord_send_success(self, sample_alert):
        """Testa envio bem-sucedido para Discord."""
        channel = DiscordChannel(webhook_url="https://discord.com/api/webhooks/xxx")

        with patch.object(channel, '_get_client') as mock_get:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=MagicMock(status_code=204))
            mock_get.return_value = mock_client

            result = await channel.send(sample_alert)

            assert result is True

    @pytest.mark.asyncio
    async def test_discord_payload_format(self, sample_alert):
        """Testa formato do payload Discord."""
        channel = DiscordChannel(webhook_url="https://discord.com/api/webhooks/xxx")

        with patch.object(channel, '_get_client') as mock_get:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=MagicMock(status_code=200))
            mock_get.return_value = mock_client

            await channel.send(sample_alert)

            call_args = mock_client.post.call_args
            payload = call_args.kwargs.get('json', call_args[1].get('json'))

            assert "embeds" in payload
            assert payload["username"] == "Didin Hub Monitor"


# ============================================
# TESTES - WEBHOOK CHANNEL
# ============================================

class TestWebhookChannel:
    """Testes para WebhookChannel."""

    @pytest.mark.asyncio
    async def test_webhook_send_success(self, sample_alert):
        """Testa envio bem-sucedido para webhook."""
        channel = WebhookChannel(
            url="https://example.com/webhook",
            headers={"Authorization": "Bearer xxx"}
        )

        with patch.object(channel, '_get_client') as mock_get:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=MagicMock(status_code=200))
            mock_get.return_value = mock_client

            result = await channel.send(sample_alert)

            assert result is True

    @pytest.mark.asyncio
    async def test_webhook_uses_custom_headers(self, sample_alert):
        """Testa que headers customizados são usados."""
        channel = WebhookChannel(
            url="https://example.com/webhook",
            headers={"X-Custom": "value"}
        )

        with patch.object(channel, '_get_client') as mock_get:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=MagicMock(status_code=200))
            mock_get.return_value = mock_client

            await channel.send(sample_alert)

            call_args = mock_client.post.call_args
            headers = call_args.kwargs.get('headers', {})
            assert headers.get("X-Custom") == "value"


# ============================================
# TESTES - ALERT MANAGER
# ============================================

class TestAlertManager:
    """Testes para AlertManager."""

    @pytest.mark.asyncio
    async def test_send_alert_success(self, alert_manager):
        """Testa envio de alerta."""
        result = await alert_manager.send_alert(
            severity=AlertSeverity.WARNING,
            alert_type=AlertType.HIGH_LATENCY,
            title="Test",
            message="Test message",
            hub="whatsapp"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_deduplication(self, alert_manager):
        """Testa que alertas duplicados são ignorados."""
        # Primeiro alerta
        result1 = await alert_manager.send_alert(
            severity=AlertSeverity.CRITICAL,
            alert_type=AlertType.CIRCUIT_BREAKER_OPEN,
            title="CB Open",
            message="Test",
            hub="whatsapp"
        )
        assert result1 is True

        # Segundo alerta idêntico (deve ser ignorado)
        result2 = await alert_manager.send_alert(
            severity=AlertSeverity.CRITICAL,
            alert_type=AlertType.CIRCUIT_BREAKER_OPEN,
            title="CB Open",
            message="Test",
            hub="whatsapp"
        )
        assert result2 is False

    @pytest.mark.asyncio
    async def test_skip_dedup(self, alert_manager):
        """Testa skip de deduplicação."""
        await alert_manager.send_alert(
            severity=AlertSeverity.INFO,
            alert_type=AlertType.HUB_RECOVERED,
            title="Recovered",
            message="Test",
            hub="instagram"
        )

        # Com skip_dedup=True deve passar
        result = await alert_manager.send_alert(
            severity=AlertSeverity.INFO,
            alert_type=AlertType.HUB_RECOVERED,
            title="Recovered",
            message="Test",
            hub="instagram",
            skip_dedup=True
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_rate_limiting(self, alert_manager):
        """Testa rate limiting de alertas."""
        # Enviar até o limite (5 por minuto)
        for i in range(5):
            await alert_manager.send_alert(
                severity=AlertSeverity.INFO,
                alert_type=AlertType.HUB_RECOVERED,
                title=f"Alert {i}",
                message="Test",
                hub=f"hub{i}",  # Hubs diferentes para evitar dedup
                skip_dedup=True
            )

        # Próximo deve ser rejeitado por rate limit
        result = await alert_manager.send_alert(
            severity=AlertSeverity.CRITICAL,
            alert_type=AlertType.CIRCUIT_BREAKER_OPEN,
            title="Alert 6",
            message="Test",
            hub="newHub",
            skip_dedup=True
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_circuit_breaker_open_alert(self, alert_manager):
        """Testa alerta de circuit breaker aberto."""
        result = await alert_manager.send_circuit_breaker_open(
            hub="whatsapp",
            failure_count=5,
            threshold=5
        )
        assert result is True

        # Verificar histórico
        history = alert_manager.get_history()
        assert len(history) == 1
        assert history[0]["alert_type"] == "circuit_breaker_open"
        assert history[0]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_alert(self, alert_manager):
        """Testa alerta de circuit breaker half-open."""
        result = await alert_manager.send_circuit_breaker_half_open("instagram")
        assert result is True

    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_alert(self, alert_manager):
        """Testa alerta de circuit breaker fechado."""
        result = await alert_manager.send_circuit_breaker_closed("tiktok")
        assert result is True

        history = alert_manager.get_history()
        assert history[-1]["severity"] == "recovery"

    @pytest.mark.asyncio
    async def test_high_latency_alert(self, alert_manager):
        """Testa alerta de latência alta."""
        result = await alert_manager.send_high_latency_alert(
            hub="whatsapp",
            latency_ms=5000,
            threshold_ms=2000
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_low_success_rate_alert(self, alert_manager):
        """Testa alerta de taxa de sucesso baixa."""
        # Warning para > 50%
        result1 = await alert_manager.send_low_success_rate_alert(
            hub="instagram",
            success_rate=75.0,
            threshold=90.0
        )
        assert result1 is True

        history = alert_manager.get_history()
        assert history[-1]["severity"] == "warning"

    @pytest.mark.asyncio
    async def test_critical_success_rate_alert(self, alert_manager):
        """Testa alerta crítico para taxa de sucesso muito baixa."""
        result = await alert_manager.send_low_success_rate_alert(
            hub="tiktok",
            success_rate=30.0,
            threshold=90.0
        )
        assert result is True

        history = alert_manager.get_history()
        assert history[-1]["severity"] == "critical"

    def test_add_channel(self, alert_manager):
        """Testa adição de canal."""
        initial_count = len(alert_manager.channels)

        mock_channel = MagicMock()
        mock_channel.name = "test"
        alert_manager.add_channel(mock_channel)

        assert len(alert_manager.channels) == initial_count + 1

    def test_remove_channel(self, alert_manager):
        """Testa remoção de canal."""
        # LogChannel é adicionado por padrão
        result = alert_manager.remove_channel("log")
        assert result is True

        # Tentar remover novamente deve falhar
        result = alert_manager.remove_channel("log")
        assert result is False

    def test_get_history(self, alert_manager):
        """Testa obtenção de histórico."""
        history = alert_manager.get_history()
        assert isinstance(history, list)

    def test_clear_history(self, alert_manager):
        """Testa limpeza de histórico."""
        alert_manager._alert_history.append(MagicMock())
        alert_manager.clear_history()

        assert len(alert_manager._alert_history) == 0
        assert len(alert_manager._last_alerts) == 0


# ============================================
# TESTES - FACTORY FUNCTIONS
# ============================================

class TestFactoryFunctions:
    """Testes para funções factory."""

    def test_get_alert_manager_singleton(self):
        """Testa que get_alert_manager retorna singleton."""
        manager1 = get_alert_manager()
        manager2 = get_alert_manager()

        assert manager1 is manager2

    def test_configure_alert_manager(self):
        """Testa configuração do AlertManager."""
        manager = configure_alert_manager(
            slack_webhook="https://hooks.slack.com/xxx",
            discord_webhook="https://discord.com/api/webhooks/xxx",
            dedup_window=120,
            max_per_minute=20
        )

        # Deve ter 3 canais: log + slack + discord
        assert len(manager.channels) == 3
        assert manager.dedup_window == 120
        assert manager.max_alerts_per_minute == 20


# ============================================
# TESTES - MÚLTIPLOS CANAIS
# ============================================

class TestMultipleChannels:
    """Testes com múltiplos canais."""

    @pytest.mark.asyncio
    async def test_send_to_all_channels(self, alert_manager):
        """Testa envio para todos os canais."""
        # Adicionar canal mock
        mock_channel = AsyncMock()
        mock_channel.name = "mock"
        mock_channel.send = AsyncMock(return_value=True)
        alert_manager.add_channel(mock_channel)

        result = await alert_manager.send_alert(
            severity=AlertSeverity.INFO,
            alert_type=AlertType.HUB_RECOVERED,
            title="Test",
            message="Test",
            hub="test"
        )

        assert result is True
        mock_channel.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_partial_channel_failure(self, alert_manager):
        """Testa que falha parcial ainda retorna True."""
        # Canal que falha
        failing_channel = AsyncMock()
        failing_channel.name = "failing"
        failing_channel.send = AsyncMock(return_value=False)
        alert_manager.add_channel(failing_channel)

        # Canal que sucede
        success_channel = AsyncMock()
        success_channel.name = "success"
        success_channel.send = AsyncMock(return_value=True)
        alert_manager.add_channel(success_channel)

        result = await alert_manager.send_alert(
            severity=AlertSeverity.WARNING,
            alert_type=AlertType.HIGH_LATENCY,
            title="Test",
            message="Test",
            hub="test"
        )

        # Deve retornar True porque pelo menos um canal teve sucesso
        assert result is True
