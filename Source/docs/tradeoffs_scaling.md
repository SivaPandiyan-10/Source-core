**Trade-offs & Scaling**

- **Structured DB (SQLite):** ACID, simple transactions, ideal for financial records and exact queries. Pros: reliability, SQL. Cons: not ideal for semantic search, limited horizontal scaling.
- **Vector DB:** Pros: semantic search, fast nearest-neighbour. Cons: storage and indexing complexity; FAISS or Milvus recommended for large datasets.
- **When to scale:** Move embeddings to FAISS (local) or Milvus/Weaviate (server). Move SQLite to Postgres for concurrent multi-user SaaS.
- **Concurrency:** Use a thread pool for embedding/LLM calls; DB writes should be serialized or use transactional DB server.
- **Latency:** Keep embedding microservice colocated; batch embeddings when indexing large corpora.
