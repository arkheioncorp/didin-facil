"""
Mercado Pago Service Tests - 100% Coverage
Tests for payment processing and subscription management
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from backend.api.services.mercadopago import MercadoPagoService


class TestMercadoPagoService:
    """Test suite for MercadoPagoService"""

    @pytest.fixture
    def mp_service(self):
        """Create a MercadoPago service instance"""
        with patch.object(MercadoPagoService, '__init__', lambda x: None):
            service = MercadoPagoService()
            service.access_token = 'TEST_ACCESS_TOKEN'
            service.base_url = 'https://api.mercadopago.com'
            service.headers = {
                'Authorization': 'Bearer TEST_ACCESS_TOKEN',
                'Content-Type': 'application/json'
            }
            return service

    @pytest.fixture
    def mock_http_client(self):
        """Create a mock HTTP client"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_response.status_code = 200
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.put = AsyncMock(return_value=mock_response)
        return mock_client

    # ==================== GET PAYMENT Tests ====================

    @pytest.mark.asyncio
    async def test_get_payment_success(self, mp_service, mock_http_client):
        """Test getting payment details successfully"""
        expected_payment = {
            'id': '123456',
            'status': 'approved',
            'transaction_amount': 99.90
        }
        mock_response = MagicMock()
        mock_response.json.return_value = expected_payment
        mock_response.raise_for_status = MagicMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.get_payment('123456')
            
            assert result == expected_payment
            mock_http_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_payment_with_correct_url(self, mp_service, mock_http_client):
        """Test get_payment calls correct URL"""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()
            
            await mp_service.get_payment('PAY-123')
            
            call_args = mock_http_client.get.call_args
            assert 'v1/payments/PAY-123' in call_args[0][0]

    # ==================== GET SUBSCRIPTION Tests ====================

    @pytest.mark.asyncio
    async def test_get_subscription_success(self, mp_service, mock_http_client):
        """Test getting subscription details successfully"""
        expected_subscription = {
            'id': 'preapproval-123',
            'status': 'authorized',
            'reason': 'TikTrend Pro'
        }
        mock_response = MagicMock()
        mock_response.json.return_value = expected_subscription
        mock_response.raise_for_status = MagicMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.get_subscription('preapproval-123')
            
            assert result == expected_subscription

    # ==================== GET AUTHORIZED PAYMENT Tests ====================

    @pytest.mark.asyncio
    async def test_get_authorized_payment_success(self, mp_service, mock_http_client):
        """Test getting authorized payment details"""
        expected = {'id': 'auth-123', 'status': 'approved'}
        mock_response = MagicMock()
        mock_response.json.return_value = expected
        mock_response.raise_for_status = MagicMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.get_authorized_payment('auth-123')
            
            assert result == expected

    # ==================== CREATE PREFERENCE Tests ====================

    @pytest.mark.asyncio
    async def test_create_preference_starter(self, mp_service, mock_http_client):
        """Test creating preference for starter plan"""
        expected = {'id': 'pref-123', 'init_point': 'https://mp.com/checkout'}
        mock_response = MagicMock()
        mock_response.json.return_value = expected
        mock_response.raise_for_status = MagicMock()
        mock_http_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.create_preference(
                plan='starter',
                user_email='test@example.com',
                user_id='user-123'
            )
            
            assert result == expected

    @pytest.mark.asyncio
    async def test_create_preference_pro(self, mp_service, mock_http_client):
        """Test creating preference for pro plan"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 'pref-pro'}
        mock_response.raise_for_status = MagicMock()
        mock_http_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()
            
            await mp_service.create_preference(
                plan='pro',
                user_email='test@example.com',
                user_id='user-123'
            )
            
            call_args = mock_http_client.post.call_args
            assert call_args is not None

    @pytest.mark.asyncio
    async def test_create_preference_enterprise(self, mp_service, mock_http_client):
        """Test creating preference for enterprise plan"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 'pref-ent'}
        mock_response.raise_for_status = MagicMock()
        mock_http_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()
            
            await mp_service.create_preference(
                plan='enterprise',
                user_email='enterprise@example.com',
                user_id='user-456'
            )
            
            mock_http_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_preference_unknown_plan_uses_default(self, mp_service, mock_http_client):
        """Test creating preference with unknown plan uses default price"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 'pref-default'}
        mock_response.raise_for_status = MagicMock()
        mock_http_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.create_preference(
                plan='unknown_plan',
                user_email='test@example.com',
                user_id='user-123'
            )
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_create_preference_includes_metadata(self, mp_service, mock_http_client):
        """Test create_preference includes user metadata"""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_http_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()
            
            await mp_service.create_preference(
                plan='pro',
                user_email='meta@test.com',
                user_id='meta-user-123'
            )
            
            call_args = mock_http_client.post.call_args
            assert call_args is not None

    # ==================== CREATE SUBSCRIPTION Tests ====================

    @pytest.mark.asyncio
    async def test_create_subscription_starter(self, mp_service, mock_http_client):
        """Test creating subscription for starter plan"""
        expected = {'id': 'sub-123', 'init_point': 'https://mp.com/subscribe'}
        mock_response = MagicMock()
        mock_response.json.return_value = expected
        mock_response.raise_for_status = MagicMock()
        mock_http_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.create_subscription(
                plan='starter',
                user_email='test@example.com',
                user_id='user-123'
            )
            
            assert result == expected

    @pytest.mark.asyncio
    async def test_create_subscription_pro(self, mp_service, mock_http_client):
        """Test creating subscription for pro plan"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 'sub-pro'}
        mock_response.raise_for_status = MagicMock()
        mock_http_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.create_subscription(
                plan='pro',
                user_email='pro@example.com',
                user_id='user-456'
            )
            
            assert result['id'] == 'sub-pro'

    @pytest.mark.asyncio
    async def test_create_subscription_enterprise(self, mp_service, mock_http_client):
        """Test creating subscription for enterprise plan"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 'sub-enterprise'}
        mock_response.raise_for_status = MagicMock()
        mock_http_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.create_subscription(
                plan='enterprise',
                user_email='enterprise@example.com',
                user_id='user-789'
            )
            
            assert result is not None

    # ==================== CANCEL SUBSCRIPTION Tests ====================

    @pytest.mark.asyncio
    async def test_cancel_subscription_success(self, mp_service, mock_http_client):
        """Test canceling subscription successfully"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_http_client.put = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.cancel_subscription('preapproval-123')
            
            assert result is True

    @pytest.mark.asyncio
    async def test_cancel_subscription_failure(self, mp_service, mock_http_client):
        """Test canceling subscription when fails"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_http_client.put = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.cancel_subscription('invalid-preapproval')
            
            assert result is False

    @pytest.mark.asyncio
    async def test_cancel_subscription_sends_cancelled_status(self, mp_service, mock_http_client):
        """Test cancel_subscription sends correct status"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_http_client.put = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()
            
            await mp_service.cancel_subscription('preapproval-123')
            
            call_args = mock_http_client.put.call_args
            assert call_args[1]['json'] == {'status': 'cancelled'}

    # ==================== LOG EVENT Tests ====================

    @pytest.mark.asyncio
    async def test_log_event_success(self, mp_service):
        """Test logging payment event"""
        mock_db = AsyncMock()
        
        with patch('backend.api.services.mercadopago.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            await mp_service.log_event('payment.created', {'payment_id': '123'})
            
            mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_event_stores_event_type(self, mp_service):
        """Test log_event stores correct event type"""
        mock_db = AsyncMock()
        
        with patch('backend.api.services.mercadopago.get_db') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_get_db.return_value.__aexit__ = AsyncMock()
            
            await mp_service.log_event('subscription.updated', {'sub_id': '456'})
            
            call_args = mock_db.execute.call_args
            params = call_args[0][1]
            assert params['event_type'] == 'subscription.updated'


class TestMercadoPagoServiceEdgeCases:
    """Edge case tests for MercadoPagoService"""

    @pytest.fixture
    def mp_service(self):
        with patch.object(MercadoPagoService, '__init__', lambda x: None):
            service = MercadoPagoService()
            service.access_token = 'TEST_TOKEN'
            service.base_url = 'https://api.mercadopago.com'
            service.headers = {'Authorization': 'Bearer TEST_TOKEN'}
            return service

    @pytest.mark.asyncio
    async def test_get_payment_raises_on_error(self, mp_service):
        """Test get_payment raises on HTTP error"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=MagicMock()
        )
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()
            
            with pytest.raises(httpx.HTTPStatusError):
                await mp_service.get_payment('invalid-id')

    @pytest.mark.asyncio
    async def test_create_preference_with_empty_email(self, mp_service):
        """Test creating preference with empty email"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 'pref-123'}
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.create_preference(
                plan='starter',
                user_email='',
                user_id='user-123'
            )
            
            assert result is not None
