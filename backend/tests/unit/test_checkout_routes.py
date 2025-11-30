"""
Tests for Checkout Routes
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from datetime import datetime


class TestCheckoutCreate:
    """Tests for checkout creation endpoint"""

    @pytest.fixture
    def valid_checkout_request(self):
        from api.routes.checkout import CheckoutRequest
        return CheckoutRequest(
            name="Test User",
            email="test@example.com",
            cpf="12345678901",
            phone="11999999999",
            payment_method="pix",
            product_id="tiktrend_lifetime",
            coupon=None
        )

    @pytest.mark.asyncio
    async def test_create_checkout_pix_success(self, valid_checkout_request):
        from api.routes.checkout import create_checkout

        mock_mp = AsyncMock()
        mock_mp.create_payment.return_value = {
            "id": "pref_123",
            "init_point": "https://payment.url"
        }
        mock_mp.create_pix_payment.return_value = {
            "qr_code": "qr_code_data",
            "qr_code_base64": "base64_data",
            "copy_paste": "pix_code",
            "date_of_expiration": "2024-12-31T23:59:59"
        }

        with patch("api.routes.checkout.MercadoPagoService", return_value=mock_mp):
            result = await create_checkout(valid_checkout_request)

            assert result.status == "pending"
            assert result.pix_qr_code == "qr_code_data"
            assert result.pix_copy_paste == "pix_code"
            assert result.order_id.startswith("TTF-")

    @pytest.mark.asyncio
    async def test_create_checkout_card_success(self):
        from api.routes.checkout import create_checkout, CheckoutRequest

        request = CheckoutRequest(
            name="Test User",
            email="test@example.com",
            cpf="12345678901",
            payment_method="card",
            product_id="tiktrend_lifetime"
        )

        mock_mp = AsyncMock()
        mock_mp.create_payment.return_value = {
            "id": "pref_123",
            "init_point": "https://payment.url"
        }

        with patch("api.routes.checkout.MercadoPagoService", return_value=mock_mp):
            result = await create_checkout(request)

            assert result.status == "pending"
            assert result.payment_url == "https://payment.url"
            assert result.pix_qr_code is None

    @pytest.mark.asyncio
    async def test_create_checkout_invalid_product(self):
        from api.routes.checkout import create_checkout, CheckoutRequest

        request = CheckoutRequest(
            name="Test User",
            email="test@example.com",
            cpf="12345678901",
            payment_method="pix",
            product_id="invalid_product"
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_checkout(request)

        assert exc_info.value.status_code == 400
        assert "Invalid product" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_checkout_with_valid_coupon(self):
        from api.routes.checkout import create_checkout, CheckoutRequest

        request = CheckoutRequest(
            name="Test User",
            email="test@example.com",
            cpf="12345678901",
            payment_method="card",
            product_id="tiktrend_lifetime",
            coupon="LAUNCH10"
        )

        mock_mp = AsyncMock()
        mock_mp.create_payment.return_value = {
            "id": "pref_123",
            "init_point": "https://payment.url"
        }

        # Patch COUPONS with a valid, non-expired coupon
        with patch("api.routes.checkout.MercadoPagoService", return_value=mock_mp), \
             patch("api.routes.checkout.COUPONS", {
                 "LAUNCH10": {"discount": 0.10, "expires": "2099-12-31"}
             }):
            result = await create_checkout(request)

            # Price should have 10% discount (49.90 * 0.9 = 44.91)
            assert result.total == 44.91
            assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_create_checkout_payment_error(self, valid_checkout_request):
        from api.routes.checkout import create_checkout

        mock_mp = AsyncMock()
        mock_mp.create_payment.side_effect = Exception("Payment gateway error")

        with patch("api.routes.checkout.MercadoPagoService", return_value=mock_mp):
            with pytest.raises(HTTPException) as exc_info:
                await create_checkout(valid_checkout_request)

            assert exc_info.value.status_code == 500
            assert "Payment processing error" in exc_info.value.detail


class TestCouponValidation:
    """Tests for coupon validation endpoint"""

    @pytest.mark.asyncio
    async def test_validate_coupon_success(self):
        from api.routes.checkout import validate_coupon, CouponValidateRequest

        request = CouponValidateRequest(
            code="LAUNCH10",
            product_id="tiktrend_lifetime"
        )

        # Patch to ensure coupon is valid and not expired
        with patch("api.routes.checkout.COUPONS", {
            "LAUNCH10": {"discount": 0.10, "expires": "2099-12-31"}
        }):
            result = await validate_coupon(request)

            assert result.valid is True
            assert result.discount == 0.10
            assert "10%" in result.message

    @pytest.mark.asyncio
    async def test_validate_coupon_invalid_code(self):
        from api.routes.checkout import validate_coupon, CouponValidateRequest

        request = CouponValidateRequest(
            code="INVALIDCODE",
            product_id="tiktrend_lifetime"
        )

        result = await validate_coupon(request)

        assert result.valid is False
        assert "inválido" in result.message.lower()

    @pytest.mark.asyncio
    async def test_validate_coupon_invalid_product(self):
        from api.routes.checkout import validate_coupon, CouponValidateRequest

        request = CouponValidateRequest(
            code="LAUNCH10",
            product_id="nonexistent_product"
        )

        result = await validate_coupon(request)

        assert result.valid is False
        assert "inválido" in result.message.lower()

    @pytest.mark.asyncio
    async def test_validate_coupon_expired(self):
        from api.routes.checkout import validate_coupon, CouponValidateRequest

        request = CouponValidateRequest(
            code="EXPIRED",
            product_id="tiktrend_lifetime"
        )

        with patch("api.routes.checkout.COUPONS", {
            "EXPIRED": {"discount": 0.20, "expires": "2020-01-01"}
        }):
            result = await validate_coupon(request)

            assert result.valid is False
            assert "expirado" in result.message.lower()


class TestPaymentStatus:
    """Tests for payment status endpoint"""

    @pytest.mark.asyncio
    async def test_get_status_pending(self):
        from api.routes.checkout import get_payment_status

        result = await get_payment_status("TTF-20240101-ABCD1234")

        assert result.status == "pending"
        assert result.order_id == "TTF-20240101-ABCD1234"
        assert result.payment_method == "pix"


class TestProductList:
    """Tests for product listing"""

    @pytest.mark.asyncio
    async def test_list_products(self):
        from api.routes.checkout import list_products

        result = await list_products()

        assert "products" in result
        assert len(result["products"]) > 0
        product_ids = [p["id"] for p in result["products"]]
        assert "tiktrend_lifetime" in product_ids


class TestPaymentRedirects:
    """Tests for payment redirect endpoints"""

    @pytest.mark.asyncio
    async def test_payment_success_approved(self):
        from api.routes.checkout import payment_success

        mock_license = AsyncMock()
        mock_license.generate_license_key.return_value = "LICENSE-KEY-123"

        with patch("api.routes.checkout.LicenseService", return_value=mock_license):
            result = await payment_success(
                collection_id="123",
                collection_status="approved",
                payment_id="456",
                status="approved",
                external_reference="TTF-123",
                payment_type="pix",
                merchant_order_id="789",
                preference_id="pref_123"
            )

            assert result["success"] is True
            assert result["license_key"] == "LICENSE-KEY-123"

    @pytest.mark.asyncio
    async def test_payment_success_not_approved(self):
        from api.routes.checkout import payment_success

        result = await payment_success(
            status="rejected",
            external_reference="TTF-123"
        )

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_payment_failure(self):
        from api.routes.checkout import payment_failure

        result = await payment_failure(
            collection_id="123",
            collection_status="rejected",
            external_reference="TTF-123"
        )

        assert result["success"] is False
        assert result["order_id"] == "TTF-123"

    @pytest.mark.asyncio
    async def test_payment_pending_pix(self):
        from api.routes.checkout import payment_pending

        result = await payment_pending(
            collection_id="123",
            collection_status="pending",
            external_reference="TTF-123",
            payment_type="pix"
        )

        assert result["status"] == "pending"
        assert result["success"] is True
        assert "pix" in result["redirect"]

    @pytest.mark.asyncio
    async def test_payment_pending_boleto(self):
        from api.routes.checkout import payment_pending

        result = await payment_pending(
            collection_id="123",
            collection_status="pending",
            external_reference="TTF-123",
            payment_type="ticket"
        )

        assert result["status"] == "pending"
        assert "boleto" in result["redirect"]

