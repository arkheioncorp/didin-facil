"""
Testes extensivos para Accounting Service
Aumenta cobertura de api/services/accounting.py
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
import pytest_asyncio

# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_db():
    """Mock database connection."""
    db = MagicMock()
    db.fetch_all = AsyncMock(return_value=[])
    db.fetch_one = AsyncMock(return_value=None)
    db.execute = AsyncMock(return_value=MagicMock())
    db.add = MagicMock()
    db.commit = AsyncMock()
    return db


@pytest.fixture
def mock_async_session():
    """Mock AsyncSession."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def sample_user_id():
    return str(uuid.uuid4())


@pytest.fixture
def sample_package_id():
    return str(uuid.uuid4())


# ============================================
# TEST PRICING CONSTANTS
# ============================================

class TestPricingConstants:
    """Testes para constantes de preço."""

    def test_openai_pricing_structure(self):
        """Verifica estrutura de preços OpenAI."""
        from api.services.accounting import OPENAI_PRICING
        
        assert "gpt-4-turbo-preview" in OPENAI_PRICING
        assert "gpt-4o" in OPENAI_PRICING
        assert "gpt-4o-mini" in OPENAI_PRICING
        assert "gpt-3.5-turbo" in OPENAI_PRICING
        
        for model, prices in OPENAI_PRICING.items():
            assert "input" in prices
            assert "output" in prices

    def test_usd_to_brl_rate(self):
        """Verifica taxa USD para BRL."""
        from api.services.accounting import USD_TO_BRL
        
        assert isinstance(USD_TO_BRL, Decimal)
        assert USD_TO_BRL > Decimal("0")

    def test_mp_fee_values(self):
        """Verifica taxas do MercadoPago."""
        from api.services.accounting import MP_FEE_FIXED, MP_FEE_PERCENT
        
        assert isinstance(MP_FEE_PERCENT, Decimal)
        assert isinstance(MP_FEE_FIXED, Decimal)
        assert MP_FEE_PERCENT > Decimal("0")

    def test_credit_costs_structure(self):
        """Verifica estrutura de custos de crédito."""
        from api.services.accounting import CREDIT_COSTS, OperationType
        
        assert OperationType.COPY_GENERATION in CREDIT_COSTS
        assert OperationType.TREND_ANALYSIS in CREDIT_COSTS
        assert OperationType.PRODUCT_SCRAPING in CREDIT_COSTS
        
        for op, cost in CREDIT_COSTS.items():
            assert isinstance(cost, int)
            assert cost >= 0

    def test_default_credit_packages(self):
        """Verifica pacotes de crédito padrão."""
        from api.services.accounting import DEFAULT_CREDIT_PACKAGES
        
        assert len(DEFAULT_CREDIT_PACKAGES) >= 4
        
        for pkg in DEFAULT_CREDIT_PACKAGES:
            assert "name" in pkg
            assert "slug" in pkg
            assert "credits" in pkg
            assert "price_brl" in pkg


# ============================================
# TEST ACCOUNTING SERVICE INITIALIZATION
# ============================================

class TestAccountingServiceInit:
    """Testes para inicialização do AccountingService."""

    def test_init_with_database(self, mock_db):
        """Inicializa com conexão Database."""
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        assert service.db == mock_db

    def test_init_with_async_session(self, mock_async_session):
        """Inicializa com AsyncSession."""
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_async_session)
        assert service.db == mock_async_session


# ============================================
# TEST CREDIT PACKAGES
# ============================================

class TestGetActivePackages:
    """Testes para get_active_packages."""

    @pytest.mark.asyncio
    async def test_returns_active_packages(self, mock_db):
        """Retorna pacotes ativos."""
        # Create a proper mock row with _mapping attribute
        mock_row = MagicMock()
        mock_row._mapping = {
            "id": str(uuid.uuid4()),
            "name": "Starter",
            "slug": "starter",
            "credits": 50,
            "price_brl": "9.90",
            "price_usd": None,
            "discount_percent": 0,
            "original_price": None,
            "description": "Test",
            "badge": None,
            "is_featured": False,
            "sort_order": 1,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        mock_row.__getitem__ = lambda self, key: self._mapping[key]
        
        mock_db.fetch_all = AsyncMock(return_value=[mock_row])
        
        from api.services.accounting import AccountingService
        service = AccountingService(mock_db)
        
        packages = await service.get_active_packages()
        
        assert len(packages) == 1
        mock_db.fetch_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculates_price_per_credit(self, mock_db):
        """Calcula preço por crédito."""
        mock_row = MagicMock()
        mock_row._mapping = {
            "id": str(uuid.uuid4()),
            "name": "Pro",
            "slug": "pro",
            "credits": 100,
            "price_brl": "20.00",
            "price_usd": None,
            "discount_percent": 0,
            "original_price": None,
            "description": "Test",
            "badge": None,
            "is_featured": False,
            "sort_order": 1,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        mock_row.__getitem__ = lambda self, key: self._mapping[key]
        
        mock_db.fetch_all = AsyncMock(return_value=[mock_row])
        
        from api.services.accounting import AccountingService
        service = AccountingService(mock_db)
        
        packages = await service.get_active_packages()
        
        assert len(packages) == 1
        assert packages[0].price_per_credit == Decimal("0.20")

    @pytest.mark.asyncio
    async def test_handles_zero_credits(self, mock_db):
        """Trata pacotes com zero créditos."""
        mock_row = MagicMock()
        mock_row._mapping = {
            "id": str(uuid.uuid4()),
            "name": "Free",
            "slug": "free",
            "credits": 0,
            "price_brl": "0.00",
            "price_usd": None,
            "discount_percent": 0,
            "original_price": None,
            "description": "Test",
            "badge": None,
            "is_featured": False,
            "sort_order": 1,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        mock_row.__getitem__ = lambda self, key: self._mapping[key]
        
        mock_db.fetch_all = AsyncMock(return_value=[mock_row])
        
        from api.services.accounting import AccountingService
        service = AccountingService(mock_db)
        
        packages = await service.get_active_packages()
        
        assert packages[0].price_per_credit == Decimal("0")


class TestGetPackageBySlug:
    """Testes para get_package_by_slug."""

    @pytest.mark.asyncio
    async def test_returns_package_when_found(self, mock_db):
        """Retorna pacote quando encontrado."""
        mock_row = MagicMock()
        mock_row._mapping = {
            "id": str(uuid.uuid4()),
            "name": "Starter",
            "slug": "starter",
            "credits": 50,
            "price_brl": "9.90",
            "price_usd": None,
            "discount_percent": 0,
            "original_price": None,
            "description": "Test",
            "badge": None,
            "is_featured": False,
            "sort_order": 1,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        mock_row.__getitem__ = lambda self, key: self._mapping[key]
        
        mock_db.fetch_one = AsyncMock(return_value=mock_row)
        
        from api.services.accounting import AccountingService
        service = AccountingService(mock_db)
        
        pkg = await service.get_package_by_slug("starter")
        
        assert pkg is not None
        assert pkg.slug == "starter"

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, mock_db):
        """Retorna None quando não encontrado."""
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        from api.services.accounting import AccountingService
        service = AccountingService(mock_db)
        
        pkg = await service.get_package_by_slug("nonexistent")
        
        assert pkg is None


# ============================================
# TEST COST CALCULATION
# ============================================

class TestCalculateOpenAICost:
    """Testes para calculate_openai_cost."""

    def test_calculates_gpt4_turbo_cost(self, mock_db):
        """Calcula custo do GPT-4 Turbo."""
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        
        result = service.calculate_openai_cost(
            model="gpt-4-turbo-preview",
            tokens_input=1000,
            tokens_output=500
        )
        
        assert "total_usd" in result
        assert "total_brl" in result
        assert result["total_usd"] > Decimal("0")
        assert result["total_brl"] > result["total_usd"]

    def test_calculates_gpt4o_mini_cost(self, mock_db):
        """Calcula custo do GPT-4o Mini (mais barato)."""
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        
        result = service.calculate_openai_cost(
            model="gpt-4o-mini",
            tokens_input=1000,
            tokens_output=500
        )
        
        assert result["total_usd"] > Decimal("0")
        # GPT-4o mini should be cheaper
        assert result["total_usd"] < Decimal("0.05")

    def test_uses_default_pricing_for_unknown_model(self, mock_db):
        """Usa preço padrão para modelo desconhecido."""
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        
        result = service.calculate_openai_cost(
            model="unknown-model",
            tokens_input=1000,
            tokens_output=500
        )
        
        # Should use gpt-4-turbo-preview pricing
        assert result["total_usd"] > Decimal("0")
        assert result["model"] == "unknown-model"

    def test_includes_token_counts(self, mock_db):
        """Inclui contagem de tokens no resultado."""
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        
        result = service.calculate_openai_cost(
            model="gpt-4o",
            tokens_input=1500,
            tokens_output=750
        )
        
        assert result["tokens_input"] == 1500
        assert result["tokens_output"] == 750

    def test_zero_tokens(self, mock_db):
        """Trata zero tokens."""
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        
        result = service.calculate_openai_cost(
            model="gpt-4o",
            tokens_input=0,
            tokens_output=0
        )
        
        assert result["total_usd"] == Decimal("0")


# ============================================
# TEST API USAGE LOGGING
# ============================================

class TestLogApiUsage:
    """Testes para log_api_usage."""

    @pytest.mark.asyncio
    async def test_logs_usage_with_cost(self, mock_db, sample_user_id):
        """Registra uso da API com custo."""
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        
        log = await service.log_api_usage(
            user_id=sample_user_id,
            provider="openai",
            model="gpt-4o",
            operation_type="copy_generation",
            tokens_input=1000,
            tokens_output=500,
            request_duration_ms=1500
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert log is not None

    @pytest.mark.asyncio
    async def test_logs_cached_request(self, mock_db, sample_user_id):
        """Registra requisição cacheada."""
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        
        await service.log_api_usage(
            user_id=sample_user_id,
            provider="openai",
            model="gpt-4o",
            operation_type="copy_generation",
            tokens_input=0,
            tokens_output=0,
            was_cached=True
        )
        
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_logs_with_metadata(self, mock_db, sample_user_id):
        """Registra com metadados."""
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        
        metadata = {"prompt_type": "product_description", "language": "pt-BR"}
        
        await service.log_api_usage(
            user_id=sample_user_id,
            provider="openai",
            model="gpt-4o",
            operation_type="copy_generation",
            tokens_input=500,
            tokens_output=200,
            metadata=metadata
        )
        
        mock_db.add.assert_called_once()


# ============================================
# TEST FINANCIAL TRANSACTIONS
# ============================================

class TestRecordCreditPurchase:
    """Testes para record_credit_purchase."""

    @pytest.mark.asyncio
    async def test_records_purchase(self, mock_db, sample_user_id, sample_package_id):
        """Registra compra de créditos."""
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        
        # Mock _update_user_financial_summary
        with patch.object(service, '_update_user_financial_summary', new_callable=AsyncMock):
            tx = await service.record_credit_purchase(
                user_id=sample_user_id,
                package_id=sample_package_id,
                amount_brl=Decimal("24.90"),
                credits=150,
                payment_id="payment-123",
                payment_method="pix"
            )
            
            mock_db.add.assert_called()
            mock_db.commit.assert_called()
            assert tx is not None

    @pytest.mark.asyncio
    async def test_calculates_fees(self, mock_db, sample_user_id, sample_package_id):
        """Calcula taxas de pagamento."""
        from api.services.accounting import MP_FEE_PERCENT, AccountingService
        
        service = AccountingService(mock_db)
        
        amount = Decimal("100.00")
        expected_fee = amount * MP_FEE_PERCENT / 100
        
        with patch.object(service, '_update_user_financial_summary', new_callable=AsyncMock):
            tx = await service.record_credit_purchase(
                user_id=sample_user_id,
                package_id=sample_package_id,
                amount_brl=amount,
                credits=100,
                payment_id="payment-123",
                payment_method="credit_card"
            )
            
            assert tx.cost_brl == expected_fee


class TestRecordCreditUsage:
    """Testes para record_credit_usage."""

    @pytest.mark.asyncio
    async def test_records_usage(self, mock_db, sample_user_id):
        """Registra uso de créditos."""
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        
        tx = await service.record_credit_usage(
            user_id=sample_user_id,
            operation_type="copy_generation",
            credits_used=2,
            cost_brl=Decimal("0.05"),
            tokens_input=500,
            tokens_output=200
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert tx.credits_amount == -2  # Negative for consumption

    @pytest.mark.asyncio
    async def test_records_with_metadata(self, mock_db, sample_user_id):
        """Registra uso com metadados."""
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        
        await service.record_credit_usage(
            user_id=sample_user_id,
            operation_type="trend_analysis",
            credits_used=5,
            metadata={"source": "tiktok", "category": "fashion"}
        )
        
        mock_db.add.assert_called_once()


class TestRecordLicensePurchase:
    """Testes para record_license_purchase."""

    @pytest.mark.asyncio
    async def test_records_license(self, mock_db, sample_user_id):
        """Registra compra de licença."""
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        
        tx = await service.record_license_purchase(
            user_id=sample_user_id,
            amount_brl=Decimal("297.00"),
            payment_id="license-payment-123",
            payment_method="pix"
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert "Licença" in tx.description


# ============================================
# TEST USER FINANCIAL SUMMARY
# ============================================

class TestUpdateUserFinancialSummary:
    """Testes para _update_user_financial_summary."""

    @pytest.mark.asyncio
    async def test_creates_new_summary(self, mock_async_session, sample_user_id):
        """Cria novo resumo financeiro."""
        from api.services.accounting import AccountingService

        # Mock execute to return no existing summary
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_async_session.execute = AsyncMock(return_value=mock_result)
        
        service = AccountingService(mock_async_session)
        
        await service._update_user_financial_summary(
            user_id=sample_user_id,
            amount_spent=Decimal("50.00"),
            credits_purchased=100
        )
        
        mock_async_session.add.assert_called_once()
        mock_async_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_existing_summary(self, mock_async_session, sample_user_id):
        """Atualiza resumo existente."""
        from api.services.accounting import AccountingService

        # Create mock existing summary
        existing_summary = MagicMock()
        existing_summary.total_spent = Decimal("100.00")
        existing_summary.total_credits_purchased = 200
        existing_summary.purchase_count = 2
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=existing_summary)
        mock_async_session.execute = AsyncMock(return_value=mock_result)
        
        service = AccountingService(mock_async_session)
        
        await service._update_user_financial_summary(
            user_id=sample_user_id,
            amount_spent=Decimal("50.00"),
            credits_purchased=100
        )
        
        assert existing_summary.total_spent == Decimal("150.00")
        assert existing_summary.total_credits_purchased == 300
        assert existing_summary.purchase_count == 3


# ============================================
# TEST DASHBOARD METRICS
# ============================================

class TestGetDashboardMetrics:
    """Testes para get_dashboard_metrics."""

    @pytest.mark.asyncio
    async def test_returns_metrics_structure(self, mock_db):
        """Retorna estrutura de métricas."""
        mock_db.fetch_one = AsyncMock(return_value={"total": 0})
        
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        
        metrics = await service.get_dashboard_metrics(days=30)
        
        assert "period_days" in metrics
        assert "total_revenue" in metrics
        assert "total_costs" in metrics
        assert "gross_profit" in metrics
        assert "credits_sold" in metrics
        assert "credits_consumed" in metrics

    @pytest.mark.asyncio
    async def test_calculates_profit_margin(self, mock_db):
        """Calcula margem de lucro."""
        # Mock revenue = 100, costs = 20, openai = 10
        async def mock_fetch_one(query, params=None):
            if "SUM(amount_brl)" in query:
                return {"total": 100}
            elif "SUM(cost_brl)" in query and "api_usage_logs" not in query:
                return {"total": 20}
            elif "api_usage_logs" in query:
                return {"total": 10}
            elif "COUNT(*)" in query:
                return {"total": 10}
            elif "credits_amount" in query:
                if "credit_purchase" in str(params):
                    return {"total": 500}
                return {"total": 300}
            return {"total": 0}
        
        mock_db.fetch_one = AsyncMock(side_effect=mock_fetch_one)
        
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        
        metrics = await service.get_dashboard_metrics(days=30)
        
        # gross_profit = 100 - 20 - 10 = 70
        # margin = 70 / 100 * 100 = 70%
        assert metrics["gross_profit"] == 70.0
        assert metrics["profit_margin_percent"] == 70.0

    @pytest.mark.asyncio
    async def test_handles_zero_revenue(self, mock_db):
        """Trata receita zero."""
        mock_db.fetch_one = AsyncMock(return_value={"total": 0})
        
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        
        metrics = await service.get_dashboard_metrics(days=30)
        
        assert metrics["profit_margin_percent"] == 0.0

    @pytest.mark.asyncio
    async def test_uses_custom_days(self, mock_db):
        """Usa período customizado."""
        mock_db.fetch_one = AsyncMock(return_value={"total": 0})
        
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        
        metrics = await service.get_dashboard_metrics(days=7)
        
        assert metrics["period_days"] == 7


# ============================================
# TEST OPERATION TYPES
# ============================================

class TestOperationTypes:
    """Testes para OperationType enum."""

    def test_all_operation_types_exist(self):
        """Verifica que todos os tipos de operação existem."""
        from api.database.accounting_models import OperationType
        
        assert OperationType.COPY_GENERATION
        assert OperationType.TREND_ANALYSIS
        assert OperationType.NICHE_REPORT
        assert OperationType.PRODUCT_SCRAPING
        assert OperationType.AI_CHAT
        assert OperationType.IMAGE_GENERATION


class TestTransactionTypes:
    """Testes para TransactionType enum."""

    def test_transaction_types_exist(self):
        """Verifica que tipos de transação existem."""
        from api.database.accounting_models import TransactionType
        
        assert TransactionType.CREDIT_PURCHASE
        assert TransactionType.CREDIT_USAGE
        assert TransactionType.LICENSE_PURCHASE


class TestPaymentStatus:
    """Testes para PaymentStatus enum."""

    def test_payment_statuses_exist(self):
        """Verifica que status de pagamento existem."""
        from api.database.accounting_models import PaymentStatus
        
        assert PaymentStatus.APPROVED
        assert PaymentStatus.PENDING
        assert PaymentStatus.REJECTED
