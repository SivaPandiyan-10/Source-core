**Converting to SaaS / Deployment Notes**

- **API Layer:** Extract a REST API around `CoreEngine` in C++ (FastCGI or gRPC) or run a thin Python/Go API that talks to the C++ core.
- **Shared Services:** Replace local SQLite with managed Postgres, and FAISS with a vector DB service (Milvus, Weaviate). Move embeddings microservice to a container with autoscaling.
- **Multi-tenant design:** Add per-tenant encryption keys, tenant-scoped databases, and usage quotas.
- **Security & Privacy:** Keep encryption-at-rest and TLS for all internal traffic; rotate keys via a secrets manager.
- **Monitoring:** Add logging, metrics (Prometheus), and tracing (Jaeger) around LLM calls and vector queries.
