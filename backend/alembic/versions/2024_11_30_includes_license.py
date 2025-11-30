"""add includes_license to credit_packages

Revision ID: 2024_11_30_includes_license
Revises: 29453621bb63
Create Date: 2024-11-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '2024_11_30_includes_license'
down_revision = '29453621bb63'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add includes_license column to credit_packages table.
    This column indicates if the package includes a lifetime license.
    """
    # Check if column already exists
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('credit_packages')]
    
    if 'includes_license' not in columns:
        # Add the includes_license column
        op.add_column(
            'credit_packages',
            sa.Column(
                'includes_license',
                sa.Boolean(),
                nullable=False,
                server_default='false',
                comment='Whether this package includes a lifetime license'
            )
        )
        
        # Update Starter package to include license
        op.execute("""
            UPDATE credit_packages 
            SET includes_license = true 
            WHERE slug = 'starter'
        """)
    else:
        print("Column 'includes_license' already exists, skipping...")


def downgrade() -> None:
    """Remove includes_license column from credit_packages"""
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('credit_packages')]
    
    if 'includes_license' in columns:
        op.drop_column('credit_packages', 'includes_license')
