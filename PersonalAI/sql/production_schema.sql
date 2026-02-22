-- PostgreSQL Production Schema for Personal AI Assistant
-- This schema includes all tables, indexes, and policies for multi-tenant deployment

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- AUTHENTICATION & USERS
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(255),
  organization_id UUID,  -- For multi-tenancy
  encryption_key BYTEA NOT NULL,  -- Per-user key (encrypted with master key)
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE,
  mfa_enabled BOOLEAN DEFAULT FALSE,
  mfa_secret VARCHAR(255),
  -- Privacy & Compliance
  data_retention_days INT DEFAULT 730,  -- 2 years default
  gdpr_consent BOOLEAN DEFAULT FALSE,
  email_opt_in BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_organization_id ON users(organization_id);

-- Row-Level Security for multi-tenancy
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_self_access ON users
  USING (user_id = CURRENT_SETTING('app.current_user_id')::uuid);

CREATE TABLE IF NOT EXISTS sessions (
  session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE NOT NULL,
  jwt_token_hash VARCHAR(255) UNIQUE NOT NULL,
  refresh_token_hash VARCHAR(255) UNIQUE,
  ip_address INET,
  user_agent TEXT,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_revoked BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- ============================================================================
-- DOCUMENTS & KNOWLEDGE BASE
-- ============================================================================

CREATE TABLE IF NOT EXISTS documents (
  doc_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE NOT NULL,
  source_type VARCHAR(50) NOT NULL,  -- 'local_upload', 'rss_feed', 'web_crawl', 'api'
  source_url VARCHAR(2048),
  source_name VARCHAR(255),
  title VARCHAR(512) NOT NULL,
  description TEXT,
  raw_content TEXT,
  content_hash BYTEA,  -- SHA256(content) for deduplication
  file_size_bytes BIGINT,
  file_name VARCHAR(255),
  mime_type VARCHAR(100),
  -- Classification & Metadata
  category VARCHAR(100),
  tags VARCHAR(255)[],  -- Array of tags
  language VARCHAR(10) DEFAULT 'en',
  -- Lifecycle
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  published_at TIMESTAMP,
  accessed_at TIMESTAMP,
  archived_at TIMESTAMP,
  is_archived BOOLEAN DEFAULT FALSE,
  is_encrypted BOOLEAN DEFAULT FALSE,
  
  -- Tracking
  retrieval_count INT DEFAULT 0,
  last_retrieved_at TIMESTAMP,
  embedding_generated BOOLEAN DEFAULT FALSE,
  embedding_model VARCHAR(255),
  
  CONSTRAINT unique_user_content_hash UNIQUE (user_id, content_hash)
);

CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_source_type ON documents(source_type);
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX idx_documents_archived ON documents(is_archived);
CREATE INDEX idx_documents_content_hash ON documents(content_hash);
CREATE INDEX idx_documents_tags ON documents USING GIN(tags);

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY documents_user_isolation ON documents
  USING (user_id = CURRENT_SETTING('app.current_user_id')::uuid);

CREATE TABLE IF NOT EXISTS document_chunks (
  chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  doc_id UUID REFERENCES documents(doc_id) ON DELETE CASCADE NOT NULL,
  sequence_num INT NOT NULL,  -- Order within document
  chunk_text TEXT NOT NULL,
  token_count INT,
  char_count INT,
  chunk_hash BYTEA,
  is_encrypted BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  CONSTRAINT unique_doc_sequence UNIQUE (doc_id, sequence_num)
);

CREATE INDEX idx_chunks_doc_id ON document_chunks(doc_id);
CREATE INDEX idx_chunks_sequence ON document_chunks(doc_id, sequence_num);

-- ============================================================================
-- VECTOR EMBEDDINGS (Metadata Only)
-- ============================================================================

CREATE TABLE IF NOT EXISTS chunk_vectors (
  vector_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chunk_id UUID REFERENCES document_chunks(chunk_id) ON DELETE CASCADE NOT NULL,
  doc_id UUID REFERENCES documents(doc_id) ON DELETE CASCADE NOT NULL,
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE NOT NULL,
  
  -- Embedding Metadata
  embedding_model VARCHAR(255) NOT NULL,  -- "sentence-transformers/all-MiniLM-L6-v2"
  embedding_dim INT NOT NULL,
  embedding_vector VECTOR,  -- For PgVector (384-dim with MiniLM-L6-v2)
  vector_hash BYTEA,
  
  -- Ranking Signals
  source_weight FLOAT DEFAULT 0.5,  -- 0.9=RSS, 0.5=Local, 0.3=Web
  recency_score FLOAT,  -- 1.0 = today, decays with time
  relevance_baseline FLOAT DEFAULT 0.5,
  
  -- Tracking
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  retrieval_count INT DEFAULT 0,
  
  CONSTRAINT unique_chunk_embedding UNIQUE (chunk_id, embedding_model)
);

CREATE INDEX idx_chunk_vectors_user_id ON chunk_vectors(user_id);
CREATE INDEX idx_chunk_vectors_doc_id ON chunk_vectors(doc_id);
CREATE INDEX idx_chunk_vectors_embedding_model ON chunk_vectors(embedding_model);
CREATE INDEX idx_chunk_vectors_vector ON chunk_vectors USING IVFFlat (embedding_vector vector_cosine_ops);

ALTER TABLE chunk_vectors ENABLE ROW LEVEL SECURITY;
CREATE POLICY chunk_vectors_user_isolation ON chunk_vectors
  USING (user_id = CURRENT_SETTING('app.current_user_id')::uuid);

-- ============================================================================
-- RSS FEEDS & WEB INGESTION
-- ============================================================================

CREATE TABLE IF NOT EXISTS rss_feeds (
  feed_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE NOT NULL,
  feed_url VARCHAR(2048) NOT NULL,
  feed_name VARCHAR(255) NOT NULL,
  feed_description TEXT,
  category VARCHAR(100),
  source_weight FLOAT DEFAULT 0.8,  -- Reliability weight
  fetch_interval_minutes INT DEFAULT 1440,  -- Default: daily
  last_fetched TIMESTAMP,
  last_successful_fetch TIMESTAMP,
  consecutive_failures INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE,
  
  CONSTRAINT unique_url_per_user UNIQUE (user_id, feed_url)
);

CREATE INDEX idx_rss_feeds_user_id ON rss_feeds(user_id);
CREATE INDEX idx_rss_feeds_active_next_fetch ON rss_feeds(is_active, last_fetched) 
  WHERE is_active = TRUE;

ALTER TABLE rss_feeds ENABLE ROW LEVEL SECURITY;
CREATE POLICY rss_feeds_user_isolation ON rss_feeds
  USING (user_id = CURRENT_SETTING('app.current_user_id')::uuid);

CREATE TABLE IF NOT EXISTS articles (
  article_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  feed_id UUID REFERENCES rss_feeds(feed_id) ON DELETE CASCADE NOT NULL,
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE NOT NULL,
  
  -- Article Identifiers
  url_hash BYTEA NOT NULL,  -- SHA256(URL)
  url VARCHAR(2048),
  title VARCHAR(512) NOT NULL,
  description TEXT,
  body_content TEXT,
  
  -- Metadata
  author VARCHAR(255),
  published_date TIMESTAMP,
  ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  -- Tracking
  is_read BOOLEAN DEFAULT FALSE,
  is_saved BOOLEAN DEFAULT FALSE,
  is_archived BOOLEAN DEFAULT FALSE,
  relevance_score FLOAT DEFAULT 0.5,
  
  -- Content Quality
  body_length INT,
  image_count INT DEFAULT 0,
  
  CONSTRAINT unique_feed_url UNIQUE (feed_id, url_hash)
);

CREATE INDEX idx_articles_feed_id ON articles(feed_id);
CREATE INDEX idx_articles_user_id ON articles(user_id);
CREATE INDEX idx_articles_published_date ON articles(published_date DESC);
CREATE INDEX idx_articles_ingested_at ON articles(ingested_at DESC);
CREATE INDEX idx_articles_url_hash ON articles(url_hash);

ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
CREATE POLICY articles_user_isolation ON articles
  USING (user_id = CURRENT_SETTING('app.current_user_id')::uuid);

-- ============================================================================
-- SESSION MEMORY & INTERACTIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS session_memory (
  memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE NOT NULL,
  session_id UUID REFERENCES sessions(session_id) ON DELETE SET NULL,
  
  -- Memory Content
  memory_type VARCHAR(50) NOT NULL,  -- 'turn', 'note', 'reminder', 'fact'
  content TEXT NOT NULL,
  structured_data JSONB,  -- For structured recalls
  
  -- Context
  context_metadata JSONB,
  relevant_documents UUID[],  -- Array of doc_ids
  source_model VARCHAR(255),  -- Which model generated this
  
  -- Lifecycle
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP,  -- For short-term memory expiration
  accessed_at TIMESTAMP,
  
  CONSTRAINT memory_not_expired CHECK (expires_at IS NULL OR expires_at > created_at)
);

CREATE INDEX idx_session_memory_user_id ON session_memory(user_id);
CREATE INDEX idx_session_memory_session_id ON session_memory(session_id);
CREATE INDEX idx_session_memory_created_at ON session_memory(created_at DESC);
CREATE INDEX idx_session_memory_expires_at ON session_memory(expires_at) 
  WHERE expires_at IS NOT NULL;

ALTER TABLE session_memory ENABLE ROW LEVEL SECURITY;
CREATE POLICY session_memory_user_isolation ON session_memory
  USING (user_id = CURRENT_SETTING('app.current_user_id')::uuid);

CREATE TABLE IF NOT EXISTS interactions (
  interaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE NOT NULL,
  session_id UUID REFERENCES sessions(session_id) ON DELETE SET NULL,
  
  -- Interaction Details
  interaction_type VARCHAR(50),  -- 'chat', 'search', 'document_upload', 'feedback'
  query_text TEXT,
  response_text TEXT,
  
  -- RAG Context
  retrieved_documents UUID[],
  retrieved_count INT DEFAULT 0,
  retrieval_latency_ms INT,
  
  -- LLM Metrics
  model_used VARCHAR(255),
  completion_tokens INT,
  query_tokens INT,
  total_tokens INT,
  generation_latency_ms INT,
  
  -- Feedback
  user_rating INT,  -- 1-5 stars
  user_feedback TEXT,
  
  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ip_address INET,
  user_agent TEXT,
  
  CONSTRAINT valid_rating CHECK (user_rating IS NULL OR (user_rating >= 1 AND user_rating <= 5))
);

CREATE INDEX idx_interactions_user_id ON interactions(user_id);
CREATE INDEX idx_interactions_session_id ON interactions(session_id);
CREATE INDEX idx_interactions_created_at ON interactions(created_at DESC);

ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY interactions_user_isolation ON interactions
  USING (user_id = CURRENT_SETTING('app.current_user_id')::uuid);

-- ============================================================================
-- FINANCIAL DATA (Encrypted at Rest)
-- ============================================================================

CREATE TABLE IF NOT EXISTS expenses (
  expense_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE NOT NULL,
  
  -- Financial Details (encrypted in app layer)
  date_recorded DATE NOT NULL,
  amount NUMERIC(12, 2) NOT NULL,
  category VARCHAR(100),
  subcategory VARCHAR(100),
  description TEXT,
  
  -- Metadata
  method VARCHAR(50),  -- 'cash', 'credit_card', 'bank_transfer'
  merchant VARCHAR(255),
  tags VARCHAR(255)[],
  
  -- Encryption
  is_encrypted BOOLEAN DEFAULT TRUE,
  encrypted_details BYTEA,
  
  -- Tracking
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  CONSTRAINT expense_amount_positive CHECK (amount > 0)
);

CREATE INDEX idx_expenses_user_id ON expenses(user_id);
CREATE INDEX idx_expenses_date_recorded ON expenses(user_id, date_recorded DESC);
CREATE INDEX idx_expenses_category ON expenses(user_id, category);

ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;
CREATE POLICY expenses_user_isolation ON expenses
  USING (user_id = CURRENT_SETTING('app.current_user_id')::uuid);

CREATE TABLE IF NOT EXISTS budget_allocations (
  budget_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE NOT NULL,
  category VARCHAR(100) NOT NULL,
  monthly_limit NUMERIC(12, 2),
  alert_threshold_percent INT DEFAULT 80,  -- Alert at 80%
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  CONSTRAINT unique_user_category UNIQUE (user_id, category)
);

CREATE INDEX idx_budget_allocations_user_id ON budget_allocations(user_id);

-- ============================================================================
-- AUDIT & LOGGING
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
  log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
  
  -- Action Details
  action VARCHAR(100),  -- 'login', 'knowledge_upload', 'chat_query', 'export_data'
  resource_type VARCHAR(50),
  resource_id UUID,
  status VARCHAR(20),  -- 'success', 'failure', 'warning'
  error_message TEXT,
  
  -- Context
  ip_address INET,
  user_agent TEXT,
  endpoint VARCHAR(255),
  http_method VARCHAR(10),
  http_status_code INT,
  
  -- Performance
  duration_ms INT,
  
  -- Extra Details
  details JSONB,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_log_user_id ON audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_log_action ON audit_log(action, created_at DESC);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id);

-- ============================================================================
-- RATE LIMITING & QUOTAS
-- ============================================================================

CREATE TABLE IF NOT EXISTS rate_limits (
  limit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE NOT NULL,
  endpoint VARCHAR(255),
  request_count INT DEFAULT 0,
  window_start TIMESTAMP NOT NULL,
  window_end TIMESTAMP NOT NULL,
  
  CONSTRAINT unique_user_endpoint_window UNIQUE (user_id, endpoint, window_start),
  CONSTRAINT window_valid CHECK (window_end > window_start)
);

CREATE INDEX idx_rate_limits_user_endpoint ON rate_limits(user_id, endpoint, window_start DESC);

CREATE TABLE IF NOT EXISTS user_quotas (
  quota_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE NOT NULL,
  
  -- Monthly Quotas
  documents_per_month INT DEFAULT 1000,
  api_calls_per_month INT DEFAULT 100000,
  storage_gb INT DEFAULT 50,
  concurrent_sessions INT DEFAULT 5,
  
  -- Tracking
  documents_used INT DEFAULT 0,
  api_calls_used INT DEFAULT 0,
  storage_used_gb INT DEFAULT 0,
  
  reset_date DATE DEFAULT CURRENT_DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  CONSTRAINT unique_user_quota UNIQUE (user_id, reset_date)
);

CREATE INDEX idx_user_quotas_user_id ON user_quotas(user_id);

-- ============================================================================
-- VECTOR SCHEMA (for PgVector Extension)
-- ============================================================================

-- Note: The embedding_vector column in chunk_vectors uses PgVector
-- Install: CREATE EXTENSION pgvector;
-- Usage: embedding_vector VECTOR (stored as E'[...]')
-- Query:
--   SELECT * FROM chunk_vectors 
--   WHERE embedding_vector <-> query_embedding < 0.5
--   ORDER BY embedding_vector <-> query_embedding
--   LIMIT 10;

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rss_feeds_updated_at BEFORE UPDATE ON rss_feeds
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- GDPR: Hard delete helper
CREATE OR REPLACE FUNCTION gdpr_delete_user(delete_user_id UUID)
RETURNS void AS $$
BEGIN
  DELETE FROM interactions WHERE user_id = delete_user_id;
  DELETE FROM session_memory WHERE user_id = delete_user_id;
  DELETE FROM chunk_vectors WHERE user_id = delete_user_id;
  DELETE FROM articles WHERE user_id = delete_user_id;
  DELETE FROM expenses WHERE user_id = delete_user_id;
  DELETE FROM budget_allocations WHERE user_id = delete_user_id;
  DELETE FROM document_chunks WHERE doc_id IN (
    SELECT doc_id FROM documents WHERE user_id = delete_user_id
  );
  DELETE FROM documents WHERE user_id = delete_user_id;
  DELETE FROM rss_feeds WHERE user_id = delete_user_id;
  DELETE FROM sessions WHERE user_id = delete_user_id;
  DELETE FROM users WHERE user_id = delete_user_id;
  
  INSERT INTO audit_log(action, status, details)
  VALUES ('gdpr_delete_user', 'success', jsonb_build_object('user_id', delete_user_id));
END;
$$ LANGUAGE plpgsql;

-- Maintenance: Auto-cleanup expired sessions & short-term memory
CREATE OR REPLACE FUNCTION cleanup_expired_data()
RETURNS void AS $$
BEGIN
  DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP;
  DELETE FROM session_memory WHERE expires_at < CURRENT_TIMESTAMP;
  DELETE FROM articles WHERE archived_at < CURRENT_TIMESTAMP - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- MATERIALIZED VIEWS (for Analytics & Dashboards)
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS user_stats_mv AS
SELECT
  u.user_id,
  u.email,
  COUNT(DISTINCT d.doc_id) as total_documents,
  COUNT(DISTINCT i.interaction_id) as total_interactions,
  MAX(u.last_login) as last_active,
  COUNT(DISTINCT CASE WHEN i.created_at > NOW() - INTERVAL '30 days' THEN i.interaction_id END) as interactions_30d
FROM users u
LEFT JOIN documents d ON u.user_id = d.user_id
LEFT JOIN interactions i ON u.user_id = i.user_id
GROUP BY u.user_id, u.email;

CREATE UNIQUE INDEX idx_user_stats_mv_user_id ON user_stats_mv(user_id);

-- Performance statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS performance_stats_mv AS
SELECT
  TRUNC(i.created_at) as date,
  i.model_used,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY i.retrieval_latency_ms) as p50_retrieval_ms,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY i.retrieval_latency_ms) as p95_retrieval_ms,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY i.generation_latency_ms) as p50_generation_ms,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY i.generation_latency_ms) as p95_generation_ms,
  AVG(i.user_rating) as avg_user_rating,
  COUNT(*) as total_queries
FROM interactions i
GROUP BY TRUNC(i.created_at), i.model_used;

-- ============================================================================
-- SETTINGS & CONFIGURATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_preferences (
  pref_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE NOT NULL UNIQUE,
  
  -- UI Preferences
  theme VARCHAR(20) DEFAULT 'light',  -- 'light', 'dark', 'auto'
  language VARCHAR(10) DEFAULT 'en',
  timezone VARCHAR(50) DEFAULT 'UTC',
  
  -- Notification Settings
  email_notifications BOOLEAN DEFAULT TRUE,
  digest_frequency VARCHAR(20) DEFAULT 'weekly',  -- 'daily', 'weekly', 'never'
  alert_expense_threshold BOOLEAN DEFAULT TRUE,
  
  -- Privacy Settings
  allow_web_scraping BOOLEAN DEFAULT TRUE,
  share_usage_analytics BOOLEAN DEFAULT FALSE,
  local_only_mode BOOLEAN DEFAULT FALSE,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Recent documents with retrieval stats
CREATE OR REPLACE VIEW recent_documents_view AS
SELECT
  d.doc_id,
  d.user_id,
  d.title,
  d.source_type,
  d.created_at,
  d.retrieval_count,
  COUNT(dc.chunk_id) as total_chunks,
  COALESCE(SUM(dc.token_count), 0) as total_tokens
FROM documents d
LEFT JOIN document_chunks dc ON d.doc_id = dc.doc_id
GROUP BY d.doc_id, d.user_id, d.title, d.source_type, d.created_at, d.retrieval_count;

-- User activity summary
CREATE OR REPLACE VIEW user_activity_view AS
SELECT
  u.user_id,
  u.email,
  COUNT(DISTINCT i.interaction_id) FILTER (WHERE i.created_at > NOW() - INTERVAL '7 days') as interactions_7d,
  COUNT(DISTINCT i.interaction_id) FILTER (WHERE i.created_at > NOW() - INTERVAL '30 days') as interactions_30d,
  MAX(i.created_at) as last_interaction_at
FROM users u
LEFT JOIN interactions i ON u.user_id = i.user_id
GROUP BY u.user_id, u.email;
