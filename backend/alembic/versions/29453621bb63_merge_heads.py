"""merge_heads

Revision ID: 29453621bb63
Revises: 2024_11_26_crm, 2024_11_30_profile
Create Date: 2025-11-30 17:32:17.583083

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '29453621bb63'
down_revision: Union[str, None] = ('2024_11_26_crm', '2024_11_30_profile')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
