# Personal AI Assistant — Production Architecture

## Executive Summary

A modular, production-ready Personal AI system combining:
- **Angular** frontend (ChatGPT-style UI)
- **Python FastAPI** orchestration layer
- **C++ Core Engine** for financial calculations and encryption
- **Local Ollama LLM** + streaming
- **FAISS/PostgreSQL** vector storage
- **Multi-source** knowledge ingestion (local files, RSS, web crawling)
- **JWT + encryption** security
- **SaaS-scalable** multi-tenant architecture

---

## 1. Component Architecture

### High-Level Tier Breakdown

```
┌─────────────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                          │
│            Angular Web Frontend (TypeScript)                 │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ • Chat Interface (streaming)    • Analytics Dashboard   │ │
│  │ • File Upload (drag-drop)       • News Feed Viewer      │ │
│  │ • Knowledge Management          • Settings & Auth       │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS/WebSocket
┌──────────────────────┴──────────────────────────────────────┐
│              ORCHESTRATION LAYER (FastAPI)                  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ • API Gateway (auth, rate-limit)                        │ │
│  │ • RAG Pipeline (query → embedding → retrieval)          │ │
│  │ • WebSocket/SSE for streaming                           │ │
│  │ • Job Scheduler (Celery)                                │ │
│  │ • Web Ingestion  (RSS + crawling)                        │ │
│  └─────────────────────────────────────────────────────────┘ │
└────┬──────────────────────────────────────────┬──────────────┘
     │ REST/gRPC                                │
┌────┴────────────────────────┐    ┌───────────┴─────────────┐
│   C++ CORE ENGINE            │    │ EMBEDDING MICROSERVICE  │
│ ┌──────────────────────────┐ │    │ ┌───────────────────┐  │
│ │ Memory Management        │ │    │ │ REST API: /embed  │  │
│ │ Encryption (libsodium)   │ │    │ │ Sentence-Transform│  │
│ │ Financial Calculations   │ │    │ │ MiniLM-L6-v2      │  │
│ │ Structured DB Ops        │ │    │ └───────────────────┘  │
│ │ Vector Similarity Calc   │ │    └────────────────────────┘
│ └──────────────────────────┘ │
└─────┬──────────────────────────┘
      │ IPC/Sockets
┌─────┴──────────────────────────┐
│   DATA LAYER                    │
│ ┌────────────────────────────┐ │
│ │ SQLite (dev)/PostgreSQL    │ │
│ │ • Structured data          │ │
│ │ • Users, sessions, config  │ │
│ │ • Financial ledger         │ │
│ └────────────────────────────┘ │
│ ┌────────────────────────────┐ │
│ │ FAISS (dev)/Milvus (prod)  │ │
│ │ • Vector embeddings        │ │
│ │ • Similarity search        │ │
│ └────────────────────────────┘ │
│ ┌────────────────────────────┐ │
│ │ Redis Cache                │ │
│ │ • Session tokens           │ │
│ │ • Rate-limit counters      │ │
│ └────────────────────────────┘ │
└────────────────────────────────┘
```

### Service Deployment Topology

```
┌──────────────────────────────────┐
│  Docker Container Registry       │
├──────────────────────────────────┤
│ • personal-ai-frontend:v1.0      │ (Node.js + Nginx)
│ • personal-ai-api:v1.0           │ (FastAPI)
│ • personal-ai-core:v1.0          │ (C++ gRPC server)
│ • personal-ai-embeddings:v1.0    │ (FastAPI + Transformers)
│ • personal-ai-scheduler:v1.0     │ (Celery worker)
└──────────────────────────────────┘
         │
┌────────┴────────────────────────────────────────┐
│      Docker Compose / Kubernetes                │
├─────────────────────────────────────────────────┤
│ Frontend Pod:  personal-ai-frontend             │
│ API Pod (3x):  personal-ai-api (load-balanced) │
│ Core Pod:      personal-ai-core                 │
│ Embed Pod (2x):personal-ai-embeddings           │
│ Schedule Pod:  personal-ai-scheduler            │
│ Cache:         Redis                            │
│ Database:      PostgreSQL + PgVector            │
│ Vector DB:     Milvus                           │
│ Monitor:       Prometheus + Grafana             │
│ Logs:          ELK Stack (optional)             │
└─────────────────────────────────────────────────┘
```

---

## 2. Data Flow Diagram

### Chat Query → LLM Response Flow

```
User Input (Chat Message)
    ↓
[1] Frontend WebSocket → API Gateway (JWT validated)
    ↓
[2] API extracts query → Embedding Service (REST call)
    ↓
[3] Embedding returned as vector [384-dim for MiniLM-L6]
    ↓
[4] Query → FAISS Index (cosine similarity search, k=20)
    ↓
[5] Retrieve top-K documents with:
    • Metadata (source, date, category)
    • Hybrid ranking: 0.7*relevance + 0.2*recency + 0.1*source_weight
    ↓
[6] Construct RAG prompt:
    SYSTEM: "You are a personal AI assistant with knowledge from:"
    CONTEXT: [retrieved docs ranked by hybrid score]
    USER: [original query]
    ↓
[7] Stream to Ollama LLM (e.g., mistral, llama2)
    ↓
[8] LLM generates response in chunks
    ↓
[9] Stream to WebSocket client (delta tokens)
    ↓
[10] Frontend renders + logs to session memory → C++ Core Engine
    ↓
[11] Response complete → store in long-term DB
```

### Knowledge Ingestion Flow (Local Files)

```
User uploads: [file.pdf, doc.docx, text.txt]
    ↓
[1] File stored in staging directory
    ↓
[2] Content extraction (pdfplumber/python-docx/plain text)
    ↓
[3] Text cleaning (HTML tags, special chars, lower-case)
    ↓
[4] Chunking: 500-token overlapping segments (stride=250)
    ↓
[5] For each chunk:
    a) Generate embedding via Embedding Service
    b) Compute hash(chunk) for dedup
    c) Store in FAISS with metadata:
       - user_id, source_file, chunk_id
       - timestamp, category (optional)
       - hash(content)
    ↓
[6] Index written to persistent storage
    ↓
[7] Notification: "3 documents indexed with 42 chunks"
```

### Web Ingestion Flow (RSS + Crawling)

```
Daily 02:00 UTC - Scheduler triggers ingestion
    ↓
[1] Fetch RSS feeds: [tech_news, finance, news]
    ↓
[2] For each article:
    a) Extract: title, URL, date, description
    b) Deduplicate: hash(URL) in DB?
    c) If new: crawl full article HTML
    d) Clean HTML (remove ads, tracking, boilerplate)
    e) Extract body text
    ↓
[3] Chunk article (500-token segments)
    ↓
[4] For each chunk:
    a) Embed via microservice
    b) Store metadata: source_url, feed_name, article_date
    c) source_weight: tech_news=0.9, finance=0.8, ...
    ↓
[5] Maintain recency index: boost (1 + daysSince/365)^0.5
    ↓
[6] Cleanup: remove articles older than 90 days
    ↓
[7] Log: "Ingested 47 articles, 523 chunks, 12 duplicates skipped"
```

---

## 3. API Endpoints

### REST API (FastAPI)

```
Authentication:
  POST   /api/v1/auth/register
  POST   /api/v1/auth/login
  POST   /api/v1/auth/logout
  POST   /api/v1/auth/refresh
  GET    /api/v1/auth/me

Chat:
  WebSocket /ws/chat/{session_id}  (streaming chat)
  GET    /api/v1/chat/history/{limit}
  POST   /api/v1/chat/clear-session

Knowledge:
  POST   /api/v1/knowledge/upload      (single file)
  POST   /api/v1/knowledge/upload-batch (multiple)
  GET    /api/v1/knowledge/list
  GET    /api/v1/knowledge/{id}
  DELETE /api/v1/knowledge/{id}
  POST   /api/v1/knowledge/search      (semantic search)
  POST   /api/v1/knowledge/index-scan  (trigger local scan)

News Feed:
  GET    /api/v1/news/feeds
  POST   /api/v1/news/subscribe
  DELETE /api/v1/news/unsubscribe/{feed_id}
  GET    /api/v1/news/articles?limit=50&offset=0
  POST   /api/v1/news/ingest-now      (trigger crawler)

Analytics:
  GET    /api/v1/analytics/summary
  GET    /api/v1/analytics/usage
  GET    /api/v1/analytics/knowledge-stats
  GET    /api/v1/analytics/interaction-heatmap

Financial (via C++ Core):
  POST   /api/v1/finance/record-expense
  GET    /api/v1/finance/summary
  GET    /api/v1/finance/trends
  POST   /api/v1/finance/budget-alert

Settings:
  GET    /api/v1/settings
  PATCH  /api/v1/settings
  POST   /api/v1/settings/change-password
  POST   /api/v1/settings/export-data

Admin:
  GET    /api/v1/admin/users
  GET    /api/v1/admin/logs
  POST   /api/v1/admin/cleanup-vectors
  POST   /api/v1/admin/reindex-faiss

Health:
  GET    /health
  GET    /health/readiness
  GET    /metrics (Prometheus)
```

### Embedding Microservice

```
POST /embed
  Request:
    {
      "text": "sample text",
      "model": "sentence-transformers/all-MiniLM-L6-v2"
    }
  Response:
    {
      "embedding": [float... 384 dims],
      "model": "...",
      "tokens": 5
    }

GET /models
  Returns: [{"name": "all-MiniLM-L6-v2", "dims": 384, ...}]

GET /health
  Returns: {"status": "ready"}
```

### C++ Core gRPC API

```
service CoreEngine {
  rpc EncryptString(EncryptRequest) returns (EncryptResponse);
  rpc DecryptString(DecryptRequest) returns (DecryptResponse);
  rpc CalculateFinancial(FinancialQuery) returns (FinancialResult);
  rpc QueryVectorSimilarity(VectorQuery) returns (VectorResults);
  rpc StoreMemory(MemoryItem) returns (MemoryID);
  rpc RetrieveMemory(MemoryQuery) returns (MemoryItems);
}
```

---

## 4. Database Schema

### SQLite / PostgreSQL Schema

```sql
-- Users & Authentication
CREATE TABLE users (
  user_id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash BYTEA NOT NULL,
  encryption_key BYTEA NOT NULL,  -- Per-user key, encrypted with master key
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE sessions (
  session_id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
  jwt_token TEXT NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge Base
CREATE TABLE documents (
  doc_id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
  source_type ENUM('local_upload', 'rss_feed', 'web_crawl'),
  source_url VARCHAR(2048),
  source_name VARCHAR(255),
  title VARCHAR(255),
  raw_content TEXT,
  content_hash BYTEA,  -- SHA256(content) for deduplication
  file_size_bytes BIGINT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_archived BOOLEAN DEFAULT FALSE
);

CREATE TABLE document_chunks (
  chunk_id UUID PRIMARY KEY,
  doc_id UUID REFERENCES documents(doc_id) ON DELETE CASCADE,
  sequence_num INT,  -- Order within document
  chunk_text TEXT NOT NULL,
  token_count INT,
  chunk_hash BYTEA,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vector Embeddings (metadata only; vectors go to FAISS/Milvus)
CREATE TABLE chunk_vectors (
  vector_id UUID PRIMARY KEY,
  chunk_id UUID REFERENCES document_chunks(chunk_id) ON DELETE CASCADE,
  doc_id UUID REFERENCES documents(doc_id),
  user_id UUID REFERENCES users(user_id),
  embedding_model VARCHAR(100),  -- "sentence-transformers/all-MiniLM-L6-v2"
  embedding_dim INT,
  vector_hash BYTEA,  -- Hash of embedding for dedup
  source_weight FLOAT DEFAULT 0.5,  -- 0.9 for finance, 0.5 local
  recency_score FLOAT,  -- Temporal decay
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  -- Vector binary data stored in FAISS/Milvus with same vector_id
);

-- News Feeds & Articles
CREATE TABLE rss_feeds (
  feed_id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
  feed_url VARCHAR(2048) NOT NULL,
  feed_name VARCHAR(255),
  category VARCHAR(50),
  last_fetched TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE articles (
  article_id UUID PRIMARY KEY,
  feed_id UUID REFERENCES rss_feeds(feed_id) ON DELETE CASCADE,
  url_hash BYTEA,  -- SHA256(URL) for deduplication
  title VARCHAR(512),
  url VARCHAR(2048),
  description TEXT,
  body_content TEXT,
  published_date TIMESTAMP,
  ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(feed_id, url_hash)
);

-- Session Memory
CREATE TABLE session_memory (
  memory_id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
  session_id UUID REFERENCES sessions(session_id) ON DELETE CASCADE,
  memory_type ENUM('turn', 'note', 'reminder'),
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP  -- Auto-cleanup
);

-- Financial Data (via C++ Core Engine, encrypted at rest)
CREATE TABLE expenses (
  expense_id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
  date_recorded DATE,
  amount NUMERIC(10, 2),
  category VARCHAR(50),
  description TEXT,
  encrypted_details BYTEA,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE financial_summary (
  summary_id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
  month DATE,  -- First day of month
  total_income NUMERIC(12, 2),
  total_expense NUMERIC(12, 2),
  category_breakdown JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit & Logging
CREATE TABLE audit_log (
  log_id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(user_id),
  action VARCHAR(100),  -- "knowledge_upload", "chat_query", "data_export"
  resource_type VARCHAR(50),
  resource_id UUID,
  status ENUM('success', 'failure'),
  details JSONB,
  ip_address INET,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rate Limiting
CREATE TABLE rate_limit_counters (
  counter_id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
  endpoint VARCHAR(255),
  request_count INT DEFAULT 1,
  window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, endpoint, window_start)
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_chunks_doc_id ON document_chunks(doc_id);
CREATE INDEX idx_articles_url_hash ON articles(url_hash);
CREATE INDEX idx_session_memory_user_id ON session_memory(user_id, created_at DESC);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id, created_at DESC);
```

---

## 5. Vector Schema (FAISS / Milvus)

### FAISS Index Layout (Local Dev)

```
FAISS Index: personal_ai_v1.faiss
├── Dimensions: 384 (sentence-transformers/all-MiniLM-L6-v2)
├── Index Type: IVFFlat + HNSW hybrid
├── Total Vectors: ~1M for typical user (100k docs × 10 chunks avg)
├── Distance Metric: L2 (cosine via normalization)
│
├── Vector Metadata (stored separately in SQLite):
│   {
│     "vector_id": "uuid",
│     "chunk_id": "uuid",
│     "doc_id": "uuid",
│     "source_type": "rss_feed",
│     "user_id": "uuid",
│     "timestamp": "2026-02-22T10:30:00Z",
│     "source_weight": 0.9,
│     "recency_boost": 1.2
│   }
│
└── Query Process:
    [query_text] → [embedding 384-dim]
    → FAISS.search(query_vec, k=20)
    → returns [(doc_id, distance), ...]
    → post-process with hybrid ranking
    → return top-10 to LLM
```

### Milvus Vector Collection (Production)

```yaml
Collection: documents
  Schema:
    - pk: vector_id (INT, primary_key=True)
    - embedding: (FLOAT_VECTOR, dim=384)
    - user_id: (VARCHAR, max_length=100)
    - doc_id: (VARCHAR, max_length=100)
    - source_type: (VARCHAR, max_length=50)
    - source_weight: (FLOAT)
    - recency_score: (FLOAT)
    - created_at: (INT64, timestamp_ms)
  
  Index:
    - Metric: COSINE
    - Index Type: HNSW (fast approximate)
    - m: 16, ef_construction: 200, ef: 50
  
  Partitions:
    - by_user: partition_key=user_id
    - by_source: partition_key=source_type
  
  Search Query:
    Milvus.search(
      query_vectors=[...],
      top_k=20,
      metric_type="COSINE",
      params={"nprobe": 16},
      filter="user_id == 'user123' AND source_weight > 0.5"
    )
```

---

## 6. Web Ingestion Pipeline

### RSS Scraper Architecture

```python
# Pseudocode

class NewsIngestionPipeline:
  def __init__(self):
    self.rss_feeds = load_user_subscriptions()
    self.html_cleaner = HtmlCleaner()
    self.chunker = DocumentChunker(chunk_size=500, overlap=250)
    self.embedding_client = EmbeddingClient()
    self.deduplicator = UrlDeduplicator()

  async def ingest_all():
    for feed_url in self.rss_feeds:
      articles = await fetch_rss(feed_url)
      for article in articles:
        await process_article(article)

  async def process_article(article):
    # 1. Deduplicate by URL
    url_hash = sha256(article.url)
    if url_hash in deduplicator:
      logging.info(f"Skip duplicate: {article.url}")
      return

    # 2. Respect robots.txt & rate limit
    if not robots_txt_allows(article.url):
      return

    # 3. Fetch full HTML
    html = await http_get(article.url, timeout=10s)
    
    # 4. Extract & clean
    body_text = self.html_cleaner.extract_content(html)
    
    # 5. Chunk
    chunks = self.chunker.chunk(body_text)
    
    # 6. Embed & store
    for chunk_text in chunks:
      embedding = await self.embedding_client.embed(chunk_text)
      
      vector_id = store_in_faiss(
        embedding,
        metadata={
          "article_id": article.id,
          "source_url": article.url,
          "published_date": article.published_date,
          "source_weight": 0.9,  # Tech news = 0.9
          "recency_score": compute_recency(article.published_date)
        }
      )
      
      store_in_postgres(
        vector_id,
        chunk_text,
        article.id
      )

  def compute_recency(pub_date):
    days_old = (now - pub_date).days
    # Boost recent articles, decay with time
    return 1 + (1 / (1 + days_old / 7)) * 0.5

# Scheduled every day at 02:00 UTC
@scheduler.scheduled_job('cron', hour=2, minute=0)
def daily_ingest():
  asyncio.run(NewsIngestionPipeline().ingest_all())
```

### Crawling Configuration

```yaml
# config/web_ingestion.yaml

ingestion:
  schedule: "0 2 * * *"  # 02:00 UTC daily
  timeout_per_article: 10  # seconds
  max_articles_per_feed: 100
  retention_days: 90  # Archive older than 90 days

deduplication:
  strategy: "url_hash_sha256"
  check_content_hash: true  # Also compare body hash

html_cleaning:
  remove_tags: ["script", "style", "nav", "footer", "advertisement"]
  min_paragraph_length: 20
  remove_boilerplate: true
  extract_metadata: ["title", "author", "publish_date"]

rate_limiting:
  requests_per_second: 1
  respect_robots_txt: true
  user_agent: "PersonalAI/1.0 (+https://example.com/bot)"

feeds:
  - name: "TechCrunch"
    url: "https://techcrunch.com/feed/"
    category: "technology"
    source_weight: 0.95
    enabled: true
  
  - name: "Hacker News"
    url: "https://news.ycombinator.com/rss"
    category: "technology"
    source_weight: 0.90
    enabled: true

  - name: "Financial Times Tech"
    url: "https://www.ft.com/tech?format=rss"
    category: "finance"
    source_weight: 0.85
    enabled: true
```

---

## 7. RAG Logic Flow

### Complete Retrieval-Augmented Generation Pipeline

```
PHASE 1: Query Understanding
┌─────────────────────────────────────────┐
│ User Query: "What AI trends emerged recently?" │
├─────────────────────────────────────────┤
│ 1. Input validation & sanitization      │
│ 2. Intent classification (optional)     │
│    • Info retrieval: 80%                │
│    • Financial query: 5%                │
│    • Status check: 15%                  │
│ 3. Query expansion (synonyms, terms)    │
│    • "AI trends" + "machine learning"   │
│    • "emerged" + "appeared", "launched" │
└─────────────────────────────────────────┘
       ↓
PHASE 2: Embedding & Retrieval
┌─────────────────────────────────────────┐
│ 1. Generate query embedding             │
│    query_vec = embed_service(           │
│      "What AI trends emerged recently?" │
│    )  # [384 floats]                    │
│                                         │
│ 2. FAISS similarity search              │
│    results = faiss.search(              │
│      query_vec,                         │
│      k=20,  # Get 20 candidates         │
│      metric=L2                          │
│    )                                    │
│    # Returns [(chunk_id, distance), ..] │
│                                         │
│ 3. Retrieve metadata for top 20         │
│    • Document source (RSS / local)      │
│    • Publication date                   │
│    • Source reliability weight          │
└─────────────────────────────────────────┘
       ↓
PHASE 3: Hybrid Ranking
┌─────────────────────────────────────────┐
│ For each of 20 candidates:              │
│                                         │
│ relevance_score = 1 / (1 + distance)    │
│ recency_score = 1 + exp(-days_old/7)    │
│ source_score = source_weight            │
│                                         │
│ final_score =                           │
│   0.70 * relevance_score +              │
│   0.20 * recency_score +                │
│ 0.10 * source_score                     │
│                                         │
│ SORT by final_score DESC                │
│ TAKE top 10 documents                   │
└─────────────────────────────────────────┘
       ↓
PHASE 4: Context Injection
┌──────────────────────────────────────────┐
│ Construct RAG Prompt:                     │
│                                          │
│ prompt = f"""                            │
│ You are a knowledgeable AI assistant.    │
│ Use the provided context to answer the   │
│ user's question.                         │
│                                          │
│ CONTEXT:                                 │
│ {ranked_docs[0:10]}  # Format each with  │
│                       source, relevance  │
│                                          │
│ Your session memory notes:               │
│ {session_memory[-5:]}                    │
│                                          │
│ QUESTION:                                │
│ {original_query}                         │
│                                          │
│ ANSWER:                                  │
│ """                                      │
└──────────────────────────────────────────┘
       ↓
PHASE 5: LLM Generation (Streaming)
┌──────────────────────────────────────────┐
│ 1. Call Ollama with streaming            │
│    ollama.generate(                      │
│      model="mistral",                    │
│      prompt=prompt,                      │
│      stream=True                         │
│    )                                     │
│                                          │
│ 2. For each token chunk:                 │
│    • Buffer for efficient transport      │
│    • Send via WebSocket to client        │
│    • Accumulate full response            │
│                                          │
│ 3. Error handling:                       │
│    • Timeout → "Let me generate summary" │
│    • LLM error → fallback to retrieval   │
└──────────────────────────────────────────┘
       ↓
PHASE 6: Post-Processing & Storage
┌──────────────────────────────────────────┐
│ 1. Stream complete → store interaction   │
│    session_memory.add({                  │
│      "role": "assistant",                │
│      "content": full_response,           │
│      "sources": ranked_docs.sources,     │
│      "timestamp": now()                  │
│    })                                    │
│                                          │
│ 2. Log to audit trail                    │
│    audit_log.add({                       │
│      "action": "chat_query",             │
│      "query_tokens": len(tokenize(q)),   │
│      "retrieved_docs": 10,               │
│      "generation_ms": elapsed            │
│    })                                    │
│                                          │
│ 3. Update user analytics                 │
│    analytics.increment("messages", 1)    │
│    analytics.add("total_tokens", ...)    │
└──────────────────────────────────────────┘

Entire flow: ~2 sec (100ms embed + 500ms retrieval + 1000ms LLM + 400ms I/O)
```

---

## 8. Security Model

### Authentication & Authorization

```
┌─────────────────────────────────────┐
│  User Login                          │
├─────────────────────────────────────┤
│ POST /api/v1/auth/login              │
│ {                                    │
│   "email": "user@example.com",       │
│   "password": "secret",              │
│   "mfa_token": "optional"            │
│ }                                    │
└─────────────────────────────────────┘
       ↓
┌─────────────────────────────────────┐
│ [1] Hash password + rate-limit check │
│ [2] Validate credentials in DB       │
│ [3] TOTP/MFA check (if enabled)      │
│ [4] Generate JWT token (15 min exp)  │
│ [5] Generate refresh token (7 days)  │
│ [6] Store in Redis session cache     │
└─────────────────────────────────────┘
       ↓
Response:
{
  "access_token": "eyJhbGc...",  ← JWT HS256
  "refresh_token": "refresh_...",
  "expires_in": 900,
  "encryption_key": "<encrypted>",  ← User's per-user key
  "mfa_required": false
}

┌─────────────────────────────────────┐
│  Subsequent API Calls               │
├─────────────────────────────────────┤
│ Header: Authorization: Bearer JWT    │
│                                      │
│ [1] Validate JWT signature (HS256)   │
│ [2] Check expiration                 │
│ [3] Check revocation in Redis        │
│ [4] Extract user_id, scopes          │
│ [5] Verify endpoint permissions      │
│ [6] Rate-limit check                 │
│ [7] Proceed to handler               │
└─────────────────────────────────────┘
```

### Data Encryption

```
┌─────────────────────────────────────┐
│  At-Rest Encryption (Data in DB)    │
├─────────────────────────────────────┤
│                                      │
│  Master Key (KMS or env):            │
│  MASTER_KEY = KMS.decrypt(...) or    │
│               read from sealed vault │
│                                      │
│  Per-User Key (stored encrypted):    │
│  user.encryption_key = encrypt(      │
│    random_256_bits,                  │
│    master_key                        │
│  )                                   │
│                                      │
│  Sensitive Fields Encryption:        │
│  encrypted_financial = AES-256-GCM(  │
│    financial_data,                   │
│    user_encryption_key,              │
│    nonce=random_96_bits,             │
│    aad=user_id                       │
│  )                                   │
│                                      │
│  Stored in DB as: [nonce || ct || tag] │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  In-Transit Encryption (TLS 1.3)    │
├─────────────────────────────────────┤
│                                      │
│  All HTTP → HTTPS (TLS 1.3 minimum) │
│  WebSocket → WSS (TLS 1.3)           │
│  TLS cert: Let's Encrypt (auto)      │
│  SNI: Optional (H2)                  │
│  HSTS: max-age=31536000 (1 year)     │
│                                      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Application-Layer Security         │
├─────────────────────────────────────┤
│                                      │
│  Input Validation:                   │
│  • SQL injection: Parameterized ORM  │
│  • XSS: Sanitize outputs (Angular)   │
│  • CSRF: CSRF token in forms         │
│                                      │
│  Rate Limiting:                      │
│  • /auth/login: 5 attempts/min       │
│  • /api/chat: 100 msgs/hour          │
│  • /api/knowledge/upload: 10/day     │
│                                      │
│  Secrets Management:                 │
│  • Never commit secrets (git hooks)  │
│  • Vault: HashiCorp Vault            │
│  • Rotation: auto-rotate keys        │
│                                      │
│  Audit Logging:                      │
│  • All sensitive actions logged      │
│  • IP, timestamp, user_id, result    │
│  • Immutable log storage             │
│                                      │
└─────────────────────────────────────┘
```

### Privacy & Compliance

```
GDPR / CCPA Compliance:
├── Data Minimization
│   └─ Collect only necessary fields
├── Right to Access
│   └─ GET /api/v1/settings/export-data
├── Right to Deletion
│   └─ DELETE /api/v1/settings/delete-account
│       (Hard delete + GDPR right-to-be-forgotten)
├── Data Residency
│   └─ EU customers: PostgreSQL in EU region
├── Consent Management
│   └─ Track user opt-ins (analytics, newsletters)
└── Incident Response
    └─ Log all breaches, notify within 72h

Security Scanning:
├── SAST (Static): GitHub CodeQL, SonarQube
├── DAST (Dynamic): OWASP ZAP, Burp
├── Dependency: Dependabot, Snyk
├── Secrets: git-secrets, Vault
└── Penetration Testing: Quarterly
```

---

## 9. Scalability & Multi-Tenancy

### Horizontal Scaling Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Load Balancer (Round-robin / Sticky Sessions)          │
├─────────────────────────────────────────────────────────┤
│         │          │          │                          │
│         ↓          ↓          ↓                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                   │
│  │ FastAPI │ │ FastAPI │ │ FastAPI │ (auto-scale 3-30) │
│  │ Pod 1   │ │ Pod 2   │ │ Pod 3   │                   │
│  └────┬────┘ └────┬────┘ └────┬────┘                   │
│       │           │           │                        │
│       └───────────┼───────────┘                        │
│                   │                                    │
│           ┌───────┴────────┐                          │
│           ↓                ↓                          │
│    ┌─────────────┐  ┌──────────────┐                │
│    │ Redis Pool  │  │ PostgreSQL   │                │
│    │ (cluster)   │  │ (replicated) │                │
│    └─────────────┘  └──────────────┘                │
│                                                     │
│    ┌──────────────────────────────────────┐        │
│    │ Embedding Service (auto-scale 2-10)  │        │
│    │ - GPU acceleration (optional)         │        │
│    │ - Multi-model support                │        │
│    └──────────────────────────────────────┘        │
│                                                     │
│    ┌──────────────────────────────────────┐        │
│    │ Milvus Vector DB (distributed)       │        │
│    │ - Sharded by user_id                 │        │
│    │ - Replicas: 3                        │        │
│    │ - Disk-based indexes                 │        │
│    └──────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────┘

Scaling Strategy:
├── Frontend: CDN (Cloudflare) + edge caching
├── API: Horizontal pods (Kubernetes HPA)
├── Database: Read replicas + connection pooling
├── Vector DB: Partitioning by user_id
├── Embedding: GPU nodes + batch processing
├── Cache: Redis cluster (sharded)
└── Logs: ELK with 30-day rolling window

Monitoring & Autoscaling:
├── Metrics: Prometheus (CPU, memory, latency)
├── Alerts: AlertManager (Slack, PagerDuty)
├── Autoscaling: Kubernetes HPA
│   ├─ FastAPI: Scale when CPU > 70%
│   ├─ Embeddings: Scale when queue depth > 100
│   └─ Milvus: Scale when memory > 80%
├── Dashboard: Grafana (key metrics)
└── Logs: ELK Stack (searchable)
```

### Multi-Tenancy Isolation

```
┌─────────────────────────────────────────────────────┐
│  SQL Row-Level Security (PostgreSQL)               │
├─────────────────────────────────────────────────────┤
│                                                    │
│  CREATE POLICY user_isolation ON documents         │
│    USING (user_id = current_user_id);              │
│                                                    │
│  SELECT * FROM documents;                          │
│  ↓  (RLS automatically filters)                    │
│  Only rows WHERE user_id = authenticated_user      │
│                                                    │
│  Applies to ALL queries (immune to bug injection)  │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  FAISS Index Partitioning by user_id              │
├─────────────────────────────────────────────────────┤
│                                                    │
│  Option A: Separate indexes per user               │
│  ├─ faiss_user_uuid_1.idx                         │
│  ├─ faiss_user_uuid_2.idx                         │
│  └─ Load on-demand per request                    │
│                                                    │
│  Option B: Single index with filtering             │
│  ├─ HNSW index: all vectors                       │
│  ├─ Metadata: user_id tagged with each vector     │
│  └─ Query: filter by user_id during search        │
│                                                    │
│  Option C: Milvus Partitions (production)          │
│  ├─ partition_key = user_id                       │
│  ├─ Auto-partition by shard                       │
│  └─ Search scoped to user partition               │
│                                                    │
└─────────────────────────────────────────────────────┘

Database Resources per Tenant:
├── Compute: Shared (connection pooling)
├── Storage: Dedicated (logical partitions)
├── Memory: Shared (cache eviction)
├── Bandwidth: Rate-limited per user
└── Secrets: Isolated (per-user encryption key)
```

---

## 10. Deployment Roadmap

### Phase 1: Beta (Current)

**Tech Stack:**
- Frontend: Angular + WebSocket (local dev)
- Backend: FastAPI (single instance)
- Core: C++ (local TCP)
- DB: SQLite + FAISS
- Auth: JWT (no MFA)
- Hosting: Single server or docker-compose

**Targets:**
- Single user
- ~10k documents
- ~1k embedding queries/day
- Manual deployment
- No monitoring

---

### Phase 2: MVP (Production Small-Scale — 3 months out)

**Tech Stack:**
- Frontend: Angular + CDN (Cloudflare)
- Backend: FastAPI (3 instances, load-balanced)
- Core: C++ gRPC service
- DB: PostgreSQL + PgVector extension
- Cache: Redis (single instance)
- Vector: Milvus (single node)
- Auth: JWT + TOTP
- Hosting: Kubernetes (AWS EKS)

**Targets:**
- 100 users
- ~100k documents per user avg
- ~50k embedding queries/day total
- CI/CD pipeline (GitHub Actions)
- Basic monitoring (Prometheus)

**Deployment Script:**
```bash
# AWS EKS deployment
aws eks create-cluster --name personal-ai-mvp
helm install personal-ai ./helm-charts/mvp \
  --values values-prod.yaml \
  --namespace default

# Auto-scaling
kubectl autoscale deployment personal-ai-api \
  --min=3 --max=10 \
  --cpu-percent=70
```

---

### Phase 3: Scale (Production Large — 12 months out)

**Tech Stack:**
- Frontend: Angular + React Native (mobile)
- Backend: FastAPI + async workers (Celery)
- Core: C++ (distributed via gRPC mesh)
- DB: PostgreSQL + streaming replicas
- Vector: Milvus + multi-node cluster
- Cache: Redis cluster (6 nodes)
- Auth: OAuth 2.0 + OIDC
- Hosting: Multi-region Kubernetes

**Targets:**
- 10k+ users
- ~1M+ total documents
- ~1M embedding queries/day
- 99.95% SLA
- Full observability (Prometheus, Jaeger, ELK)
- Disaster recovery (3-region replication)

**Regional Distribution:**
```
┌──────────────────────────────────────────┐
│  Global CDN (Cloudflare)                 │
├──────────────────────────────────────────┤
│  ├─ US-East (primary)    ├─ EU-West   │
│  ├─ US-West              ├─ Asia-SG   │
│  └─ Auto-routing (latency optimization) │
└──────────────────────────────────────────┘

Each Region:
├─ Kubernetes Cluster (EKS/GKE)
├─ PostgreSQL with cross-region replication
├─ Milvus cluster (sharded by user)
├─ Redis cluster
└─ Local FAISS for read-heavy queries
```

---

## 11. Technology Alternatives

### Frontend Alternatives

| Requirement | Primary | Alternative 1 | Alternative 2 |
|---|---|---|---|
| **Framework** | Angular | React | Vue.js |
| **Real-time** | WebSocket | Server-Sent Events (SSE) | gRPC-web |
| **State** | NgRx | Redux | Pinia (Vue) |
| **Styling** | TailwindCSS | Material Design | Bootstrap |
| **Charts** | Chart.js | D3.js | Plotly |

### Backend Alternatives

| Requirement | Primary | Alternative 1 | Alternative 2 |
|---|---|---|---|
| **Framework** | FastAPI (Python) | Flask | Django |
| **Async** | asyncio | gevent | Trio |
| **WebSocket** | FastAPI-WebSocket | Django-Channels | starlette |
| **Job Queue** | Celery (RabbitMQ) | APScheduler (local) | Airflow |
| **RAG Framework** | LangChain | LlamaIndex | Semantic Kernel |

### LLM Alternatives

| Requirement | Primary | Alternative 1 | Alternative 2 |
|---|---|---|---|
| **Local LLM** | Ollama | LM Studio | GPT4All |
| **Embedding Model** | sentence-transformers | OpenAI API | Hugging Face Inference |
| **LLM Models** | mistral, llama2 | PHI, neural-chat | Falcon, Alpaca |

### Data Layer Alternatives

| Requirement | Primary | Alternative 1 | Alternative 2 |
|---|---|---|---|
| **Relational** | PostgreSQL | MySQL/MariaDB | SQLServer |
| **Vector DB** | Milvus + PgVector | Weaviate | Pinecone (cloud) |
| **Cache** | Redis | Memcached | DragonflyDB |
| **Full-Text** | PostgreSQL FTS | Elasticsearch | MeiliSearch |
| **Column Store** | ClickHouse (analytics) | DuckDB | Druid |

### C++ Engine Alternatives

| Requirement | Primary | Alternative 1 | Alternative 2 |
|---|---|---|---|
| **Encryption** | libsodium | OpenSSL | Bouncy Castle (JNI) |
| **gRPC** | grpcpp | REST (simpler) | Cap'n Proto |
| **Concurrency** | std::thread + mutex | Boost.Asio | asio (header-only) |

### Infrastructure Alternatives

| Requirement | Primary | Alternative 1 | Alternative 2 |
|---|---|---|---|
| **Container** | Docker | Podman | Singularity |
| **Orchestration** | Kubernetes | Docker Swarm | Nomad (HashiCorp) |
| **Cloud** | AWS (EKS) | GCP (GKE) | Azure (AKS) |
| **CI/CD** | GitHub Actions | GitLab CI | Jenkins |
| **Monitoring** | Prometheus + Grafana | Datadog | New Relic |
| **Logging** | ELK Stack | Loki (Grafana) | Splunk |

---

## 12. Quick Start & References

### Local Development

```bash
# Clone and setup
git clone https://github.com/your-org/personal-ai
cd personal-ai

# Backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py

# Frontend
cd ../frontend && npm install && ng serve

# C++ Core
cd ../core && cmake -B build && ninja -C build

# Embedding Service
cd ../embeddings && python embedding_service.py

# Browser: http://localhost:4200
```

### Production Deployment

```bash
# Docker images
docker build -t personal-ai-api:v1 ./backend
docker build -t personal-ai-frontend:v1 ./frontend
docker build -t personal-ai-core:v1 ./core
docker build -t personal-ai-embeddings:v1 ./embeddings

# Push to registry
docker push your-registry/personal-ai-api:v1

# Deploy via Helm
helm install personal-ai ./helm-charts/prod \
  --values production.yaml \
  --namespace personal-ai
```

---

## Conclusion

This architecture is designed for:
✅ **Scalability:** Support 10k+ users across regions  
✅ **Security:** Encryption at rest & in transit, audit logging  
✅ **Performance:** Sub-2s RAG latency, streaming responses  
✅ **Reliability:** 99.95% SLA with auto-failover  
✅ **Developer Experience:** Clear separation of concerns, modular design  
✅ **Cost Efficiency:** Progressive scaling from $500/mo beta to $50k+/mo at scale  

**Next Steps:**
1. Implement FastAPI backend with vector retrieval
2. Build Angular frontend with WebSocket streaming
3. Deploy MVP on AWS EKS
4. Collect user feedback & iterate
5. Scale to multi-region by year 2
