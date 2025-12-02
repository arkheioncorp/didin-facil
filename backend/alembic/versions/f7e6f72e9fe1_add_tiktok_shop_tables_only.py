"""add_tiktok_shop_tables_only

Revision ID: f7e6f72e9fe1
Revises: bcb7a239bab3
Create Date: 2025-12-02 13:58:00.237426

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7e6f72e9fe1'
down_revision: Union[str, None] = 'bcb7a239bab3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
