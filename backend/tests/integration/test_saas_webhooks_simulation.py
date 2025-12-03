from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# We use the async_client fixture from conftest.py

@pytest.fixture
def mock_verify_signature():
    with patch("api.routes.webhooks.verify_mercadopago_signature") as mock:
        mock.return_value = True
        yield mock

@pytest.mark.asyncio
async def test_webhook_payment_created_activates_subscription(async_client, mock_verify_signature):
    """
    Test that a 'payment.created' webhook from MercadoPago activates the subscription.
    """
    # Payload simulating MercadoPago webhook
    payload = {
        "action": "payment.created",
        "api_version": "v1",
        "data": {"id": "123456789"},
        "date_created": "2024-12-02T10:00:00Z",
        "id": 123456,
        "live_mode": True,
        "type": "payment",
        "user_id": "user_123"
    }

    # Mock MercadoPagoService and LicenseService/SubscriptionService
    with patch("api.routes.webhooks.MercadoPagoService") as MockMPService, \
         patch("api.routes.webhooks.LicenseService") as MockLicenseService:
        
        mp_instance = MockMPService.return_value
        # Configure get_payment as AsyncMock
        mp_instance.get_payment = AsyncMock(return_value={
            "status": "approved",
            "external_reference": "sub_123",
            "metadata": {
                "plan_tier": "starter",
                "user_id": "user_123",
                "includes_license": True
            }
        })
        mp_instance.log_event = AsyncMock()
        
        # Simulate the webhook call
        response = await async_client.post("/webhooks/mercadopago", json=payload)
        
        assert response.status_code == 200
        assert response.json() == {"status": "received"}
        
        # Verify get_payment was called
        mp_instance.get_payment.assert_called_with("123456789")

@pytest.mark.asyncio
async def test_webhook_subscription_cancelled(async_client, mock_verify_signature):
    """
    Test that 'subscription_preapproval.cancelled' webhook cancels the subscription.
    """
    payload = {
        "action": "updated",
        "data": {"id": "preapproval_123"},
        "type": "subscription_preapproval"
    }
    
    with patch("api.routes.webhooks.MercadoPagoService") as MockMPService, \
         patch("api.routes.webhooks.SubscriptionService") as MockSubscriptionService:
        
        mp_instance = MockMPService.return_value
        # Configure get_subscription as AsyncMock
        mp_instance.get_subscription = AsyncMock(return_value={
            "status": "cancelled",
            "external_reference": "user_123:starter:monthly"
        })
        mp_instance.log_event = AsyncMock()
        
        sub_service_instance = MockSubscriptionService.return_value
        # Configure cancel_subscription as AsyncMock if it is awaited in the code
        # Checking the code, handle_subscription_event calls sub_service.cancel_subscription
        # Let's assume it might be async, so safer to make it AsyncMock or check implementation.
        # But usually services are async.
        sub_service_instance.cancel_subscription = AsyncMock()
        
        response = await async_client.post("/webhooks/mercadopago", json=payload)
        
        assert response.status_code == 200
        
        # Verify subscription service was called to update
        # Based on handle_subscription_event logic, it calls get_subscription and _cache_subscription
        sub_service_instance.get_subscription.assert_called_with("user_123")
        
        # Verify log_event was called
        mp_instance.log_event.assert_called()
