"""
Unit tests for Accounting Service
Tests for financial tracking and reporting
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from api.services.accounting import (CREDIT_COSTS, DEFAULT_CREDIT_PACKAGES,
                                     MP_FEE_PERCENT, OPENAI_PRICING,
                                     USD_TO_BRL, AccountingService)


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
    db.fetch_val = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    db.refresh = AsyncMock()
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


# ============================================
# ADDITIONAL ACCOUNTING SERVICE TESTS
# ============================================

class TestApiUsageLogging:
    """Tests for API usage logging"""

    @pytest.mark.asyncio
    async def test_log_api_usage_calculates_cost(self, mock_db):
        """Test that log_api_usage calculates costs correctly"""
        service = AccountingService(mock_db)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        result = await service.log_api_usage(
            user_id=str(uuid4()),
            provider="openai",
            model="gpt-4o-mini",
            operation_type="copy_generation",
            tokens_input=1000,
            tokens_output=500,
            request_duration_ms=1200,
            was_cached=False,
            metadata={"test": "value"}
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_log_api_usage_with_none_user(self, mock_db):
        """Test API logging with None user_id"""
        service = AccountingService(mock_db)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        result = await service.log_api_usage(
            user_id=None,
            provider="openai",
            model="gpt-4o",
            operation_type="copy_generation",
            tokens_input=500,
            tokens_output=250
        )
        
        # Should not raise, user_id can be None
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_api_usage_cached(self, mock_db):
        """Test API logging for cached request"""
        service = AccountingService(mock_db)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        await service.log_api_usage(
            user_id=str(uuid4()),
            provider="openai",
            model="gpt-4o",
            operation_type="copy_generation",
            tokens_input=0,
            tokens_output=0,
            was_cached=True
        )
        
        mock_db.add.assert_called_once()


class TestFinancialTransactions:
    """Tests for financial transaction recording"""

    @pytest.mark.asyncio
    async def test_record_credit_purchase(self, mock_db):
        """Test recording a credit purchase"""
        service = AccountingService(mock_db)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        # Mock the user financial summary query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        user_id = str(uuid4())
        package_id = str(uuid4())
        
        result = await service.record_credit_purchase(
            user_id=user_id,
            package_id=package_id,
            amount_brl=Decimal("24.90"),
            credits=150,
            payment_id="MP123456",
            payment_method="pix"
        )
        
        assert result is not None
        mock_db.add.assert_called()

    @pytest.mark.asyncio
    async def test_record_credit_usage(self, mock_db):
        """Test recording credit usage"""
        service = AccountingService(mock_db)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        result = await service.record_credit_usage(
            user_id=str(uuid4()),
            operation_type="copy_generation",
            credits_used=1,
            cost_brl=Decimal("0.05"),
            tokens_input=1000,
            tokens_output=500,
            metadata={"prompt": "test"}
        )
        
        assert result is not None
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_license_purchase(self, mock_db):
        """Test recording a license purchase"""
        service = AccountingService(mock_db)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        result = await service.record_license_purchase(
            user_id=str(uuid4()),
            amount_brl=Decimal("197.00"),
            payment_id="MP789012",
            payment_method="credit_card"
        )
        
        assert result is not None
        mock_db.add.assert_called_once()


class TestUserFinancialSummary:
    """Tests for user financial summary updates"""

    @pytest.mark.asyncio
    async def test_update_user_summary_new_user(self, mock_db):
        """Test creating new user financial summary"""
        service = AccountingService(mock_db)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        # User has no existing summary
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        await service._update_user_financial_summary(
            user_id=str(uuid4()),
            amount_spent=Decimal("24.90"),
            credits_purchased=150
        )
        
        # Should add new summary
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_update_user_summary_existing_user(self, mock_db):
        """Test updating existing user financial summary"""
        service = AccountingService(mock_db)
        mock_db.commit = AsyncMock()
        
        # User has existing summary
        existing_summary = MagicMock()
        existing_summary.total_spent = Decimal("50.00")
        existing_summary.total_credits_purchased = 200
        existing_summary.purchase_count = 2
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_summary
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        await service._update_user_financial_summary(
            user_id=str(uuid4()),
            amount_spent=Decimal("24.90"),
            credits_purchased=150
        )
        
        # Summary should be updated
        assert existing_summary.total_spent == Decimal("74.90")
        assert existing_summary.total_credits_purchased == 350
        assert existing_summary.purchase_count == 3
        mock_db.commit.assert_called()


class TestDashboardMetrics:
    """Tests for dashboard metrics"""

    @pytest.mark.asyncio
    async def test_get_dashboard_metrics(self, mock_db):
        """Test getting dashboard metrics"""
        service = AccountingService(mock_db)
        
        # Mock all the scalar returns
        mock_db.execute = AsyncMock()
        mock_scalar_result = MagicMock()
        mock_scalar_result.scalar.return_value = Decimal("1000.00")
        mock_db.execute.return_value = mock_scalar_result
        
        result = await service.get_dashboard_metrics(days=30)
        
        assert "period_days" in result
        assert result["period_days"] == 30
        assert "total_revenue" in result
        assert "gross_profit" in result
        assert "profit_margin_percent" in result

    @pytest.mark.asyncio
    async def test_get_dashboard_metrics_empty(self, mock_db):
        """Test dashboard metrics with no data"""
        service = AccountingService(mock_db)
        
        # Mock returns None/0
        mock_scalar_result = MagicMock()
        mock_scalar_result.scalar.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_scalar_result)
        
        result = await service.get_dashboard_metrics(days=7)
        
        assert result["total_revenue"] == 0
        assert result["gross_profit"] == 0
        assert result["profit_margin_percent"] == 0


class TestRevenueByDay:
    """Tests for daily revenue reports"""

    @pytest.mark.asyncio
    async def test_get_revenue_by_day(self, mock_db):
        """Test getting revenue by day"""
        service = AccountingService(mock_db)
        
        # Mock fetchall
        mock_row = MagicMock()
        mock_row.date = "2024-01-15"
        mock_row.revenue = Decimal("100.00")
        mock_row.costs = Decimal("10.00")
        mock_row.transactions = 5
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await service.get_revenue_by_day(days=30)
        
        assert len(result) == 1
        assert result[0]["date"] == "2024-01-15"
        assert result[0]["revenue"] == 100.0
        assert result[0]["profit"] == 90.0

    @pytest.mark.asyncio
    async def test_get_revenue_by_day_empty(self, mock_db):
        """Test revenue by day with no data"""
        service = AccountingService(mock_db)
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await service.get_revenue_by_day(days=7)
        
        assert result == []


class TestOperationsBreakdown:
    """Tests for operations breakdown"""

    @pytest.mark.asyncio
    async def test_get_operations_breakdown(self, mock_db):
        """Test getting operations breakdown"""
        service = AccountingService(mock_db)
        
        mock_row1 = MagicMock()
        mock_row1.operation_type = "copy_generation"
        mock_row1.count = 50
        
        mock_row2 = MagicMock()
        mock_row2.operation_type = "trend_analysis"
        mock_row2.count = 20
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row1, mock_row2]
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await service.get_operations_breakdown(days=30)
        
        assert result["copy_generation"] == 50
        assert result["trend_analysis"] == 20

    @pytest.mark.asyncio
    async def test_get_operations_breakdown_empty(self, mock_db):
        """Test operations breakdown with no data"""
        service = AccountingService(mock_db)
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await service.get_operations_breakdown(days=7)
        
        assert result == {}


class TestTopUsers:
    """Tests for top users report"""

    @pytest.mark.asyncio
    async def test_get_top_users(self, mock_db):
        """Test getting top spending users"""
        service = AccountingService(mock_db)
        
        mock_user = MagicMock()
        mock_user.user_id = uuid4()
        mock_user.total_spent = Decimal("500.00")
        mock_user.total_credits_purchased = 2000
        mock_user.total_credits_used = 1500
        mock_user.purchase_count = 10
        mock_user.lifetime_profit = Decimal("450.00")
        
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_user]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await service.get_top_users(limit=10)
        
        assert len(result) == 1
        assert result[0]["total_spent"] == 500.0
        assert result[0]["credits_purchased"] == 2000


class TestPackageSalesStats:
    """Tests for package sales statistics"""

    @pytest.mark.asyncio
    async def test_get_package_sales_stats(self, mock_db):
        """Test getting package sales stats"""
        service = AccountingService(mock_db)
        
        mock_row = MagicMock()
        mock_row.name = "Pro"
        mock_row.slug = "pro"
        mock_row.sales = 25
        mock_row.revenue = Decimal("622.50")
        mock_row.credits = 3750
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await service.get_package_sales_stats(days=30)
        
        assert len(result) == 1
        assert result[0]["name"] == "Pro"
        assert result[0]["sales"] == 25
        assert result[0]["revenue"] == 622.50


class TestDailyReportGeneration:
    """Tests for daily report generation"""

    @pytest.mark.asyncio
    async def test_generate_daily_report_new(self, mock_db):
        """Test generating new daily report"""
        service = AccountingService(mock_db)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        # No existing report
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_result.fetchone.return_value = MagicMock(
            credit_revenue=Decimal("100"),
            license_revenue=Decimal("0"),
            payment_fees=Decimal("5"),
            transactions_count=5,
            credits_sold=500,
            copies=10,
            trends=5,
            niches=2
        )
        mock_result.scalar.return_value = Decimal("10")
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await service.generate_daily_report()
        
        assert result is not None
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_generate_daily_report_update(self, mock_db):
        """Test updating existing daily report"""
        service = AccountingService(mock_db)
        mock_db.commit = AsyncMock()
        
        # Existing report
        existing_report = MagicMock()
        existing_report.updated_at = None
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_report
        mock_result.fetchone.return_value = MagicMock(
            credit_revenue=Decimal("200"),
            license_revenue=Decimal("100"),
            payment_fees=Decimal("15"),
            transactions_count=10,
            credits_sold=1000,
            copies=20,
            trends=10,
            niches=5
        )
        mock_result.scalar.return_value = Decimal("20")
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await service.generate_daily_report()
        
        assert result == existing_report
        mock_db.commit.assert_called()


class TestEdgeCasesAccounting:
    """Edge case tests for accounting"""

    def test_calculate_openai_cost_zero_tokens(self, mock_db):
        """Test cost calculation with zero tokens"""
        service = AccountingService(mock_db)
        result = service.calculate_openai_cost("gpt-4o", 0, 0)
        
        assert result["total_usd"] == Decimal("0")
        assert result["total_brl"] == Decimal("0")

    def test_calculate_openai_cost_large_tokens(self, mock_db):
        """Test cost calculation with large token counts"""
        service = AccountingService(mock_db)
        result = service.calculate_openai_cost("gpt-4o", 100000, 50000)
        
        # Should handle large numbers
        assert result["total_usd"] > Decimal("0")
        assert result["tokens_input"] == 100000
        assert result["tokens_output"] == 50000

    @pytest.mark.asyncio
    async def test_get_dashboard_metrics_custom_days(self, mock_db):
        """Test dashboard metrics with custom period"""
        service = AccountingService(mock_db)
        
        mock_scalar_result = MagicMock()
        mock_scalar_result.scalar.return_value = Decimal("500.00")
        mock_db.execute = AsyncMock(return_value=mock_scalar_result)
        
        result = await service.get_dashboard_metrics(days=90)
        
        assert result["period_days"] == 90
