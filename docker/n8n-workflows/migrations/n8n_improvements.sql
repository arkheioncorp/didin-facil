-- ================================================
-- n8n Improvements - Database Schema
-- ================================================
-- Author: Didin Fácil Team
-- Date: 2025-11-30
-- Description: Schema para melhorias nas automações n8n
-- ================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ================================================
-- 1. WORKFLOW LOGS - Logging Estruturado
-- ================================================

CREATE TABLE IF NOT EXISTS workflow_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_name VARCHAR(255) NOT NULL,
    execution_id VARCHAR(255),
    conversation_id VARCHAR(255),
    user_id VARCHAR(255),
    intent VARCHAR(100),
    message_content TEXT,
    response_content TEXT,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    execution_time_ms INTEGER,
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX idx_workflow_logs_workflow ON workflow_logs(workflow_name);
CREATE INDEX idx_workflow_logs_conversation ON workflow_logs(conversation_id);
CREATE INDEX idx_workflow_logs_created ON workflow_logs(created_at DESC);
CREATE INDEX idx_workflow_logs_success ON workflow_logs(success);
CREATE INDEX idx_workflow_logs_intent ON workflow_logs(intent);

-- ================================================
-- 2. CONVERSATION CONTEXT - Histórico de Mensagens
-- ================================================

CREATE TABLE IF NOT EXISTS conversation_context (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id VARCHAR(255) NOT NULL,
    message_type VARCHAR(50) NOT NULL, -- 'incoming' or 'outgoing'
    content TEXT NOT NULL,
    sender_id VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX idx_context_conversation ON conversation_context(conversation_id, created_at DESC);
CREATE INDEX idx_context_created ON conversation_context(created_at DESC);

-- ================================================
-- 3. CONVERSATION STATE - Estados de Conversa
-- ================================================

CREATE TABLE IF NOT EXISTS conversation_state (
    conversation_id VARCHAR(255) PRIMARY KEY,
    current_state VARCHAR(100) NOT NULL,
    data JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice
CREATE INDEX idx_state_updated ON conversation_state(updated_at DESC);

-- ================================================
-- 4. RATE LIMITS - Controle de Taxa
-- ================================================

CREATE TABLE IF NOT EXISTS rate_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id VARCHAR(255) NOT NULL,
    message_count INTEGER DEFAULT 1,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    blocked BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX idx_rate_limits_conversation ON rate_limits(conversation_id);
CREATE INDEX idx_rate_limits_window ON rate_limits(window_start, window_end);
CREATE INDEX idx_rate_limits_blocked ON rate_limits(blocked);

-- ================================================
-- 5. A/B TESTS - Framework de Testes
-- ================================================

CREATE TABLE IF NOT EXISTS ab_tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_name VARCHAR(255) NOT NULL,
    variant_id VARCHAR(100) NOT NULL,
    conversation_id VARCHAR(255) NOT NULL,
    user_responded BOOLEAN DEFAULT false,
    response_time_seconds INTEGER,
    conversion BOOLEAN DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX idx_ab_tests_name ON ab_tests(test_name);
CREATE INDEX idx_ab_tests_variant ON ab_tests(variant_id);
CREATE INDEX idx_ab_tests_created ON ab_tests(created_at DESC);

-- ================================================
-- 6. UNANSWERED QUESTIONS - FAQs não respondidas
-- ================================================

CREATE TABLE IF NOT EXISTS unanswered_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id VARCHAR(255),
    question TEXT NOT NULL,
    context TEXT,
    frequency INTEGER DEFAULT 1,
    resolved BOOLEAN DEFAULT false,
    suggested_answer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Índices
CREATE INDEX idx_unanswered_resolved ON unanswered_questions(resolved);
CREATE INDEX idx_unanswered_frequency ON unanswered_questions(frequency DESC);
CREATE INDEX idx_unanswered_created ON unanswered_questions(created_at DESC);

-- ================================================
-- 7. CHATBOT METRICS - Métricas Diárias
-- ================================================

CREATE TABLE IF NOT EXISTS chatbot_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL,
    total_messages INTEGER DEFAULT 0,
    incoming_messages INTEGER DEFAULT 0,
    outgoing_messages INTEGER DEFAULT 0,
    auto_resolved INTEGER DEFAULT 0,
    human_handoff INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER,
    ai_calls INTEGER DEFAULT 0,
    ai_cost_usd DECIMAL(10, 6) DEFAULT 0,
    unique_conversations INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date)
);

-- Índice
CREATE INDEX idx_metrics_date ON chatbot_metrics(date DESC);

-- ================================================
-- 8. AI CONVERSATIONS - Histórico de IA
-- ================================================

CREATE TABLE IF NOT EXISTS ai_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id VARCHAR(255) NOT NULL,
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    model VARCHAR(100) NOT NULL,
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),
    response_time_ms INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX idx_ai_conv_id ON ai_conversations(conversation_id);
CREATE INDEX idx_ai_created ON ai_conversations(created_at DESC);
CREATE INDEX idx_ai_model ON ai_conversations(model);

-- ================================================
-- 9. WEBHOOKS LOG - Rastreamento de Webhooks
-- ================================================

CREATE TABLE IF NOT EXISTS webhook_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    webhook_path VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    payload JSONB,
    response JSONB,
    status_code INTEGER,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX idx_webhook_path ON webhook_logs(webhook_path);
CREATE INDEX idx_webhook_created ON webhook_logs(created_at DESC);
CREATE INDEX idx_webhook_status ON webhook_logs(status_code);

-- ================================================
-- VIEWS ÚTEIS
-- ================================================

-- View: Métricas em tempo real (últimas 24h)
CREATE OR REPLACE VIEW v_realtime_metrics AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as total_executions,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed,
    AVG(execution_time_ms) as avg_execution_time,
    SUM(tokens_used) as total_tokens,
    SUM(cost_usd) as total_cost
FROM workflow_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour DESC;

-- View: Top intents
CREATE OR REPLACE VIEW v_top_intents AS
SELECT 
    intent,
    COUNT(*) as count,
    AVG(execution_time_ms) as avg_time,
    SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as success_rate
FROM workflow_logs
WHERE created_at > NOW() - INTERVAL '7 days'
    AND intent IS NOT NULL
GROUP BY intent
ORDER BY count DESC;

-- View: AI Usage Summary
CREATE OR REPLACE VIEW v_ai_usage_summary AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as api_calls,
    SUM(tokens_used) as total_tokens,
    AVG(tokens_used) as avg_tokens,
    SUM(cost_usd) as total_cost,
    AVG(response_time_ms) as avg_response_time
FROM ai_conversations
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- ================================================
-- FUNCTIONS ÚTEIS
-- ================================================

-- Function: Cleanup old logs (manter últimos 90 dias)
CREATE OR REPLACE FUNCTION cleanup_old_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM workflow_logs WHERE created_at < NOW() - INTERVAL '90 days';
    DELETE FROM conversation_context WHERE created_at < NOW() - INTERVAL '90 days';
    DELETE FROM webhook_logs WHERE created_at < NOW() - INTERVAL '90 days';
    DELETE FROM rate_limits WHERE window_end < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- Function: Get conversation context (últimas 5 mensagens)
CREATE OR REPLACE FUNCTION get_conversation_context(conv_id VARCHAR)
RETURNS TABLE (
    message_type VARCHAR,
    content TEXT,
    created_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cc.message_type,
        cc.content,
        cc.created_at
    FROM conversation_context cc
    WHERE cc.conversation_id = conv_id
    ORDER BY cc.created_at DESC
    LIMIT 5;
END;
$$ LANGUAGE plpgsql;

-- ================================================
-- GRANTS (ajustar conforme seu usuário)
-- ================================================

-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tiktrend;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tiktrend;

-- ================================================
-- COMENTÁRIOS
-- ================================================

COMMENT ON TABLE workflow_logs IS 'Logs estruturados de execução de workflows n8n';
COMMENT ON TABLE conversation_context IS 'Histórico de mensagens para contexto de conversa';
COMMENT ON TABLE conversation_state IS 'Estado atual de cada conversa';
COMMENT ON TABLE rate_limits IS 'Controle de taxa de mensagens por conversa';
COMMENT ON TABLE ab_tests IS 'Framework para A/B testing de respostas';
COMMENT ON TABLE unanswered_questions IS 'Registro de perguntas não respondidas automaticamente';
COMMENT ON TABLE chatbot_metrics IS 'Métricas agregadas diárias do chatbot';
COMMENT ON TABLE ai_conversations IS 'Histórico de interações com IA (OpenAI)';
COMMENT ON TABLE webhook_logs IS 'Log de chamadas de webhooks';

-- ================================================
-- FIM DO SCHEMA
-- ================================================
