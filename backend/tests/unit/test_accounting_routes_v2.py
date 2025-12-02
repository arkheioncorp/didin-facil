"""
Testes para Accounting Routes (Admin Dashboard)
================================================
Cobertura completa para api/routes/accounting.py
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from io import BytesIO, StringIO
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

# ==================== FIXTURES ====================

@pytest.fixture
def mock_admin_user():
    """Mock de usuário admin."""
    return {
        "id": str(uuid4()),
        "email": "admin@test.com",
        "name": "Admin User",
        "is_admin": True,
    }


@pytest.fixture
def mock_db():
    """Mock do database."""
    db = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_accounting_service():
    """Mock do AccountingService."""
    service = MagicMock()
    service.get_dashboard_metrics = AsyncMock(return_value={
        "period_days": 30,
        "total_revenue": 15000.0,
        "total_costs": 3000.0,
        "openai_costs": 2500.0,
        "gross_profit": 12000.0,
        "profit_margin_percent": 80.0,
        "credits_sold": 5000,
        "credits_consumed": 4500,
        "transactions_count": 150,
        "avg_transaction_value": 100.0,
    })
    service.get_revenue_by_day = AsyncMock(return_value=[
        {"date": "2025-12-01", "revenue": 500.0, "costs": 100.0,
         "profit": 400.0, "transactions": 5},
        {"date": "2025-12-02", "revenue": 600.0, "costs": 120.0,
         "profit": 480.0, "transactions": 6},
    ])
    service.get_operations_breakdown = AsyncMock(return_value={
        "copy_generation": 100,
        "trend_analysis": 50,
        "niche_report": 30,
        "ai_chat": 200,
        "image_generation": 20,
    })
    service.get_top_users = AsyncMock(return_value=[
        {
            "user_id": str(uuid4()),
            "total_spent": 500.0,
            "credits_purchased": 1000,
            "credits_used": 900,
            "purchase_count": 5,
            "lifetime_profit": 400.0,
        }
    ])
    service.get_package_sales_stats = AsyncMock(return_value=[
        {"name": "Starter", "slug": "starter", "sales": 50,
         "revenue": 2500.0, "credits": 5000},
        {"name": "Pro", "slug": "pro", "sales": 30,
         "revenue": 6000.0, "credits": 9000},
    ])
    service.get_active_packages = AsyncMock(return_value=[])
    service.generate_daily_report = AsyncMock()
    return service


# ==================== SCHEMAS TESTS ====================

class TestSchemas:
    """Testes dos modelos Pydantic."""

    def test_dashboard_metrics_schema(self):
        """Testa schema DashboardMetrics."""
        from api.routes.accounting import DashboardMetrics

        metrics = DashboardMetrics(
            period_days=30,
            total_revenue=15000.0,
            total_costs=3000.0,
            openai_costs=2500.0,
            gross_profit=12000.0,
            profit_margin_percent=80.0,
            credits_sold=5000,
            credits_consumed=4500,
            transactions_count=150,
            avg_transaction_value=100.0,
        )

        assert metrics.period_days == 30
        assert metrics.total_revenue == 15000.0
        assert metrics.profit_margin_percent == 80.0

    def test_daily_revenue_item_schema(self):
        """Testa schema DailyRevenueItem."""
        from api.routes.accounting import DailyRevenueItem

        item = DailyRevenueItem(
            date="2025-12-01",
            revenue=500.0,
            costs=100.0,
            profit=400.0,
            transactions=5,
        )

        assert item.date == "2025-12-01"
        assert item.profit == 400.0

    def test_operations_breakdown_schema(self):
        """Testa schema OperationsBreakdown."""
        from api.routes.accounting import OperationsBreakdown

        ops = OperationsBreakdown(
            copy_generation=100,
            trend_analysis=50,
            ai_chat=200,
        )

        assert ops.copy_generation == 100
        assert ops.niche_report == 0  # Default value

    def test_top_user_schema(self):
        """Testa schema TopUser."""
        from api.routes.accounting import TopUser

        user = TopUser(
            user_id=str(uuid4()),
            total_spent=500.0,
            credits_purchased=1000,
            credits_used=900,
            purchase_count=5,
            lifetime_profit=400.0,
        )

        assert user.total_spent == 500.0
        assert user.credits_purchased == 1000

    def test_package_sales_schema(self):
        """Testa schema PackageSales."""
        from api.routes.accounting import PackageSales

        pkg = PackageSales(
            name="Pro",
            slug="pro",
            sales=30,
            revenue=6000.0,
            credits=9000,
        )

        assert pkg.name == "Pro"
        assert pkg.revenue == 6000.0

    def test_credit_package_response_schema(self):
        """Testa schema CreditPackageResponse."""
        from api.routes.accounting import CreditPackageResponse

        pkg = CreditPackageResponse(
            id=str(uuid4()),
            name="Starter Pack",
            slug="starter",
            credits=100,
            price_brl=49.90,
            price_per_credit=0.499,
            original_price=59.90,
            discount_percent=17,
            description="Great for beginners",
            badge="Popular",
            is_featured=True,
        )

        assert pkg.credits == 100
        assert pkg.is_featured is True

    def test_credit_package_response_optional_fields(self):
        """Testa campos opcionais do CreditPackageResponse."""
        from api.routes.accounting import CreditPackageResponse

        pkg = CreditPackageResponse(
            id=str(uuid4()),
            name="Basic",
            slug="basic",
            credits=50,
            price_brl=29.90,
            price_per_credit=0.598,
            original_price=None,
            discount_percent=0,
            description=None,
            badge=None,
            is_featured=False,
        )

        assert pkg.original_price is None
        assert pkg.badge is None

    def test_financial_summary_schema(self):
        """Testa schema FinancialSummary."""
        from api.routes.accounting import (DailyRevenueItem, DashboardMetrics,
                                           FinancialSummary,
                                           OperationsBreakdown, PackageSales,
                                           TopUser)

        summary = FinancialSummary(
            metrics=DashboardMetrics(
                period_days=30,
                total_revenue=15000.0,
                total_costs=3000.0,
                openai_costs=2500.0,
                gross_profit=12000.0,
                profit_margin_percent=80.0,
                credits_sold=5000,
                credits_consumed=4500,
                transactions_count=150,
                avg_transaction_value=100.0,
            ),
            revenue_by_day=[],
            operations_breakdown=OperationsBreakdown(),
            top_users=[],
            package_sales=[],
        )

        assert summary.metrics.total_revenue == 15000.0


# ==================== DASHBOARD ENDPOINTS TESTS ====================

class TestDashboardEndpoints:
    """Testes dos endpoints de dashboard."""

    @pytest.mark.asyncio
    async def test_get_dashboard_metrics(
        self, mock_admin_user, mock_db, mock_accounting_service
    ):
        """Testa endpoint de métricas do dashboard."""
        with patch("api.routes.accounting.require_admin",
                   return_value=mock_admin_user), \
             patch("api.routes.accounting.get_db", return_value=mock_db), \
             patch("api.routes.accounting.AccountingService",
                   return_value=mock_accounting_service):
            from api.routes.accounting import get_dashboard_metrics

            result = await get_dashboard_metrics(
                days=30,
                current_user=mock_admin_user,
                db=mock_db
            )

            assert result.period_days == 30
            assert result.total_revenue == 15000.0
            mock_accounting_service.get_dashboard_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_daily_revenue(
        self, mock_admin_user, mock_db, mock_accounting_service
    ):
        """Testa endpoint de receita diária."""
        with patch("api.routes.accounting.require_admin",
                   return_value=mock_admin_user), \
             patch("api.routes.accounting.get_db", return_value=mock_db), \
             patch("api.routes.accounting.AccountingService",
                   return_value=mock_accounting_service):
            from api.routes.accounting import get_daily_revenue

            result = await get_daily_revenue(
                days=30,
                current_user=mock_admin_user,
                db=mock_db
            )

            assert len(result) == 2
            assert result[0].revenue == 500.0

    @pytest.mark.asyncio
    async def test_get_operations_breakdown(
        self, mock_admin_user, mock_db, mock_accounting_service
    ):
        """Testa endpoint de breakdown de operações."""
        with patch("api.routes.accounting.require_admin",
                   return_value=mock_admin_user), \
             patch("api.routes.accounting.get_db", return_value=mock_db), \
             patch("api.routes.accounting.AccountingService",
                   return_value=mock_accounting_service):
            from api.routes.accounting import get_operations_breakdown

            result = await get_operations_breakdown(
                days=30,
                current_user=mock_admin_user,
                db=mock_db
            )

            assert result.copy_generation == 100
            assert result.ai_chat == 200

    @pytest.mark.asyncio
    async def test_get_top_users(
        self, mock_admin_user, mock_db, mock_accounting_service
    ):
        """Testa endpoint de top usuários."""
        with patch("api.routes.accounting.require_admin",
                   return_value=mock_admin_user), \
             patch("api.routes.accounting.get_db", return_value=mock_db), \
             patch("api.routes.accounting.AccountingService",
                   return_value=mock_accounting_service):
            from api.routes.accounting import get_top_users

            result = await get_top_users(
                limit=10,
                current_user=mock_admin_user,
                db=mock_db
            )

            assert len(result) == 1
            assert result[0].total_spent == 500.0

    @pytest.mark.asyncio
    async def test_get_package_sales(
        self, mock_admin_user, mock_db, mock_accounting_service
    ):
        """Testa endpoint de vendas por pacote."""
        with patch("api.routes.accounting.require_admin",
                   return_value=mock_admin_user), \
             patch("api.routes.accounting.get_db", return_value=mock_db), \
             patch("api.routes.accounting.AccountingService",
                   return_value=mock_accounting_service):
            from api.routes.accounting import get_package_sales

            result = await get_package_sales(
                days=30,
                current_user=mock_admin_user,
                db=mock_db
            )

            assert len(result) == 2
            assert result[0].name == "Starter"

    @pytest.mark.asyncio
    async def test_get_financial_summary(
        self, mock_admin_user, mock_db, mock_accounting_service
    ):
        """Testa endpoint de resumo financeiro completo."""
        with patch("api.routes.accounting.require_admin",
                   return_value=mock_admin_user), \
             patch("api.routes.accounting.get_db", return_value=mock_db), \
             patch("api.routes.accounting.AccountingService",
                   return_value=mock_accounting_service):
            from api.routes.accounting import get_financial_summary

            result = await get_financial_summary(
                days=30,
                current_user=mock_admin_user,
                db=mock_db
            )

            assert result.metrics.total_revenue == 15000.0
            assert len(result.revenue_by_day) == 2
            assert result.operations_breakdown.copy_generation == 100


# ==================== PACKAGES ENDPOINTS TESTS ====================

class TestPackagesEndpoints:
    """Testes dos endpoints de pacotes."""

    @pytest.mark.asyncio
    async def test_list_credit_packages_empty(self, mock_db):
        """Testa listagem vazia de pacotes."""
        mock_service = MagicMock()
        mock_service.get_active_packages = AsyncMock(return_value=[])

        with patch("api.routes.accounting.get_db", return_value=mock_db), \
             patch("api.routes.accounting.AccountingService",
                   return_value=mock_service):
            from api.routes.accounting import list_credit_packages

            result = await list_credit_packages(db=mock_db)

            assert result == []

    @pytest.mark.asyncio
    async def test_list_credit_packages_with_data(self, mock_db):
        """Testa listagem de pacotes com dados."""
        mock_package = MagicMock()
        mock_package.id = uuid4()
        mock_package.name = "Pro Pack"
        mock_package.slug = "pro"
        mock_package.credits = 500
        mock_package.price_brl = Decimal("199.90")
        mock_package.price_per_credit = Decimal("0.40")
        mock_package.original_price = Decimal("249.90")
        mock_package.discount_percent = 20
        mock_package.description = "For professionals"
        mock_package.badge = "Best Value"
        mock_package.is_featured = True

        mock_service = MagicMock()
        mock_service.get_active_packages = AsyncMock(
            return_value=[mock_package]
        )

        with patch("api.routes.accounting.get_db", return_value=mock_db), \
             patch("api.routes.accounting.AccountingService",
                   return_value=mock_service):
            from api.routes.accounting import list_credit_packages

            result = await list_credit_packages(db=mock_db)

            assert len(result) == 1
            assert result[0].name == "Pro Pack"
            assert result[0].credits == 500
            assert result[0].is_featured is True


# ==================== REPORTS ENDPOINTS TESTS ====================

class TestReportsEndpoints:
    """Testes dos endpoints de relatórios."""

    @pytest.mark.asyncio
    async def test_generate_daily_report(
        self, mock_admin_user, mock_db
    ):
        """Testa geração de relatório diário."""
        mock_report = MagicMock()
        mock_report.report_date = datetime.now(timezone.utc).date()
        mock_report.total_revenue = Decimal("1500.00")
        mock_report.gross_profit = Decimal("1200.00")

        mock_service = MagicMock()
        mock_service.generate_daily_report = AsyncMock(
            return_value=mock_report
        )

        with patch("api.routes.accounting.require_admin",
                   return_value=mock_admin_user), \
             patch("api.routes.accounting.get_db", return_value=mock_db), \
             patch("api.routes.accounting.AccountingService",
                   return_value=mock_service):
            from api.routes.accounting import generate_daily_report

            result = await generate_daily_report(
                date=None,
                current_user=mock_admin_user,
                db=mock_db
            )

            assert result["success"] is True
            assert result["total_revenue"] == 1500.0

    @pytest.mark.asyncio
    async def test_generate_daily_report_with_date(
        self, mock_admin_user, mock_db
    ):
        """Testa geração de relatório diário com data específica."""
        target_date = datetime(2025, 11, 15, tzinfo=timezone.utc)
        mock_report = MagicMock()
        mock_report.report_date = target_date.date()
        mock_report.total_revenue = Decimal("2000.00")
        mock_report.gross_profit = Decimal("1600.00")

        mock_service = MagicMock()
        mock_service.generate_daily_report = AsyncMock(
            return_value=mock_report
        )

        with patch("api.routes.accounting.require_admin",
                   return_value=mock_admin_user), \
             patch("api.routes.accounting.get_db", return_value=mock_db), \
             patch("api.routes.accounting.AccountingService",
                   return_value=mock_service):
            from api.routes.accounting import generate_daily_report

            result = await generate_daily_report(
                date=target_date,
                current_user=mock_admin_user,
                db=mock_db
            )

            assert result["success"] is True
            mock_service.generate_daily_report.assert_called_with(target_date)

    def test_export_route_exists(self):
        """Testa que rota de export existe."""
        from api.routes.accounting import router

        # Verifica que a rota existe (sem executar)
        route_paths = []
        for route in router.routes:
            if hasattr(route, 'path'):
                route_paths.append(route.path)
        
        assert "/reports/export" in route_paths


# ==================== COST TRACKING ENDPOINTS TESTS ====================

class TestCostTrackingEndpoints:
    """Testes dos endpoints de tracking de custos."""

    @pytest.mark.asyncio
    async def test_get_openai_costs(self, mock_admin_user, mock_db):
        """Testa endpoint de custos OpenAI."""
        mock_row = MagicMock()
        mock_row.total_cost = Decimal("250.00")
        mock_row.total_input = 1000000
        mock_row.total_output = 500000
        mock_row.request_count = 5000
        mock_row.avg_duration = 450.5

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("api.routes.accounting.require_admin",
                   return_value=mock_admin_user), \
             patch("api.routes.accounting.get_db", return_value=mock_db):
            from api.routes.accounting import get_openai_costs

            result = await get_openai_costs(
                days=30,
                current_user=mock_admin_user,
                db=mock_db
            )

            assert result["period_days"] == 30
            assert result["total_cost_brl"] == 250.0
            assert result["request_count"] == 5000

    @pytest.mark.asyncio
    async def test_get_openai_costs_empty(self, mock_admin_user, mock_db):
        """Testa endpoint de custos OpenAI sem dados."""
        mock_row = MagicMock()
        mock_row.total_cost = None
        mock_row.total_input = None
        mock_row.total_output = None
        mock_row.request_count = None
        mock_row.avg_duration = None

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("api.routes.accounting.require_admin",
                   return_value=mock_admin_user), \
             patch("api.routes.accounting.get_db", return_value=mock_db):
            from api.routes.accounting import get_openai_costs

            result = await get_openai_costs(
                days=30,
                current_user=mock_admin_user,
                db=mock_db
            )

            assert result["total_cost_brl"] == 0
            assert result["request_count"] == 0

    @pytest.mark.asyncio
    async def test_get_costs_by_operation(self, mock_admin_user, mock_db):
        """Testa endpoint de custos por operação."""
        mock_rows = [
            MagicMock(
                operation_type="copy_generation",
                cost=Decimal("100.00"),
                count=1000,
                tokens=500000
            ),
            MagicMock(
                operation_type="chat",
                cost=Decimal("150.00"),
                count=2000,
                tokens=800000
            ),
        ]

        mock_result = MagicMock()
        mock_result.fetchall.return_value = mock_rows
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("api.routes.accounting.require_admin",
                   return_value=mock_admin_user), \
             patch("api.routes.accounting.get_db", return_value=mock_db):
            from api.routes.accounting import get_costs_by_operation

            result = await get_costs_by_operation(
                days=30,
                current_user=mock_admin_user,
                db=mock_db
            )

            assert len(result) == 2
            assert result[0]["operation"] == "copy_generation"
            assert result[0]["cost_brl"] == 100.0

    @pytest.mark.asyncio
    async def test_get_costs_by_operation_empty(
        self, mock_admin_user, mock_db
    ):
        """Testa endpoint de custos por operação vazio."""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("api.routes.accounting.require_admin",
                   return_value=mock_admin_user), \
             patch("api.routes.accounting.get_db", return_value=mock_db):
            from api.routes.accounting import get_costs_by_operation

            result = await get_costs_by_operation(
                days=7,
                current_user=mock_admin_user,
                db=mock_db
            )

            assert result == []


# ==================== EDGE CASES ====================

class TestEdgeCases:
    """Testes de casos extremos."""

    @pytest.mark.asyncio
    async def test_dashboard_metrics_with_different_periods(
        self, mock_admin_user, mock_db, mock_accounting_service
    ):
        """Testa métricas com diferentes períodos."""
        with patch("api.routes.accounting.require_admin",
                   return_value=mock_admin_user), \
             patch("api.routes.accounting.get_db", return_value=mock_db), \
             patch("api.routes.accounting.AccountingService",
                   return_value=mock_accounting_service):
            from api.routes.accounting import get_dashboard_metrics

            # 7 dias
            result = await get_dashboard_metrics(
                days=7,
                current_user=mock_admin_user,
                db=mock_db
            )
            assert result is not None

            # 365 dias
            result = await get_dashboard_metrics(
                days=365,
                current_user=mock_admin_user,
                db=mock_db
            )
            assert result is not None

    @pytest.mark.asyncio
    async def test_top_users_with_different_limits(
        self, mock_admin_user, mock_db, mock_accounting_service
    ):
        """Testa top users com diferentes limites."""
        with patch("api.routes.accounting.require_admin",
                   return_value=mock_admin_user), \
             patch("api.routes.accounting.get_db", return_value=mock_db), \
             patch("api.routes.accounting.AccountingService",
                   return_value=mock_accounting_service):
            from api.routes.accounting import get_top_users

            # Limite mínimo
            result = await get_top_users(
                limit=1,
                current_user=mock_admin_user,
                db=mock_db
            )
            assert result is not None

            # Limite máximo
            result = await get_top_users(
                limit=100,
                current_user=mock_admin_user,
                db=mock_db
            )
            assert result is not None

    @pytest.mark.asyncio
    async def test_package_with_null_optional_fields(self, mock_db):
        """Testa pacote com campos opcionais nulos."""
        mock_package = MagicMock()
        mock_package.id = uuid4()
        mock_package.name = "Basic"
        mock_package.slug = "basic"
        mock_package.credits = 50
        mock_package.price_brl = Decimal("29.90")
        mock_package.price_per_credit = Decimal("0.598")
        mock_package.original_price = None  # Sem preço original
        mock_package.discount_percent = None  # Sem desconto
        mock_package.description = None
        mock_package.badge = None
        mock_package.is_featured = False

        mock_service = MagicMock()
        mock_service.get_active_packages = AsyncMock(
            return_value=[mock_package]
        )

        with patch("api.routes.accounting.get_db", return_value=mock_db), \
             patch("api.routes.accounting.AccountingService",
                   return_value=mock_service):
            from api.routes.accounting import list_credit_packages

            result = await list_credit_packages(db=mock_db)

            assert len(result) == 1
            assert result[0].original_price is None
            assert result[0].discount_percent == 0
