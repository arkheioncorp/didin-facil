"""Database polish and optimization

Revision ID: db_polish_2025_12_04
Revises: f7e1d9729949
Create Date: 2025-12-04

This migration adds indexes for frequently queried columns.
Uses IF NOT EXISTS for idempotency.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'db_polish_2025_12_04'
down_revision: Union[str, None] = 'f7e1d9729949'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance optimization indexes."""
    
    # USERS - email lookup (login)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_email
        ON users (email)
    """)
    
    # USERS - admin lookup
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_admin
        ON users (id)
        WHERE is_admin = true
    """)
    
    # USERS - users with credits
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_with_credits
        ON users (credits_balance)
        WHERE credits_balance > 0
    """)
    
    # PRODUCTS - trending products
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_trending
        ON products (is_trending, created_at DESC)
        WHERE is_trending = true
    """)
    
    # PRODUCTS - in-stock products
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_in_stock
        ON products (in_stock)
        WHERE in_stock = true
    """)
    
    # PRODUCTS - by source
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_source
        ON products (source)
    """)
    
    # FINANCIAL - user transactions
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_financial_transactions_user
        ON financial_transactions (user_id, created_at DESC)
    """)
    
    # SUBSCRIPTIONS - user subscriptions
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_subscriptions_user
        ON subscriptions (user_id)
    """)
    
    # FAVORITES - user favorites
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_favorites_user
        ON favorites (user_id, created_at DESC)
    """)


def downgrade() -> None:
    """Remove indexes."""
    indexes = [
        'idx_users_email',
        'idx_users_admin',
        'idx_users_with_credits',
        'idx_products_trending',
        'idx_products_in_stock',
        'idx_products_source',
        'idx_financial_transactions_user',
        'idx_subscriptions_user',
        'idx_favorites_user',
    ]
    
    for idx in indexes:
        op.execute(f"DROP INDEX IF EXISTS {idx}")
