-- Database initialization script for Lovable Automation Service
-- This script creates the necessary tables and indexes

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create lovable_sessions table
CREATE TABLE IF NOT EXISTS lovable_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL,
    firebase_token TEXT,
    session_cookies JSONB DEFAULT '{}',
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Additional fields for session tracking
    message_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    browser_context_id VARCHAR(255),
    page_url TEXT
);

-- Create message_queue table
CREATE TABLE IF NOT EXISTS message_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    project_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'normal',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Session assignment
    assigned_session_id UUID REFERENCES lovable_sessions(id),
    
    -- Timing
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Context and metadata
    project_context JSONB DEFAULT '{}',
    files JSONB,
    current_page VARCHAR(255) DEFAULT 'index',
    view VARCHAR(255) DEFAULT 'preview',
    
    -- Error tracking
    error_message TEXT,
    error_details JSONB DEFAULT '{}'
);

-- Create response_data table
CREATE TABLE IF NOT EXISTS response_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID REFERENCES message_queue(id) ON DELETE CASCADE,
    ai_message_id VARCHAR(255),
    success BOOLEAN DEFAULT true,
    
    -- Response content
    response_content TEXT,
    code_changes JSONB,
    
    -- Streaming data
    streaming_chunks JSONB DEFAULT '[]',
    is_streaming BOOLEAN DEFAULT false,
    is_streaming_complete BOOLEAN DEFAULT false,
    
    -- Metadata
    model_used VARCHAR(255),
    tokens_used INTEGER,
    processing_time FLOAT,
    
    -- Error information
    error_message TEXT,
    error_code VARCHAR(100),
    
    -- Timing
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Create usage_logs table for tracking and analytics
CREATE TABLE IF NOT EXISTS usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES lovable_sessions(id),
    message_id UUID REFERENCES message_queue(id),
    
    -- Usage metrics
    tokens_saved FLOAT DEFAULT 0,
    message_length INTEGER DEFAULT 0,
    request_count INTEGER DEFAULT 1,
    processing_time FLOAT,
    
    -- Timing
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create retry_queue table
CREATE TABLE IF NOT EXISTS retry_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID REFERENCES message_queue(id) ON DELETE CASCADE,
    error_message TEXT NOT NULL,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Retry configuration
    strategy VARCHAR(50) DEFAULT 'exponential_backoff',
    base_delay FLOAT DEFAULT 5.0,
    max_delay FLOAT DEFAULT 300.0,
    backoff_multiplier FLOAT DEFAULT 2.0,
    
    -- Timing
    next_retry TIMESTAMP NOT NULL,
    retry_delay FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_sessions_active ON lovable_sessions(is_active, expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_email ON lovable_sessions(email);
CREATE INDEX IF NOT EXISTS idx_sessions_last_used ON lovable_sessions(last_used_at);

CREATE INDEX IF NOT EXISTS idx_queue_status ON message_queue(status, created_at);
CREATE INDEX IF NOT EXISTS idx_queue_user ON message_queue(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_queue_project ON message_queue(project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_queue_session ON message_queue(assigned_session_id);
CREATE INDEX IF NOT EXISTS idx_queue_priority ON message_queue(priority, created_at);

CREATE INDEX IF NOT EXISTS idx_response_message ON response_data(message_id);
CREATE INDEX IF NOT EXISTS idx_response_success ON response_data(success, created_at);

CREATE INDEX IF NOT EXISTS idx_usage_session ON usage_logs(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_usage_message ON usage_logs(message_id);
CREATE INDEX IF NOT EXISTS idx_usage_date ON usage_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_retry_next ON retry_queue(next_retry);
CREATE INDEX IF NOT EXISTS idx_retry_message ON retry_queue(message_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for lovable_sessions
DROP TRIGGER IF EXISTS update_lovable_sessions_updated_at ON lovable_sessions;
CREATE TRIGGER update_lovable_sessions_updated_at
    BEFORE UPDATE ON lovable_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE OR REPLACE VIEW active_sessions AS
SELECT 
    id,
    email,
    message_count,
    error_count,
    last_used_at,
    created_at,
    expires_at,
    (expires_at > NOW()) AS is_valid
FROM lovable_sessions 
WHERE is_active = true;

CREATE OR REPLACE VIEW queue_stats AS
SELECT 
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (NOW() - created_at))) as avg_age_seconds
FROM message_queue 
GROUP BY status;

CREATE OR REPLACE VIEW session_stats AS
SELECT 
    COUNT(*) as total_sessions,
    COUNT(*) FILTER (WHERE is_active = true) as active_sessions,
    COUNT(*) FILTER (WHERE expires_at > NOW()) as valid_sessions,
    AVG(message_count) as avg_messages_per_session,
    SUM(message_count) as total_messages_processed
FROM lovable_sessions;

-- Insert sample data for testing (optional)
-- Uncomment the following lines if you want sample data

/*
-- Sample session
INSERT INTO lovable_sessions (email, is_active) 
VALUES ('test@example.com', true)
ON CONFLICT DO NOTHING;

-- Sample message
INSERT INTO message_queue (user_id, project_id, content, status)
VALUES ('test-user', 'test-project', 'Create a hello world component', 'pending')
ON CONFLICT DO NOTHING;
*/

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
