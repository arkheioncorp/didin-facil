import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_mercadopago_webhook_payment_approved_new_license():
    # Mock payload
    payload = {
        "type": "payment",
        "action": "payment.approved",
        "data": {"id": "123456789"},
        "date_created": "2023-01-01T00:00:00Z",
        "id": 123456789,
        "live_mode": False,
        "user_id": "test_user",
        "api_version": "v1"
    }
    
    # Mock signature verification
    with patch("backend.api.routes.webhooks.verify_mercadopago_signature", return_value=True):
        # Mock Services
        with patch("backend.api.routes.webhooks.MercadoPagoService") as MockMPService, \
             patch("backend.api.routes.webhooks.LicenseService") as MockLicenseService:
            
            mp_instance = MockMPService.return_value
            license_instance = MockLicenseService.return_value
            
            # Setup MP Service mock
            mp_instance.get_payment = AsyncMock(return_value={
                "status": "approved",
                "metadata": {"plan": "pro"},
                "payer": {"email": "new_user@example.com"}
            })
            mp_instance.log_event = AsyncMock()
            mp_instance.send_license_email = AsyncMock()
            
            # Setup License Service mock
            license_instance.get_license_by_email = AsyncMock(return_value=None) # No existing license
            license_instance.create_license = AsyncMock(return_value="LICENSE-KEY-123")
            
            # Send request
            response = client.post(
                "/webhooks/mercadopago",
                json=payload,
                headers={"x-signature": "test", "x-request-id": "test"}
            )
            
            assert response.status_code == 200
            assert response.json() == {"status": "received"}
            
            # Verify interactions
            mp_instance.get_payment.assert_called_once_with("123456789")
            license_instance.get_license_by_email.assert_called_once_with("new_user@example.com")
            license_instance.create_license.assert_called_once_with(
                email="new_user@example.com",
                plan="pro",
                duration_days=30,
                payment_id="123456789"
            )
            mp_instance.send_license_email.assert_called_once_with(
                "new_user@example.com", "LICENSE-KEY-123", "pro"
            )

@pytest.mark.asyncio
async def test_mercadopago_webhook_payment_approved_extend_license():
    # Mock payload
    payload = {
        "type": "payment",
        "action": "payment.approved",
        "data": {"id": "987654321"},
        "date_created": "2023-01-01T00:00:00Z",
        "id": 987654321,
        "live_mode": False,
        "user_id": "test_user",
        "api_version": "v1"
    }
    
    # Mock signature verification
    with patch("backend.api.routes.webhooks.verify_mercadopago_signature", return_value=True):
        # Mock Services
        with patch("backend.api.routes.webhooks.MercadoPagoService") as MockMPService, \
             patch("backend.api.routes.webhooks.LicenseService") as MockLicenseService:
            
            mp_instance = MockMPService.return_value
            license_instance = MockLicenseService.return_value
            
            # Setup MP Service mock
            mp_instance.get_payment = AsyncMock(return_value={
                "status": "approved",
                "metadata": {"plan": "starter"},
                "payer": {"email": "existing_user@example.com"}
            })
            mp_instance.log_event = AsyncMock()
            
            # Setup License Service mock
            license_instance.get_license_by_email = AsyncMock(return_value={"id": "license-uuid-123"}) # Existing license
            license_instance.extend_license = AsyncMock()
            
            # Send request
            response = client.post(
                "/webhooks/mercadopago",
                json=payload,
                headers={"x-signature": "test", "x-request-id": "test"}
            )
            
            assert response.status_code == 200
            assert response.json() == {"status": "received"}
            
            # Verify interactions
            mp_instance.get_payment.assert_called_once_with("987654321")
            license_instance.get_license_by_email.assert_called_once_with("existing_user@example.com")
            license_instance.extend_license.assert_called_once_with(
                license_id="license-uuid-123",
                days=30,
                payment_id="987654321"
            )
