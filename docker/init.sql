-- ===========================================
-- TikTrend Finder - Database Initialization
-- ===========================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ===========================================
-- Users Table
-- ===========================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    verification_token VARCHAR(255),
    reset_token VARCHAR(255),
    reset_token_expires TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

-- ===========================================
-- Licenses Table
-- ===========================================
CREATE TABLE IF NOT EXISTS licenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    license_key VARCHAR(255) UNIQUE NOT NULL,
    plan VARCHAR(50) NOT NULL DEFAULT 'free',
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    max_devices INTEGER DEFAULT 1,
    current_devices INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    features JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_plan CHECK (plan IN ('free', 'starter', 'pro', 'enterprise')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'expired', 'suspended', 'cancelled'))
);

CREATE INDEX idx_licenses_user_id ON licenses(user_id);
CREATE INDEX idx_licenses_license_key ON licenses(license_key);
CREATE INDEX idx_licenses_status ON licenses(status);

-- ===========================================
-- License Devices Table
-- ===========================================
CREATE TABLE IF NOT EXISTS license_devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    license_id UUID NOT NULL REFERENCES licenses(id) ON DELETE CASCADE,
    device_id VARCHAR(255) NOT NULL,
    device_name VARCHAR(255),
    device_info JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(license_id, device_id)
);

CREATE INDEX idx_license_devices_license_id ON license_devices(license_id);

-- ===========================================
-- Quota Usage Table
-- ===========================================
CREATE TABLE IF NOT EXISTS quota_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quota_type VARCHAR(50) NOT NULL,
    count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_quota_usage_user_id ON quota_usage(user_id);
CREATE INDEX idx_quota_usage_type_date ON quota_usage(quota_type, created_at);

-- ===========================================
-- Products Table
-- ===========================================
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tiktok_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    original_price DECIMAL(10, 2),
    currency VARCHAR(10) DEFAULT 'BRL',
    category VARCHAR(255),
    subcategory VARCHAR(255),
    seller_name VARCHAR(255),
    seller_rating DECIMAL(3, 2),
    product_rating DECIMAL(3, 2),
    reviews_count INTEGER DEFAULT 0,
    sales_count INTEGER DEFAULT 0,
    sales_7d INTEGER DEFAULT 0,
    sales_30d INTEGER DEFAULT 0,
    commission_rate DECIMAL(5, 2),
    image_url TEXT,
    images JSONB DEFAULT '[]',
    video_url TEXT,
    product_url TEXT,
    affiliate_url TEXT,
    has_free_shipping BOOLEAN DEFAULT false,
    is_trending BOOLEAN DEFAULT false,
    is_on_sale BOOLEAN DEFAULT false,
    in_stock BOOLEAN DEFAULT true,
    processed_image_url TEXT,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_tiktok_id ON products(tiktok_id);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_is_trending ON products(is_trending);
CREATE INDEX idx_products_sales_7d ON products(sales_7d DESC);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_products_updated_at ON products(updated_at);
CREATE INDEX idx_products_title_trgm ON products USING gin(title gin_trgm_ops);

-- ===========================================
-- Copy History Table
-- ===========================================
CREATE TABLE IF NOT EXISTS copy_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    platform VARCHAR(50),
    tone VARCHAR(50),
    copy_text TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    is_favorite BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_copy_history_user_id ON copy_history(user_id);
CREATE INDEX idx_copy_history_product_id ON copy_history(product_id);
CREATE INDEX idx_copy_history_created_at ON copy_history(created_at DESC);

-- ===========================================
-- Payments Table
-- ===========================================
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    license_id UUID REFERENCES licenses(id) ON DELETE SET NULL,
    external_id VARCHAR(255) UNIQUE,
    payment_method VARCHAR(50),
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'BRL',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    metadata JSONB DEFAULT '{}',
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_payment_status CHECK (status IN ('pending', 'approved', 'rejected', 'refunded', 'cancelled'))
);

CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_external_id ON payments(external_id);
CREATE INDEX idx_payments_status ON payments(status);

-- ===========================================
-- Scraping Jobs Table
-- ===========================================
CREATE TABLE IF NOT EXISTS scraping_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    params JSONB DEFAULT '{}',
    result JSONB,
    error TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_job_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX idx_scraping_jobs_status ON scraping_jobs(status);
CREATE INDEX idx_scraping_jobs_created_at ON scraping_jobs(created_at);

-- ===========================================
-- User Favorites Table
-- ===========================================
CREATE TABLE IF NOT EXISTS user_favorites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, product_id)
);

CREATE INDEX idx_user_favorites_user_id ON user_favorites(user_id);

-- ===========================================
-- Daily Stats Table
-- ===========================================
CREATE TABLE IF NOT EXISTS daily_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE UNIQUE NOT NULL,
    active_users INTEGER DEFAULT 0,
    copies_generated INTEGER DEFAULT 0,
    new_products INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    revenue DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_daily_stats_date ON daily_stats(date);

-- ===========================================
-- API Logs Table (for rate limiting and analytics)
-- ===========================================
CREATE TABLE IF NOT EXISTS api_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_logs_user_id ON api_logs(user_id);
CREATE INDEX idx_api_logs_created_at ON api_logs(created_at);
CREATE INDEX idx_api_logs_endpoint ON api_logs(endpoint);

-- ===========================================
-- Functions
-- ===========================================

-- Auto-update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables with updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_licenses_updated_at
    BEFORE UPDATE ON licenses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payments_updated_at
    BEFORE UPDATE ON payments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===========================================
-- Initial Data
-- ===========================================

-- Default admin user removed for security.
-- Please create an admin user manually or via a secure setup script.

COMMIT;
