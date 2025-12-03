"""Testes abrangentes para Webhooks Routes."""

import hashlib
import hmac
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class TestVerifyMercadoPagoSignature:
    """Testes para verificação de assinatura do Mercado Pago."""

    def test_verify_signature_no_signature(self):
        """Teste sem assinatura."""
        from api.routes.webhooks import verify_mercadopago_signature
        result = verify_mercadopago_signature(b"body", "", "req-id")
        assert result is False

    def test_verify_signature_no_secret(self):
        """Teste sem secret configurado."""
        from api.routes.webhooks import verify_mercadopago_signature
        with patch("api.routes.webhooks.settings") as mock_settings:
            mock_settings.MERCADO_PAGO_WEBHOOK_SECRET = None
            result = verify_mercadopago_signature(b"body", "ts=123,v1=abc", "req-id")
            assert result is False

    def test_verify_signature_invalid_format(self):
        """Teste com formato inválido de assinatura."""
        from api.routes.webhooks import verify_mercadopago_signature
        with patch("api.routes.webhooks.settings") as mock_settings:
            mock_settings.MERCADO_PAGO_WEBHOOK_SECRET = "secret"
            result = verify_mercadopago_signature(b"body", "invalid", "req-id")
            assert result is False

    def test_verify_signature_missing_ts(self):
        """Teste sem timestamp na assinatura."""
        from api.routes.webhooks import verify_mercadopago_signature
        with patch("api.routes.webhooks.settings") as mock_settings:
            mock_settings.MERCADO_PAGO_WEBHOOK_SECRET = "secret"
            result = verify_mercadopago_signature(b"body", "v1=abc", "req-id")
            assert result is False

    def test_verify_signature_missing_v1(self):
        """Teste sem v1 na assinatura."""
        from api.routes.webhooks import verify_mercadopago_signature
        with patch("api.routes.webhooks.settings") as mock_settings:
            mock_settings.MERCADO_PAGO_WEBHOOK_SECRET = "secret"
            result = verify_mercadopago_signature(b"body", "ts=123", "req-id")
            assert result is False


class TestMercadoPagoWebhookModel:
    """Testes para o modelo MercadoPagoWebhook."""

    def test_model_creation(self):
        """Teste de criação do modelo."""
        from api.routes.webhooks import MercadoPagoWebhook
        webhook = MercadoPagoWebhook(
            action="payment.created",
            api_version="v1",
            data={"id": "123"},
            date_created="2024-01-01T00:00:00Z",
            id=12345,
            live_mode=True,
            type="payment",
            user_id="user123"
        )
        assert webhook.action == "payment.created"
        assert webhook.type == "payment"
        assert webhook.live_mode is True


class TestEvolutionWebhookModel:
    """Testes para o modelo EvolutionWebhook."""

    def test_model_minimal(self):
        """Teste de modelo mínimo."""
        from api.routes.webhooks import EvolutionWebhook
        webhook = EvolutionWebhook(
            event="MESSAGES_UPSERT",
            instance="default",
            data={"message": "test"}
        )
        assert webhook.event == "MESSAGES_UPSERT"
        assert webhook.destination is None

    def test_model_full(self):
        """Teste de modelo completo."""
        from api.routes.webhooks import EvolutionWebhook
        webhook = EvolutionWebhook(
            event="MESSAGES_UPSERT",
            instance="default",
            data={"message": "test"},
            destination="5511999999999",
            date_time="2024-01-01T00:00:00Z",
            sender="5511888888888",
            server_url="https://api.evolution.com",
            apikey="apikey123"
        )
        assert webhook.destination == "5511999999999"
        assert webhook.server_url == "https://api.evolution.com"


class TestHandlePaymentEvent:
    """Testes para handle_payment_event."""

    @pytest.fixture
    def mock_mp_service(self):
        service = AsyncMock()
        service.get_payment = AsyncMock(return_value={
            "id": "123",
            "status": "approved",
            "payer": {"email": "test@example.com"},
            "metadata": {
                "product_type": "credits",
                "credits": "100",
                "includes_license": False,
                "package_slug": "basic"
            }
        })
        service.log_event = AsyncMock()
        service.send_credits_email = AsyncMock()
        return service

    @pytest.fixture
    def mock_license_service(self):
        service = AsyncMock()
        service.add_credits = AsyncMock()
        service.activate_lifetime_license = AsyncMock()
        service.get_license_by_email = AsyncMock(return_value={"id": "lic-123"})
        service.deactivate_license = AsyncMock()
        return service

    async def test_payment_created(self, mock_mp_service, mock_license_service):
        """Teste de pagamento criado."""
        from api.routes.webhooks import handle_payment_event
        await handle_payment_event(
            action="payment.created",
            data={"id": "123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        mock_mp_service.log_event.assert_called_once_with("payment_created", mock_mp_service.get_payment.return_value)

    async def test_payment_approved_with_credits(self, mock_mp_service, mock_license_service):
        """Teste de pagamento aprovado com créditos."""
        from api.routes.webhooks import handle_payment_event
        await handle_payment_event(
            action="payment.approved",
            data={"id": "123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        mock_license_service.add_credits.assert_called_once()

    async def test_payment_approved_with_license(self, mock_mp_service, mock_license_service):
        """Teste de pagamento aprovado com licença."""
        from api.routes.webhooks import handle_payment_event
        mock_mp_service.get_payment.return_value["metadata"]["includes_license"] = True
        await handle_payment_event(
            action="payment.approved",
            data={"id": "123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        mock_license_service.activate_lifetime_license.assert_called_once()

    async def test_payment_cancelled(self, mock_mp_service, mock_license_service):
        """Teste de pagamento cancelado."""
        from api.routes.webhooks import handle_payment_event
        await handle_payment_event(
            action="payment.cancelled",
            data={"id": "123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        mock_mp_service.log_event.assert_called_with("payment_cancelled", mock_mp_service.get_payment.return_value)

    async def test_payment_refunded_license(self, mock_mp_service, mock_license_service):
        """Teste de reembolso de licença."""
        from api.routes.webhooks import handle_payment_event
        mock_mp_service.get_payment.return_value["metadata"]["product_type"] = "license"
        await handle_payment_event(
            action="payment.refunded",
            data={"id": "123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        mock_license_service.deactivate_license.assert_called_once()

    async def test_payment_no_id(self, mock_mp_service, mock_license_service):
        """Teste sem ID de pagamento."""
        from api.routes.webhooks import handle_payment_event
        result = await handle_payment_event(
            action="payment.created",
            data={},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        assert result is None
        mock_mp_service.get_payment.assert_not_called()


class TestHandleSubscriptionEvent:
    """Testes para handle_subscription_event."""

    @pytest.fixture
    def mock_mp_service(self):
        service = AsyncMock()
        service.get_subscription = AsyncMock(return_value={
            "id": "sub-123",
            "status": "authorized",
            "external_reference": "user-123:pro:monthly"
        })
        service.log_event = AsyncMock()
        return service

    @pytest.fixture
    def mock_license_service(self):
        return AsyncMock()

    async def test_subscription_no_id(self, mock_mp_service, mock_license_service):
        """Teste sem ID de assinatura."""
        from api.routes.webhooks import handle_subscription_event
        result = await handle_subscription_event(
            action="updated",
            data={},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        assert result is None

    async def test_subscription_no_external_reference(self, mock_mp_service, mock_license_service):
        """Teste sem external_reference."""
        from api.routes.webhooks import handle_subscription_event
        mock_mp_service.get_subscription.return_value["external_reference"] = None
        result = await handle_subscription_event(
            action="updated",
            data={"id": "sub-123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        assert result is None


class TestHandleSubscriptionPayment:
    """Testes para handle_subscription_payment."""

    @pytest.fixture
    def mock_mp_service(self):
        service = AsyncMock()
        service.get_payment = AsyncMock(return_value={
            "id": "pay-123",
            "status": "approved",
            "external_reference": "user-123"
        })
        service.log_event = AsyncMock()
        return service

    @pytest.fixture
    def mock_license_service(self):
        return AsyncMock()

    async def test_subscription_payment_no_id(self, mock_mp_service, mock_license_service):
        """Teste sem ID de pagamento."""
        from api.routes.webhooks import handle_subscription_payment
        result = await handle_subscription_payment(
            action="created",
            data={},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        assert result is None


class TestWebhookEndpoints:
    """Testes para endpoints de webhook."""

    @pytest.fixture
    def mock_request(self):
        request = AsyncMock()
        request.body = AsyncMock(return_value=json.dumps({
            "type": "payment",
            "action": "payment.created",
            "data": {"id": "123"}
        }).encode())
        return request

    async def test_stripe_webhook(self):
        """Teste do webhook do Stripe."""
        from api.routes.webhooks import stripe_webhook
        mock_request = AsyncMock()
        result = await stripe_webhook(mock_request)
        assert result["status"] == "not_implemented"

    async def test_evolution_webhook_messages_upsert(self):
        """Teste do webhook Evolution para mensagens."""
        from api.routes.webhooks import EvolutionWebhook, evolution_webhook
        payload = EvolutionWebhook(
            event="MESSAGES_UPSERT",
            instance="default",
            data={"message": "test"}
        )
        result = await evolution_webhook(payload)
        assert result["status"] == "received"

    async def test_evolution_webhook_qrcode_updated(self):
        """Teste do webhook Evolution para QR Code."""
        from api.routes.webhooks import EvolutionWebhook, evolution_webhook
        payload = EvolutionWebhook(
            event="QRCODE_UPDATED",
            instance="default",
            data={"qrcode": "base64..."}
        )
        result = await evolution_webhook(payload)
        assert result["status"] == "received"

    async def test_evolution_webhook_connection_update(self):
        """Teste do webhook Evolution para conexão."""
        from api.routes.webhooks import EvolutionWebhook, evolution_webhook
        payload = EvolutionWebhook(
            event="CONNECTION_UPDATE",
            instance="default",
            data={"status": "connected", "reason": "success"}
        )
        result = await evolution_webhook(payload)
        assert result["status"] == "received"

    async def test_webhooks_health(self):
        """Teste de health check."""
        from api.routes.webhooks import webhooks_health
        result = await webhooks_health()
        assert result["status"] == "healthy"
        assert "/webhooks/mercadopago" in result["endpoints"]
        assert "/webhooks/stripe" in result["endpoints"]
        assert "/webhooks/evolution" in result["endpoints"]


class TestRouterConfig:
    """Testes para configuração do router."""

    def test_router_exists(self):
        """Teste se router existe."""
        from api.routes.webhooks import router
        assert router is not None

    def test_router_routes(self):
        """Teste se rotas existem."""
        from api.routes.webhooks import router
        routes = [r.path for r in router.routes]
        assert "/mercadopago" in routes
        assert "/stripe" in routes
        assert "/evolution" in routes
        assert "/health" in routes
