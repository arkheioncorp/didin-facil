"""
Accounting & Financial Models
Complete financial tracking system for Didin Fácil

Note: Using datetime.now(timezone.utc) instead of deprecated datetime.utcnow()
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from api.database.models import Base, utc_now
from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Index,
                        Integer, Numeric, String, Text, UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

# =============================================================================
# ENUMS
# =============================================================================

class TransactionType(str, Enum):
    """Types of financial transactions"""
    CREDIT_PURCHASE = "credit_purchase"      # User bought credits
    CREDIT_USAGE = "credit_usage"            # Credits consumed
    LICENSE_PURCHASE = "license_purchase"    # Lifetime license sold
    SUBSCRIPTION = "subscription"            # Monthly subscription
    REFUND = "refund"                        # Money returned
    BONUS = "bonus"                          # Free credits given


class OperationType(str, Enum):
    """Types of operations that consume credits/resources"""
    COPY_GENERATION = "copy_generation"
    TREND_ANALYSIS = "trend_analysis"
    NICHE_REPORT = "niche_report"
    PRODUCT_SCRAPING = "product_scraping"
    AI_CHAT = "ai_chat"
    IMAGE_GENERATION = "image_generation"


class PaymentStatus(str, Enum):
    """Payment processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    REJECTED = "rejected"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


# =============================================================================
# CREDIT PACKAGES (Products for sale)
# =============================================================================

class CreditPackage(Base):
    """Credit packages available for purchase"""
    __tablename__ = "credit_packages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    slug = Column(String(50), unique=True, nullable=False)  # starter, pro, ultra
    credits = Column(Integer, nullable=False)
    price_brl = Column(Numeric(10, 2), nullable=False)
    price_usd = Column(Numeric(10, 2), nullable=True)
    
    # Discounts
    discount_percent = Column(Integer, default=0)  # e.g., 15 = 15% off
    original_price = Column(Numeric(10, 2), nullable=True)
    
    # Display
    description = Column(Text, nullable=True)
    badge = Column(String(50), nullable=True)  # "Popular", "Best Value"
    is_featured = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    
    # License inclusion (first purchase includes lifetime license)
    includes_license = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=utc_now
    )

    @property
    def price_per_credit(self) -> Decimal:
        """Calculate price per credit"""
        if self.credits > 0:
            return self.price_brl / self.credits
        return Decimal("0")


# =============================================================================
# OPERATION COSTS (Our actual costs)
# =============================================================================

class OperationCost(Base):
    """
    Track actual operational costs for each type of operation.
    This is YOUR cost (e.g., OpenAI API costs), not user pricing.
    """
    __tablename__ = "operation_costs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Operation types: copy_generation, trend_analysis, etc.
    operation_type = Column(String(50), nullable=False)
    
    # Cost breakdown (base cost per operation)
    base_cost_brl = Column(Numeric(10, 6), nullable=False)
    avg_tokens_input = Column(Integer, default=0)
    avg_tokens_output = Column(Integer, default=0)
    # OpenAI pricing
    cost_per_1k_tokens_input = Column(Numeric(10, 6), default=0)
    cost_per_1k_tokens_output = Column(Numeric(10, 6), default=0)
    
    # Additional costs (proxy, server, etc.)
    infrastructure_cost = Column(Numeric(10, 6), default=0)
    
    # Pricing (how many credits we charge)
    credits_charged = Column(Integer, nullable=False)
    # Calculated margin
    margin_percent = Column(Numeric(5, 2), default=0)
    
    # Timestamps
    effective_from = Column(DateTime(timezone=True), server_default=func.now())
    effective_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index(
            "ix_operation_costs_type_date",
            "operation_type",
            "effective_from"
        ),
    )


# =============================================================================
# FINANCIAL TRANSACTIONS (Complete audit log)
# =============================================================================

class FinancialTransaction(Base):
    """
    Complete financial transaction log.
    Every money movement is recorded here.
    """
    __tablename__ = "financial_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    
    # Transaction details
    # Types: credit_purchase, license_purchase, etc.
    transaction_type = Column(String(50), nullable=False)
    # For credit_usage: copy_generation, etc.
    operation_type = Column(String(50), nullable=True)
    
    # Amounts (Revenue/expense in BRL)
    amount_brl = Column(Numeric(10, 2), nullable=False)
    amount_usd = Column(Numeric(10, 2), nullable=True)
    credits_amount = Column(Integer, default=0)
    
    # Cost tracking (for operations that have costs)
    cost_brl = Column(Numeric(10, 6), default=0)
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    
    # Profit calculation
    gross_profit = Column(Numeric(10, 2), default=0)
    
    # Payment info
    payment_id = Column(String(255), nullable=True)
    # Payment methods: pix, card, boleto
    payment_method = Column(String(50), nullable=True)
    payment_status = Column(String(50), default="completed")
    
    # Metadata
    description = Column(Text, nullable=True)
    # Renamed from 'metadata' (reserved by SQLAlchemy)
    extra_data = Column(JSONB, default={})
    
    # Reference to related entities
    package_id = Column(
        UUID(as_uuid=True),
        ForeignKey("credit_packages.id"),
        nullable=True
    )
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_financial_transactions_user", "user_id", "created_at"),
        Index(
            "ix_financial_transactions_type",
            "transaction_type",
            "created_at"
        ),
        Index("ix_financial_transactions_date", "created_at"),
    )


# =============================================================================
# DAILY FINANCIAL REPORTS (Aggregated stats)
# =============================================================================

class DailyFinancialReport(Base):
    """
    Daily aggregated financial metrics.
    Pre-calculated for fast dashboard loading.
    """
    __tablename__ = "daily_financial_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_date = Column(DateTime, nullable=False, unique=True)
    
    # Revenue
    total_revenue = Column(Numeric(10, 2), default=0)
    credit_sales_revenue = Column(Numeric(10, 2), default=0)
    license_sales_revenue = Column(Numeric(10, 2), default=0)
    subscription_revenue = Column(Numeric(10, 2), default=0)
    
    # Costs
    total_costs = Column(Numeric(10, 2), default=0)
    openai_costs = Column(Numeric(10, 6), default=0)
    infrastructure_costs = Column(Numeric(10, 2), default=0)
    # MercadoPago fees
    payment_fees = Column(Numeric(10, 2), default=0)
    
    # Profit
    gross_profit = Column(Numeric(10, 2), default=0)
    net_profit = Column(Numeric(10, 2), default=0)
    profit_margin_percent = Column(Numeric(5, 2), default=0)
    
    # Volume
    transactions_count = Column(Integer, default=0)
    credits_sold = Column(Integer, default=0)
    credits_consumed = Column(Integer, default=0)
    licenses_sold = Column(Integer, default=0)
    
    # Operations breakdown
    copies_generated = Column(Integer, default=0)
    trend_analyses = Column(Integer, default=0)
    niche_reports = Column(Integer, default=0)
    
    # Users
    paying_users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    
    # Refunds
    refunds_count = Column(Integer, default=0)
    refunds_amount = Column(Numeric(10, 2), default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=utc_now
    )

    __table_args__ = (
        Index("ix_daily_financial_reports_date", "report_date"),
    )


# =============================================================================
# MONTHLY FINANCIAL SUMMARY
# =============================================================================

class MonthlyFinancialSummary(Base):
    """Monthly aggregated financial summary"""
    __tablename__ = "monthly_financial_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    
    # Revenue
    total_revenue = Column(Numeric(12, 2), default=0)
    credit_sales_revenue = Column(Numeric(12, 2), default=0)
    license_sales_revenue = Column(Numeric(12, 2), default=0)
    subscription_revenue = Column(Numeric(12, 2), default=0)
    
    # Costs
    total_costs = Column(Numeric(12, 2), default=0)
    openai_costs = Column(Numeric(12, 2), default=0)
    infrastructure_costs = Column(Numeric(12, 2), default=0)
    payment_fees = Column(Numeric(12, 2), default=0)
    
    # Profit
    gross_profit = Column(Numeric(12, 2), default=0)
    net_profit = Column(Numeric(12, 2), default=0)
    profit_margin_percent = Column(Numeric(5, 2), default=0)
    
    # Volume
    transactions_count = Column(Integer, default=0)
    credits_sold = Column(Integer, default=0)
    credits_consumed = Column(Integer, default=0)
    licenses_sold = Column(Integer, default=0)
    
    # Users
    total_paying_users = Column(Integer, default=0)
    new_paying_users = Column(Integer, default=0)
    churned_users = Column(Integer, default=0)
    
    # LTV metrics
    avg_revenue_per_user = Column(Numeric(10, 2), default=0)
    avg_credits_per_user = Column(Numeric(10, 2), default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=utc_now
    )

    __table_args__ = (
        UniqueConstraint(
            "year",
            "month",
            name="uq_monthly_summary_year_month"
        ),
        Index("ix_monthly_summary_year_month", "year", "month"),
    )


# =============================================================================
# USER FINANCIAL SUMMARY (Per-user metrics)
# =============================================================================

class UserFinancialSummary(Base):
    """Per-user financial metrics for LTV analysis"""
    __tablename__ = "user_financial_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )
    
    # Lifetime value
    total_spent = Column(Numeric(10, 2), default=0)
    total_credits_purchased = Column(Integer, default=0)
    total_credits_used = Column(Integer, default=0)
    
    # Purchase history
    first_purchase_at = Column(DateTime(timezone=True), nullable=True)
    last_purchase_at = Column(DateTime(timezone=True), nullable=True)
    purchase_count = Column(Integer, default=0)
    
    # Average metrics
    avg_purchase_value = Column(Numeric(10, 2), default=0)
    avg_credits_per_purchase = Column(Integer, default=0)
    
    # Usage patterns
    total_copies_generated = Column(Integer, default=0)
    total_trend_analyses = Column(Integer, default=0)
    total_niche_reports = Column(Integer, default=0)
    
    # Cost to serve
    total_cost_to_serve = Column(Numeric(10, 6), default=0)
    
    # Calculated profit from this user
    lifetime_profit = Column(Numeric(10, 2), default=0)
    profit_margin_percent = Column(Numeric(5, 2), default=0)
    
    # Status (Top 10% spenders)
    is_high_value = Column(Boolean, default=False)
    # Churn risk: low, medium, high
    churn_risk = Column(String(20), default="low")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=utc_now
    )

    __table_args__ = (
        Index("ix_user_financial_summary_ltv", "total_spent"),
        Index("ix_user_financial_summary_high_value", "is_high_value"),
    )


# =============================================================================
# API USAGE TRACKING (For OpenAI token tracking)
# =============================================================================

class APIUsageLog(Base):
    """Detailed API usage log for cost tracking"""
    __tablename__ = "api_usage_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    
    # API details (providers: openai, anthropic, etc.)
    provider = Column(String(50), nullable=False)
    # Models: gpt-4-turbo, gpt-3.5-turbo
    model = Column(String(100), nullable=False)
    operation_type = Column(String(50), nullable=False)
    
    # Token usage
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    tokens_total = Column(Integer, default=0)
    
    # Costs
    cost_usd = Column(Numeric(10, 6), default=0)
    cost_brl = Column(Numeric(10, 6), default=0)
    
    # Request details
    request_duration_ms = Column(Integer, default=0)
    was_cached = Column(Boolean, default=False)
    
    # Metadata
    extra_data = Column(JSONB, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_api_usage_logs_user", "user_id", "created_at"),
        Index("ix_api_usage_logs_provider", "provider", "created_at"),
        Index("ix_api_usage_logs_date", "created_at"),
    )
