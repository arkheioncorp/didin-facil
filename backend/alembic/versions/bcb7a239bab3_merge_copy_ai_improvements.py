"""merge_copy_ai_improvements

Revision ID: bcb7a239bab3
Revises: 2024_11_30_includes_license, copy_ai_improvements, perf_001_fulltext
Create Date: 2025-12-02 08:36:56.561648

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bcb7a239bab3'
down_revision: Union[str, None] = ('2024_11_30_includes_license', 'copy_ai_improvements', 'perf_001_fulltext')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
