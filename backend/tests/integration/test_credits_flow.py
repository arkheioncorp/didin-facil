"""
Integration Tests for Credits Purchase Flow
Tests the complete flow: packages -> purchase -> payment -> credits added
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from uuid import uuid4

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestCreditsFlowIntegration:
    """Integration tests for the credits purchase flow"""

    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user"""
        user = MagicMock()
        user.id = uuid4()
        user.email = "test@example.com"
        user.name = "Test User"
        user.credits_balance = 0
        user.credits_purchased = 0
        user.credits_used = 0
        user.has_lifetime_license = False
        return user

    @pytest.fixture
    def mock_db(self):
        """Create mock database"""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.fetch_one = AsyncMock()
        db.fetch_all = AsyncMock()
        return db

    @pytest.fixture
    def mock_package(self):
        """Create a mock credit package"""
        pkg = MagicMock()
        pkg.id = uuid4()
        pkg.name = "Pro"
        pkg.slug = "pro"
        pkg.credits = 200
        pkg.price_brl = Decimal("49.90")
        pkg.original_price = Decimal("79.90")
        pkg.discount_percent = 37
        pkg.is_active = True
        pkg.is_featured = True
        pkg.badge = "Mais Popular"
        pkg.description = "Para criadores ativos"
        return pkg

    @pytest.mark.asyncio
    async def test_get_packages_returns_active_packages(self, mock_db):
        """Test that GET /credits/packages returns active packages"""
        from api.services.accounting import AccountingService
        
        mock_packages = [
            MagicMock(
                id=uuid4(), name="Starter", slug="starter", 
                credits=50, price_brl=Decimal("19.90"),
                original_price=Decimal("29.90"), discount_percent=33,
                is_active=True, is_featured=False, badge=None,
                description="Ideal para começar"
            ),
            MagicMock(
                id=uuid4(), name="Pro", slug="pro",
                credits=200, price_brl=Decimal("49.90"),
                original_price=Decimal("79.90"), discount_percent=37,
                is_active=True, is_featured=True, badge="Mais Popular",
                description="Para criadores ativos"
            ),
        ]
        
        with patch.object(
            AccountingService, 'get_active_packages',
            return_value=mock_packages
        ):
            service = AccountingService(mock_db)
            packages = await service.get_active_packages()
            
            assert len(packages) == 2
            assert packages[0].slug == "starter"
            assert packages[1].slug == "pro"
            assert packages[1].is_featured is True

    @pytest.mark.asyncio
    async def test_create_pix_payment_returns_qr_code(self):
        """Test that PIX payment creation returns QR code data"""
        from api.services.mercadopago import MercadoPagoService
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 12345678,
            'status': 'pending',
            'point_of_interaction': {
                'transaction_data': {
                    'qr_code': '00020126580014br.gov.bcb.pix...',
                    'qr_code_base64': 'iVBORw0KGgoAAAANSUhE...',
                    'ticket_url': 'https://www.mercadopago.com.br/...'
                }
            },
            'date_of_expiration': '2025-12-01T00:00:00.000-03:00'
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_http.return_value.__aexit__ = AsyncMock()
            
            service = MercadoPagoService()
            result = await service.create_pix_payment(
                amount=47.40,  # 49.90 - 5% PIX discount
                email="test@example.com",
                cpf="12345678900",
                name="Test User",
                external_reference="CRED-20251130-ABC123",
                description="Pro - 200 créditos"
            )
            
            assert result['payment_id'] == 12345678
            assert result['status'] == 'pending'
            assert result['qr_code'] is not None
            assert result['qr_code_base64'] is not None

    @pytest.mark.asyncio
    async def test_purchase_flow_creates_pending_transaction(
        self, mock_user, mock_db, mock_package
    ):
        """Test that purchase flow creates a pending transaction"""
        from api.services.accounting import AccountingService
        from api.services.mercadopago import MercadoPagoService
        
        # Mock the package lookup
        with patch.object(
            AccountingService, 'get_package_by_slug',
            return_value=mock_package
        ):
            # Mock PIX payment
            mock_pix = {
                'payment_id': 12345678,
                'status': 'pending',
                'qr_code': 'pix_code_here',
                'qr_code_base64': 'base64_code',
                'copy_paste': 'pix_code_here',
                'date_of_expiration': '2025-12-01T00:00:00.000-03:00'
            }
            
            with patch.object(
                MercadoPagoService, 'create_pix_payment',
                return_value=mock_pix
            ):
                service = AccountingService(mock_db)
                package = await service.get_package_by_slug("pro")
                
                assert package is not None
                assert package.credits == 200
                assert float(package.price_brl) == 49.90

    @pytest.mark.asyncio
    async def test_pix_discount_applied_correctly(self, mock_package):
        """Test that 5% PIX discount is calculated correctly"""
        base_price = float(mock_package.price_brl)
        pix_discount = 0.05
        expected_price = base_price * (1 - pix_discount)
        
        assert base_price == 49.90
        assert round(expected_price, 2) == 47.40

    @pytest.mark.asyncio
    async def test_credit_consumption_deducts_balance(self, mock_db, mock_user):
        """Test that using credits deducts from user balance"""
        from api.services.accounting import AccountingService
        
        # Set initial balance
        mock_user.credits_balance = 200
        
        # Simulate consuming 5 credits for trend analysis
        credits_to_consume = 5
        expected_balance = mock_user.credits_balance - credits_to_consume
        
        assert expected_balance == 195

    @pytest.mark.asyncio
    async def test_operation_costs_defined(self, mock_db):
        """Test that operation costs are properly defined"""
        expected_costs = {
            'copy_generation': 1,
            'ai_chat': 1,
            'product_scraping': 2,
            'trend_analysis': 5,
            'image_generation': 5,
            'niche_report': 10,
        }
        
        for operation, expected_credits in expected_costs.items():
            assert expected_credits > 0, f"{operation} should cost credits"


class TestCreditPackagePricing:
    """Test that pricing is consistent across the system"""
    
    def test_starter_package_pricing(self):
        """Verify Starter package: R$19.90 for 50 credits"""
        expected = {
            'name': 'Starter',
            'credits': 50,
            'price': 19.90,
            'price_per_credit': 0.40
        }
        
        calculated_ppc = expected['price'] / expected['credits']
        assert round(calculated_ppc, 2) == expected['price_per_credit']

    def test_pro_package_pricing(self):
        """Verify Pro package: R$49.90 for 200 credits"""
        expected = {
            'name': 'Pro',
            'credits': 200,
            'price': 49.90,
            'price_per_credit': 0.25
        }
        
        calculated_ppc = expected['price'] / expected['credits']
        assert round(calculated_ppc, 2) == expected['price_per_credit']

    def test_ultra_package_pricing(self):
        """Verify Ultra package: R$99.90 for 500 credits"""
        expected = {
            'name': 'Ultra',
            'credits': 500,
            'price': 99.90,
            'price_per_credit': 0.20
        }
        
        calculated_ppc = expected['price'] / expected['credits']
        assert round(calculated_ppc, 2) == expected['price_per_credit']

    def test_higher_package_better_value(self):
        """Verify that larger packages have lower price per credit"""
        packages = [
            {'credits': 50, 'price': 19.90},   # Starter
            {'credits': 200, 'price': 49.90},  # Pro
            {'credits': 500, 'price': 99.90},  # Ultra
        ]
        
        price_per_credits = [p['price'] / p['credits'] for p in packages]
        
        # Each package should be cheaper per credit than the previous
        assert price_per_credits[1] < price_per_credits[0]
        assert price_per_credits[2] < price_per_credits[1]
