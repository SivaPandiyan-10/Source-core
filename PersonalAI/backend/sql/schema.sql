-- SQLite schema for Personal AI Assistant (dev)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tenants (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  quota INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id INTEGER REFERENCES tenants(id),
  email TEXT UNIQUE,
  pw_hash TEXT,
  key_id TEXT,
  roles TEXT,
  created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id INTEGER REFERENCES tenants(id),
  owner_id INTEGER REFERENCES users(id),
  title TEXT,
  source_url TEXT,
  source_type TEXT,
  created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  last_ingested_at TEXT,
  sha256_url TEXT,
  meta_json TEXT
);

CREATE TABLE IF NOT EXISTS chunks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  document_id INTEGER REFERENCES documents(id),
  chunk_index INTEGER,
  text TEXT,
  token_count INTEGER,
  start_offset INTEGER,
  end_offset INTEGER,
  created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS embeddings_meta (
  vector_id TEXT PRIMARY KEY,
  chunk_id INTEGER REFERENCES chunks(id),
  tenant_id INTEGER,
  model TEXT,
  dim INTEGER,
  created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  source TEXT,
  recency_score REAL,
  source_weight REAL,
  vector_offset INTEGER,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS news_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT,
  url TEXT,
  source TEXT,
  published_at TEXT,
  category TEXT,
  summary TEXT,
  sha256_url TEXT,
  ingest_job_id TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  context_json TEXT,
  last_active_at TEXT,
  expires_at TEXT
);

CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  type TEXT,
  status TEXT,
  payload_json TEXT,
  started_at TEXT,
  finished_at TEXT,
  error_json TEXT
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
  token TEXT PRIMARY KEY,
  user_email TEXT,
  issued_at TEXT,
  expires_at TEXT
);
