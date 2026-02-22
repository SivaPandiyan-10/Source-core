**RAG Design**

- Chunking: Split long documents into ~500-token overlapping chunks and store chunk metadata (source, offset, tags).
- Embeddings: Use `python/embedding_service.py` to generate vectors; store vectors alongside metadata.
- Vector Store: Start with an in-process FAISS or simple cosine-search index on disk; each vector saved with pointer to `knowledge` row.
- Retrieval: Query -> embed -> cosine similarity -> top-K -> inject into prompt template before LLM call.

Notes on tradeoffs are in `architecture.md`.
