-- ================================================
-- DIDIN FÁCIL - TABELAS PARA AUTOMAÇÕES N8N
-- ================================================

-- Extensão para busca por similaridade
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ================================================
-- 1. FAQ - Perguntas Frequentes
-- ================================================
CREATE TABLE IF NOT EXISTS faqs (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(100),
    keywords TEXT,
    times_asked INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para busca rápida
CREATE INDEX IF NOT EXISTS idx_faqs_question_trgm ON faqs USING gin (question gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_faqs_keywords_trgm ON faqs USING gin (keywords gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_faqs_category ON faqs (category);

-- FAQs iniciais
INSERT INTO faqs (question, answer, category, keywords) VALUES
('Como funciona o Didin Fácil?', 'O Didin Fácil é uma plataforma de comparação de preços. Buscamos os melhores preços em diversas lojas e mostramos onde você pode economizar mais! 💰', 'geral', 'funciona como usar plataforma'),
('O Didin Fácil é gratuito?', 'Sim! O Didin Fácil é 100% gratuito para você. Ganhamos uma pequena comissão das lojas quando você compra através dos nossos links.', 'geral', 'preço custo gratuito grátis pagar'),
('Como criar alerta de preço?', 'Para criar um alerta, basta buscar o produto desejado e clicar em "Criar Alerta". Você será notificado quando o preço baixar! 🔔', 'alertas', 'alerta notificação avisar baixar preço'),
('Quais lojas vocês comparam?', 'Comparamos preços de várias lojas como Amazon, Mercado Livre, Magazine Luiza, Americanas, Casas Bahia e muitas outras!', 'lojas', 'lojas parceiros onde comprar'),
('Como entrar em contato?', 'Você pode nos contatar por:\n📧 Email: contato@didin.com.br\n📱 WhatsApp: (92) 98844-9768\n🌐 Site: didin.com.br/contato', 'contato', 'contato email telefone whatsapp'),
('Qual o horário de atendimento?', '📅 Segunda a Sexta: 8h às 18h\n📅 Sábado: 8h às 12h\n📅 Domingo: Fechado\n\nAtendimento online 24h pelo app!', 'atendimento', 'horário funcionamento atendimento aberto'),
('É seguro comprar pelos links?', 'Sim! Todos os nossos links direcionam para as lojas oficiais. O pagamento é feito diretamente na loja escolhida, com toda segurança. 🔒', 'segurança', 'seguro confiável golpe fraude'),
('Como cancelar alerta de preço?', 'Acesse seu perfil, vá em "Meus Alertas" e clique em "Cancelar" no alerta desejado. Você também pode responder "PARAR" a qualquer notificação.', 'alertas', 'cancelar parar desativar alerta');

-- ================================================
-- 2. Perguntas não respondidas (para melhoria)
-- ================================================
CREATE TABLE IF NOT EXISTS unanswered_questions (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    conversation_id INTEGER,
    contact_phone VARCHAR(20),
    resolved BOOLEAN DEFAULT false,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_unanswered_resolved ON unanswered_questions (resolved);

-- ================================================
-- 3. Estado da conversa (para fluxos com estado)
-- ================================================
CREATE TABLE IF NOT EXISTS conversation_state (
    conversation_id INTEGER PRIMARY KEY,
    state VARCHAR(50) NOT NULL DEFAULT 'initial',
    context JSONB DEFAULT '{}',
    last_intent VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conv_state ON conversation_state (state);

-- ================================================
-- 4. Log de conversas com IA
-- ================================================
CREATE TABLE IF NOT EXISTS ai_conversations (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    tokens_used INTEGER,
    model VARCHAR(50),
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_conv_id ON ai_conversations (conversation_id);
CREATE INDEX IF NOT EXISTS idx_ai_created ON ai_conversations (created_at);

-- ================================================
-- 5. Alertas de preço
-- ================================================
CREATE TABLE IF NOT EXISTS price_alerts (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    product_name VARCHAR(500),
    target_price DECIMAL(10,2) NOT NULL,
    user_phone VARCHAR(20) NOT NULL,
    user_email VARCHAR(255),
    notified BOOLEAN DEFAULT false,
    notified_at TIMESTAMP,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alerts_product ON price_alerts (product_id);
CREATE INDEX IF NOT EXISTS idx_alerts_user ON price_alerts (user_phone);
CREATE INDEX IF NOT EXISTS idx_alerts_active ON price_alerts (active, notified);

-- ================================================
-- 6. Log de notificações enviadas
-- ================================================
CREATE TABLE IF NOT EXISTS notification_logs (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER REFERENCES price_alerts(id),
    user_phone VARCHAR(20),
    product_name VARCHAR(500),
    price_at_notification DECIMAL(10,2),
    notification_type VARCHAR(50) DEFAULT 'whatsapp',
    status VARCHAR(20) DEFAULT 'sent',
    error_message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notif_alert ON notification_logs (alert_id);
CREATE INDEX IF NOT EXISTS idx_notif_sent ON notification_logs (sent_at);

-- ================================================
-- 7. Agendamentos
-- ================================================
CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER,
    contact_phone VARCHAR(20) NOT NULL,
    contact_name VARCHAR(200),
    appointment_type VARCHAR(100) NOT NULL,
    scheduled_at TIMESTAMP NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    status VARCHAR(20) DEFAULT 'scheduled',
    notes TEXT,
    google_event_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_appt_phone ON appointments (contact_phone);
CREATE INDEX IF NOT EXISTS idx_appt_scheduled ON appointments (scheduled_at);
CREATE INDEX IF NOT EXISTS idx_appt_status ON appointments (status);

-- ================================================
-- 8. Métricas do chatbot
-- ================================================
CREATE TABLE IF NOT EXISTS chatbot_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    total_messages INTEGER DEFAULT 0,
    auto_responses INTEGER DEFAULT 0,
    human_transfers INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER,
    satisfaction_score DECIMAL(3,2),
    unique_users INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date)
);

CREATE INDEX IF NOT EXISTS idx_metrics_date ON chatbot_metrics (date);

-- ================================================
-- Função para atualizar updated_at
-- ================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers
CREATE TRIGGER update_faqs_updated_at BEFORE UPDATE ON faqs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversation_state_updated_at BEFORE UPDATE ON conversation_state
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ================================================
-- Permissões
-- ================================================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tiktrend;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tiktrend;
