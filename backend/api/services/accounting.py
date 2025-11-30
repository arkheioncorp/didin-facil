"""
Accounting Service
Complete financial tracking and reporting for Didin Fácil
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from api.database.accounting_models import (
    CreditPackage, OperationCost, FinancialTransaction,
    DailyFinancialReport, MonthlyFinancialSummary,
    UserFinancialSummary, APIUsageLog,
    TransactionType, OperationType, PaymentStatus
)


# =============================================================================
# PRICING CONSTANTS
# =============================================================================

# OpenAI Pricing (as of Nov 2025) - USD per 1K tokens
OPENAI_PRICING = {
    "gpt-4-turbo-preview": {
        "input": Decimal("0.01"),   # $0.01 per 1K input tokens
        "output": Decimal("0.03"),  # $0.03 per 1K output tokens
    },
    "gpt-4o": {
        "input": Decimal("0.005"),
        "output": Decimal("0.015"),
    },
    "gpt-4o-mini": {
        "input": Decimal("0.00015"),
        "output": Decimal("0.0006"),
    },
    "gpt-3.5-turbo": {
        "input": Decimal("0.0005"),
        "output": Decimal("0.0015"),
    },
}

# USD to BRL conversion (update periodically)
USD_TO_BRL = Decimal("5.70")

# MercadoPago fees
MP_FEE_PERCENT = Decimal("4.99")  # 4.99% per transaction
MP_FEE_FIXED = Decimal("0.00")    # Fixed fee per transaction

# Credit costs (in credits)
CREDIT_COSTS = {
    OperationType.COPY_GENERATION: 1,
    OperationType.TREND_ANALYSIS: 2,
    OperationType.NICHE_REPORT: 5,
    OperationType.PRODUCT_SCRAPING: 0,  # Free
    OperationType.AI_CHAT: 1,
    OperationType.IMAGE_GENERATION: 3,
}

# Default credit packages
DEFAULT_CREDIT_PACKAGES = [
    {
        "name": "Iniciante",
        "slug": "starter",
        "credits": 50,
        "price_brl": Decimal("9.90"),
        "description": "Ideal para começar a testar",
        "badge": None,
        "is_featured": False,
        "sort_order": 1,
    },
    {
        "name": "Popular",
        "slug": "pro",
        "credits": 150,
        "price_brl": Decimal("24.90"),
        "original_price": Decimal("29.70"),
        "discount_percent": 16,
        "description": "O mais escolhido pelos usuários",
        "badge": "Mais Popular",
        "is_featured": True,
        "sort_order": 2,
    },
    {
        "name": "Profissional",
        "slug": "ultra",
        "credits": 500,
        "price_brl": Decimal("69.90"),
        "original_price": Decimal("99.50"),
        "discount_percent": 30,
        "description": "Máxima economia para uso intenso",
        "badge": "Melhor Valor",
        "is_featured": False,
        "sort_order": 3,
    },
    {
        "name": "Enterprise",
        "slug": "enterprise",
        "credits": 2000,
        "price_brl": Decimal("199.90"),
        "original_price": Decimal("398.00"),
        "discount_percent": 50,
        "description": "Para equipes e agências",
        "badge": "50% OFF",
        "is_featured": False,
        "sort_order": 4,
    },
]


class AccountingService:
    """Complete financial tracking service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # CREDIT PACKAGES
    # =========================================================================

    async def get_active_packages(self) -> List[CreditPackage]:
        """Get all active credit packages for purchase"""
        result = await self.db.execute(
            select(CreditPackage)
            .where(CreditPackage.is_active == True)
            .order_by(CreditPackage.sort_order)
        )
        return result.scalars().all()

    async def get_package_by_slug(self, slug: str) -> Optional[CreditPackage]:
        """Get a specific package by slug"""
        result = await self.db.execute(
            select(CreditPackage).where(CreditPackage.slug == slug)
        )
        return result.scalar_one_or_none()

    async def seed_default_packages(self):
        """Seed default credit packages if none exist"""
        existing = await self.db.execute(select(func.count(CreditPackage.id)))
        count = existing.scalar()
        
        if count == 0:
            for pkg_data in DEFAULT_CREDIT_PACKAGES:
                package = CreditPackage(
                    id=uuid.uuid4(),
                    **pkg_data
                )
                self.db.add(package)
            await self.db.commit()

    # =========================================================================
    # COST TRACKING
    # =========================================================================

    def calculate_openai_cost(
        self,
        model: str,
        tokens_input: int,
        tokens_output: int
    ) -> Dict[str, Decimal]:
        """Calculate OpenAI API cost for a request"""
        pricing = OPENAI_PRICING.get(model, OPENAI_PRICING["gpt-4-turbo-preview"])
        
        cost_input_usd = (Decimal(tokens_input) / 1000) * pricing["input"]
        cost_output_usd = (Decimal(tokens_output) / 1000) * pricing["output"]
        total_usd = cost_input_usd + cost_output_usd
        total_brl = total_usd * USD_TO_BRL
        
        return {
            "cost_input_usd": cost_input_usd,
            "cost_output_usd": cost_output_usd,
            "total_usd": total_usd,
            "total_brl": total_brl,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "model": model,
        }

    async def log_api_usage(
        self,
        user_id: str,
        provider: str,
        model: str,
        operation_type: str,
        tokens_input: int,
        tokens_output: int,
        request_duration_ms: int = 0,
        was_cached: bool = False,
        metadata: dict = None
    ) -> APIUsageLog:
        """Log API usage with cost calculation"""
        costs = self.calculate_openai_cost(model, tokens_input, tokens_output)
        
        log = APIUsageLog(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id) if user_id else None,
            provider=provider,
            model=model,
            operation_type=operation_type,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_total=tokens_input + tokens_output,
            cost_usd=costs["total_usd"],
            cost_brl=costs["total_brl"],
            request_duration_ms=request_duration_ms,
            was_cached=was_cached,
            metadata=metadata or {},
        )
        
        self.db.add(log)
        await self.db.commit()
        
        return log

    # =========================================================================
    # FINANCIAL TRANSACTIONS
    # =========================================================================

    async def record_credit_purchase(
        self,
        user_id: str,
        package_id: str,
        amount_brl: Decimal,
        credits: int,
        payment_id: str,
        payment_method: str,
    ) -> FinancialTransaction:
        """Record a credit purchase transaction"""
        # Calculate payment fees
        payment_fees = (amount_brl * MP_FEE_PERCENT / 100) + MP_FEE_FIXED
        gross_profit = amount_brl - payment_fees
        
        transaction = FinancialTransaction(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            transaction_type=TransactionType.CREDIT_PURCHASE.value,
            amount_brl=amount_brl,
            credits_amount=credits,
            cost_brl=payment_fees,
            gross_profit=gross_profit,
            payment_id=payment_id,
            payment_method=payment_method,
            payment_status=PaymentStatus.APPROVED.value,
            package_id=uuid.UUID(package_id),
            description=f"Compra de {credits} créditos",
        )
        
        self.db.add(transaction)
        await self.db.commit()
        
        # Update user financial summary
        await self._update_user_financial_summary(user_id, amount_brl, credits)
        
        return transaction

    async def record_credit_usage(
        self,
        user_id: str,
        operation_type: str,
        credits_used: int,
        cost_brl: Decimal = Decimal("0"),
        tokens_input: int = 0,
        tokens_output: int = 0,
        metadata: dict = None
    ) -> FinancialTransaction:
        """Record credit consumption"""
        transaction = FinancialTransaction(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            transaction_type=TransactionType.CREDIT_USAGE.value,
            operation_type=operation_type,
            amount_brl=Decimal("0"),  # No revenue, just consumption
            credits_amount=-credits_used,  # Negative for consumption
            cost_brl=cost_brl,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            gross_profit=-cost_brl,  # Negative = cost
            description=f"Uso de {credits_used} crédito(s) - {operation_type}",
            metadata=metadata or {},
        )
        
        self.db.add(transaction)
        await self.db.commit()
        
        return transaction

    async def record_license_purchase(
        self,
        user_id: str,
        amount_brl: Decimal,
        payment_id: str,
        payment_method: str,
    ) -> FinancialTransaction:
        """Record a license purchase transaction"""
        payment_fees = (amount_brl * MP_FEE_PERCENT / 100) + MP_FEE_FIXED
        gross_profit = amount_brl - payment_fees
        
        transaction = FinancialTransaction(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            transaction_type=TransactionType.LICENSE_PURCHASE.value,
            amount_brl=amount_brl,
            cost_brl=payment_fees,
            gross_profit=gross_profit,
            payment_id=payment_id,
            payment_method=payment_method,
            payment_status=PaymentStatus.APPROVED.value,
            description="Licença Vitalícia TikTrend Finder",
        )
        
        self.db.add(transaction)
        await self.db.commit()
        
        return transaction

    async def _update_user_financial_summary(
        self,
        user_id: str,
        amount_spent: Decimal,
        credits_purchased: int
    ):
        """Update user's financial summary after purchase"""
        user_uuid = uuid.UUID(user_id)
        
        result = await self.db.execute(
            select(UserFinancialSummary).where(
                UserFinancialSummary.user_id == user_uuid
            )
        )
        summary = result.scalar_one_or_none()
        
        now = datetime.now(timezone.utc)
        
        if summary:
            summary.total_spent += amount_spent
            summary.total_credits_purchased += credits_purchased
            summary.last_purchase_at = now
            summary.purchase_count += 1
            summary.avg_purchase_value = summary.total_spent / summary.purchase_count
            summary.avg_credits_per_purchase = summary.total_credits_purchased // summary.purchase_count
            summary.updated_at = now
        else:
            summary = UserFinancialSummary(
                id=uuid.uuid4(),
                user_id=user_uuid,
                total_spent=amount_spent,
                total_credits_purchased=credits_purchased,
                first_purchase_at=now,
                last_purchase_at=now,
                purchase_count=1,
                avg_purchase_value=amount_spent,
                avg_credits_per_purchase=credits_purchased,
            )
            self.db.add(summary)
        
        await self.db.commit()

    # =========================================================================
    # REPORTS & ANALYTICS
    # =========================================================================

    async def get_dashboard_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get dashboard metrics for admin panel"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Total revenue
        revenue_result = await self.db.execute(
            select(func.sum(FinancialTransaction.amount_brl))
            .where(
                and_(
                    FinancialTransaction.created_at >= start_date,
                    FinancialTransaction.transaction_type.in_([
                        TransactionType.CREDIT_PURCHASE.value,
                        TransactionType.LICENSE_PURCHASE.value,
                    ]),
                    FinancialTransaction.payment_status == PaymentStatus.APPROVED.value
                )
            )
        )
        total_revenue = revenue_result.scalar() or Decimal("0")
        
        # Total costs
        costs_result = await self.db.execute(
            select(func.sum(FinancialTransaction.cost_brl))
            .where(FinancialTransaction.created_at >= start_date)
        )
        total_costs = costs_result.scalar() or Decimal("0")
        
        # OpenAI costs
        openai_costs_result = await self.db.execute(
            select(func.sum(APIUsageLog.cost_brl))
            .where(APIUsageLog.created_at >= start_date)
        )
        openai_costs = openai_costs_result.scalar() or Decimal("0")
        
        # Credits sold
        credits_result = await self.db.execute(
            select(func.sum(FinancialTransaction.credits_amount))
            .where(
                and_(
                    FinancialTransaction.created_at >= start_date,
                    FinancialTransaction.transaction_type == TransactionType.CREDIT_PURCHASE.value,
                    FinancialTransaction.payment_status == PaymentStatus.APPROVED.value
                )
            )
        )
        credits_sold = credits_result.scalar() or 0
        
        # Credits consumed
        credits_used_result = await self.db.execute(
            select(func.sum(func.abs(FinancialTransaction.credits_amount)))
            .where(
                and_(
                    FinancialTransaction.created_at >= start_date,
                    FinancialTransaction.transaction_type == TransactionType.CREDIT_USAGE.value
                )
            )
        )
        credits_consumed = credits_used_result.scalar() or 0
        
        # Transactions count
        transactions_result = await self.db.execute(
            select(func.count(FinancialTransaction.id))
            .where(
                and_(
                    FinancialTransaction.created_at >= start_date,
                    FinancialTransaction.transaction_type.in_([
                        TransactionType.CREDIT_PURCHASE.value,
                        TransactionType.LICENSE_PURCHASE.value,
                    ])
                )
            )
        )
        transactions_count = transactions_result.scalar() or 0
        
        # Calculate metrics
        gross_profit = total_revenue - total_costs - openai_costs
        profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else Decimal("0")
        
        return {
            "period_days": days,
            "total_revenue": float(total_revenue),
            "total_costs": float(total_costs),
            "openai_costs": float(openai_costs),
            "gross_profit": float(gross_profit),
            "profit_margin_percent": float(profit_margin),
            "credits_sold": int(credits_sold),
            "credits_consumed": int(credits_consumed),
            "transactions_count": int(transactions_count),
            "avg_transaction_value": float(total_revenue / transactions_count) if transactions_count > 0 else 0,
        }

    async def get_revenue_by_day(self, days: int = 30) -> List[Dict]:
        """Get daily revenue for charts"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        result = await self.db.execute(
            select(
                func.date(FinancialTransaction.created_at).label("date"),
                func.sum(FinancialTransaction.amount_brl).label("revenue"),
                func.sum(FinancialTransaction.cost_brl).label("costs"),
                func.count(FinancialTransaction.id).label("transactions")
            )
            .where(
                and_(
                    FinancialTransaction.created_at >= start_date,
                    FinancialTransaction.transaction_type.in_([
                        TransactionType.CREDIT_PURCHASE.value,
                        TransactionType.LICENSE_PURCHASE.value,
                    ]),
                    FinancialTransaction.payment_status == PaymentStatus.APPROVED.value
                )
            )
            .group_by(func.date(FinancialTransaction.created_at))
            .order_by(func.date(FinancialTransaction.created_at))
        )
        
        return [
            {
                "date": str(row.date),
                "revenue": float(row.revenue or 0),
                "costs": float(row.costs or 0),
                "profit": float((row.revenue or 0) - (row.costs or 0)),
                "transactions": row.transactions,
            }
            for row in result.fetchall()
        ]

    async def get_operations_breakdown(self, days: int = 30) -> Dict[str, int]:
        """Get breakdown of operations by type"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        result = await self.db.execute(
            select(
                FinancialTransaction.operation_type,
                func.count(FinancialTransaction.id).label("count")
            )
            .where(
                and_(
                    FinancialTransaction.created_at >= start_date,
                    FinancialTransaction.transaction_type == TransactionType.CREDIT_USAGE.value
                )
            )
            .group_by(FinancialTransaction.operation_type)
        )
        
        return {row.operation_type: row.count for row in result.fetchall()}

    async def get_top_users(self, limit: int = 10) -> List[Dict]:
        """Get top spending users"""
        result = await self.db.execute(
            select(UserFinancialSummary)
            .order_by(UserFinancialSummary.total_spent.desc())
            .limit(limit)
        )
        
        return [
            {
                "user_id": str(row.user_id),
                "total_spent": float(row.total_spent),
                "credits_purchased": row.total_credits_purchased,
                "credits_used": row.total_credits_used,
                "purchase_count": row.purchase_count,
                "lifetime_profit": float(row.lifetime_profit),
            }
            for row in result.scalars().all()
        ]

    async def get_package_sales_stats(self, days: int = 30) -> List[Dict]:
        """Get sales stats per package"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        result = await self.db.execute(
            select(
                CreditPackage.name,
                CreditPackage.slug,
                func.count(FinancialTransaction.id).label("sales"),
                func.sum(FinancialTransaction.amount_brl).label("revenue"),
                func.sum(FinancialTransaction.credits_amount).label("credits")
            )
            .join(CreditPackage, FinancialTransaction.package_id == CreditPackage.id)
            .where(
                and_(
                    FinancialTransaction.created_at >= start_date,
                    FinancialTransaction.transaction_type == TransactionType.CREDIT_PURCHASE.value,
                    FinancialTransaction.payment_status == PaymentStatus.APPROVED.value
                )
            )
            .group_by(CreditPackage.name, CreditPackage.slug)
            .order_by(func.sum(FinancialTransaction.amount_brl).desc())
        )
        
        return [
            {
                "name": row.name,
                "slug": row.slug,
                "sales": row.sales,
                "revenue": float(row.revenue or 0),
                "credits": row.credits,
            }
            for row in result.fetchall()
        ]

    # =========================================================================
    # DAILY REPORT GENERATION
    # =========================================================================

    async def generate_daily_report(self, date: datetime = None) -> DailyFinancialReport:
        """Generate or update daily financial report"""
        if date is None:
            date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        # Check if report exists
        result = await self.db.execute(
            select(DailyFinancialReport).where(
                DailyFinancialReport.report_date == start_of_day
            )
        )
        report = result.scalar_one_or_none()
        
        # Calculate metrics
        metrics = await self._calculate_daily_metrics(start_of_day, end_of_day)
        
        if report:
            for key, value in metrics.items():
                setattr(report, key, value)
            report.updated_at = datetime.now(timezone.utc)
        else:
            report = DailyFinancialReport(
                id=uuid.uuid4(),
                report_date=start_of_day,
                **metrics
            )
            self.db.add(report)
        
        await self.db.commit()
        return report

    async def _calculate_daily_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate all metrics for a day"""
        # Revenue queries
        revenue_query = select(
            func.sum(FinancialTransaction.amount_brl).filter(
                FinancialTransaction.transaction_type == TransactionType.CREDIT_PURCHASE.value
            ).label("credit_revenue"),
            func.sum(FinancialTransaction.amount_brl).filter(
                FinancialTransaction.transaction_type == TransactionType.LICENSE_PURCHASE.value
            ).label("license_revenue"),
            func.sum(FinancialTransaction.cost_brl).label("payment_fees"),
            func.count(FinancialTransaction.id).label("transactions_count"),
            func.sum(FinancialTransaction.credits_amount).filter(
                FinancialTransaction.transaction_type == TransactionType.CREDIT_PURCHASE.value
            ).label("credits_sold"),
        ).where(
            and_(
                FinancialTransaction.created_at >= start_date,
                FinancialTransaction.created_at < end_date,
                FinancialTransaction.payment_status == PaymentStatus.APPROVED.value
            )
        )
        
        revenue_result = await self.db.execute(revenue_query)
        revenue = revenue_result.fetchone()
        
        # OpenAI costs
        openai_query = select(func.sum(APIUsageLog.cost_brl)).where(
            and_(
                APIUsageLog.created_at >= start_date,
                APIUsageLog.created_at < end_date
            )
        )
        openai_result = await self.db.execute(openai_query)
        openai_costs = openai_result.scalar() or Decimal("0")
        
        # Credits consumed
        credits_used_query = select(
            func.sum(func.abs(FinancialTransaction.credits_amount))
        ).where(
            and_(
                FinancialTransaction.created_at >= start_date,
                FinancialTransaction.created_at < end_date,
                FinancialTransaction.transaction_type == TransactionType.CREDIT_USAGE.value
            )
        )
        credits_used_result = await self.db.execute(credits_used_query)
        credits_consumed = credits_used_result.scalar() or 0
        
        # Operations count
        ops_query = select(
            func.count(FinancialTransaction.id).filter(
                FinancialTransaction.operation_type == OperationType.COPY_GENERATION.value
            ).label("copies"),
            func.count(FinancialTransaction.id).filter(
                FinancialTransaction.operation_type == OperationType.TREND_ANALYSIS.value
            ).label("trends"),
            func.count(FinancialTransaction.id).filter(
                FinancialTransaction.operation_type == OperationType.NICHE_REPORT.value
            ).label("niches"),
        ).where(
            and_(
                FinancialTransaction.created_at >= start_date,
                FinancialTransaction.created_at < end_date,
                FinancialTransaction.transaction_type == TransactionType.CREDIT_USAGE.value
            )
        )
        ops_result = await self.db.execute(ops_query)
        ops = ops_result.fetchone()
        
        # Calculate totals
        credit_revenue = Decimal(revenue.credit_revenue or 0)
        license_revenue = Decimal(revenue.license_revenue or 0)
        total_revenue = credit_revenue + license_revenue
        payment_fees = Decimal(revenue.payment_fees or 0)
        total_costs = payment_fees + openai_costs
        gross_profit = total_revenue - total_costs
        profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else Decimal("0")
        
        return {
            "total_revenue": total_revenue,
            "credit_sales_revenue": credit_revenue,
            "license_sales_revenue": license_revenue,
            "total_costs": total_costs,
            "openai_costs": openai_costs,
            "payment_fees": payment_fees,
            "gross_profit": gross_profit,
            "net_profit": gross_profit,  # Same for now, can add more costs
            "profit_margin_percent": profit_margin,
            "transactions_count": revenue.transactions_count or 0,
            "credits_sold": revenue.credits_sold or 0,
            "credits_consumed": credits_consumed,
            "copies_generated": ops.copies if ops else 0,
            "trend_analyses": ops.trends if ops else 0,
            "niche_reports": ops.niches if ops else 0,
        }
