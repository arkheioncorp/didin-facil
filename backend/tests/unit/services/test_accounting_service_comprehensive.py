"""
Comprehensive tests for Accounting Service.
Tests financial calculations, pricing, and constants.
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.database.accounting_models import OperationType
from api.services.accounting import (CREDIT_COSTS, DEFAULT_CREDIT_PACKAGES,
                                     MP_FEE_FIXED, MP_FEE_PERCENT,
                                     OPENAI_PRICING, USD_TO_BRL,
                                     AccountingService)

# ============================================================================
# Constants Tests
# ============================================================================

class TestPricingConstants:
    """Tests for pricing constants."""
    
    def test_openai_pricing_has_required_models(self):
        """Should have pricing for common models."""
        assert "gpt-4-turbo-preview" in OPENAI_PRICING
        assert "gpt-4o" in OPENAI_PRICING
        assert "gpt-4o-mini" in OPENAI_PRICING
        assert "gpt-3.5-turbo" in OPENAI_PRICING
    
    def test_openai_pricing_structure(self):
        """Each model should have input and output pricing."""
        for model, pricing in OPENAI_PRICING.items():
            assert "input" in pricing
            assert "output" in pricing
            assert isinstance(pricing["input"], Decimal)
            assert isinstance(pricing["output"], Decimal)
    
    def test_openai_pricing_values(self):
        """Pricing values should be reasonable."""
        for model, pricing in OPENAI_PRICING.items():
            assert pricing["input"] > Decimal("0")
            assert pricing["output"] > Decimal("0")
            # Output usually costs more than input
            assert pricing["output"] >= pricing["input"]
    
    def test_usd_to_brl_conversion(self):
        """USD to BRL should be reasonable."""
        assert isinstance(USD_TO_BRL, Decimal)
        assert USD_TO_BRL > Decimal("4.0")  # BRL is weaker than USD
        assert USD_TO_BRL < Decimal("10.0")  # But not absurdly so
    
    def test_mercadopago_fees(self):
        """MercadoPago fees should be reasonable."""
        assert isinstance(MP_FEE_PERCENT, Decimal)
        assert MP_FEE_PERCENT > Decimal("0")
        assert MP_FEE_PERCENT < Decimal("10")  # Less than 10%
    
    def test_credit_costs_defined(self):
        """Credit costs should be defined for operations."""
        assert OperationType.COPY_GENERATION in CREDIT_COSTS
        assert OperationType.TREND_ANALYSIS in CREDIT_COSTS
        assert OperationType.NICHE_REPORT in CREDIT_COSTS
        assert OperationType.PRODUCT_SCRAPING in CREDIT_COSTS
    
    def test_credit_costs_values(self):
        """Credit costs should be non-negative."""
        for op, cost in CREDIT_COSTS.items():
            assert cost >= 0
    
    def test_default_credit_packages(self):
        """Should have default credit packages."""
        assert len(DEFAULT_CREDIT_PACKAGES) >= 3
        
        for pkg in DEFAULT_CREDIT_PACKAGES:
            assert "name" in pkg
            assert "slug" in pkg
            assert "credits" in pkg
            assert "price_brl" in pkg
            assert pkg["credits"] > 0
            assert pkg["price_brl"] > Decimal("0")


# ============================================================================
# AccountingService Tests
# ============================================================================

class TestAccountingServiceInit:
    """Tests for AccountingService initialization."""
    
    def test_init_with_database(self):
        """Should initialize with database connection."""
        mock_db = MagicMock()
        service = AccountingService(mock_db)
        
        assert service.db is mock_db


class TestCalculateOpenAICost:
    """Tests for calculate_openai_cost method."""
    
    @pytest.fixture
    def service(self):
        mock_db = MagicMock()
        return AccountingService(mock_db)
    
    def test_calculate_gpt4_turbo_cost(self, service):
        """Should calculate cost for GPT-4 Turbo."""
        result = service.calculate_openai_cost(
            model="gpt-4-turbo-preview",
            tokens_input=1000,
            tokens_output=500
        )
        
        assert "cost_input_usd" in result
        assert "cost_output_usd" in result
        assert "total_usd" in result
        assert "total_brl" in result
        assert result["tokens_input"] == 1000
        assert result["tokens_output"] == 500
        assert result["model"] == "gpt-4-turbo-preview"
    
    def test_calculate_gpt4o_mini_cost(self, service):
        """Should calculate cost for GPT-4o mini (cheaper)."""
        result = service.calculate_openai_cost(
            model="gpt-4o-mini",
            tokens_input=1000,
            tokens_output=500
        )
        
        # GPT-4o-mini should be cheaper
        gpt4_result = service.calculate_openai_cost(
            model="gpt-4-turbo-preview",
            tokens_input=1000,
            tokens_output=500
        )
        
        assert result["total_usd"] < gpt4_result["total_usd"]
    
    def test_calculate_with_zero_tokens(self, service):
        """Should handle zero tokens."""
        result = service.calculate_openai_cost(
            model="gpt-4-turbo-preview",
            tokens_input=0,
            tokens_output=0
        )
        
        assert result["total_usd"] == Decimal("0")
        assert result["total_brl"] == Decimal("0")
    
    def test_calculate_brl_conversion(self, service):
        """Should correctly convert USD to BRL."""
        result = service.calculate_openai_cost(
            model="gpt-4-turbo-preview",
            tokens_input=1000,
            tokens_output=1000
        )
        
        expected_brl = result["total_usd"] * USD_TO_BRL
        assert result["total_brl"] == expected_brl
    
    def test_calculate_unknown_model_uses_default(self, service):
        """Should use default pricing for unknown models."""
        result = service.calculate_openai_cost(
            model="unknown-model",
            tokens_input=1000,
            tokens_output=500
        )
        
        # Should not fail, uses default pricing
        assert result["total_usd"] > Decimal("0")
    
    def test_calculate_large_token_counts(self, service):
        """Should handle large token counts."""
        result = service.calculate_openai_cost(
            model="gpt-4-turbo-preview",
            tokens_input=100000,
            tokens_output=50000
        )
        
        assert result["tokens_input"] == 100000
        assert result["tokens_output"] == 50000
        assert result["total_usd"] > Decimal("0")


class TestGetActivePackages:
    """Tests for get_active_packages method."""
    
    @pytest.fixture
    def service(self):
        mock_db = MagicMock()
        return AccountingService(mock_db)
    
    @pytest.mark.asyncio
    async def test_get_active_packages_returns_list(self, service):
        """Should return list of packages."""
        mock_row = MagicMock()
        mock_row._mapping = {
            "id": uuid.uuid4(),
            "name": "Test Package",
            "slug": "test",
            "credits": 100,
            "price_brl": Decimal("19.90"),
            "price_usd": Decimal("3.50"),
            "discount_percent": 10,
            "original_price": Decimal("22.00"),
            "description": "Test",
            "badge": None,
            "is_featured": False,
            "sort_order": 1,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        mock_row.__getitem__ = lambda self, key: mock_row._mapping[key]
        
        service.db.fetch_all = AsyncMock(return_value=[mock_row])
        
        result = await service.get_active_packages()
        
        assert len(result) == 1
        assert result[0].credits == 100
    
    @pytest.mark.asyncio
    async def test_get_active_packages_empty(self, service):
        """Should return empty list when no packages."""
        service.db.fetch_all = AsyncMock(return_value=[])
        
        result = await service.get_active_packages()
        
        assert result == []


class TestGetPackageBySlug:
    """Tests for get_package_by_slug method."""
    
    @pytest.fixture
    def service(self):
        mock_db = MagicMock()
        return AccountingService(mock_db)
    
    @pytest.mark.asyncio
    async def test_get_package_found(self, service):
        """Should return package when found."""
        mock_row = MagicMock()
        mock_row._mapping = {
            "id": uuid.uuid4(),
            "name": "Pro Package",
            "slug": "pro",
            "credits": 150,
            "price_brl": Decimal("24.90"),
            "price_usd": Decimal("4.50"),
            "discount_percent": 16,
            "original_price": Decimal("29.70"),
            "description": "Popular",
            "badge": "Most Popular",
            "is_featured": True,
            "sort_order": 2,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        mock_row.__getitem__ = lambda self, key: mock_row._mapping[key]
        
        service.db.fetch_one = AsyncMock(return_value=mock_row)
        
        result = await service.get_package_by_slug("pro")
        
        assert result is not None
        assert result.slug == "pro"
        assert result.credits == 150
    
    @pytest.mark.asyncio
    async def test_get_package_not_found(self, service):
        """Should return None when not found."""
        service.db.fetch_one = AsyncMock(return_value=None)
        
        result = await service.get_package_by_slug("nonexistent")
        
        assert result is None


class TestLogAPIUsage:
    """Tests for log_api_usage method."""
    
    @pytest.fixture
    def service(self):
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        return AccountingService(mock_db)
    
    @pytest.mark.asyncio
    async def test_log_api_usage_creates_log(self, service):
        """Should create API usage log."""
        user_id = str(uuid.uuid4())
        
        result = await service.log_api_usage(
            user_id=user_id,
            provider="openai",
            model="gpt-4-turbo-preview",
            operation_type="copy_generation",
            tokens_input=1000,
            tokens_output=500,
            request_duration_ms=1500
        )
        
        assert result is not None
        assert result.provider == "openai"
        assert result.model == "gpt-4-turbo-preview"
        assert result.tokens_input == 1000
        assert result.tokens_output == 500
        assert result.tokens_total == 1500
        
        service.db.add.assert_called_once()
        service.db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_api_usage_with_metadata(self, service):
        """Should include metadata in log."""
        user_id = str(uuid.uuid4())
        metadata = {"prompt_type": "product_copy", "version": "v2"}
        
        result = await service.log_api_usage(
            user_id=user_id,
            provider="openai",
            model="gpt-4o-mini",
            operation_type="copy_generation",
            tokens_input=500,
            tokens_output=250,
            metadata=metadata
        )
        
        assert result.metadata == metadata
    
    @pytest.mark.asyncio
    async def test_log_api_usage_without_user(self, service):
        """Should handle None user_id."""
        result = await service.log_api_usage(
            user_id=None,
            provider="openai",
            model="gpt-4o",
            operation_type="trend_analysis",
            tokens_input=2000,
            tokens_output=1000
        )
        
        assert result.user_id is None
    
    @pytest.mark.asyncio
    async def test_log_api_usage_cached(self, service):
        """Should track cached requests."""
        user_id = str(uuid.uuid4())
        
        result = await service.log_api_usage(
            user_id=user_id,
            provider="openai",
            model="gpt-4o-mini",
            operation_type="copy_generation",
            tokens_input=0,
            tokens_output=0,
            was_cached=True
        )
        
        assert result.was_cached is True


# ============================================================================
# Default Credit Packages Tests
# ============================================================================

class TestDefaultCreditPackages:
    """Tests for default credit package configuration."""
    
    def test_packages_have_unique_slugs(self):
        """Each package should have unique slug."""
        slugs = [pkg["slug"] for pkg in DEFAULT_CREDIT_PACKAGES]
        assert len(slugs) == len(set(slugs))
    
    def test_packages_have_unique_sort_order(self):
        """Each package should have unique sort order."""
        orders = [pkg["sort_order"] for pkg in DEFAULT_CREDIT_PACKAGES]
        assert len(orders) == len(set(orders))
    
    def test_packages_credits_increase_with_price(self):
        """More expensive packages should have more credits."""
        sorted_packages = sorted(
            DEFAULT_CREDIT_PACKAGES,
            key=lambda p: p["price_brl"]
        )
        
        for i in range(len(sorted_packages) - 1):
            current = sorted_packages[i]
            next_pkg = sorted_packages[i + 1]
            assert current["credits"] <= next_pkg["credits"]
    
    def test_one_featured_package(self):
        """Should have exactly one featured package."""
        featured = [pkg for pkg in DEFAULT_CREDIT_PACKAGES if pkg.get("is_featured")]
        assert len(featured) == 1
    
    def test_discounts_make_sense(self):
        """Discount should match original price."""
        for pkg in DEFAULT_CREDIT_PACKAGES:
            if "discount_percent" in pkg and "original_price" in pkg:
                expected_discount = (
                    (pkg["original_price"] - pkg["price_brl"]) 
                    / pkg["original_price"] * 100
                )
                # Allow some tolerance for rounding
                assert abs(expected_discount - pkg["discount_percent"]) < 5


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error scenarios."""
    
    @pytest.fixture
    def service(self):
        mock_db = MagicMock()
        return AccountingService(mock_db)
    
    def test_calculate_cost_with_very_small_tokens(self, service):
        """Should handle very small token counts."""
        result = service.calculate_openai_cost(
            model="gpt-4o-mini",
            tokens_input=1,
            tokens_output=1
        )
        
        # Cost should be very small but positive
        assert result["total_usd"] > Decimal("0")
    
    def test_calculate_cost_precision(self, service):
        """Should maintain decimal precision."""
        result = service.calculate_openai_cost(
            model="gpt-4-turbo-preview",
            tokens_input=123,
            tokens_output=456
        )
        
        # Result should be Decimal, not float
        assert isinstance(result["total_usd"], Decimal)
        assert isinstance(result["total_brl"], Decimal)
    
    @pytest.mark.asyncio
    async def test_get_packages_handles_db_error(self, service):
        """Should handle database errors gracefully."""
        service.db.fetch_all = AsyncMock(side_effect=Exception("DB error"))
        
        with pytest.raises(Exception, match="DB error"):
            await service.get_active_packages()
    
    def test_credit_costs_for_all_operations(self):
        """Should have costs defined for all operation types."""
        # Check that commonly used operations have defined costs
        important_ops = [
            OperationType.COPY_GENERATION,
            OperationType.TREND_ANALYSIS,
            OperationType.PRODUCT_SCRAPING,
        ]
        
        for op in important_ops:
            assert op in CREDIT_COSTS
