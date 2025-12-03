"""merge_saas_and_tiktok

Revision ID: f7e1d9729949
Revises: 2024_12_02_saas_subscriptions, 5b99b618a354
Create Date: 2025-12-02 16:05:21.868175

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7e1d9729949'
down_revision: Union[str, None] = ('2024_12_02_saas_subscriptions', '5b99b618a354')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
