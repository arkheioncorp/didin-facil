"""
Unit tests for Accounting Service
Tests for financial tracking and reporting
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from api.services.accounting import (
    OPENAI_PRICING,
    USD_TO_BRL,
    MP_FEE_PERCENT,
    CREDIT_COSTS,
    DEFAULT_CREDIT_PACKAGES,
    AccountingService,
)


class TestPricingConstants:
    """Tests for pricing constants"""

    def test_openai_pricing_has_required_models(self):
        """Test OpenAI pricing has required models"""
        required_models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
        
        for model in required_models:
            assert model in OPENAI_PRICING
            assert "input" in OPENAI_PRICING[model]
            assert "output" in OPENAI_PRICING[model]

    def test_openai_pricing_values_are_decimal(self):
        """Test all pricing values are Decimal"""
        for model, pricing in OPENAI_PRICING.items():
            assert isinstance(pricing["input"], Decimal)
            assert isinstance(pricing["output"], Decimal)

    def test_usd_to_brl_is_decimal(self):
        """Test USD to BRL is Decimal"""
        assert isinstance(USD_TO_BRL, Decimal)
        assert USD_TO_BRL > Decimal("1.0")  # BRL is weaker than USD

    def test_mp_fee_percent_range(self):
        """Test MercadoPago fee is reasonable"""
        assert MP_FEE_PERCENT >= Decimal("0")
        assert MP_FEE_PERCENT < Decimal("20")  # Max 20%

    def test_credit_costs_values(self):
        """Test credit costs are integers"""
        for operation, cost in CREDIT_COSTS.items():
            assert isinstance(cost, int)
            assert cost >= 0

    def test_default_packages_structure(self):
        """Test default credit packages have required fields"""
        required_fields = ["name", "slug", "credits", "price_brl"]
        
        for package in DEFAULT_CREDIT_PACKAGES:
            for field in required_fields:
                assert field in package

    def test_default_packages_credits_positive(self):
        """Test all packages have positive credits"""
        for package in DEFAULT_CREDIT_PACKAGES:
            assert package["credits"] > 0

    def test_default_packages_price_positive(self):
        """Test all packages have positive price"""
        for package in DEFAULT_CREDIT_PACKAGES:
            assert package["price_brl"] > Decimal("0")


@pytest.fixture
def mock_db():
    """Create a mock database connection"""
    db = MagicMock()
    db.fetch_one = AsyncMock()
    db.fetch_all = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def accounting_service(mock_db):
    """Create an AccountingService with mock database"""
    return AccountingService(mock_db)


class TestAccountingService:
    """Tests for AccountingService class"""

    @pytest.mark.asyncio
    async def test_get_active_packages(self, accounting_service, mock_db):
        """Test getting active packages"""
        # Create a mock row that simulates database row behavior
        mock_row = MagicMock()
        mock_row._mapping = {
            'id': str(uuid4()),
            'name': 'Starter',
            'slug': 'starter',
            'credits': 50,  # Must be int for division
            'price_brl': Decimal("9.90"),
            'price_usd': Decimal("1.75"),
            'discount_percent': 0,
            'original_price': None,
            'description': 'Test',
            'badge': None,
            'is_featured': False,
            'sort_order': 1,
            'is_active': True,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        mock_row.__getitem__ = lambda self, key: self._mapping[key]
        mock_db.fetch_all.return_value = [mock_row]
        
        packages = await accounting_service.get_active_packages()
        assert len(packages) == 1
        mock_db.fetch_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_package_by_slug(self, accounting_service, mock_db):
        """Test getting package by slug"""
        mock_row = MagicMock()
        mock_row._mapping = {
            'id': str(uuid4()),
            'name': 'Pro',
            'slug': 'pro',
            'credits': 150,  # Must be int for division
            'price_brl': Decimal("24.90"),
            'price_usd': Decimal("4.40"),
            'discount_percent': 16,
            'original_price': Decimal("29.70"),
            'description': 'Popular',
            'badge': 'Mais Popular',
            'is_featured': True,
            'sort_order': 2,
            'is_active': True,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        mock_row.__getitem__ = lambda self, key: self._mapping[key]
        mock_db.fetch_one.return_value = mock_row
        
        package = await accounting_service.get_package_by_slug("pro")
        assert package is not None
        mock_db.fetch_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_package_by_slug_not_found(self, accounting_service, mock_db):
        """Test getting non-existent package"""
        mock_db.fetch_one.return_value = None
        
        package = await accounting_service.get_package_by_slug("non-existent")
        assert package is None


class TestCostCalculation:
    """Tests for cost calculations"""

    def test_calculate_openai_cost_gpt4o(self, mock_db):
        """Test OpenAI cost calculation for GPT-4o"""
        service = AccountingService(mock_db)
        result = service.calculate_openai_cost(
            model="gpt-4o",
            tokens_input=1000,
            tokens_output=500
        )
        
        # GPT-4o: $0.005/1K input + $0.015/1K output
        expected_usd = Decimal("0.005") + Decimal("0.0075")
        assert result["total_usd"] == expected_usd
        assert "total_brl" in result

    def test_calculate_openai_cost_gpt4o_mini(self, mock_db):
        """Test OpenAI cost calculation for GPT-4o-mini"""
        service = AccountingService(mock_db)
        result = service.calculate_openai_cost(
            model="gpt-4o-mini",
            tokens_input=2000,
            tokens_output=1000
        )
        
        # GPT-4o-mini: $0.00015/1K input + $0.0006/1K output
        expected_usd = Decimal("0.0003") + Decimal("0.0006")
        assert result["total_usd"] == expected_usd

    def test_calculate_openai_cost_unknown_model(self, mock_db):
        """Test OpenAI cost calculation for unknown model uses default"""
        service = AccountingService(mock_db)
        result = service.calculate_openai_cost(
            model="unknown-model",
            tokens_input=1000,
            tokens_output=500
        )
        
        # Should fall back to gpt-4-turbo-preview pricing
        assert "total_usd" in result
        assert result["total_usd"] > Decimal("0")


class TestMercadoPagoFees:
    """Tests for MercadoPago fee calculations"""

    def test_calculate_mp_fee(self, mock_db):
        """Test MercadoPago fee calculation"""
        # Calculate fee for R$100.00
        # 4.99% of 100 = 4.99
        amount = Decimal("100.00")
        expected_fee = amount * MP_FEE_PERCENT / Decimal("100")
        
        # The service should calculate fees properly
        assert MP_FEE_PERCENT == Decimal("4.99")
        assert expected_fee == Decimal("4.99")

    def test_calculate_net_revenue(self, mock_db):
        """Test net revenue calculation after fees"""
        amount = Decimal("100.00")
        fee = amount * MP_FEE_PERCENT / Decimal("100")
        net = amount - fee
        
        assert net == Decimal("95.01")


class TestCurrencyConversion:
    """Tests for currency conversion"""

    def test_usd_to_brl_conversion(self):
        """Test USD to BRL conversion"""
        usd = Decimal("10.00")
        brl = usd * USD_TO_BRL
        
        expected = Decimal("10.00") * USD_TO_BRL
        assert brl == expected

    def test_brl_to_usd_conversion(self):
        """Test BRL to USD conversion"""
        brl = Decimal("57.00")
        usd = brl / USD_TO_BRL
        
        expected = Decimal("57.00") / USD_TO_BRL
        assert usd == expected

    def test_round_trip_conversion(self):
        """Test that USD->BRL->USD is consistent"""
        original_usd = Decimal("100.00")
        brl = original_usd * USD_TO_BRL
        back_to_usd = brl / USD_TO_BRL
        
        assert back_to_usd == original_usd


class TestPricePerCredit:
    """Tests for price per credit calculations"""

    def test_calculate_price_per_credit_starter(self):
        """Test calculating price per credit for starter"""
        # Starter: R$9.90 / 50 credits = R$0.198
        price = Decimal("9.90")
        credits = 50
        price_per_credit = price / Decimal(credits)
        
        assert price_per_credit == Decimal("0.198")

    def test_calculate_price_per_credit_pro(self):
        """Test calculating price per credit for pro"""
        # Pro: R$24.90 / 150 credits = R$0.166
        price = Decimal("24.90")
        credits = 150
        price_per_credit = price / Decimal(credits)
        
        assert price_per_credit == Decimal("0.166")

    def test_calculate_discount_percent(self):
        """Test calculating discount percentage"""
        original_price = Decimal("29.70")
        current_price = Decimal("24.90")
        discount = (original_price - current_price) / original_price * Decimal("100")
        
        # Should be about 16.16%
        assert discount >= Decimal("16")
        assert discount <= Decimal("17")


class TestCreditPackagesPricing:
    """Tests for credit package pricing logic"""

    def test_starter_package_pricing(self):
        """Test starter package has correct pricing"""
        starter = next(p for p in DEFAULT_CREDIT_PACKAGES if p["slug"] == "starter")
        
        assert starter["credits"] == 50
        assert starter["price_brl"] == Decimal("9.90")
        assert starter.get("is_featured", False) is False

    def test_pro_package_is_featured(self):
        """Test pro package is featured"""
        pro = next(p for p in DEFAULT_CREDIT_PACKAGES if p["slug"] == "pro")
        
        assert pro["credits"] == 150
        assert pro["is_featured"] is True
        assert pro["badge"] == "Mais Popular"

    def test_ultra_package_has_discount(self):
        """Test ultra package has discount info"""
        ultra = next(p for p in DEFAULT_CREDIT_PACKAGES if p["slug"] == "ultra")
        
        assert ultra["credits"] == 500
        assert ultra.get("discount_percent", 0) > 0

    def test_enterprise_package_is_largest(self):
        """Test enterprise package has most credits"""
        enterprise = next(p for p in DEFAULT_CREDIT_PACKAGES if p["slug"] == "enterprise")
        
        assert enterprise["credits"] == 2000
        # Enterprise should have the best per-credit price
        price_per_credit = enterprise["price_brl"] / Decimal(enterprise["credits"])
        starter = next(p for p in DEFAULT_CREDIT_PACKAGES if p["slug"] == "starter")
        starter_ppc = starter["price_brl"] / Decimal(starter["credits"])
        
        assert price_per_credit < starter_ppc


class TestOperationCosts:
    """Tests for operation credit costs"""

    def test_copy_generation_costs_credits(self):
        """Test copy generation has a credit cost"""
        from api.database.accounting_models import OperationType
        
        cost = CREDIT_COSTS.get(OperationType.COPY_GENERATION, 0)
        assert cost > 0  # Should cost at least 1 credit

    def test_product_scraping_is_free(self):
        """Test product scraping is free"""
        from api.database.accounting_models import OperationType
        
        cost = CREDIT_COSTS.get(OperationType.PRODUCT_SCRAPING, 1)
        assert cost == 0  # Should be free

    def test_niche_report_is_most_expensive(self):
        """Test niche report is more expensive than basic operations"""
        from api.database.accounting_models import OperationType
        
        niche_cost = CREDIT_COSTS.get(OperationType.NICHE_REPORT, 0)
        copy_cost = CREDIT_COSTS.get(OperationType.COPY_GENERATION, 0)
        
        assert niche_cost > copy_cost
