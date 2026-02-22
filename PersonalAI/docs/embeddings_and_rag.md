**Embeddings & RAG**

- **Embedding microservice:** `python/embedding_service.py` exposes `/embed` (JSON). The C++ side (optional) calls `EmbeddingHttpClient` to get vectors.
- **Chunking:** Documents and long notes should be split into ~400-800 token chunks with small overlap; each chunk gets an embedding and metadata (source, offset, tags).
- **Storage:** Chunks map to `knowledge.id`. Embeddings stored in `VectorStore` as CSV text (simple, portable). For production use replace with FAISS or Milvus for better performance.
- **Retrieval:** Query -> embed -> cosine similarity -> top-K results -> assemble context. Inject with a prompt template that prioritizes high-score, then recency and tags.
- **Prompt injection:** Use a system prompt that includes instruction, role, and the retrieved context section, then the user query.
