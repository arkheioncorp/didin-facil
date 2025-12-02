"""
Testes para api/routes/webhooks.py
Mercado Pago payment webhooks and other integrations
"""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.webhooks import (EvolutionWebhook, MercadoPagoWebhook,
                                 handle_payment_event,
                                 handle_subscription_event,
                                 handle_subscription_payment,
                                 verify_mercadopago_signature)

# ==================== TEST MODELS ====================

class TestMercadoPagoWebhookModel:
    """Testes para modelo MercadoPagoWebhook."""

    def test_valid_webhook(self):
        """Webhook válido com todos os campos."""
        webhook = MercadoPagoWebhook(
            action="payment.approved",
            api_version="v1",
            data={"id": 12345},
            date_created="2024-01-01T00:00:00",
            id=1,
            live_mode=True,
            type="payment",
            user_id="123456"
        )
        
        assert webhook.action == "payment.approved"
        assert webhook.type == "payment"
        assert webhook.data["id"] == 12345

    def test_webhook_minimal_data(self):
        """Webhook com dados mínimos."""
        webhook = MercadoPagoWebhook(
            action="payment.created",
            api_version="v1",
            data={},
            date_created="2024-01-01",
            id=1,
            live_mode=False,
            type="payment",
            user_id="user"
        )
        
        assert webhook.data == {}


class TestEvolutionWebhookModel:
    """Testes para modelo EvolutionWebhook."""

    def test_minimal_webhook(self):
        """Webhook com campos mínimos."""
        webhook = EvolutionWebhook(
            event="MESSAGES_UPSERT",
            instance="my-instance",
            data={"key": "value"}
        )
        
        assert webhook.event == "MESSAGES_UPSERT"
        assert webhook.destination is None
        assert webhook.date_time is None

    def test_full_webhook(self):
        """Webhook com todos os campos."""
        webhook = EvolutionWebhook(
            event="CONNECTION_UPDATE",
            instance="instance-1",
            data={"status": "connected"},
            destination="https://example.com",
            date_time="2024-01-01T12:00:00",
            sender="+5511999999999",
            server_url="https://api.evolution.com",
            apikey="secret-key"
        )
        
        assert webhook.destination == "https://example.com"
        assert webhook.sender == "+5511999999999"


# ==================== TEST VERIFY SIGNATURE ====================

class TestVerifyMercadoPagoSignature:
    """Testes para verify_mercadopago_signature."""

    def test_missing_signature(self):
        """Sem assinatura deve retornar False."""
        result = verify_mercadopago_signature(
            body=b'{"test": true}',
            signature=None,
            request_id="req-123"
        )
        
        assert result is False

    def test_empty_signature(self):
        """Assinatura vazia deve retornar False."""
        result = verify_mercadopago_signature(
            body=b'{"test": true}',
            signature="",
            request_id="req-123"
        )
        
        assert result is False

    @patch('api.routes.webhooks.settings')
    def test_missing_secret(self, mock_settings):
        """Sem secret configurado deve retornar False."""
        mock_settings.MERCADO_PAGO_WEBHOOK_SECRET = None
        
        result = verify_mercadopago_signature(
            body=b'{"test": true}',
            signature="ts=123,v1=abc",
            request_id="req-123"
        )
        
        assert result is False

    @patch('api.routes.webhooks.settings')
    def test_invalid_signature_format(self, mock_settings):
        """Formato de assinatura inválido deve retornar False."""
        mock_settings.MERCADO_PAGO_WEBHOOK_SECRET = "secret"
        mock_settings.MERCADOPAGO_WEBHOOK_SECRET = "secret"
        
        result = verify_mercadopago_signature(
            body=b'{"test": true}',
            signature="invalid-format",
            request_id="req-123"
        )
        
        assert result is False

    @patch('api.routes.webhooks.settings')
    def test_missing_ts_in_signature(self, mock_settings):
        """Sem timestamp na assinatura deve retornar False."""
        mock_settings.MERCADO_PAGO_WEBHOOK_SECRET = "secret"
        mock_settings.MERCADOPAGO_WEBHOOK_SECRET = "secret"
        
        result = verify_mercadopago_signature(
            body=b'{"test": true}',
            signature="v1=abc123",
            request_id="req-123"
        )
        
        assert result is False

    @patch('api.routes.webhooks.settings')
    def test_missing_v1_in_signature(self, mock_settings):
        """Sem v1 na assinatura deve retornar False."""
        mock_settings.MERCADO_PAGO_WEBHOOK_SECRET = "secret"
        mock_settings.MERCADOPAGO_WEBHOOK_SECRET = "secret"
        
        result = verify_mercadopago_signature(
            body=b'{"test": true}',
            signature="ts=123",
            request_id="req-123"
        )
        
        assert result is False

    @patch('api.routes.webhooks.settings')
    def test_valid_signature(self, mock_settings):
        """Assinatura válida deve retornar True."""
        secret = "test-secret"
        request_id = "req-123"
        ts = "1234567890"
        
        mock_settings.MERCADO_PAGO_WEBHOOK_SECRET = secret
        mock_settings.MERCADOPAGO_WEBHOOK_SECRET = secret
        
        # Calcular assinatura esperada
        manifest = f"id:{request_id};request-id:{request_id};ts:{ts};"
        expected_sig = hmac.new(
            secret.encode(),
            manifest.encode(),
            hashlib.sha256
        ).hexdigest()
        
        signature = f"ts={ts},v1={expected_sig}"
        
        result = verify_mercadopago_signature(
            body=b'{"test": true}',
            signature=signature,
            request_id=request_id
        )
        
        assert result is True

    @patch('api.routes.webhooks.settings')
    def test_wrong_signature(self, mock_settings):
        """Assinatura incorreta deve retornar False."""
        mock_settings.MERCADO_PAGO_WEBHOOK_SECRET = "secret"
        mock_settings.MERCADOPAGO_WEBHOOK_SECRET = "secret"
        
        result = verify_mercadopago_signature(
            body=b'{"test": true}',
            signature="ts=123,v1=wrong_signature",
            request_id="req-123"
        )
        
        assert result is False

    @patch('api.routes.webhooks.settings')
    def test_exception_handling(self, mock_settings):
        """Exceções devem retornar False."""
        mock_settings.MERCADO_PAGO_WEBHOOK_SECRET = "secret"
        mock_settings.MERCADOPAGO_WEBHOOK_SECRET = "secret"
        
        # Assinatura malformada que causa exceção
        result = verify_mercadopago_signature(
            body=b'{"test": true}',
            signature="=malformed=signature=",
            request_id="req-123"
        )
        
        assert result is False


# ==================== TEST HANDLE PAYMENT EVENT ====================

class TestHandlePaymentEvent:
    """Testes para handle_payment_event."""

    @pytest.fixture
    def mock_mp_service(self):
        """Mock do MercadoPagoService."""
        service = AsyncMock()
        service.get_payment = AsyncMock()
        service.log_event = AsyncMock()
        service.send_credits_email = AsyncMock()
        return service

    @pytest.fixture
    def mock_license_service(self):
        """Mock do LicenseService."""
        service = AsyncMock()
        service.add_credits = AsyncMock()
        service.activate_lifetime_license = AsyncMock()
        service.get_license_by_email = AsyncMock()
        service.deactivate_license = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_no_payment_id(self, mock_mp_service, mock_license_service):
        """Sem payment_id deve retornar early."""
        await handle_payment_event(
            action="payment.approved",
            data={},  # Sem id
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        
        mock_mp_service.get_payment.assert_not_called()

    @pytest.mark.asyncio
    async def test_payment_created(self, mock_mp_service, mock_license_service):
        """Payment created deve logar evento."""
        mock_mp_service.get_payment.return_value = {"id": "123"}
        
        await handle_payment_event(
            action="payment.created",
            data={"id": "payment_123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        
        mock_mp_service.log_event.assert_called_with(
            "payment_created", {"id": "123"}
        )

    @pytest.mark.asyncio
    async def test_payment_approved_with_credits(
        self, mock_mp_service, mock_license_service
    ):
        """Payment approved deve adicionar créditos."""
        mock_mp_service.get_payment.return_value = {
            "id": "123",
            "payer": {"email": "user@test.com"},
            "metadata": {
                "product_type": "credits",
                "credits": 100,
                "includes_license": False
            }
        }
        
        await handle_payment_event(
            action="payment.approved",
            data={"id": "payment_123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        
        mock_license_service.add_credits.assert_called_once_with(
            email="user@test.com",
            amount=100,
            payment_id="payment_123"
        )

    @pytest.mark.asyncio
    async def test_payment_approved_with_license(
        self, mock_mp_service, mock_license_service
    ):
        """Payment approved deve ativar licença lifetime."""
        mock_mp_service.get_payment.return_value = {
            "id": "123",
            "payer": {"email": "user@test.com"},
            "metadata": {
                "product_type": "license",
                "credits": 0,
                "includes_license": True
            }
        }
        
        await handle_payment_event(
            action="payment.approved",
            data={"id": "payment_123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        
        mock_license_service.activate_lifetime_license.assert_called_once_with(
            email="user@test.com",
            payment_id="payment_123"
        )

    @pytest.mark.asyncio
    async def test_payment_approved_sends_email(
        self, mock_mp_service, mock_license_service
    ):
        """Payment approved deve enviar email de confirmação."""
        mock_mp_service.get_payment.return_value = {
            "id": "123",
            "payer": {"email": "user@test.com"},
            "metadata": {
                "credits": 50,
                "includes_license": True
            }
        }
        
        await handle_payment_event(
            action="payment.approved",
            data={"id": "payment_123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        
        mock_mp_service.send_credits_email.assert_called_once_with(
            "user@test.com", 50, True
        )

    @pytest.mark.asyncio
    async def test_payment_approved_no_email(
        self, mock_mp_service, mock_license_service
    ):
        """Payment approved sem email não deve processar."""
        mock_mp_service.get_payment.return_value = {
            "id": "123",
            "payer": {},  # Sem email
            "metadata": {"credits": 100}
        }
        
        await handle_payment_event(
            action="payment.approved",
            data={"id": "payment_123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        
        mock_license_service.add_credits.assert_not_called()

    @pytest.mark.asyncio
    async def test_payment_cancelled(self, mock_mp_service, mock_license_service):
        """Payment cancelled deve apenas logar."""
        mock_mp_service.get_payment.return_value = {"id": "123"}
        
        await handle_payment_event(
            action="payment.cancelled",
            data={"id": "payment_123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        
        mock_mp_service.log_event.assert_called_with(
            "payment_cancelled", {"id": "123"}
        )

    @pytest.mark.asyncio
    async def test_payment_refunded_deactivates_license(
        self, mock_mp_service, mock_license_service
    ):
        """Payment refunded deve desativar licença."""
        mock_mp_service.get_payment.return_value = {
            "id": "123",
            "payer": {"email": "user@test.com"},
            "metadata": {"product_type": "license"}
        }
        mock_license_service.get_license_by_email.return_value = {
            "id": "license_123"
        }
        
        await handle_payment_event(
            action="payment.refunded",
            data={"id": "payment_123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        
        mock_license_service.deactivate_license.assert_called_once_with(
            license_id="license_123",
            reason="refund"
        )

    @pytest.mark.asyncio
    async def test_payment_refunded_no_license(
        self, mock_mp_service, mock_license_service
    ):
        """Refund sem licença existente não deve falhar."""
        mock_mp_service.get_payment.return_value = {
            "id": "123",
            "payer": {"email": "user@test.com"},
            "metadata": {"product_type": "license"}
        }
        mock_license_service.get_license_by_email.return_value = None
        
        await handle_payment_event(
            action="payment.refunded",
            data={"id": "payment_123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        
        mock_license_service.deactivate_license.assert_not_called()


# ==================== TEST HANDLE SUBSCRIPTION EVENT ====================

class TestHandleSubscriptionEvent:
    """Testes para handle_subscription_event."""

    @pytest.fixture
    def mock_mp_service(self):
        service = AsyncMock()
        service.get_subscription = AsyncMock()
        service.log_event = AsyncMock()
        return service

    @pytest.fixture
    def mock_license_service(self):
        service = AsyncMock()
        service.get_license_by_email = AsyncMock()
        service.create_license = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_no_preapproval_id(
        self, mock_mp_service, mock_license_service
    ):
        """Sem preapproval_id deve retornar early."""
        await handle_subscription_event(
            action="created",
            data={},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        
        mock_mp_service.get_subscription.assert_not_called()

    @pytest.mark.asyncio
    async def test_subscription_created(
        self, mock_mp_service, mock_license_service
    ):
        """Subscription created deve logar evento."""
        mock_mp_service.get_subscription.return_value = {"id": "sub_123"}
        
        await handle_subscription_event(
            action="created",
            data={"id": "preapproval_123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        
        mock_mp_service.log_event.assert_called_with(
            "subscription_created", {"id": "sub_123"}
        )

    @pytest.mark.asyncio
    async def test_subscription_updated_authorized_creates_license(
        self, mock_mp_service, mock_license_service
    ):
        """Subscription updated autorizada deve criar licença se não existe."""
        mock_mp_service.get_subscription.return_value = {
            "id": "sub_123",
            "status": "authorized",
            "payer_email": "user@test.com"
        }
        mock_license_service.get_license_by_email.return_value = None
        
        await handle_subscription_event(
            action="updated",
            data={"id": "preapproval_123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        
        mock_license_service.create_license.assert_called_once_with(
            email="user@test.com",
            plan="lifetime",
            duration_days=-1
        )

    @pytest.mark.asyncio
    async def test_subscription_updated_existing_license(
        self, mock_mp_service, mock_license_service
    ):
        """Subscription updated com licença existente não cria nova."""
        mock_mp_service.get_subscription.return_value = {
            "id": "sub_123",
            "status": "authorized",
            "payer_email": "user@test.com"
        }
        mock_license_service.get_license_by_email.return_value = {
            "id": "existing_license"
        }
        
        await handle_subscription_event(
            action="updated",
            data={"id": "preapproval_123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        
        mock_license_service.create_license.assert_not_called()

    @pytest.mark.asyncio
    async def test_subscription_cancelled(
        self, mock_mp_service, mock_license_service
    ):
        """Subscription cancelled deve apenas logar."""
        mock_mp_service.get_subscription.return_value = {"id": "sub_123"}
        
        await handle_subscription_event(
            action="cancelled",
            data={"id": "preapproval_123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        
        # Deve logar duas vezes devido ao código duplicado
        assert mock_mp_service.log_event.call_count == 2


# ==================== TEST HANDLE SUBSCRIPTION PAYMENT ====================

class TestHandleSubscriptionPayment:
    """Testes para handle_subscription_payment."""

    @pytest.fixture
    def mock_mp_service(self):
        service = AsyncMock()
        service.get_authorized_payment = AsyncMock()
        service.get_subscription = AsyncMock()
        service.log_event = AsyncMock()
        return service

    @pytest.fixture
    def mock_license_service(self):
        service = AsyncMock()
        service.get_license_by_email = AsyncMock()
        service.extend_license = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_no_payment_id(
        self, mock_mp_service, mock_license_service
    ):
        """Sem payment_id deve retornar early."""
        await handle_subscription_payment(
            action="created",
            data={},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        
        mock_mp_service.get_authorized_payment.assert_not_called()

    @pytest.mark.asyncio
    async def test_payment_created_approved(
        self, mock_mp_service, mock_license_service
    ):
        """Payment created aprovado deve estender licença."""
        mock_mp_service.get_authorized_payment.return_value = {
            "id": "pay_123",
            "status": "approved",
            "preapproval_id": "preapproval_123"
        }
        mock_mp_service.get_subscription.return_value = {
            "payer_email": "user@test.com"
        }
        mock_license_service.get_license_by_email.return_value = {
            "id": "license_123"
        }
        
        await handle_subscription_payment(
            action="created",
            data={"id": "pay_123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        
        mock_license_service.extend_license.assert_called_once_with(
            license_id="license_123",
            days=30,
            payment_id="pay_123"
        )

    @pytest.mark.asyncio
    async def test_payment_created_not_approved(
        self, mock_mp_service, mock_license_service
    ):
        """Payment created não aprovado não estende licença."""
        mock_mp_service.get_authorized_payment.return_value = {
            "id": "pay_123",
            "status": "pending",  # Não aprovado
            "preapproval_id": "preapproval_123"
        }
        
        await handle_subscription_payment(
            action="created",
            data={"id": "pay_123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        
        mock_license_service.extend_license.assert_not_called()

    @pytest.mark.asyncio
    async def test_payment_no_license(
        self, mock_mp_service, mock_license_service
    ):
        """Payment sem licença existente não tenta estender."""
        mock_mp_service.get_authorized_payment.return_value = {
            "id": "pay_123",
            "status": "approved",
            "preapproval_id": "preapproval_123"
        }
        mock_mp_service.get_subscription.return_value = {
            "payer_email": "user@test.com"
        }
        mock_license_service.get_license_by_email.return_value = None
        
        await handle_subscription_payment(
            action="created",
            data={"id": "pay_123"},
            mp_service=mock_mp_service,
            license_service=mock_license_service
        )
        
        mock_license_service.extend_license.assert_not_called()


# ==================== TEST WEBHOOK ENDPOINTS ====================

class TestMercadoPagoWebhookEndpoint:
    """Testes para endpoint mercadopago_webhook."""

    @pytest.mark.asyncio
    @patch('api.routes.webhooks.verify_mercadopago_signature')
    @patch('api.routes.webhooks.MercadoPagoService')
    @patch('api.routes.webhooks.LicenseService')
    async def test_invalid_signature(self, MockLicense, MockMP, mock_verify):
        """Assinatura inválida deve retornar 401."""
        from api.routes.webhooks import mercadopago_webhook
        from fastapi import HTTPException
        
        mock_verify.return_value = False
        
        mock_request = AsyncMock()
        mock_request.body = AsyncMock(return_value=b'{"type": "payment"}')
        
        with pytest.raises(HTTPException) as exc_info:
            await mercadopago_webhook(
                request=mock_request,
                x_signature="invalid",
                x_request_id="req-123"
            )
        
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @patch('api.routes.webhooks.verify_mercadopago_signature')
    @patch('api.routes.webhooks.handle_payment_event')
    @patch('api.routes.webhooks.MercadoPagoService')
    @patch('api.routes.webhooks.LicenseService')
    async def test_payment_event(
        self, MockLicense, MockMP, mock_handle, mock_verify
    ):
        """Evento payment deve chamar handle_payment_event."""
        from api.routes.webhooks import mercadopago_webhook
        
        mock_verify.return_value = True
        
        payload = {
            "type": "payment",
            "action": "payment.approved",
            "data": {"id": "123"}
        }
        mock_request = AsyncMock()
        mock_request.body = AsyncMock(return_value=json.dumps(payload).encode())
        
        result = await mercadopago_webhook(
            request=mock_request,
            x_signature="valid",
            x_request_id="req-123"
        )
        
        assert result == {"status": "received"}
        mock_handle.assert_called_once()


class TestStripeWebhookEndpoint:
    """Testes para endpoint stripe_webhook."""

    @pytest.mark.asyncio
    async def test_returns_not_implemented(self):
        """Stripe webhook deve retornar not_implemented."""
        from api.routes.webhooks import stripe_webhook
        
        mock_request = AsyncMock()
        
        result = await stripe_webhook(mock_request)
        
        assert result == {"status": "not_implemented"}


class TestEvolutionWebhookEndpoint:
    """Testes para endpoint evolution_webhook."""

    @pytest.mark.asyncio
    async def test_messages_upsert(self):
        """Evento MESSAGES_UPSERT deve ser processado."""
        from api.routes.webhooks import evolution_webhook
        
        payload = EvolutionWebhook(
            event="MESSAGES_UPSERT",
            instance="my-instance",
            data={"message": "Hello"}
        )
        
        result = await evolution_webhook(payload)
        
        assert result == {"status": "received"}

    @pytest.mark.asyncio
    async def test_qrcode_updated(self):
        """Evento QRCODE_UPDATED deve ser processado."""
        from api.routes.webhooks import evolution_webhook
        
        payload = EvolutionWebhook(
            event="QRCODE_UPDATED",
            instance="my-instance",
            data={"qrcode": "data:image/png;base64,..."}
        )
        
        result = await evolution_webhook(payload)
        
        assert result == {"status": "received"}

    @pytest.mark.asyncio
    async def test_connection_update(self):
        """Evento CONNECTION_UPDATE deve ser processado."""
        from api.routes.webhooks import evolution_webhook
        
        payload = EvolutionWebhook(
            event="CONNECTION_UPDATE",
            instance="my-instance",
            data={"status": "connected", "reason": None}
        )
        
        result = await evolution_webhook(payload)
        
        assert result == {"status": "received"}

    @pytest.mark.asyncio
    async def test_unknown_event(self):
        """Evento desconhecido deve ser aceito."""
        from api.routes.webhooks import evolution_webhook
        
        payload = EvolutionWebhook(
            event="UNKNOWN_EVENT",
            instance="my-instance",
            data={}
        )
        
        result = await evolution_webhook(payload)
        
        assert result == {"status": "received"}


class TestWebhooksHealthEndpoint:
    """Testes para endpoint webhooks_health."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Health check deve retornar status healthy."""
        from api.routes.webhooks import webhooks_health
        
        result = await webhooks_health()
        
        assert result["status"] == "healthy"
        assert "endpoints" in result
        assert "/webhooks/mercadopago" in result["endpoints"]
        assert "/webhooks/stripe" in result["endpoints"]
        assert "/webhooks/evolution" in result["endpoints"]
