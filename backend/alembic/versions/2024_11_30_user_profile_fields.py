"""Add user profile fields

Revision ID: 2024_11_30_profile
Revises: f8c935eb4759
Create Date: 2024-11-30

Adiciona novos campos de perfil do usuário:
- avatar_url: URL do avatar
- phone: Telefone
- language: Idioma preferido
- timezone: Fuso horário
- is_email_verified: Email verificado
- last_login_at: Último login
- bonus_balance: Créditos bônus
- bonus_expires_at: Expiração dos créditos bônus
- last_purchase_at: Última compra
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2024_11_30_profile'
down_revision = 'f8c935eb4759'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add new user profile columns."""
    # Add profile fields
    op.add_column('users', sa.Column(
        'avatar_url',
        sa.String(500),
        nullable=True
    ))
    op.add_column('users', sa.Column(
        'phone',
        sa.String(50),
        nullable=True
    ))
    op.add_column('users', sa.Column(
        'language',
        sa.String(10),
        nullable=True,
        server_default='pt-BR'
    ))
    op.add_column('users', sa.Column(
        'timezone',
        sa.String(50),
        nullable=True,
        server_default='America/Sao_Paulo'
    ))
    
    # Add email verification
    op.add_column('users', sa.Column(
        'is_email_verified',
        sa.Boolean(),
        nullable=True,
        server_default='false'
    ))
    
    # Add last login tracking
    op.add_column('users', sa.Column(
        'last_login_at',
        sa.DateTime(),
        nullable=True
    ))
    
    # Add bonus credits fields
    op.add_column('users', sa.Column(
        'bonus_balance',
        sa.Integer(),
        nullable=True,
        server_default='0'
    ))
    op.add_column('users', sa.Column(
        'bonus_expires_at',
        sa.DateTime(),
        nullable=True
    ))
    op.add_column('users', sa.Column(
        'last_purchase_at',
        sa.DateTime(),
        nullable=True
    ))
    
    # Update existing rows with defaults
    op.execute("""
        UPDATE users 
        SET language = 'pt-BR',
            timezone = 'America/Sao_Paulo',
            is_email_verified = false,
            bonus_balance = 0
        WHERE language IS NULL
    """)


def downgrade() -> None:
    """Remove user profile columns."""
    op.drop_column('users', 'last_purchase_at')
    op.drop_column('users', 'bonus_expires_at')
    op.drop_column('users', 'bonus_balance')
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'is_email_verified')
    op.drop_column('users', 'timezone')
    op.drop_column('users', 'language')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'avatar_url')
