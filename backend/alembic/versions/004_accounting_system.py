"""add accounting and financial tables

Revision ID: 004_accounting_system
Revises: f8c935eb4759
Create Date: 2025-11-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_accounting_system'
down_revision = 'f8c935eb4759'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # CREDIT PACKAGES TABLE
    # ==========================================================================
    op.create_table(
        'credit_packages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(50), nullable=False),
        sa.Column('credits', sa.Integer(), nullable=False),
        sa.Column('price_brl', sa.Numeric(10, 2), nullable=False),
        sa.Column('price_usd', sa.Numeric(10, 2), nullable=True),
        sa.Column('discount_percent', sa.Integer(), server_default='0'),
        sa.Column('original_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('badge', sa.String(50), nullable=True),
        sa.Column('is_featured', sa.Boolean(), server_default='false'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )

    # ==========================================================================
    # OPERATION COSTS TABLE
    # ==========================================================================
    op.create_table(
        'operation_costs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('operation_type', sa.String(50), nullable=False),
        sa.Column('base_cost_brl', sa.Numeric(10, 6), nullable=False),
        sa.Column('avg_tokens_input', sa.Integer(), server_default='0'),
        sa.Column('avg_tokens_output', sa.Integer(), server_default='0'),
        sa.Column('cost_per_1k_tokens_input', sa.Numeric(10, 6), server_default='0'),
        sa.Column('cost_per_1k_tokens_output', sa.Numeric(10, 6), server_default='0'),
        sa.Column('infrastructure_cost', sa.Numeric(10, 6), server_default='0'),
        sa.Column('credits_charged', sa.Integer(), nullable=False),
        sa.Column('margin_percent', sa.Numeric(5, 2), server_default='0'),
        sa.Column('effective_from', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('effective_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_operation_costs_type_date', 'operation_costs', ['operation_type', 'effective_from'])

    # ==========================================================================
    # FINANCIAL TRANSACTIONS TABLE
    # ==========================================================================
    op.create_table(
        'financial_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('transaction_type', sa.String(50), nullable=False),
        sa.Column('operation_type', sa.String(50), nullable=True),
        sa.Column('amount_brl', sa.Numeric(10, 2), nullable=False),
        sa.Column('amount_usd', sa.Numeric(10, 2), nullable=True),
        sa.Column('credits_amount', sa.Integer(), server_default='0'),
        sa.Column('cost_brl', sa.Numeric(10, 6), server_default='0'),
        sa.Column('tokens_input', sa.Integer(), server_default='0'),
        sa.Column('tokens_output', sa.Integer(), server_default='0'),
        sa.Column('gross_profit', sa.Numeric(10, 2), server_default='0'),
        sa.Column('payment_id', sa.String(255), nullable=True),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('payment_status', sa.String(50), server_default="'completed'"),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}'),
        sa.Column('package_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['package_id'], ['credit_packages.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_financial_transactions_user', 'financial_transactions', ['user_id', 'created_at'])
    op.create_index('ix_financial_transactions_type', 'financial_transactions', ['transaction_type', 'created_at'])
    op.create_index('ix_financial_transactions_date', 'financial_transactions', ['created_at'])

    # ==========================================================================
    # DAILY FINANCIAL REPORTS TABLE
    # ==========================================================================
    op.create_table(
        'daily_financial_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_date', sa.DateTime(), nullable=False),
        sa.Column('total_revenue', sa.Numeric(10, 2), server_default='0'),
        sa.Column('credit_sales_revenue', sa.Numeric(10, 2), server_default='0'),
        sa.Column('license_sales_revenue', sa.Numeric(10, 2), server_default='0'),
        sa.Column('subscription_revenue', sa.Numeric(10, 2), server_default='0'),
        sa.Column('total_costs', sa.Numeric(10, 2), server_default='0'),
        sa.Column('openai_costs', sa.Numeric(10, 6), server_default='0'),
        sa.Column('infrastructure_costs', sa.Numeric(10, 2), server_default='0'),
        sa.Column('payment_fees', sa.Numeric(10, 2), server_default='0'),
        sa.Column('gross_profit', sa.Numeric(10, 2), server_default='0'),
        sa.Column('net_profit', sa.Numeric(10, 2), server_default='0'),
        sa.Column('profit_margin_percent', sa.Numeric(5, 2), server_default='0'),
        sa.Column('transactions_count', sa.Integer(), server_default='0'),
        sa.Column('credits_sold', sa.Integer(), server_default='0'),
        sa.Column('credits_consumed', sa.Integer(), server_default='0'),
        sa.Column('licenses_sold', sa.Integer(), server_default='0'),
        sa.Column('copies_generated', sa.Integer(), server_default='0'),
        sa.Column('trend_analyses', sa.Integer(), server_default='0'),
        sa.Column('niche_reports', sa.Integer(), server_default='0'),
        sa.Column('paying_users', sa.Integer(), server_default='0'),
        sa.Column('new_users', sa.Integer(), server_default='0'),
        sa.Column('active_users', sa.Integer(), server_default='0'),
        sa.Column('refunds_count', sa.Integer(), server_default='0'),
        sa.Column('refunds_amount', sa.Numeric(10, 2), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('report_date')
    )
    op.create_index('ix_daily_financial_reports_date', 'daily_financial_reports', ['report_date'])

    # ==========================================================================
    # MONTHLY FINANCIAL SUMMARIES TABLE
    # ==========================================================================
    op.create_table(
        'monthly_financial_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('total_revenue', sa.Numeric(12, 2), server_default='0'),
        sa.Column('credit_sales_revenue', sa.Numeric(12, 2), server_default='0'),
        sa.Column('license_sales_revenue', sa.Numeric(12, 2), server_default='0'),
        sa.Column('subscription_revenue', sa.Numeric(12, 2), server_default='0'),
        sa.Column('total_costs', sa.Numeric(12, 2), server_default='0'),
        sa.Column('openai_costs', sa.Numeric(12, 2), server_default='0'),
        sa.Column('infrastructure_costs', sa.Numeric(12, 2), server_default='0'),
        sa.Column('payment_fees', sa.Numeric(12, 2), server_default='0'),
        sa.Column('gross_profit', sa.Numeric(12, 2), server_default='0'),
        sa.Column('net_profit', sa.Numeric(12, 2), server_default='0'),
        sa.Column('profit_margin_percent', sa.Numeric(5, 2), server_default='0'),
        sa.Column('transactions_count', sa.Integer(), server_default='0'),
        sa.Column('credits_sold', sa.Integer(), server_default='0'),
        sa.Column('credits_consumed', sa.Integer(), server_default='0'),
        sa.Column('licenses_sold', sa.Integer(), server_default='0'),
        sa.Column('total_paying_users', sa.Integer(), server_default='0'),
        sa.Column('new_paying_users', sa.Integer(), server_default='0'),
        sa.Column('churned_users', sa.Integer(), server_default='0'),
        sa.Column('avg_revenue_per_user', sa.Numeric(10, 2), server_default='0'),
        sa.Column('avg_credits_per_user', sa.Numeric(10, 2), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('year', 'month', name='uq_monthly_summary_year_month')
    )
    op.create_index('ix_monthly_summary_year_month', 'monthly_financial_summaries', ['year', 'month'])

    # ==========================================================================
    # USER FINANCIAL SUMMARIES TABLE
    # ==========================================================================
    op.create_table(
        'user_financial_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_spent', sa.Numeric(10, 2), server_default='0'),
        sa.Column('total_credits_purchased', sa.Integer(), server_default='0'),
        sa.Column('total_credits_used', sa.Integer(), server_default='0'),
        sa.Column('first_purchase_at', sa.DateTime(), nullable=True),
        sa.Column('last_purchase_at', sa.DateTime(), nullable=True),
        sa.Column('purchase_count', sa.Integer(), server_default='0'),
        sa.Column('avg_purchase_value', sa.Numeric(10, 2), server_default='0'),
        sa.Column('avg_credits_per_purchase', sa.Integer(), server_default='0'),
        sa.Column('total_copies_generated', sa.Integer(), server_default='0'),
        sa.Column('total_trend_analyses', sa.Integer(), server_default='0'),
        sa.Column('total_niche_reports', sa.Integer(), server_default='0'),
        sa.Column('total_cost_to_serve', sa.Numeric(10, 6), server_default='0'),
        sa.Column('lifetime_profit', sa.Numeric(10, 2), server_default='0'),
        sa.Column('profit_margin_percent', sa.Numeric(5, 2), server_default='0'),
        sa.Column('is_high_value', sa.Boolean(), server_default='false'),
        sa.Column('churn_risk', sa.String(20), server_default="'low'"),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_user_financial_summary_ltv', 'user_financial_summaries', ['total_spent'])
    op.create_index('ix_user_financial_summary_high_value', 'user_financial_summaries', ['is_high_value'])

    # ==========================================================================
    # API USAGE LOGS TABLE
    # ==========================================================================
    op.create_table(
        'api_usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('operation_type', sa.String(50), nullable=False),
        sa.Column('tokens_input', sa.Integer(), server_default='0'),
        sa.Column('tokens_output', sa.Integer(), server_default='0'),
        sa.Column('tokens_total', sa.Integer(), server_default='0'),
        sa.Column('cost_usd', sa.Numeric(10, 6), server_default='0'),
        sa.Column('cost_brl', sa.Numeric(10, 6), server_default='0'),
        sa.Column('request_duration_ms', sa.Integer(), server_default='0'),
        sa.Column('was_cached', sa.Boolean(), server_default='false'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_api_usage_logs_user', 'api_usage_logs', ['user_id', 'created_at'])
    op.create_index('ix_api_usage_logs_provider', 'api_usage_logs', ['provider', 'created_at'])
    op.create_index('ix_api_usage_logs_date', 'api_usage_logs', ['created_at'])

    # ==========================================================================
    # INSERT DEFAULT CREDIT PACKAGES
    # ==========================================================================
    op.execute("""
        INSERT INTO credit_packages (id, name, slug, credits, price_brl, original_price, discount_percent, description, badge, is_featured, sort_order, is_active)
        VALUES
            (gen_random_uuid(), 'Iniciante', 'starter', 50, 9.90, NULL, 0, 'Ideal para começar a testar', NULL, false, 1, true),
            (gen_random_uuid(), 'Popular', 'pro', 150, 24.90, 29.70, 16, 'O mais escolhido pelos usuários', 'Mais Popular', true, 2, true),
            (gen_random_uuid(), 'Profissional', 'ultra', 500, 69.90, 99.50, 30, 'Máxima economia para uso intenso', 'Melhor Valor', false, 3, true),
            (gen_random_uuid(), 'Enterprise', 'enterprise', 2000, 199.90, 398.00, 50, 'Para equipes e agências', '50% OFF', false, 4, true)
    """)

    # ==========================================================================
    # INSERT DEFAULT OPERATION COSTS
    # ==========================================================================
    op.execute("""
        INSERT INTO operation_costs (id, operation_type, base_cost_brl, avg_tokens_input, avg_tokens_output, cost_per_1k_tokens_input, cost_per_1k_tokens_output, credits_charged, margin_percent)
        VALUES
            (gen_random_uuid(), 'copy_generation', 0.12, 400, 400, 0.057, 0.171, 1, 65.00),
            (gen_random_uuid(), 'trend_analysis', 0.20, 600, 500, 0.057, 0.171, 2, 60.00),
            (gen_random_uuid(), 'niche_report', 0.50, 1000, 1500, 0.057, 0.171, 5, 55.00),
            (gen_random_uuid(), 'ai_chat', 0.08, 200, 300, 0.057, 0.171, 1, 70.00),
            (gen_random_uuid(), 'image_generation', 0.30, 0, 0, 0, 0, 3, 50.00)
    """)


def downgrade() -> None:
    op.drop_table('api_usage_logs')
    op.drop_table('user_financial_summaries')
    op.drop_table('monthly_financial_summaries')
    op.drop_table('daily_financial_reports')
    op.drop_table('financial_transactions')
    op.drop_table('operation_costs')
    op.drop_table('credit_packages')
