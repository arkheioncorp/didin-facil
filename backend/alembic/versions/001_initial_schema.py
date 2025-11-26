"""initial_schema

Revision ID: 001
Revises: 
Create Date: 2025-11-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('plan', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create licenses table
    op.create_table('licenses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('license_key', sa.String(length=50), nullable=False),
        sa.Column('plan', sa.String(length=50), nullable=False),
        sa.Column('max_devices', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('activated_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('auto_renew', sa.Boolean(), nullable=True),
        sa.Column('payment_id', sa.String(length=255), nullable=True),
        sa.Column('last_payment_id', sa.String(length=255), nullable=True),
        sa.Column('deactivation_reason', sa.String(length=255), nullable=True),
        sa.Column('deactivated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_licenses_license_key'), 'licenses', ['license_key'], unique=True)

    # Create license_devices table
    op.create_table('license_devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('license_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hwid', sa.String(length=255), nullable=False),
        sa.Column('app_version', sa.String(length=50), nullable=True),
        sa.Column('first_seen_at', sa.DateTime(), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('deactivated_at', sa.DateTime(), nullable=True),
        sa.Column('deactivation_reason', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['license_id'], ['licenses.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('license_id', 'hwid', name='uq_license_device')
    )

    # Create products table
    op.create_table('products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tiktok_id', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('original_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('seller_name', sa.String(length=255), nullable=True),
        sa.Column('seller_rating', sa.Float(), nullable=True),
        sa.Column('product_rating', sa.Float(), nullable=True),
        sa.Column('reviews_count', sa.Integer(), nullable=True),
        sa.Column('sales_count', sa.Integer(), nullable=True),
        sa.Column('sales_7d', sa.Integer(), nullable=True),
        sa.Column('sales_30d', sa.Integer(), nullable=True),
        sa.Column('commission_rate', sa.Float(), nullable=True),
        sa.Column('image_url', sa.String(length=1000), nullable=True),
        sa.Column('images', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('video_url', sa.String(length=1000), nullable=True),
        sa.Column('product_url', sa.String(length=1000), nullable=False),
        sa.Column('affiliate_url', sa.String(length=1000), nullable=True),
        sa.Column('has_free_shipping', sa.Boolean(), nullable=True),
        sa.Column('is_trending', sa.Boolean(), nullable=True),
        sa.Column('is_on_sale', sa.Boolean(), nullable=True),
        sa.Column('in_stock', sa.Boolean(), nullable=True),
        sa.Column('collected_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_tiktok_id'), 'products', ['tiktok_id'], unique=True)
    op.create_index(op.f('ix_products_category'), 'products', ['category'], unique=False)
    op.create_index(op.f('ix_products_sales_count'), 'products', ['sales_count'], unique=False)
    op.create_index(op.f('ix_products_sales_7d'), 'products', ['sales_7d'], unique=False)
    op.create_index(op.f('ix_products_sales_30d'), 'products', ['sales_30d'], unique=False)
    op.create_index(op.f('ix_products_is_trending'), 'products', ['is_trending'], unique=False)
    op.create_index('ix_products_sales_trending', 'products', ['sales_30d', 'is_trending'], unique=False)
    op.create_index('ix_products_category_sales', 'products', ['category', 'sales_30d'], unique=False)

    # Create copy_history table
    op.create_table('copy_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', sa.String(length=100), nullable=False),
        sa.Column('product_title', sa.String(length=500), nullable=False),
        sa.Column('copy_type', sa.String(length=50), nullable=False),
        sa.Column('tone', sa.String(length=50), nullable=False),
        sa.Column('copy_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_copy_history_user_date', 'copy_history', ['user_id', 'created_at'], unique=False)

    # Create payment_events table
    op.create_table('payment_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create payments table
    op.create_table('payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('plan', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('payment_method', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create scraping_jobs table
    op.create_table('scraping_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('products_scraped', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scraping_jobs_status', 'scraping_jobs', ['status', 'priority'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_scraping_jobs_status', table_name='scraping_jobs')
    op.drop_table('scraping_jobs')
    op.drop_table('payments')
    op.drop_table('payment_events')
    op.drop_index('ix_copy_history_user_date', table_name='copy_history')
    op.drop_table('copy_history')
    op.drop_index('ix_products_category_sales', table_name='products')
    op.drop_index('ix_products_sales_trending', table_name='products')
    op.drop_index(op.f('ix_products_is_trending'), table_name='products')
    op.drop_index(op.f('ix_products_sales_30d'), table_name='products')
    op.drop_index(op.f('ix_products_sales_7d'), table_name='products')
    op.drop_index(op.f('ix_products_sales_count'), table_name='products')
    op.drop_index(op.f('ix_products_category'), table_name='products')
    op.drop_index(op.f('ix_products_tiktok_id'), table_name='products')
    op.drop_table('products')
    op.drop_table('license_devices')
    op.drop_index(op.f('ix_licenses_license_key'), table_name='licenses')
    op.drop_table('licenses')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
