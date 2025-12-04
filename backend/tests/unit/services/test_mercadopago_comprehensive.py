"""
Comprehensive tests for MercadoPago Service
Tests for payment processing, subscriptions, and PIX
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


class TestMercadoPagoServiceInit:
    """Tests for MercadoPagoService initialization"""

    def test_init_with_sandbox(self):
        """Test initialization with sandbox mode"""
        with patch("api.services.mercadopago.settings") as mock_settings:
            mock_settings.MERCADOPAGO_USE_SANDBOX = True
            mock_settings.MERCADOPAGO_SANDBOX_TOKEN = "sandbox_token_123"
            mock_settings.MERCADO_PAGO_ACCESS_TOKEN = "prod_token"
            mock_settings.MERCADOPAGO_ACCESS_TOKEN = None

            from api.services.mercadopago import MercadoPagoService

            service = MercadoPagoService(use_sandbox=True)

            assert service.is_sandbox is True
            assert service.access_token == "sandbox_token_123"

    def test_init_with_production(self):
        """Test initialization with production mode"""
        with patch("api.services.mercadopago.settings") as mock_settings:
            mock_settings.MERCADOPAGO_USE_SANDBOX = False
            mock_settings.MERCADOPAGO_SANDBOX_TOKEN = None
            mock_settings.MERCADO_PAGO_ACCESS_TOKEN = "prod_token_456"
            mock_settings.MERCADOPAGO_ACCESS_TOKEN = None

            from api.services.mercadopago import MercadoPagoService

            service = MercadoPagoService(use_sandbox=False)

            assert service.is_sandbox is False
            assert service.access_token == "prod_token_456"

    def test_init_uses_env_config_when_no_param(self):
        """Test that env config is used when no param provided"""
        with patch("api.services.mercadopago.settings") as mock_settings:
            mock_settings.MERCADOPAGO_USE_SANDBOX = True
            mock_settings.MERCADOPAGO_SANDBOX_TOKEN = "sandbox_env_token"
            mock_settings.MERCADO_PAGO_ACCESS_TOKEN = None
            mock_settings.MERCADOPAGO_ACCESS_TOKEN = None

            from api.services.mercadopago import MercadoPagoService

            service = MercadoPagoService()

            assert service.is_sandbox is True

    def test_init_sets_base_url(self):
        """Test that base URL is set correctly"""
        with patch("api.services.mercadopago.settings") as mock_settings:
            mock_settings.MERCADOPAGO_USE_SANDBOX = False
            mock_settings.MERCADOPAGO_SANDBOX_TOKEN = None
            mock_settings.MERCADO_PAGO_ACCESS_TOKEN = "token"
            mock_settings.MERCADOPAGO_ACCESS_TOKEN = None

            from api.services.mercadopago import MercadoPagoService

            service = MercadoPagoService()

            assert service.base_url == "https://api.mercadopago.com"


class TestMercadoPagoServicePayments:
    """Tests for payment operations"""

    @pytest.fixture
    def mp_service(self):
        with patch("api.services.mercadopago.settings") as mock_settings:
            mock_settings.MERCADOPAGO_USE_SANDBOX = False
            mock_settings.MERCADOPAGO_SANDBOX_TOKEN = None
            mock_settings.MERCADO_PAGO_ACCESS_TOKEN = "test_token"
            mock_settings.MERCADOPAGO_ACCESS_TOKEN = None
            mock_settings.FRONTEND_URL = "https://app.didinfacil.com"
            mock_settings.API_URL = "https://api.didinfacil.com"

            from api.services.mercadopago import MercadoPagoService

            yield MercadoPagoService()

    @pytest.mark.asyncio
    async def test_get_payment_success(self, mp_service):
        """Test getting payment details"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "12345",
            "status": "approved",
            "transaction_amount": 99.90,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await mp_service.get_payment("12345")

            assert result["id"] == "12345"
            assert result["status"] == "approved"

    @pytest.mark.asyncio
    async def test_get_payment_not_found(self, mp_service):
        """Test getting non-existent payment"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not Found", request=MagicMock(), response=MagicMock()
            )
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(httpx.HTTPStatusError):
                await mp_service.get_payment("nonexistent")

    @pytest.mark.asyncio
    async def test_create_payment_success(self, mp_service):
        """Test creating a payment preference"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "pref_123",
            "init_point": "https://www.mercadopago.com/checkout/v1/redirect",
            "sandbox_init_point": "https://sandbox.mercadopago.com/checkout",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await mp_service.create_payment(
                title="100 Créditos",
                price=49.90,
                user_email="user@example.com",
                external_reference="order_123",
            )

            assert result["id"] == "pref_123"
            assert "init_point" in result


class TestMercadoPagoServicePix:
    """Tests for PIX payment operations"""

    @pytest.fixture
    def mp_service(self):
        with patch("api.services.mercadopago.settings") as mock_settings:
            mock_settings.MERCADOPAGO_USE_SANDBOX = False
            mock_settings.MERCADOPAGO_SANDBOX_TOKEN = None
            mock_settings.MERCADO_PAGO_ACCESS_TOKEN = "test_token"
            mock_settings.MERCADOPAGO_ACCESS_TOKEN = None
            mock_settings.FRONTEND_URL = "https://app.didinfacil.com"
            mock_settings.API_URL = "https://api.didinfacil.com"

            from api.services.mercadopago import MercadoPagoService

            yield MercadoPagoService()

    @pytest.mark.asyncio
    async def test_create_pix_payment_success(self, mp_service):
        """Test creating a PIX payment"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 123456789,
            "status": "pending",
            "point_of_interaction": {
                "transaction_data": {
                    "qr_code": "00020126580014br.gov.bcb.pix...",
                    "qr_code_base64": "base64_image_data",
                    "ticket_url": "https://pix.mercadopago.com/ticket",
                }
            },
            "date_of_expiration": "2025-12-04T23:59:59.000-03:00",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await mp_service.create_pix_payment(
                amount=99.90,
                email="user@example.com",
                cpf="12345678900",
                name="João Silva",
                external_reference="order_456",
            )

            assert result["payment_id"] == 123456789
            assert result["status"] == "pending"
            assert "qr_code" in result
            assert "qr_code_base64" in result

    @pytest.mark.asyncio
    async def test_create_pix_payment_with_single_name(self, mp_service):
        """Test PIX payment with single name"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 123456789,
            "status": "pending",
            "point_of_interaction": {"transaction_data": {}},
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await mp_service.create_pix_payment(
                amount=49.90,
                email="user@example.com",
                cpf="12345678900",
                name="João",  # Single name
                external_reference="order_789",
            )

            assert result["payment_id"] == 123456789


class TestMercadoPagoServiceSubscriptions:
    """Tests for subscription operations"""

    @pytest.fixture
    def mp_service(self):
        with patch("api.services.mercadopago.settings") as mock_settings:
            mock_settings.MERCADOPAGO_USE_SANDBOX = False
            mock_settings.MERCADOPAGO_SANDBOX_TOKEN = None
            mock_settings.MERCADO_PAGO_ACCESS_TOKEN = "test_token"
            mock_settings.MERCADOPAGO_ACCESS_TOKEN = None
            mock_settings.FRONTEND_URL = "https://app.didinfacil.com"
            mock_settings.API_URL = "https://api.didinfacil.com"

            from api.services.mercadopago import MercadoPagoService

            yield MercadoPagoService()

    @pytest.mark.asyncio
    async def test_create_subscription_preference(self, mp_service):
        """Test creating a subscription preference"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "preapproval_123",
            "init_point": "https://www.mercadopago.com/preapproval",
            "status": "pending",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await mp_service.create_subscription_preference(
                title="Plano Pro Mensal",
                price=29.90,
                user_email="user@example.com",
                external_reference="sub_123",
            )

            assert result["id"] == "preapproval_123"

    @pytest.mark.asyncio
    async def test_get_subscription(self, mp_service):
        """Test getting subscription details"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "preapproval_123",
            "status": "authorized",
            "payer_email": "user@example.com",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await mp_service.get_subscription("preapproval_123")

            assert result["id"] == "preapproval_123"
            assert result["status"] == "authorized"

    @pytest.mark.asyncio
    async def test_cancel_subscription(self, mp_service):
        """Test canceling a subscription"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "preapproval_123",
            "status": "cancelled",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.put = AsyncMock(
                return_value=mock_response
            )

            result = await mp_service.cancel_subscription("preapproval_123")

            assert result["status"] == "cancelled"


class TestMercadoPagoServiceErrorHandling:
    """Tests for error handling"""

    @pytest.fixture
    def mp_service(self):
        with patch("api.services.mercadopago.settings") as mock_settings:
            mock_settings.MERCADOPAGO_USE_SANDBOX = False
            mock_settings.MERCADOPAGO_SANDBOX_TOKEN = None
            mock_settings.MERCADO_PAGO_ACCESS_TOKEN = "test_token"
            mock_settings.MERCADOPAGO_ACCESS_TOKEN = None
            mock_settings.FRONTEND_URL = "https://app.didinfacil.com"
            mock_settings.API_URL = "https://api.didinfacil.com"

            from api.services.mercadopago import MercadoPagoService

            yield MercadoPagoService()

    @pytest.mark.asyncio
    async def test_api_rate_limit_error(self, mp_service):
        """Test handling of rate limit errors"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Rate Limited", request=MagicMock(), response=mock_response
            )
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(httpx.HTTPStatusError):
                await mp_service.get_payment("123")

    @pytest.mark.asyncio
    async def test_api_unauthorized_error(self, mp_service):
        """Test handling of unauthorized errors"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Unauthorized", request=MagicMock(), response=mock_response
            )
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(httpx.HTTPStatusError):
                await mp_service.create_payment(
                    title="Test",
                    price=10.0,
                    user_email="test@test.com",
                    external_reference="ref_123",
                )

    @pytest.mark.asyncio
    async def test_network_error(self, mp_service):
        """Test handling of network errors"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.ConnectError("Network error")
            )

            with pytest.raises(httpx.ConnectError):
                await mp_service.get_payment("123")
