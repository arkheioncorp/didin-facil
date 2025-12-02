"""add_tiktok_shop_tables_only

Revision ID: 5b99b618a354
Revises: f7e6f72e9fe1
Create Date: 2025-12-02 14:00:21.038133

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID

# revision identifiers, used by Alembic.
revision: str = '5b99b618a354'
down_revision: Union[str, None] = 'f7e6f72e9fe1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # TikTok Shop Connections
    op.create_table(
        'tiktok_shop_connections',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), 
                  nullable=False, index=True),
        sa.Column('app_key', sa.String(100), nullable=False),
        sa.Column('app_secret_encrypted', sa.String(500), nullable=False),
        sa.Column('service_id', sa.String(100), nullable=True),
        sa.Column('access_token', sa.String(500), nullable=True),
        sa.Column('refresh_token', sa.String(500), nullable=True),
        sa.Column('access_token_expires_at', sa.DateTime, nullable=True),
        sa.Column('refresh_token_expires_at', sa.DateTime, nullable=True),
        sa.Column('open_id', sa.String(100), nullable=True),
        sa.Column('seller_name', sa.String(255), nullable=True),
        sa.Column('seller_region', sa.String(10), nullable=True),
        sa.Column('user_type', sa.Integer, default=0),
        sa.Column('shops', JSON, default=[]),
        sa.Column('is_connected', sa.Boolean, default=False),
        sa.Column('last_sync_at', sa.DateTime, nullable=True),
        sa.Column('sync_status', sa.String(50), default='idle'),
        sa.Column('sync_error', sa.Text, nullable=True),
        sa.Column('products_synced', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), 
                  onupdate=sa.func.now()),
        sa.UniqueConstraint('user_id', name='uq_tiktok_shop_user')
    )
    
    # TikTok Shop Products
    op.create_table(
        'tiktok_shop_products',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('connection_id', UUID(as_uuid=True), 
                  sa.ForeignKey('tiktok_shop_connections.id'), nullable=False),
        sa.Column('tiktok_product_id', sa.String(100), nullable=False, index=True),
        sa.Column('shop_id', sa.String(100), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('sales_regions', ARRAY(sa.String), default=[]),
        sa.Column('listing_quality_tier', sa.String(20), nullable=True),
        sa.Column('has_draft', sa.Boolean, default=False),
        sa.Column('skus', JSON, default=[]),
        sa.Column('price', sa.Float, nullable=True),
        sa.Column('currency', sa.String(10), default='BRL'),
        sa.Column('total_inventory', sa.Integer, default=0),
        sa.Column('tiktok_created_at', sa.DateTime, nullable=True),
        sa.Column('tiktok_updated_at', sa.DateTime, nullable=True),
        sa.Column('synced_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(),
                  onupdate=sa.func.now()),
        sa.UniqueConstraint('connection_id', 'tiktok_product_id', 
                           name='uq_tiktok_shop_product')
    )
    
    op.create_index('ix_tiktok_shop_products_status', 'tiktok_shop_products', ['status'])


def downgrade() -> None:
    op.drop_index('ix_tiktok_shop_products_status', 'tiktok_shop_products')
    op.drop_table('tiktok_shop_products')
    op.drop_table('tiktok_shop_connections')
