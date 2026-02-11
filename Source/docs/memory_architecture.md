**Memory Architecture**

- **Short-term (Session):** In-memory vector and text buffer stored by `MemoryManager` during a run. Designed for fast access and cleared per session. See `include/MemoryManager.h` and `src/MemoryManager.cpp`.
- **Long-term (Persistent):** Structured records (salary, expense, knowledge) stored in SQLite (`sql/schema.sql`). Sensitive fields are encrypted with `EncryptionUtil` before write and decrypted on read.
- **Semantic Memory (Vector DB):** Embeddings generated via the Python microservice and stored in `VectorStore` (table `embeddings` in `personal_ai.db`) as CSV vectors. Retrieval uses cosine similarity to return top-K context for prompt injection.
- **Retrieval Logic:** Query -> embed -> VectorStore.query(top-K) -> fetch content from `knowledge` table -> inject highest-scoring chunks into LLM prompt.
- **Why hybrid:** Use structured DB for exact numeric queries and transactions (financials) and vector store for fuzzy semantic retrieval (notes, documents).
