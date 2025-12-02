"""Create SaaS Hybrid subscriptions tables

Revision ID: 2024_12_02_saas_subscriptions
Revises: 2024_12_02_copy_ai_improvements
Create Date: 2024-12-02 10:00:00.000000

Este migration cria as tabelas necessárias para o modelo SaaS Híbrido:
- subscriptions: Assinaturas dos usuários
- usage_records: Registro de uso de features
- subscription_events: Histórico de eventos

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2024_12_02_saas_subscriptions'
down_revision: Union[str, None] = '2024_12_02_copy_ai_improvements'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================
    # TABELA: subscriptions
    # =========================================
    op.create_table(
        'subscriptions',
        # Identificação
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()')
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
            unique=True
        ),
        
        # Plano
        sa.Column(
            'plan_tier',
            sa.String(20),
            nullable=False,
            server_default='free',
            comment='free, starter, business, enterprise'
        ),
        sa.Column(
            'billing_cycle',
            sa.String(20),
            nullable=False,
            server_default='monthly',
            comment='monthly, yearly'
        ),
        sa.Column(
            'execution_mode',
            sa.String(20),
            nullable=False,
            server_default='web_only',
            comment='web_only, hybrid, local_first'
        ),
        
        # Status
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='active',
            comment='active, trialing, past_due, canceled, expired'
        ),
        
        # Datas principais
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False
        ),
        sa.Column(
            'current_period_start',
            sa.DateTime(timezone=True),
            nullable=False
        ),
        sa.Column(
            'current_period_end',
            sa.DateTime(timezone=True),
            nullable=False
        ),
        
        # Trial
        sa.Column(
            'trial_ends_at',
            sa.DateTime(timezone=True),
            nullable=True
        ),
        
        # Cancelamento
        sa.Column(
            'canceled_at',
            sa.DateTime(timezone=True),
            nullable=True
        ),
        sa.Column(
            'cancel_reason',
            sa.String(255),
            nullable=True
        ),
        
        # MercadoPago
        sa.Column(
            'mercadopago_subscription_id',
            sa.String(100),
            nullable=True,
            index=True
        ),
        sa.Column(
            'mercadopago_payer_id',
            sa.String(100),
            nullable=True
        ),
        sa.Column(
            'last_payment_at',
            sa.DateTime(timezone=True),
            nullable=True
        ),
        sa.Column(
            'next_payment_at',
            sa.DateTime(timezone=True),
            nullable=True
        ),
        sa.Column(
            'last_payment_status',
            sa.String(50),
            nullable=True
        ),
        
        # Metadata flexível
        sa.Column(
            'metadata',
            postgresql.JSONB,
            server_default='{}',
            nullable=False
        ),
    )
    
    # Indexes adicionais
    op.create_index(
        'idx_subscriptions_status',
        'subscriptions',
        ['status']
    )
    op.create_index(
        'idx_subscriptions_period_end',
        'subscriptions',
        ['current_period_end']
    )
    op.create_index(
        'idx_subscriptions_plan_tier',
        'subscriptions',
        ['plan_tier']
    )
    
    # =========================================
    # TABELA: usage_records
    # =========================================
    op.create_table(
        'usage_records',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()')
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column(
            'subscription_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('subscriptions.id', ondelete='CASCADE'),
            nullable=True
        ),
        
        # Feature e contagem
        sa.Column(
            'feature',
            sa.String(50),
            nullable=False,
            comment='price_searches, social_posts, whatsapp_messages, etc'
        ),
        sa.Column(
            'count',
            sa.Integer,
            nullable=False,
            server_default='0'
        ),
        
        # Período
        sa.Column(
            'period_start',
            sa.Date,
            nullable=False,
            comment='Primeiro dia do período (mês)'
        ),
        sa.Column(
            'period_end',
            sa.Date,
            nullable=False,
            comment='Último dia do período (mês)'
        ),
        
        # Timestamps
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False
        ),
        
        # Constraint única
        sa.UniqueConstraint(
            'user_id', 'feature', 'period_start',
            name='uq_usage_user_feature_period'
        ),
    )
    
    # Indexes
    op.create_index(
        'idx_usage_user_period',
        'usage_records',
        ['user_id', 'period_start']
    )
    op.create_index(
        'idx_usage_feature',
        'usage_records',
        ['feature']
    )
    
    # =========================================
    # TABELA: subscription_events
    # =========================================
    op.create_table(
        'subscription_events',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()')
        ),
        sa.Column(
            'subscription_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('subscriptions.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False
        ),
        
        # Evento
        sa.Column(
            'event_type',
            sa.String(50),
            nullable=False,
            comment='created, upgraded, downgraded, canceled, reactivated, payment_success, payment_failed'
        ),
        sa.Column(
            'event_data',
            postgresql.JSONB,
            server_default='{}',
            nullable=False
        ),
        
        # Contexto
        sa.Column(
            'old_plan',
            sa.String(20),
            nullable=True
        ),
        sa.Column(
            'new_plan',
            sa.String(20),
            nullable=True
        ),
        sa.Column(
            'amount',
            sa.Numeric(10, 2),
            nullable=True
        ),
        
        # MercadoPago reference
        sa.Column(
            'mercadopago_payment_id',
            sa.String(100),
            nullable=True
        ),
        
        # Timestamps
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False
        ),
    )
    
    # Indexes
    op.create_index(
        'idx_subscription_events_subscription',
        'subscription_events',
        ['subscription_id']
    )
    op.create_index(
        'idx_subscription_events_user',
        'subscription_events',
        ['user_id']
    )
    op.create_index(
        'idx_subscription_events_type',
        'subscription_events',
        ['event_type']
    )
    op.create_index(
        'idx_subscription_events_created',
        'subscription_events',
        ['created_at']
    )
    
    # =========================================
    # UPDATES: Atualizar tabela users
    # =========================================
    # Adicionar campos para compatibilidade
    op.add_column(
        'users',
        sa.Column(
            'current_plan',
            sa.String(20),
            nullable=True,
            server_default='free',
            comment='Cache do plano atual para queries rápidas'
        )
    )
    op.add_column(
        'users',
        sa.Column(
            'subscription_status',
            sa.String(20),
            nullable=True,
            server_default='active',
            comment='Cache do status para queries rápidas'
        )
    )


def downgrade() -> None:
    # Remover colunas de users
    op.drop_column('users', 'subscription_status')
    op.drop_column('users', 'current_plan')
    
    # Remover tabelas na ordem correta
    op.drop_table('subscription_events')
    op.drop_table('usage_records')
    op.drop_table('subscriptions')
