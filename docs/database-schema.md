# ChatTrain Database Schema and Migration Guide

## Overview

This document defines the complete database schema for ChatTrain MVP1, including table structures, relationships, indexes, and migration procedures. The system supports both SQLite (development) and PostgreSQL with pgvector (production).

## Database Architecture

### Development vs Production

| Environment | Database | Features |
|-------------|----------|----------|
| Development | SQLite | File-based, single connection, testing |
| Production | PostgreSQL 16 | Multi-connection, transactions, pgvector |

### Schema Versioning

- Migration files: `migrations/YYYYMMDD_HHMMSS_description.sql`
- Version tracking: `schema_migrations` table
- Automated migrations: Alembic (SQLAlchemy)

## Core Tables

### 1. Schema Migrations

```sql
-- Track applied migrations
CREATE TABLE schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(255) NOT NULL UNIQUE,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64) NOT NULL
);

-- Index for version lookup
CREATE INDEX idx_schema_migrations_version ON schema_migrations(version);
```

### 2. Scenarios

```sql
-- Training scenario definitions
CREATE TABLE scenarios (
    id VARCHAR(255) PRIMARY KEY,  -- e.g., "onboarding.claim_handling.v1"
    title VARCHAR(500) NOT NULL,
    description TEXT,
    domain VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,  -- SemVer format
    difficulty VARCHAR(20) DEFAULT 'beginner',
    duration_minutes INTEGER,
    tags TEXT[],  -- PostgreSQL array, JSON for SQLite
    smart_goals JSONB NOT NULL,  -- Array of SMART goal objects
    llm_profile JSONB NOT NULL,  -- LLM configuration
    steps JSONB NOT NULL,  -- Array of step definitions
    completion_conditions JSONB,
    attachments JSONB,  -- Array of attachment configs
    variant VARCHAR(10) DEFAULT 'A',  -- A/B testing
    metadata JSONB,
    status VARCHAR(20) DEFAULT 'active',  -- active, deprecated, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    
    -- Constraints
    CONSTRAINT chk_difficulty CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
    CONSTRAINT chk_variant CHECK (variant IN ('A', 'B')),
    CONSTRAINT chk_status CHECK (status IN ('active', 'deprecated', 'archived'))
);

-- Indexes
CREATE INDEX idx_scenarios_domain ON scenarios(domain);
CREATE INDEX idx_scenarios_status ON scenarios(status);
CREATE INDEX idx_scenarios_created_at ON scenarios(created_at);
CREATE INDEX idx_scenarios_variant ON scenarios(variant);

-- Full-text search index (PostgreSQL)
CREATE INDEX idx_scenarios_search ON scenarios USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));
```

### 3. Sessions

```sql
-- User training sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id VARCHAR(255) NOT NULL REFERENCES scenarios(id),
    user_id VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'created',
    current_step_id VARCHAR(255),
    variant VARCHAR(10) DEFAULT 'A',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completion_reason VARCHAR(100),  -- all_steps_finished, time_limit, user_exit
    session_data JSONB,  -- Custom session state
    metadata JSONB,
    
    -- Constraints
    CONSTRAINT chk_session_status CHECK (status IN ('created', 'in_progress', 'completed', 'abandoned', 'error')),
    CONSTRAINT chk_session_variant CHECK (variant IN ('A', 'B')),
    CONSTRAINT chk_completion_reason CHECK (
        completion_reason IS NULL OR 
        completion_reason IN ('all_steps_finished', 'time_limit', 'user_exit', 'system_error')
    )
);

-- Indexes
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_scenario_id ON sessions(scenario_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_started_at ON sessions(started_at);
CREATE INDEX idx_sessions_completed_at ON sessions(completed_at);
CREATE INDEX idx_sessions_last_activity ON sessions(last_activity_at);

-- Compound indexes for common queries
CREATE INDEX idx_sessions_user_status ON sessions(user_id, status);
CREATE INDEX idx_sessions_scenario_status ON sessions(scenario_id, status);
```

### 4. Messages

```sql
-- Chat messages within sessions
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    step_id VARCHAR(255),  -- Reference to scenario step
    role VARCHAR(20) NOT NULL,  -- user, assistant, system, feedback
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    token_count INTEGER,  -- For cost tracking
    response_time_ms INTEGER,  -- LLM response time
    metadata JSONB,  -- Additional message data
    
    -- Constraints
    CONSTRAINT chk_message_role CHECK (role IN ('user', 'assistant', 'system', 'feedback')),
    CONSTRAINT chk_token_count CHECK (token_count >= 0),
    CONSTRAINT chk_response_time CHECK (response_time_ms >= 0)
);

-- Indexes
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_step_id ON messages(step_id);

-- Compound index for session message retrieval
CREATE INDEX idx_messages_session_timestamp ON messages(session_id, timestamp);
```

### 5. Feedback

```sql
-- Evaluation feedback for user responses
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    step_id VARCHAR(255) NOT NULL,
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    evaluation_type VARCHAR(50) NOT NULL,  -- rule_based, gpt_judge, hybrid
    score INTEGER CHECK (score >= 0 AND score <= 100),
    criteria JSONB,  -- Detailed evaluation criteria
    comments TEXT,
    suggestions TEXT[],  -- Array of improvement suggestions
    evaluator_version VARCHAR(50),  -- Version of evaluation logic
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    
    -- Constraints
    CONSTRAINT chk_evaluation_type CHECK (
        evaluation_type IN ('rule_based', 'gpt_judge', 'hybrid', 'manual')
    )
);

-- Indexes
CREATE INDEX idx_feedback_session_id ON feedback(session_id);
CREATE INDEX idx_feedback_step_id ON feedback(step_id);
CREATE INDEX idx_feedback_evaluation_type ON feedback(evaluation_type);
CREATE INDEX idx_feedback_created_at ON feedback(created_at);

-- Compound index for session feedback retrieval
CREATE INDEX idx_feedback_session_step ON feedback(session_id, step_id);
```

### 6. Documents (Vector Storage)

```sql
-- Document chunks for RAG system
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id VARCHAR(255) NOT NULL REFERENCES scenarios(id),
    filename VARCHAR(255) NOT NULL,
    chunk_index INTEGER NOT NULL DEFAULT 0,  -- For document chunking
    content TEXT NOT NULL,
    content_type VARCHAR(50) NOT NULL,  -- pdf, markdown, text
    embedding VECTOR(1536),  -- OpenAI embedding dimension (PostgreSQL only)
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-ada-002',
    chunk_metadata JSONB,  -- Chunk-specific metadata (page numbers, sections)
    file_hash VARCHAR(64),  -- SHA-256 of original file
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    
    -- Constraints  
    CONSTRAINT chk_content_type CHECK (
        content_type IN ('pdf', 'markdown', 'text', 'html')
    ),
    CONSTRAINT chk_chunk_index CHECK (chunk_index >= 0)
);

-- Indexes
CREATE INDEX idx_documents_scenario_id ON documents(scenario_id);
CREATE INDEX idx_documents_filename ON documents(filename);
CREATE INDEX idx_documents_content_type ON documents(content_type);
CREATE INDEX idx_documents_processed_at ON documents(processed_at);

-- Vector similarity search index (PostgreSQL only)
CREATE INDEX documents_embedding_idx ON documents 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Full-text search index
CREATE INDEX idx_documents_content_search ON documents 
USING gin(to_tsvector('english', content));

-- Compound index for scenario document retrieval
CREATE INDEX idx_documents_scenario_filename ON documents(scenario_id, filename);
```

### 7. User Activity Logs

```sql
-- User activity tracking for analytics
CREATE TABLE user_activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    user_id VARCHAR(255) NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    activity_data JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,  -- For security auditing
    user_agent TEXT,
    
    -- Constraints
    CONSTRAINT chk_activity_type CHECK (
        activity_type IN (
            'session_start', 'session_end', 'message_sent', 'document_viewed',
            'feedback_received', 'export_generated', 'error_occurred'
        )
    )
);

-- Indexes
CREATE INDEX idx_activity_logs_user_id ON user_activity_logs(user_id);
CREATE INDEX idx_activity_logs_session_id ON user_activity_logs(session_id);
CREATE INDEX idx_activity_logs_activity_type ON user_activity_logs(activity_type);
CREATE INDEX idx_activity_logs_timestamp ON user_activity_logs(timestamp);

-- Compound index for user activity analysis
CREATE INDEX idx_activity_logs_user_timestamp ON user_activity_logs(user_id, timestamp);
```

### 8. System Configuration

```sql
-- System-wide configuration settings
CREATE TABLE system_config (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255)
);

-- Default configuration values
INSERT INTO system_config (key, value, description) VALUES
('llm_rate_limit', '{"requests_per_minute": 10, "tokens_per_hour": 50000}', 'LLM API rate limiting'),
('session_timeout_minutes', '60', 'Inactive session timeout'),
('max_document_size_mb', '10', 'Maximum upload document size'),
('vector_search_k', '3', 'Number of documents to retrieve for RAG'),
('evaluation_timeout_seconds', '30', 'Timeout for evaluation requests');
```

## Views and Materialized Views

### Session Summary View

```sql
-- Aggregated session statistics
CREATE VIEW session_summary AS
SELECT 
    s.id,
    s.scenario_id,
    s.user_id,
    s.status,
    s.started_at,
    s.completed_at,
    EXTRACT(EPOCH FROM (COALESCE(s.completed_at, NOW()) - s.started_at))/60 AS duration_minutes,
    COUNT(m.id) AS message_count,
    COUNT(f.id) AS feedback_count,
    AVG(f.score) AS average_score,
    MAX(f.score) AS max_score,
    MIN(f.score) AS min_score
FROM sessions s
LEFT JOIN messages m ON s.id = m.session_id
LEFT JOIN feedback f ON s.id = f.session_id
GROUP BY s.id, s.scenario_id, s.user_id, s.status, s.started_at, s.completed_at;
```

### Scenario Performance View

```sql
-- Scenario completion and performance metrics
CREATE VIEW scenario_performance AS
SELECT 
    sc.id AS scenario_id,
    sc.title,
    sc.domain,
    COUNT(s.id) AS total_sessions,
    COUNT(CASE WHEN s.status = 'completed' THEN 1 END) AS completed_sessions,
    ROUND(
        100.0 * COUNT(CASE WHEN s.status = 'completed' THEN 1 END) / NULLIF(COUNT(s.id), 0), 
        2
    ) AS completion_rate,
    AVG(
        CASE WHEN s.status = 'completed' 
        THEN EXTRACT(EPOCH FROM (s.completed_at - s.started_at))/60 
        END
    ) AS avg_completion_time_minutes,
    AVG(f.score) AS avg_score
FROM scenarios sc
LEFT JOIN sessions s ON sc.id = s.scenario_id
LEFT JOIN feedback f ON s.id = f.session_id
GROUP BY sc.id, sc.title, sc.domain;
```

## Database Functions

### Update Last Activity

```sql
-- Function to update session last activity
CREATE OR REPLACE FUNCTION update_session_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sessions 
    SET last_activity_at = CURRENT_TIMESTAMP
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update session activity
CREATE TRIGGER trigger_update_session_activity
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_session_activity();
```

### Vector Search Function

```sql
-- Function for semantic document search (PostgreSQL only)
CREATE OR REPLACE FUNCTION search_documents(
    query_embedding VECTOR(1536),
    scenario_filter VARCHAR(255) DEFAULT NULL,
    limit_count INTEGER DEFAULT 3
)
RETURNS TABLE(
    document_id UUID,
    filename VARCHAR(255),
    content TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id,
        d.filename,
        d.content,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM documents d
    WHERE (scenario_filter IS NULL OR d.scenario_id = scenario_filter)
    ORDER BY d.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;
```

## Migration Files

### Migration 001: Initial Schema

```sql
-- migrations/20250622_000001_initial_schema.sql
-- Description: Create initial database schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable vector extension (PostgreSQL only)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create all tables in dependency order
-- (Include all CREATE TABLE statements from above)
```

### Migration 002: Add Indexes

```sql
-- migrations/20250622_000002_add_indexes.sql
-- Description: Add performance indexes

-- (Include all CREATE INDEX statements from above)
```

### Migration 003: Add Views

```sql
-- migrations/20250622_000003_add_views.sql
-- Description: Create reporting views

-- (Include all CREATE VIEW statements from above)
```

## Data Retention and Cleanup

### Automated Cleanup Jobs

```sql
-- Clean up old abandoned sessions (>7 days inactive)
DELETE FROM sessions 
WHERE status IN ('created', 'in_progress') 
AND last_activity_at < CURRENT_TIMESTAMP - INTERVAL '7 days';

-- Archive completed sessions older than 2 years
UPDATE sessions 
SET status = 'archived',
    metadata = COALESCE(metadata, '{}') || '{"archived_at": "' || CURRENT_TIMESTAMP || '"}'
WHERE status = 'completed' 
AND completed_at < CURRENT_TIMESTAMP - INTERVAL '2 years';

-- Clean up orphaned documents
DELETE FROM documents 
WHERE scenario_id NOT IN (SELECT id FROM scenarios);

-- Clean up old activity logs (>90 days)
DELETE FROM user_activity_logs 
WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '90 days';
```

## Performance Optimization

### Query Optimization Tips

1. **Session Queries**: Always include session_id in WHERE clauses
2. **Message Retrieval**: Use timestamp ordering for pagination
3. **Vector Search**: Limit embedding queries to specific scenarios
4. **Feedback Analysis**: Use pre-aggregated views for reporting

### Index Maintenance

```sql
-- Reindex vector search (PostgreSQL)
REINDEX INDEX documents_embedding_idx;

-- Update table statistics
ANALYZE sessions;
ANALYZE messages;
ANALYZE feedback;
ANALYZE documents;
```

### Connection Pooling

```python
# SQLAlchemy configuration
DATABASE_CONFIG = {
    'pool_size': 20,
    'max_overflow': 30,
    'pool_timeout': 30,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
```

## Backup and Recovery

### Development (SQLite)

```bash
# Backup
sqlite3 chattrain.db ".backup backup.db"

# Restore
cp backup.db chattrain.db
```

### Production (PostgreSQL)

```bash
# Backup
pg_dump -h localhost -U chattrain -d chattrain > backup.sql

# Restore
psql -h localhost -U chattrain -d chattrain < backup.sql
```

---

This database schema provides the complete foundation for TDD implementation with proper relationships, indexes, and performance optimization for ChatTrain MVP1.