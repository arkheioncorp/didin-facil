"""CRM tables migration

Revision ID: 2024_11_26_crm
Revises: previous_migration
Create Date: 2024-11-26

Creates tables for the CRM module:
- crm_contacts
- crm_leads
- crm_pipelines
- crm_deals
- crm_activities
- crm_tags
- crm_segments
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers
revision = '2024_11_26_crm'
down_revision = '004_accounting_system'  # Depends on accounting migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CRM Contacts
    op.create_table(
        'crm_contacts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False, index=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('job_title', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('instagram', sa.String(100), nullable=True),
        sa.Column('tiktok', sa.String(100), nullable=True),
        sa.Column('whatsapp', sa.String(50), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('source', sa.String(50), default='manual'),
        sa.Column('tags', JSONB, default='[]'),
        sa.Column('custom_fields', JSONB, default='{}'),
        sa.Column('subscribed', sa.Boolean, default=True),
        sa.Column('subscription_date', sa.DateTime, nullable=True),
        sa.Column('unsubscribe_date', sa.DateTime, nullable=True),
        sa.Column('lead_score', sa.Integer, default=0),
        sa.Column('engagement_score', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('last_activity_at', sa.DateTime, nullable=True),
    )
    
    # Indexes for contacts
    op.create_index(
        'idx_crm_contacts_email',
        'crm_contacts',
        ['user_id', 'email'],
        unique=True
    )
    op.create_index(
        'idx_crm_contacts_status',
        'crm_contacts',
        ['user_id', 'status']
    )
    op.create_index(
        'idx_crm_contacts_source',
        'crm_contacts',
        ['user_id', 'source']
    )
    op.create_index(
        'idx_crm_contacts_subscribed',
        'crm_contacts',
        ['user_id', 'subscribed']
    )
    
    # CRM Leads
    op.create_table(
        'crm_leads',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False, index=True),
        sa.Column(
            'contact_id', sa.String(36),
            sa.ForeignKey('crm_contacts.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('source', sa.String(50), default='organic'),
        sa.Column('status', sa.String(50), default='new'),
        sa.Column('estimated_value', sa.Numeric(12, 2), default=0),
        sa.Column('currency', sa.String(10), default='BRL'),
        sa.Column('score', sa.Integer, default=0),
        sa.Column('temperature', sa.String(20), default='cold'),
        sa.Column('interested_products', JSONB, default='[]'),
        sa.Column('interests', JSONB, default='[]'),
        sa.Column('assigned_to', sa.String(36), nullable=True),
        sa.Column('qualified_at', sa.DateTime, nullable=True),
        sa.Column('converted_at', sa.DateTime, nullable=True),
        sa.Column('lost_at', sa.DateTime, nullable=True),
        sa.Column('lost_reason', sa.Text, nullable=True),
        sa.Column('tags', JSONB, default='[]'),
        sa.Column('custom_fields', JSONB, default='{}'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('last_contact_at', sa.DateTime, nullable=True),
        sa.Column('next_follow_up', sa.DateTime, nullable=True),
    )
    
    # Indexes for leads
    op.create_index('idx_crm_leads_status', 'crm_leads', ['user_id', 'status'])
    op.create_index('idx_crm_leads_source', 'crm_leads', ['user_id', 'source'])
    op.create_index(
        'idx_crm_leads_temperature',
        'crm_leads',
        ['user_id', 'temperature']
    )
    op.create_index(
        'idx_crm_leads_assigned',
        'crm_leads',
        ['user_id', 'assigned_to']
    )
    op.create_index(
        'idx_crm_leads_contact',
        'crm_leads',
        ['contact_id']
    )
    
    # CRM Pipelines
    op.create_table(
        'crm_pipelines',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('stages', JSONB, default='[]'),
        sa.Column('currency', sa.String(10), default='BRL'),
        sa.Column('deal_rotting_days', sa.Integer, default=30),
        sa.Column('total_deals', sa.Integer, default=0),
        sa.Column('total_value', sa.Numeric(15, 2), default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Indexes for pipelines
    op.create_index(
        'idx_crm_pipelines_default',
        'crm_pipelines',
        ['user_id', 'is_default']
    )
    op.create_index(
        'idx_crm_pipelines_active',
        'crm_pipelines',
        ['user_id', 'is_active']
    )
    
    # CRM Deals
    op.create_table(
        'crm_deals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False, index=True),
        sa.Column(
            'contact_id', sa.String(36),
            sa.ForeignKey('crm_contacts.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column('lead_id', sa.String(36), nullable=True),
        sa.Column(
            'pipeline_id', sa.String(36),
            sa.ForeignKey('crm_pipelines.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column('stage_id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('value', sa.Numeric(15, 2), default=0),
        sa.Column('currency', sa.String(10), default='BRL'),
        sa.Column('status', sa.String(50), default='open'),
        sa.Column('probability', sa.Integer, default=0),
        sa.Column('expected_close_date', sa.DateTime, nullable=True),
        sa.Column('actual_close_date', sa.DateTime, nullable=True),
        sa.Column('won_at', sa.DateTime, nullable=True),
        sa.Column('lost_at', sa.DateTime, nullable=True),
        sa.Column('lost_reason', sa.Text, nullable=True),
        sa.Column('assigned_to', sa.String(36), nullable=True),
        sa.Column('products', JSONB, default='[]'),
        sa.Column('tags', JSONB, default='[]'),
        sa.Column('custom_fields', JSONB, default='{}'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('last_activity_at', sa.DateTime, nullable=True),
        sa.Column('stage_entered_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Indexes for deals
    op.create_index('idx_crm_deals_status', 'crm_deals', ['user_id', 'status'])
    op.create_index(
        'idx_crm_deals_pipeline',
        'crm_deals',
        ['user_id', 'pipeline_id']
    )
    op.create_index('idx_crm_deals_stage', 'crm_deals', ['pipeline_id', 'stage_id'])
    op.create_index('idx_crm_deals_contact', 'crm_deals', ['contact_id'])
    op.create_index(
        'idx_crm_deals_assigned',
        'crm_deals',
        ['user_id', 'assigned_to']
    )
    op.create_index('idx_crm_deals_value', 'crm_deals', ['user_id', 'value'])
    
    # CRM Activities
    op.create_table(
        'crm_activities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False, index=True),
        sa.Column('contact_id', sa.String(36), nullable=True),
        sa.Column('lead_id', sa.String(36), nullable=True),
        sa.Column('deal_id', sa.String(36), nullable=True),
        sa.Column('activity_type', sa.String(50), default='note'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('content', sa.Text, nullable=True),
        sa.Column('metadata', JSONB, default='{}'),
        sa.Column('is_done', sa.Boolean, default=False),
        sa.Column('due_date', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('performed_by', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Indexes for activities
    op.create_index(
        'idx_crm_activities_contact',
        'crm_activities',
        ['user_id', 'contact_id']
    )
    op.create_index(
        'idx_crm_activities_lead',
        'crm_activities',
        ['user_id', 'lead_id']
    )
    op.create_index(
        'idx_crm_activities_deal',
        'crm_activities',
        ['user_id', 'deal_id']
    )
    op.create_index(
        'idx_crm_activities_type',
        'crm_activities',
        ['user_id', 'activity_type']
    )
    op.create_index(
        'idx_crm_activities_due',
        'crm_activities',
        ['user_id', 'is_done', 'due_date']
    )
    
    # CRM Tags
    op.create_table(
        'crm_tags',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('color', sa.String(20), default='#3B82F6'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Unique index for tags
    op.create_index(
        'idx_crm_tags_name',
        'crm_tags',
        ['user_id', sa.func.lower(sa.text('name'))],
        unique=True
    )
    
    # CRM Segments
    op.create_table(
        'crm_segments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('conditions', JSONB, default='[]'),
        sa.Column('match_type', sa.String(20), default='all'),
        sa.Column('segment_type', sa.String(50), default='contacts'),
        sa.Column('count', sa.Integer, default=0),
        sa.Column('last_computed_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Indexes for segments
    op.create_index(
        'idx_crm_segments_type',
        'crm_segments',
        ['user_id', 'segment_type']
    )


def downgrade() -> None:
    op.drop_table('crm_segments')
    op.drop_table('crm_tags')
    op.drop_table('crm_activities')
    op.drop_table('crm_deals')
    op.drop_table('crm_pipelines')
    op.drop_table('crm_leads')
    op.drop_table('crm_contacts')
