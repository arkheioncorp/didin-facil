"""add_fulltext_search_index

Revision ID: perf_001_fulltext
Revises: f8c935eb4759
Create Date: 2025-12-02

Performance optimization: Add GIN index for full-text search on products
This replaces expensive ILIKE queries with efficient tsvector search.

Expected improvement: -80% search query latency
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'perf_001_fulltext'
down_revision: Union[str, None] = 'f8c935eb4759'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add full-text search index for products."""
    # Create the GIN index for full-text search
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_fulltext
        ON products
        USING GIN (
            to_tsvector('portuguese',
                COALESCE(title, '') || ' ' || COALESCE(description, '')
            )
        )
        WHERE deleted_at IS NULL
    """)

    # Add index for price range queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_price_active
        ON products (price)
        WHERE deleted_at IS NULL
    """)

    # Add index for category + price combined queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_category_price
        ON products (category, price)
        WHERE deleted_at IS NULL
    """)

    # Add descending index for created_at (common sort order)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_created_desc
        ON products (created_at DESC)
        WHERE deleted_at IS NULL
    """)

    # Add index for user favorites lookup (if table exists)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'favorites'
            ) THEN
                CREATE INDEX IF NOT EXISTS idx_favorites_user_product
                ON favorites (user_id, product_id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Remove the full-text search indexes."""
    op.execute("DROP INDEX IF EXISTS idx_products_fulltext")
    op.execute("DROP INDEX IF EXISTS idx_products_price_active")
    op.execute("DROP INDEX IF EXISTS idx_products_category_price")
    op.execute("DROP INDEX IF EXISTS idx_products_created_desc")
    op.execute("DROP INDEX IF EXISTS idx_favorites_user_product")
