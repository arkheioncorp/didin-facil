"""
Mercado Pago Service Tests V2
Tests for the refactored payment processing service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

class TestMercadoPagoServiceV2:
    """Test suite for MercadoPagoService V2"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database"""
        db_mock = AsyncMock()
        db_mock.execute = AsyncMock()
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

    @pytest.mark.asyncio
    async def test_create_payment_success(self, mp_service, mock_http_response):
        """Test creating a generic payment preference"""
        expected_response = {'id': 'pref_123', 'init_point': 'https://mp.com/checkout'}
        mock_http_response.json.return_value = expected_response
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_http_response)
        
        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.create_payment(
                title="Test Product",
                price=100.00,
                user_email="test@example.com",
                external_reference="ref_123"
            )
            
            assert result == expected_response
            mock_client.post.assert_called_once()
            
            # Verify payload
            call_args = mock_client.post.call_args
            payload = call_args[1]['json']
            assert payload['items'][0]['title'] == "Test Product"
            assert payload['items'][0]['unit_price'] == 100.00
            assert payload['payer']['email'] == "test@example.com"
            assert payload['external_reference'] == "ref_123"

    @pytest.mark.asyncio
    async def test_create_pix_payment_success(self, mp_service, mock_http_response):
        """Test creating a PIX payment"""
        expected_response = {
            'id': 123456,
            'status': 'pending',
            'point_of_interaction': {
                'transaction_data': {
                    'qr_code': 'pix_code_123',
                    'qr_code_base64': 'base64_code',
                    'ticket_url': 'https://ticket.url'
                }
            },
            'date_of_expiration': '2024-12-31T23:59:59Z'
        }
        mock_http_response.json.return_value = expected_response
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_http_response)
        
        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_class.return_value.__aexit__ = AsyncMock()
            
            result = await mp_service.create_pix_payment(
                amount=50.00,
                email="test@example.com",
                cpf="12345678900",
                name="Test User",
                external_reference="ref_pix_123",
                description="Test PIX"
            )
            
            assert result['payment_id'] == 123456
            assert result['qr_code'] == 'pix_code_123'
            
            # Verify payload
            call_args = mock_client.post.call_args
            payload = call_args[1]['json']
            assert payload['transaction_amount'] == 50.00
            assert payload['payment_method_id'] == 'pix'
            assert payload['payer']['email'] == "test@example.com"
            assert payload['description'] == "Test PIX"
