-- ChatTrain MVP1 Database Initialization Script
-- This script sets up the initial database schema for ChatTrain

-- Enable pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- ======================
-- Main Tables
-- ======================

-- Users table (for pilot users)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'pilot_user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Sessions table (training sessions)
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    scenario_id VARCHAR(255) NOT NULL,
    scenario_version VARCHAR(50) NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active', -- active, completed, abandoned
    session_data JSONB, -- Additional session metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages table (chat messages)
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB, -- Additional message metadata
    is_masked BOOLEAN DEFAULT false, -- Whether content was masked for security
    token_count INTEGER DEFAULT 0
);

-- Feedback table (session feedback and evaluations)
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
    overall_score INTEGER CHECK (overall_score >= 0 AND overall_score <= 100),
    positive_points TEXT,
    improvement_points TEXT,
    detailed_feedback TEXT,
    rubric_scores JSONB, -- Scores for specific rubric items
    evaluator_type VARCHAR(50) DEFAULT 'llm', -- llm, human, automated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scenarios table (scenario metadata and versions)
CREATE TABLE IF NOT EXISTS scenarios (
    id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) NOT NULL,
    content_path VARCHAR(500),
    smart_goals JSONB,
    estimated_duration INTEGER, -- in minutes
    difficulty_level VARCHAR(20), -- beginner, intermediate, advanced
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(id, version)
);

-- Content embeddings table (for RAG functionality)
CREATE TABLE IF NOT EXISTS content_embeddings (
    id SERIAL PRIMARY KEY,
    scenario_id VARCHAR(255) NOT NULL,
    content_type VARCHAR(50), -- pdf, markdown, text
    content_chunk TEXT NOT NULL,
    embedding vector(1536), -- OpenAI embedding dimension
    chunk_index INTEGER,
    file_path VARCHAR(500),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System logs table
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(20) NOT NULL, -- INFO, WARNING, ERROR, DEBUG
    message TEXT NOT NULL,
    component VARCHAR(100), -- backend, frontend, database
    user_id INTEGER REFERENCES users(id),
    session_id INTEGER REFERENCES sessions(id),
    metadata JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rate limiting table
CREATE TABLE IF NOT EXISTS rate_limits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    endpoint VARCHAR(255) NOT NULL,
    request_count INTEGER DEFAULT 0,
    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, endpoint, window_start)
);

-- ======================
-- Indexes for Performance
-- ======================

-- User indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Session indexes
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_scenario_id ON sessions(scenario_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time);

-- Message indexes
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);

-- Feedback indexes
CREATE INDEX IF NOT EXISTS idx_feedback_session_id ON feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_overall_score ON feedback(overall_score);

-- Scenario indexes
CREATE INDEX IF NOT EXISTS idx_scenarios_id_version ON scenarios(id, version);
CREATE INDEX IF NOT EXISTS idx_scenarios_is_active ON scenarios(is_active);

-- Embedding indexes (using HNSW for vector similarity search)
CREATE INDEX IF NOT EXISTS idx_content_embeddings_scenario ON content_embeddings(scenario_id);
CREATE INDEX IF NOT EXISTS idx_content_embeddings_vector ON content_embeddings USING hnsw (embedding vector_cosine_ops);

-- System log indexes
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_component ON system_logs(component);
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);

-- Rate limiting indexes
CREATE INDEX IF NOT EXISTS idx_rate_limits_user_endpoint ON rate_limits(user_id, endpoint);
CREATE INDEX IF NOT EXISTS idx_rate_limits_window_start ON rate_limits(window_start);

-- ======================
-- Initial Data
-- ======================

-- Insert default pilot users (for testing)
INSERT INTO users (username, email, full_name, role) VALUES
    ('pilot1', 'pilot1@company.com', 'Pilot User 1', 'pilot_user'),
    ('pilot2', 'pilot2@company.com', 'Pilot User 2', 'pilot_user'),
    ('pilot3', 'pilot3@company.com', 'Pilot User 3', 'pilot_user'),
    ('pilot4', 'pilot4@company.com', 'Pilot User 4', 'pilot_user'),
    ('pilot5', 'pilot5@company.com', 'Pilot User 5', 'pilot_user'),
    ('admin', 'admin@company.com', 'System Administrator', 'admin')
ON CONFLICT (username) DO NOTHING;

-- Insert default scenarios
INSERT INTO scenarios (id, title, description, version, estimated_duration, difficulty_level) VALUES
    ('customer_service_v1', 'Customer Service Training', 'Basic customer service interaction training', 'v1.0.0', 30, 'beginner'),
    ('claim_handling_v1', 'Claim Handling Training', 'Insurance claim handling process training', 'v1.0.0', 30, 'intermediate')
ON CONFLICT (id, version) DO NOTHING;

-- ======================
-- Functions and Triggers
-- ======================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scenarios_updated_at BEFORE UPDATE ON scenarios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to clean up old data
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Clean up sessions older than 2 years
    DELETE FROM sessions WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '2 years';
    
    -- Clean up system logs older than 3 months
    DELETE FROM system_logs WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '3 months';
    
    -- Clean up rate limit entries older than 1 day
    DELETE FROM rate_limits WHERE window_start < CURRENT_TIMESTAMP - INTERVAL '1 day';
END;
$$ language 'plpgsql';

-- ======================
-- Database Configuration
-- ======================

-- Set timezone
SET timezone = 'UTC';

-- Enable row level security (can be configured per table as needed)
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

-- Grant permissions to the chattrain user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO chattrain;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO chattrain;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO chattrain;

-- Log successful initialization
INSERT INTO system_logs (level, message, component) 
VALUES ('INFO', 'Database schema initialized successfully', 'database');

-- Show initialization status
\echo 'ChatTrain database schema initialized successfully!'
\echo 'Tables created:'
\dt

\echo 'Indexes created:'
\di