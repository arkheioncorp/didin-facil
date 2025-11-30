"""
Webhooks Routes Tests - Full Coverage
Tests for Mercado Pago and other payment webhooks using AsyncClient.
"""

import pytest
import pytest_asyncio
import hmac
import hashlib
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from api.main import app


@pytest_asyncio.fixture
async def async_client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter before each test."""
    for middleware in app.user_middleware:
        if hasattr(middleware, 'cls'):
            if middleware.cls.__name__ == 'RateLimitMiddleware':
                pass
    yield
    for route in app.routes:
        if hasattr(route, 'app'):
            for mw in getattr(route.app, 'middleware_stack', []):
                if hasattr(mw, 'request_counts'):
                    mw.request_counts.clear()


@pytest.fixture
def mock_mp_service():
    """Mock MercadoPago service."""
    with patch("api.routes.webhooks.MercadoPagoService") as cls:
        service = AsyncMock()
        service.get_payment = AsyncMock()
        service.get_subscription = AsyncMock()
        service.get_authorized_payment = AsyncMock()
        service.log_event = AsyncMock()
        service.send_license_email = AsyncMock()
        service.send_credits_email = AsyncMock()
        cls.return_value = service
        yield service


@pytest.fixture
def mock_license_service():
    """Mock License service."""
    with patch("api.routes.webhooks.LicenseService") as cls:
        service = AsyncMock()
        service.get_license_by_email = AsyncMock()
        service.create_license = AsyncMock()
        service.add_credits = AsyncMock()
        service.deactivate_license = AsyncMock()
        service.extend_license = AsyncMock()
        service.activate_lifetime_license = AsyncMock()
        cls.return_value = service
        yield service


@pytest.fixture
def valid_signature():
    """Generate valid webhook signature."""
    ts = "1234567890"
    request_id = "test-request-id"

    with patch("api.routes.webhooks.settings") as mock_settings:
        mock_settings.MERCADO_PAGO_WEBHOOK_SECRET = "test-secret"
        mock_settings.MERCADOPAGO_WEBHOOK_SECRET = "test-secret"

        manifest = f"id:{request_id};request-id:{request_id};ts:{ts};"
        v1 = hmac.new(
            b"test-secret",
            manifest.encode(),
            hashlib.sha256
        ).hexdigest()

        return f"ts={ts},v1={v1}", request_id


class TestMercadoPagoWebhook:
    """Test Mercado Pago webhook endpoint."""

    @pytest.mark.asyncio
    async def test_webhook_invalid_signature(
        self,
        mock_mp_service,
        mock_license_service,
        async_client
    ):
        """Test webhook rejects invalid signature."""
        payload = {
            "type": "payment",
            "action": "payment.created",
            "data": {"id": "123"}
        }

        with patch(
            "api.routes.webhooks.verify_mercadopago_signature",
            return_value=False
        ):
            response = await async_client.post(
                "/webhooks/mercadopago",
                json=payload,
                headers={
                    "X-Signature": "invalid",
                    "X-Request-Id": "test"
                }
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_webhook_payment_created(
        self,
        mock_mp_service,
        mock_license_service,
        async_client
    ):
        """Test handling payment.created event."""
        mock_mp_service.get_payment.return_value = {
            "id": "123",
            "status": "pending"
        }

        payload = {
            "type": "payment",
            "action": "payment.created",
            "data": {"id": "123"}
        }

        with patch(
            "api.routes.webhooks.verify_mercadopago_signature",
            return_value=True
        ):
            response = await async_client.post(
                "/webhooks/mercadopago",
                json=payload,
                headers={
                    "X-Signature": "valid",
                    "X-Request-Id": "test"
                }
            )

        assert response.status_code == 200
        assert response.json() == {"status": "received"}
        mock_mp_service.log_event.assert_called()

    @pytest.mark.asyncio
    async def test_webhook_payment_approved_with_credits_and_license(
        self,
        mock_mp_service,
        mock_license_service,
        async_client
    ):
        """Test payment.approved adds credits and activates license."""
        mock_mp_service.get_payment.return_value = {
            "id": "123",
            "status": "approved",
            "payer": {"email": "test@example.com"},
            "metadata": {
                "product_type": "credits",
                "credits": 1000,
                "includes_license": True,
                "package_slug": "ultra"
            }
        }

        payload = {
            "type": "payment",
            "action": "payment.approved",
            "data": {"id": "123"}
        }

        with patch(
            "api.routes.webhooks.verify_mercadopago_signature",
            return_value=True
        ):
            response = await async_client.post(
                "/webhooks/mercadopago",
                json=payload,
                headers={
                    "X-Signature": "valid",
                    "X-Request-Id": "test"
                }
            )

        assert response.status_code == 200
        mock_license_service.add_credits.assert_called_once()
        mock_license_service.activate_lifetime_license.assert_called_once()
        mock_mp_service.send_credits_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_webhook_payment_approved_existing_license(
        self,
        mock_mp_service,
        mock_license_service,
        async_client
    ):
        """Test payment.approved with existing license."""
        mock_mp_service.get_payment.return_value = {
            "id": "123",
            "status": "approved",
            "payer": {"email": "test@example.com"},
            "metadata": {"product_type": "license"}
        }
        mock_license_service.get_license_by_email.return_value = {
            "id": "existing_lic"
        }

        payload = {
            "type": "payment",
            "action": "payment.approved",
            "data": {"id": "123"}
        }

        with patch(
            "api.routes.webhooks.verify_mercadopago_signature",
            return_value=True
        ):
            response = await async_client.post(
                "/webhooks/mercadopago",
                json=payload,
                headers={
                    "X-Signature": "valid",
                    "X-Request-Id": "test"
                }
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_payment_credits_only(
        self,
        mock_mp_service,
        mock_license_service,
        async_client
    ):
        """Test payment.approved for credits purchase only (no license)."""
        mock_mp_service.get_payment.return_value = {
            "id": "123",
            "status": "approved",
            "payer": {"email": "test@example.com"},
            "metadata": {
                "product_type": "credits",
                "credits": 500,
                "includes_license": False,
                "package_slug": "starter"
            }
        }

        payload = {
            "type": "payment",
            "action": "payment.approved",
            "data": {"id": "123"}
        }

        with patch(
            "api.routes.webhooks.verify_mercadopago_signature",
            return_value=True
        ):
            response = await async_client.post(
                "/webhooks/mercadopago",
                json=payload,
                headers={
                    "X-Signature": "valid",
                    "X-Request-Id": "test"
                }
            )

        assert response.status_code == 200
        mock_license_service.add_credits.assert_called_once()
        # Should not activate license for credits-only package
        mock_license_service.activate_lifetime_license.assert_not_called()


class TestSubscriptionEvents:
    """Tests for subscription events."""

    @pytest.mark.asyncio
    async def test_webhook_subscription_created(
        self,
        mock_mp_service,
        mock_license_service,
        async_client
    ):
        """Test subscription.created event."""
        mock_mp_service.get_subscription.return_value = {
            "id": "sub_123",
            "status": "authorized",
            "payer_email": "test@example.com"
        }

        payload = {
            "type": "subscription_preapproval",
            "action": "created",
            "data": {"id": "sub_123"}
        }

        with patch(
            "api.routes.webhooks.verify_mercadopago_signature",
            return_value=True
        ):
            response = await async_client.post(
                "/webhooks/mercadopago",
                json=payload,
                headers={
                    "X-Signature": "valid",
                    "X-Request-Id": "test"
                }
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_subscription_cancelled(
        self,
        mock_mp_service,
        mock_license_service,
        async_client
    ):
        """Test subscription cancellation."""
        mock_mp_service.get_subscription.return_value = {
            "id": "sub_123",
            "status": "cancelled",
            "payer_email": "test@example.com"
        }
        mock_license_service.get_license_by_email.return_value = {
            "id": "lic_123"
        }

        payload = {
            "type": "subscription_preapproval",
            "action": "updated",
            "data": {"id": "sub_123"}
        }

        with patch(
            "api.routes.webhooks.verify_mercadopago_signature",
            return_value=True
        ):
            response = await async_client.post(
                "/webhooks/mercadopago",
                json=payload,
                headers={
                    "X-Signature": "valid",
                    "X-Request-Id": "test"
                }
            )

        assert response.status_code == 200


class TestWebhookValidation:
    """Tests for webhook validation."""

    @pytest.mark.asyncio
    async def test_webhook_missing_signature_header(
        self,
        mock_mp_service,
        mock_license_service,
        async_client
    ):
        """Test webhook without signature header."""
        payload = {
            "type": "payment",
            "action": "payment.created",
            "data": {"id": "123"}
        }

        response = await async_client.post(
            "/webhooks/mercadopago",
            json=payload
        )

        # Should fail without signature
        assert response.status_code in [400, 401]

    @pytest.mark.asyncio
    async def test_webhook_empty_payload(
        self,
        mock_mp_service,
        mock_license_service,
        async_client
    ):
        """Test webhook with empty payload."""
        with patch(
            "api.routes.webhooks.verify_mercadopago_signature",
            return_value=True
        ):
            response = await async_client.post(
                "/webhooks/mercadopago",
                json={},
                headers={
                    "X-Signature": "valid",
                    "X-Request-Id": "test"
                }
            )

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_webhook_unknown_event_type(
        self,
        mock_mp_service,
        mock_license_service,
        async_client
    ):
        """Test webhook with unknown event type."""
        payload = {
            "type": "unknown_type",
            "action": "unknown.action",
            "data": {"id": "123"}
        }

        with patch(
            "api.routes.webhooks.verify_mercadopago_signature",
            return_value=True
        ):
            response = await async_client.post(
                "/webhooks/mercadopago",
                json=payload,
                headers={
                    "X-Signature": "valid",
                    "X-Request-Id": "test"
                }
            )

        # Should acknowledge but not process
        assert response.status_code == 200
