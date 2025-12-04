-- ============================================
-- SELLER BOT AUTOMATION SCHEMA
-- ============================================
-- Schema para suportar automações do Seller Bot com n8n
-- Criado em: 2025-12-01

-- Tabela de eventos de automação
CREATE TABLE IF NOT EXISTS automation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(100) NOT NULL,
    automation_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    channel VARCHAR(20) DEFAULT 'whatsapp',
    data JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'executed',
    scheduled_at TIMESTAMPTZ,
    executed_at TIMESTAMPTZ DEFAULT NOW(),
    n8n_response JSONB,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_automation_events_user ON automation_events(user_id);
CREATE INDEX idx_automation_events_type ON automation_events(automation_type);
CREATE INDEX idx_automation_events_status ON automation_events(status);
CREATE INDEX idx_automation_events_created ON automation_events(created_at);

-- Tabela de automações agendadas
CREATE TABLE IF NOT EXISTS scheduled_automations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    automation_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    scheduled_for TIMESTAMPTZ NOT NULL,
    data JSONB DEFAULT '{}',
    channel VARCHAR(20) DEFAULT 'whatsapp',
    priority VARCHAR(20) DEFAULT 'normal',
    status VARCHAR(20) DEFAULT 'pending',
    attempts INT DEFAULT 0,
    max_attempts INT DEFAULT 3,
    executed_at TIMESTAMPTZ,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scheduled_automations_status ON scheduled_automations(status);
CREATE INDEX idx_scheduled_automations_scheduled ON scheduled_automations(scheduled_for);
CREATE INDEX idx_scheduled_automations_user ON scheduled_automations(user_id);

-- Tabela de tentativas de recuperação de carrinho
CREATE TABLE IF NOT EXISTS cart_recovery_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    cart_id VARCHAR(100),
    product_name VARCHAR(255),
    price DECIMAL(10, 2),
    attempt_number INT DEFAULT 1,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    response_received BOOLEAN DEFAULT FALSE,
    converted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_cart_recovery_user ON cart_recovery_attempts(user_id);
CREATE INDEX idx_cart_recovery_created ON cart_recovery_attempts(created_at);

-- Tabela de notificações de alerta de preço
CREATE TABLE IF NOT EXISTS price_alert_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    product_name VARCHAR(255),
    old_price DECIMAL(10, 2),
    new_price DECIMAL(10, 2),
    discount INT,
    notified_at TIMESTAMPTZ DEFAULT NOW(),
    channel VARCHAR(20) DEFAULT 'whatsapp',
    clicked BOOLEAN DEFAULT FALSE,
    converted BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_price_alert_notif_user ON price_alert_notifications(user_id);
CREATE INDEX idx_price_alert_notif_date ON price_alert_notifications(notified_at);

-- Tabela de solicitações de review
CREATE TABLE IF NOT EXISTS review_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    order_id VARCHAR(100),
    product_name VARCHAR(255),
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    responded_at TIMESTAMPTZ,
    rating INT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_review_requests_user ON review_requests(user_id);
CREATE INDEX idx_review_requests_status ON review_requests(status);

-- Tabela de pedidos de handoff
CREATE TABLE IF NOT EXISTS handoff_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    user_name VARCHAR(100),
    reason VARCHAR(100),
    context_summary TEXT,
    channel VARCHAR(20),
    lead_score INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    assigned_to VARCHAR(100),
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_handoff_requests_status ON handoff_requests(status);
CREATE INDEX idx_handoff_requests_created ON handoff_requests(created_at);

-- Tabela de tickets de suporte
CREATE TABLE IF NOT EXISTS support_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    user_name VARCHAR(100),
    complaint TEXT,
    channel VARCHAR(20),
    sentiment VARCHAR(20),
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'open',
    assigned_to VARCHAR(100),
    resolution TEXT,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_support_tickets_status ON support_tickets(status);
CREATE INDEX idx_support_tickets_priority ON support_tickets(priority);
CREATE INDEX idx_support_tickets_created ON support_tickets(created_at);

-- Tabela de métricas de automação
CREATE TABLE IF NOT EXISTS automation_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    automation_type VARCHAR(50) NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    hour INT DEFAULT EXTRACT(HOUR FROM NOW()),
    
    -- Contadores
    total_triggered INT DEFAULT 0,
    total_sent INT DEFAULT 0,
    total_delivered INT DEFAULT 0,
    total_clicked INT DEFAULT 0,
    total_converted INT DEFAULT 0,
    total_errors INT DEFAULT 0,
    
    -- Métricas de tempo
    avg_delivery_time_ms INT,
    
    -- Dados agregados
    channels JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(automation_type, date, hour)
);

CREATE INDEX idx_automation_metrics_type ON automation_metrics(automation_type);
CREATE INDEX idx_automation_metrics_date ON automation_metrics(date);

-- Tabela de configurações de automação por usuário
CREATE TABLE IF NOT EXISTS user_automation_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL UNIQUE,
    
    -- Opt-outs
    opt_out_all BOOLEAN DEFAULT FALSE,
    opt_out_marketing BOOLEAN DEFAULT FALSE,
    opt_out_transactional BOOLEAN DEFAULT FALSE,
    
    -- Canais preferidos
    preferred_channel VARCHAR(20) DEFAULT 'whatsapp',
    email_enabled BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT FALSE,
    push_enabled BOOLEAN DEFAULT TRUE,
    
    -- Horários preferidos
    quiet_hours_start TIME DEFAULT '22:00',
    quiet_hours_end TIME DEFAULT '08:00',
    
    -- Frequência
    max_messages_per_day INT DEFAULT 5,
    max_messages_per_week INT DEFAULT 20,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_automation_prefs_user ON user_automation_preferences(user_id);

-- Função para incrementar métricas
CREATE OR REPLACE FUNCTION increment_automation_metric(
    p_automation_type VARCHAR(50),
    p_metric VARCHAR(50),
    p_value INT DEFAULT 1
) RETURNS VOID AS $$
BEGIN
    INSERT INTO automation_metrics (automation_type, date, hour)
    VALUES (p_automation_type, CURRENT_DATE, EXTRACT(HOUR FROM NOW()))
    ON CONFLICT (automation_type, date, hour) DO NOTHING;
    
    EXECUTE format(
        'UPDATE automation_metrics SET %I = %I + $1, updated_at = NOW() 
         WHERE automation_type = $2 AND date = $3 AND hour = $4',
        p_metric, p_metric
    ) USING p_value, p_automation_type, CURRENT_DATE, EXTRACT(HOUR FROM NOW());
END;
$$ LANGUAGE plpgsql;

-- View de métricas agregadas por dia
CREATE OR REPLACE VIEW v_automation_daily_metrics AS
SELECT 
    automation_type,
    date,
    SUM(total_triggered) as triggered,
    SUM(total_sent) as sent,
    SUM(total_delivered) as delivered,
    SUM(total_clicked) as clicked,
    SUM(total_converted) as converted,
    SUM(total_errors) as errors,
    ROUND(SUM(total_delivered)::numeric / NULLIF(SUM(total_sent), 0) * 100, 2) as delivery_rate,
    ROUND(SUM(total_clicked)::numeric / NULLIF(SUM(total_delivered), 0) * 100, 2) as click_rate,
    ROUND(SUM(total_converted)::numeric / NULLIF(SUM(total_clicked), 0) * 100, 2) as conversion_rate
FROM automation_metrics
GROUP BY automation_type, date
ORDER BY date DESC, automation_type;

-- View de métricas em tempo real
CREATE OR REPLACE VIEW v_automation_realtime_stats AS
SELECT 
    automation_type,
    SUM(CASE WHEN date = CURRENT_DATE THEN total_triggered ELSE 0 END) as today_triggered,
    SUM(CASE WHEN date = CURRENT_DATE THEN total_sent ELSE 0 END) as today_sent,
    SUM(CASE WHEN date = CURRENT_DATE THEN total_converted ELSE 0 END) as today_converted,
    SUM(CASE WHEN date >= CURRENT_DATE - INTERVAL '7 days' THEN total_triggered ELSE 0 END) as week_triggered,
    SUM(CASE WHEN date >= CURRENT_DATE - INTERVAL '7 days' THEN total_converted ELSE 0 END) as week_converted
FROM automation_metrics
GROUP BY automation_type;

-- Comentários nas tabelas
COMMENT ON TABLE automation_events IS 'Log de todos os eventos de automação disparados';
COMMENT ON TABLE scheduled_automations IS 'Fila de automações agendadas para execução futura';
COMMENT ON TABLE automation_metrics IS 'Métricas agregadas por hora de cada tipo de automação';
COMMENT ON TABLE user_automation_preferences IS 'Preferências do usuário para receber automações';

-- Grants (ajustar conforme necessário)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO tiktrend_api;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO tiktrend_api;
