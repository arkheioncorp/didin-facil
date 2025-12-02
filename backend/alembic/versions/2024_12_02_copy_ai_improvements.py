"""Copy AI improvements - preferences, saved templates, history enhancements

Revision ID: copy_ai_improvements
Revises: f8c935eb4759
Create Date: 2024-12-02

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision = 'copy_ai_improvements'
down_revision = 'f8c935eb4759'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Adiciona melhorias ao sistema Copy AI:
    1. Novas colunas na tabela copy_history
    2. Nova tabela user_copy_preferences
    3. Nova tabela user_saved_templates
    """
    
    # =========================================================================
    # 1. Adicionar colunas à tabela copy_history (se não existirem)
    # =========================================================================
    
    # Verificar e adicionar colunas individualmente
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('copy_history')]
    
    if 'product_title' not in existing_columns:
        op.add_column('copy_history', 
            sa.Column('product_title', sa.VARCHAR(500), nullable=True)
        )
    
    if 'copy_type' not in existing_columns:
        op.add_column('copy_history',
            sa.Column('copy_type', sa.VARCHAR(50), nullable=False, server_default='ad')
        )
    
    if 'word_count' not in existing_columns:
        op.add_column('copy_history',
            sa.Column('word_count', sa.Integer(), nullable=True, server_default='0')
        )
    
    if 'character_count' not in existing_columns:
        op.add_column('copy_history',
            sa.Column('character_count', sa.Integer(), nullable=True, server_default='0')
        )
    
    if 'cached' not in existing_columns:
        op.add_column('copy_history',
            sa.Column('cached', sa.Boolean(), nullable=True, server_default='false')
        )
    
    if 'credits_used' not in existing_columns:
        op.add_column('copy_history',
            sa.Column('credits_used', sa.Integer(), nullable=True, server_default='1')
        )
    
    # Criar índice para copy_type se não existir
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_copy_history_copy_type 
        ON copy_history(copy_type)
    """)
    
    # =========================================================================
    # 2. Criar tabela user_copy_preferences
    # =========================================================================
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_copy_preferences (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            
            -- Preferências de geração
            default_copy_type VARCHAR(50) DEFAULT 'tiktok_hook',
            default_tone VARCHAR(50) DEFAULT 'urgent',
            default_platform VARCHAR(50) DEFAULT 'instagram',
            default_language VARCHAR(10) DEFAULT 'pt-BR',
            include_emoji BOOLEAN DEFAULT TRUE,
            include_hashtags BOOLEAN DEFAULT TRUE,
            
            -- Configurações de cache
            prefer_cached BOOLEAN DEFAULT TRUE,
            cache_ttl_hours INTEGER DEFAULT 24,
            
            -- Limites e quotas personalizados
            max_copies_per_day INTEGER DEFAULT 50,
            
            -- Templates favoritos (IDs)
            favorite_template_ids TEXT[] DEFAULT '{}',
            
            -- Histórico de uso (analytics)
            total_copies_generated INTEGER DEFAULT 0,
            last_copy_generated_at TIMESTAMP,
            most_used_copy_type VARCHAR(50),
            most_used_tone VARCHAR(50),
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_copy_prefs_user 
        ON user_copy_preferences(user_id)
    """)
    
    # =========================================================================
    # 3. Criar tabela user_saved_templates
    # =========================================================================
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_saved_templates (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            
            name VARCHAR(200) NOT NULL,
            description TEXT,
            platform VARCHAR(50) DEFAULT 'all',
            category VARCHAR(50) DEFAULT 'custom',
            caption_template TEXT NOT NULL,
            hashtags TEXT[] DEFAULT '{}',
            variables JSONB DEFAULT '[]',
            copy_type VARCHAR(50),
            
            is_public BOOLEAN DEFAULT FALSE,
            usage_count INTEGER DEFAULT 0,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_saved_templates_user 
        ON user_saved_templates(user_id)
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_saved_templates_public 
        ON user_saved_templates(is_public) WHERE is_public = TRUE
    """)


def downgrade() -> None:
    """
    Remove as melhorias do sistema Copy AI
    """
    
    # Remover tabelas
    op.execute("DROP TABLE IF EXISTS user_saved_templates CASCADE")
    op.execute("DROP TABLE IF EXISTS user_copy_preferences CASCADE")
    
    # Remover índice
    op.execute("DROP INDEX IF EXISTS idx_copy_history_copy_type")
    
    # Remover colunas do copy_history
    op.drop_column('copy_history', 'credits_used')
    op.drop_column('copy_history', 'cached')
    op.drop_column('copy_history', 'character_count')
    op.drop_column('copy_history', 'word_count')
    op.drop_column('copy_history', 'copy_type')
    op.drop_column('copy_history', 'product_title')
