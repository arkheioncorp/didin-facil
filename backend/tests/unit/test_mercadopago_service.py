"""
Mercado Pago Service Tests
Tests for payment processing with PIX payments
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch


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
        """Test get_payment calls correct MercadoPago URL"""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_http_response)

        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_class.return_value.__aexit__ = AsyncMock()

            await mp_service.get_payment('pay_123')

            call_args = mock_client.get.call_args
            url = call_args[0][0]
            assert '/v1/payments/pay_123' in url

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

    # ==================== CREATE PIX PAYMENT Tests ====================

    @pytest.mark.asyncio
    async def test_create_pix_payment_success(
        self, mp_service, mock_http_response
    ):
        """Test creating PIX payment successfully"""
        expected_response = {
            'id': 'pix_123',
            'status': 'pending',
            'point_of_interaction': {
                'transaction_data': {
                    'qr_code': 'pix_qr_code_data',
                    'qr_code_base64': 'base64_image'
                }
            }
        }
        mock_http_response.json.return_value = expected_response
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_http_response)

        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_class.return_value.__aexit__ = AsyncMock()

            result = await mp_service.create_pix_payment(
                amount=99.90,
                email='test@example.com',
                cpf='12345678901',
                name='John Doe',
                external_reference='user123:credits',
                description='100 créditos'
            )

            assert 'payment_id' in result or result.get('id')
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_pix_payment_payload_structure(
        self, mp_service, mock_http_response
    ):
        """Test create_pix_payment sends correct payload"""
        mock_http_response.json.return_value = {'id': 'pix_123', 'status': 'pending'}
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_http_response)

        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_class.return_value.__aexit__ = AsyncMock()

            await mp_service.create_pix_payment(
                amount=49.90,
                email='payer@test.com',
                cpf='98765432100',
                name='Jane Doe',
                external_reference='ref_pix_123',
                description='Pacote de créditos'
            )

            call_args = mock_client.post.call_args
            payload = call_args.kwargs['json']

            assert payload['transaction_amount'] == 49.90
            assert payload['payment_method_id'] == 'pix'
            assert payload['payer']['email'] == 'payer@test.com'
            assert payload['external_reference'] == 'ref_pix_123'
            assert payload['description'] == 'Pacote de créditos'

    @pytest.mark.asyncio
    async def test_create_pix_payment_url(
        self, mp_service, mock_http_response
    ):
        """Test create_pix_payment calls correct URL"""
        mock_http_response.json.return_value = {'id': 'pix_123', 'status': 'pending'}
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_http_response)

        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_class.return_value.__aexit__ = AsyncMock()

            await mp_service.create_pix_payment(
                amount=99.90,
                email='test@example.com',
                cpf='12345678901',
                name='Test User',
                external_reference='ref123',
                description='Créditos'
            )

            call_args = mock_client.post.call_args
            assert '/v1/payments' in call_args[0][0]

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
        await mp_service.log_event('pix.created', {'plan': 'credits'})

        call_args = mock_db.execute.call_args
        params = call_args[0][1]
        assert params['event_type'] == 'pix.created'


class TestMercadoPagoServiceEdgeCases:
    """Edge cases and error handling tests"""

    @pytest.fixture
    def mock_db(self):
        db_mock = AsyncMock()
        db_mock.execute = AsyncMock()
        return db_mock

    @pytest.fixture
    def mp_service(self, mock_db):
        with patch('api.services.mercadopago.database', mock_db):
            from api.services.mercadopago import MercadoPagoService
            service = MercadoPagoService()
            service.db = mock_db
            return service

    @pytest.mark.asyncio
    async def test_create_payment_with_special_chars_in_email(self, mp_service):
        """Test create_payment handles special characters in email"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 'pref_123'}
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_class.return_value.__aexit__ = AsyncMock()

            result = await mp_service.create_payment(
                title='Test',
                price=10.00,
                user_email='test+tag@example.com',
                external_reference='ref'
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_create_payment_with_zero_price(self, mp_service):
        """Test create_payment with zero price"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 'pref_free'}
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_class.return_value.__aexit__ = AsyncMock()

            result = await mp_service.create_payment(
                title='Free trial',
                price=0,
                user_email='test@example.com',
                external_reference='free'
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_create_pix_payment_with_metadata(self, mp_service):
        """Test create_pix_payment with metadata"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 'pix_meta',
            'status': 'pending',
            'point_of_interaction': {
                'transaction_data': {
                    'qr_code': 'code',
                    'qr_code_base64': 'base64'
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch('httpx.AsyncClient') as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_class.return_value.__aexit__ = AsyncMock()

            result = await mp_service.create_pix_payment(
                amount=199.90,
                email='test@example.com',
                cpf='12345678901',
                name='Premium User',
                external_reference='user:500credits',
                description='500 créditos premium'
            )

            assert result is not None


# ==================== LOG EVENT Tests ====================

class TestLogEvent:
    """Tests for log_event method"""

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

    @pytest.mark.asyncio
    async def test_log_event_success(self, mp_service, mock_db):
        """Test logging payment event successfully"""
        await mp_service.log_event('payment_approved', {'id': '123'})

        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args
        assert 'INSERT INTO payment_events' in call_args[0][0]

    @pytest.mark.asyncio
    async def test_log_event_with_complex_data(self, mp_service, mock_db):
        """Test logging event with complex data"""
        complex_data = {
            'id': 'pay_123',
            'status': 'approved',
            'payer': {'email': 'test@example.com'},
            'metadata': {'credits': 100}
        }

        await mp_service.log_event('payment_created', complex_data)

        mock_db.execute.assert_called_once()


# ==================== SEND CREDITS EMAIL Tests ====================

class TestSendCreditsEmail:
    """Tests for send_credits_email method"""

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

    @pytest.mark.asyncio
    async def test_send_credits_email_no_provider(self, mp_service):
        """Test send_credits_email when no email provider configured"""
        with patch('api.services.mercadopago.settings') as mock_settings:
            mock_settings.SMTP_HOST = None
            mock_settings.RESEND_API_KEY = None

            # Should not raise exception, just log
            await mp_service.send_credits_email(
                email='test@example.com',
                credits_amount=100,
                includes_license=False
            )

    @pytest.mark.asyncio
    async def test_send_credits_email_with_license(self, mp_service):
        """Test send_credits_email with license included"""
        with patch('api.services.mercadopago.settings') as mock_settings:
            mock_settings.SMTP_HOST = None
            mock_settings.RESEND_API_KEY = None

            # Should not raise exception, just log
            await mp_service.send_credits_email(
                email='test@example.com',
                credits_amount=500,
                includes_license=True
            )

    @pytest.mark.asyncio
    async def test_send_credits_email_smtp_success(self, mp_service):
        """Test send_credits_email via SMTP"""
        with patch('api.services.mercadopago.settings') as mock_settings, \
             patch('smtplib.SMTP') as mock_smtp_class:

            mock_settings.SMTP_HOST = 'smtp.example.com'
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_TLS = True
            mock_settings.SMTP_USER = 'user'
            mock_settings.SMTP_PASSWORD = 'pass'
            mock_settings.SMTP_FROM = 'noreply@example.com'

            mock_smtp = MagicMock()
            mock_smtp_class.return_value.__enter__ = MagicMock(
                return_value=mock_smtp
            )
            mock_smtp_class.return_value.__exit__ = MagicMock()

            await mp_service.send_credits_email(
                email='test@example.com',
                credits_amount=100,
                includes_license=False
            )

    @pytest.mark.asyncio
    async def test_send_credits_email_smtp_error(self, mp_service):
        """Test send_credits_email handles SMTP errors"""
        with patch('api.services.mercadopago.settings') as mock_settings, \
             patch('smtplib.SMTP') as mock_smtp_class:

            mock_settings.SMTP_HOST = 'smtp.example.com'
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_TLS = True
            mock_settings.SMTP_USER = 'user'
            mock_settings.SMTP_PASSWORD = 'pass'
            mock_settings.SMTP_FROM = 'noreply@example.com'

            mock_smtp_class.return_value.__enter__ = MagicMock(
                side_effect=Exception("SMTP connection failed")
            )

            # Should not raise, just log error
            await mp_service.send_credits_email(
                email='test@example.com',
                credits_amount=100,
                includes_license=False
            )

    @pytest.mark.asyncio
    async def test_send_credits_email_resend_success(self, mp_service):
        """Test send_credits_email via Resend API"""
        with patch('api.services.mercadopago.settings') as mock_settings, \
             patch('httpx.AsyncClient') as mock_client_class:

            mock_settings.SMTP_HOST = None
            mock_settings.RESEND_API_KEY = 'resend_key_123'

            mock_client = AsyncMock()
            mock_client.post = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__aexit__ = AsyncMock()

            await mp_service.send_credits_email(
                email='test@example.com',
                credits_amount=100,
                includes_license=False
            )

    @pytest.mark.asyncio
    async def test_send_credits_email_resend_error(self, mp_service):
        """Test send_credits_email handles Resend API errors"""
        with patch('api.services.mercadopago.settings') as mock_settings, \
             patch('httpx.AsyncClient') as mock_client_class:

            mock_settings.SMTP_HOST = None
            mock_settings.RESEND_API_KEY = 'resend_key_123'

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=Exception("API Error"))
            mock_client_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__aexit__ = AsyncMock()

            # Should not raise, just log error
            await mp_service.send_credits_email(
                email='test@example.com',
                credits_amount=100,
                includes_license=False
            )
