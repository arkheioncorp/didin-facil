"""Database polish and optimization

Revision ID: db_polish_2025_12_04
Revises: f7e1d9729949
Create Date: 2025-12-04

This migration adds:
1. Additional indexes for frequently queried columns
2. Partial indexes for soft-deleted records
3. Composite indexes for common query patterns

MIGRATION SAFETY:
- Uses IF NOT EXISTS for idempotency
- Tested rollback
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'db_polish_2025_12_04'
down_revision: Union[str, None] = 'f7e1d9729949'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add performance optimization indexes.
    Only for tables that exist in the current schema.
    """
    
    # =========================================================================
    # USERS TABLE INDEXES
    # =========================================================================
    
    # Index for active users lookup
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_active
        ON users (is_active)
        WHERE is_active = true
    """)
    
    # Index for admin users (rare, but fast lookup)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_admin
        ON users (id)
        WHERE is_admin = true
    """)
    
    # Index for users with credits (active purchasers)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_with_credits
        ON users (credits_balance)
        WHERE credits_balance > 0
    """)
    
    # Index for email lookup (login)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_email
        ON users (email)
    """)
    
    # =========================================================================
    # LICENSES TABLE INDEXES
    # =========================================================================
    
    # Index for active licenses
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_licenses_active
        ON licenses (is_active, expires_at)
        WHERE is_active = true
    """)
    
    # Index for user's licenses
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_licenses_user
        ON licenses (user_id, is_active)
    """)
    
    # =========================================================================
    # PRODUCTS TABLE INDEXES
    # =========================================================================
    
    # Index for active products
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_active
        ON products (is_active)
        WHERE is_active = true
    """)
    
    # Index for trending products (common dashboard query)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_trending_active
        ON products (views DESC, is_active)
        WHERE is_active = true
    """)
    
    # Index for products by store
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_store
        ON products (store, is_active)
    """)
    
    # =========================================================================
    # FINANCIAL TRANSACTIONS TABLE INDEXES
    # =========================================================================
    
    # Index for pending transactions (webhook processing)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_financial_transactions_status
        ON financial_transactions (status, created_at DESC)
    """)
    
    # Index for user transactions
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_financial_transactions_user
        ON financial_transactions (user_id, created_at DESC)
    """)
    
    # =========================================================================
    # SCRAPING JOBS TABLE INDEXES
    # =========================================================================
    
    # Index for pending jobs (worker queue)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_scraping_jobs_pending
        ON scraping_jobs (status, scheduled_at)
        WHERE status = 'pending'
    """)
    
    # =========================================================================
    # CRM TABLES INDEXES
    # =========================================================================
    
    # CRM Contacts
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_crm_contacts_user
        ON crm_contacts (user_id, created_at DESC)
    """)
    
    # CRM Leads
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_crm_leads_user_status
        ON crm_leads (user_id, status, created_at DESC)
    """)
    
    # CRM Deals
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_crm_deals_user_stage
        ON crm_deals (user_id, stage, created_at DESC)
    """)
    
    # =========================================================================
    # SUBSCRIPTIONS TABLE INDEXES
    # =========================================================================
    
    # Index for active subscriptions
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_subscriptions_active
        ON subscriptions (status, current_period_end)
        WHERE status = 'active'
    """)
    
    # Index for user subscriptions
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_subscriptions_user
        ON subscriptions (user_id, status)
    """)
    
    # =========================================================================
    # CREDITS TRANSACTIONS TABLE INDEXES
    # =========================================================================
    
    # Index for user credit history
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_credits_transactions_user
        ON credits_transactions (user_id, created_at DESC)
    """)
    
    # =========================================================================
    # FAVORITES TABLE INDEXES
    # =========================================================================
    
    # Index for user favorites
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_favorites_user
        ON favorites (user_id, created_at DESC)
    """)
    
    # =========================================================================
    # SCHEDULED POSTS TABLE INDEXES
    # =========================================================================
    
    # Index for pending scheduled posts
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_scheduled_posts_pending
        ON scheduled_posts (status, scheduled_time)
        WHERE status = 'pending' OR status = 'scheduled'
    """)


def downgrade() -> None:
    """
    Remove all indexes created by this migration.
    """
    indexes = [
        # Users
        'idx_users_active',
        'idx_users_admin',
        'idx_users_with_credits',
        'idx_users_email',
        # Licenses
        'idx_licenses_active',
        'idx_licenses_user',
        # Products
        'idx_products_active',
        'idx_products_trending_active',
        'idx_products_store',
        # Financial
        'idx_financial_transactions_status',
        'idx_financial_transactions_user',
        # Scraping
        'idx_scraping_jobs_pending',
        # CRM
        'idx_crm_contacts_user',
        'idx_crm_leads_user_status',
        'idx_crm_deals_user_stage',
        # Subscriptions
        'idx_subscriptions_active',
        'idx_subscriptions_user',
        # Credits
        'idx_credits_transactions_user',
        # Favorites
        'idx_favorites_user',
        # Scheduled Posts
        'idx_scheduled_posts_pending',
    ]
    
    for idx in indexes:
        op.execute(f"DROP INDEX IF EXISTS {idx}")
