Personal AI Assistant - Backend (generated scaffolding)

Files added:

- `openapi.yaml` : minimal OpenAPI spec for key endpoints
- `main.py` : FastAPI scaffold (auth, upload, search, websocket chat)
- `embed_service.py` : embedding microservice using sentence-transformers
- `ingest/chunker.py` : simple chunker (500-token chunks with overlap)
- `ingest/rss_ingest.py` : RSS fetcher & article extractor
- `sql/schema.sql` : SQLite schema for dev
- `requirements.txt` : Python dependencies for services

Quick start (dev):

1. Create a virtualenv and install requirements:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Run the embedding service:

```powershell
python embed_service.py
```

3. Run the backend API:

```powershell
python main.py
```

Notes:
- The scaffold is minimal and contains placeholders (auth, job queue, FAISS integration).
- `embed_service.py` loads `sentence-transformers/all-MiniLM-L6-v2` by default.
- Use `sqlite` and the provided schema for development; migrate to Postgres for production.
