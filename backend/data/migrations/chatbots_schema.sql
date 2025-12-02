-- Chatbots Database Schema
-- Migration for chatbot management system

-- Chatbots table (user chatbot configurations)
CREATE TABLE IF NOT EXISTS chatbots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    typebot_id VARCHAR(255), -- External Typebot flow ID
    status VARCHAR(50) DEFAULT 'draft', -- draft, active, paused, archived
    channels TEXT[], -- ['whatsapp', 'instagram', 'web', 'app']
    
    -- Statistics
    total_sessions INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    completion_rate DECIMAL(5, 2) DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_chatbots_user_id ON chatbots(user_id);
CREATE INDEX idx_chatbots_status ON chatbots(status);
CREATE INDEX idx_chatbots_created_at ON chatbots(user_id, created_at DESC);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_chatbots_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_chatbots_updated_at
    BEFORE UPDATE ON chatbots
    FOR EACH ROW
    EXECUTE FUNCTION update_chatbots_updated_at();
