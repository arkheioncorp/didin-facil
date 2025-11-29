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


class TestMercadoPagoService:
    """Test suite for MercadoPagoService"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database"""
        db_mock = AsyncMock()
        db_mock.execute = AsyncMock()
        db_mock.fetch_all = AsyncMock(return_value=[])
        return db_mock

    @pytest.fixture
    def mp_service(self, mock_db):
        """Create a MercadoPago service instance"""
        with patch('api.services.mercadopago.database', mock_db):
            from api.services.mercadopago import MercadoPagoService
            service = MercadoPagoService()
            service.db = mock_db
            return service

    @pytest.fixture
    def mock_http_response(self):
        """Create a mock HTTP response"""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_response.status_code = 200
        return mock_response

    # ==================== GET PAYMENT Tests ====================

    @pytest.mark.asyncio
    async def test_get_payment_success(self, mp_service, mock_http_response):
        """Test getting payment details successfully"""
        expected_payment = {
            'id': '123456',
            'status': 'approved',
            'transaction_amount': 99.90
        }
        mock_http_response.json.return_value = expected_payment
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_http_response)
        
        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.get_payment('123456')
            
            assert result == expected_payment
            mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_payment_with_correct_url(
        self, mp_service, mock_http_response
    ):
        """Test get_payment calls correct URL"""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_http_response)
        
        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_class.return_value.__aexit__ = AsyncMock()
            
            await mp_service.get_payment('123456')
            
            call_args = mock_client.get.call_args
            assert '/v1/payments/123456' in call_args[0][0]

    # ==================== GET SUBSCRIPTION Tests ====================

    @pytest.mark.asyncio
    async def test_get_subscription_success(
        self, mp_service, mock_http_response
    ):
        """Test getting subscription details successfully"""
        expected_sub = {
            'id': 'sub_123',
            'status': 'authorized',
            'payer_email': 'test@example.com'
        }
        mock_http_response.json.return_value = expected_sub
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_http_response)
        
        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.get_subscription('sub_123')
            
            assert result == expected_sub

    # ==================== GET AUTHORIZED PAYMENT Tests ====================

    @pytest.mark.asyncio
    async def test_get_authorized_payment_success(
        self, mp_service, mock_http_response
    ):
        """Test getting authorized payment details"""
        expected_payment = {'id': 'auth_123', 'status': 'approved'}
        mock_http_response.json.return_value = expected_payment
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_http_response)
        
        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.get_authorized_payment('auth_123')
            
            assert result == expected_payment

    # ==================== CREATE PAYMENT Tests ====================

    @pytest.mark.asyncio
    async def test_create_payment_success(
        self, mp_service, mock_http_response
    ):
        """Test creating payment preference successfully"""
        expected_response = {
            'id': 'pref_123',
            'init_point': 'https://mercadopago.com/checkout/123'
        }
        mock_http_response.json.return_value = expected_response
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_http_response)
        
        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.create_payment(
                title='Plano Pro',
                price=79.90,
                user_email='test@example.com',
                external_reference='user123:pro'
            )
            
            assert result == expected_response
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_payment_payload_structure(
        self, mp_service, mock_http_response
    ):
        """Test create_payment sends correct payload structure"""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_http_response)
        
        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_class.return_value.__aexit__ = AsyncMock()
            
            await mp_service.create_payment(
                title='Test Plan',
                price=99.90,
                user_email='buyer@test.com',
                external_reference='ref123'
            )
            
            call_args = mock_client.post.call_args
            payload = call_args.kwargs['json']
            
            assert 'items' in payload
            assert payload['items'][0]['title'] == 'Test Plan'
            assert payload['items'][0]['unit_price'] == 99.90
            assert payload['payer']['email'] == 'buyer@test.com'
            assert payload['external_reference'] == 'ref123'

    # ==================== CREATE SUBSCRIPTION Tests ====================
    # Note: create_subscription is deprecated - raises NotImplementedError
    # The system now uses lifetime license + credits model

    @pytest.mark.asyncio
    async def test_create_subscription_raises_not_implemented(
        self, mp_service, mock_http_response
    ):
        """Test create_subscription raises NotImplementedError (deprecated)"""
        with pytest.raises(NotImplementedError) as exc_info:
            await mp_service.create_subscription(
                plan='starter',
                user_email='test@example.com',
                user_id='user123'
            )
        
        assert "Subscriptions are deprecated" in str(exc_info.value)

    # ==================== CREATE LICENSE PAYMENT Tests ====================

    @pytest.mark.asyncio
    async def test_create_license_payment_success(
        self, mp_service, mock_http_response
    ):
        """Test creating lifetime license payment"""
        expected_response = {'id': 'pref_123', 'init_point': 'https://...'}
        mock_http_response.json.return_value = expected_response
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_http_response)
        
        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.create_license_payment(
                user_email='test@example.com',
                user_id='user123'
            )
            
            assert result == expected_response
            call_args = mock_client.post.call_args
            payload = call_args.kwargs['json']
            assert payload['items'][0]['unit_price'] == 49.90
            assert 'Licença Vitalícia' in payload['items'][0]['title']
            assert payload['metadata']['product_type'] == 'license'

    @pytest.mark.asyncio
    async def test_create_license_payment_uses_correct_url(
        self, mp_service, mock_http_response
    ):
        """Test create_license_payment calls correct URL"""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_http_response)
        
        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_class.return_value.__aexit__ = AsyncMock()
            
            await mp_service.create_license_payment(
                user_email='test@example.com',
                user_id='user123'
            )
            
            call_args = mock_client.post.call_args
            assert '/checkout/preferences' in call_args[0][0]

    @pytest.mark.asyncio
    async def test_create_license_payment_external_reference(
        self, mp_service, mock_http_response
    ):
        """Test create_license_payment sets correct external_reference"""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_http_response)
        
        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_class.return_value.__aexit__ = AsyncMock()
            
            await mp_service.create_license_payment(
                user_email='test@example.com',
                user_id='user456'
            )
            
            call_args = mock_client.post.call_args
            payload = call_args.kwargs['json']
            assert payload['external_reference'] == 'user456:lifetime'

    # ==================== CANCEL SUBSCRIPTION Tests ====================

    @pytest.mark.asyncio
    async def test_cancel_subscription_success(
        self, mp_service, mock_http_response
    ):
        """Test cancelling subscription successfully"""
        mock_http_response.status_code = 200
        mock_client = AsyncMock()
        mock_client.put = AsyncMock(return_value=mock_http_response)
        
        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.cancel_subscription('sub_123')
            
            assert result is True
            call_args = mock_client.put.call_args
            assert call_args.kwargs['json'] == {'status': 'cancelled'}

    @pytest.mark.asyncio
    async def test_cancel_subscription_failure(
        self, mp_service, mock_http_response
    ):
        """Test cancelling subscription fails"""
        mock_http_response.status_code = 400
        mock_client = AsyncMock()
        mock_client.put = AsyncMock(return_value=mock_http_response)
        
        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.cancel_subscription('invalid_sub')
            
            assert result is False

    # ==================== LOG EVENT Tests ====================

    @pytest.mark.asyncio
    async def test_log_event_success(self, mp_service, mock_db):
        """Test logging payment event"""
        await mp_service.log_event('payment.approved', {'amount': 99.90})
        
        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args
        assert 'payment_events' in call_args[0][0]

    @pytest.mark.asyncio
    async def test_log_event_stores_event_type(self, mp_service, mock_db):
        """Test log_event stores correct event type"""
        await mp_service.log_event('subscription.created', {'plan': 'pro'})
        
        call_args = mock_db.execute.call_args
        params = call_args[0][1]
        assert params['event_type'] == 'subscription.created'

    # ==================== SEND LICENSE EMAIL Tests ====================

    @pytest.mark.asyncio
    async def test_send_license_email(self, mp_service, capsys):
        """Test send_license_email prints expected message"""
        await mp_service.send_license_email(
            email='user@test.com',
            license_key='LIC-KEY-123',
            plan='pro'
        )
        
        captured = capsys.readouterr()
        assert 'user@test.com' in captured.out
        assert 'LIC-KEY-123' in captured.out

    # ==================== GET PAYMENT HISTORY Tests ====================

    @pytest.mark.asyncio
    async def test_get_payment_history_with_results(self, mp_service, mock_db):
        """Test getting payment history with results"""
        payments = [
            {'id': '1', 'amount': 29.90, 'plan': 'starter'},
            {'id': '2', 'amount': 79.90, 'plan': 'pro'}
        ]
        mock_db.fetch_all = AsyncMock(return_value=payments)
        
        result = await mp_service.get_payment_history('user123')
        
        assert len(result) == 2
        assert result[0]['amount'] == 29.90

    @pytest.mark.asyncio
    async def test_get_payment_history_empty(self, mp_service, mock_db):
        """Test getting payment history with no results"""
        mock_db.fetch_all = AsyncMock(return_value=[])
        
        result = await mp_service.get_payment_history('new_user')
        
        assert result == []


class TestMercadoPagoServiceEdgeCases:
    """Edge case tests for MercadoPagoService"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def mp_service(self, mock_db):
        with patch('api.services.mercadopago.database', mock_db):
            from api.services.mercadopago import MercadoPagoService
            service = MercadoPagoService()
            service.db = mock_db
            return service

    @pytest.mark.asyncio
    async def test_get_payment_raises_on_http_error(self, mp_service):
        """Test get_payment raises on HTTP error"""
        # Configure mock client that raises on get
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
            'Not Found',
            request=MagicMock(),
            response=MagicMock()
        ))
        
        # Use AsyncMock for the context manager
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_client
        mock_async_client.__aexit__.return_value = None
        
        with patch(
            'api.services.mercadopago.httpx.AsyncClient',
            return_value=mock_async_client
        ):
            with pytest.raises(httpx.HTTPStatusError):
                await mp_service.get_payment('invalid_id')

    @pytest.mark.asyncio
    async def test_create_payment_with_special_chars_in_email(
        self, mp_service
    ):
        """Test create_payment handles special characters in email"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 'test'}
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_class.return_value.__aexit__ = AsyncMock()
            
            await mp_service.create_payment(
                title='Test',
                price=10.0,
                user_email='test+tag@example.com',
                external_reference='ref'
            )
            
            call_args = mock_client.post.call_args
            payload = call_args.kwargs['json']
            assert payload['payer']['email'] == 'test+tag@example.com'
