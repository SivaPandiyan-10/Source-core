# Scaling & Deployment Roadmap

Phase 0 — Local / Dev
- Single-node FAISS, SQLite, Ollama single-instance.
- Docker Compose for local orchestration.

Phase 1 — Production (Single Region)
- K8s with deployments for backend, embed service, workers.
- PostgreSQL (managed) replaces SQLite; Redis for sessions and caching.
- FAISS either as statefulset with PVs or move to Milvus/Weaviate.
- Ollama on GPU node(s); autoscale worker pools.

Phase 2 — Scale & High Throughput
- Use IVF+PQ / quantized indices for FAISS or migrate to Milvus for distributed indexing.
- Add read replicas for Postgres, partition large tables by tenant/date.
- Offload old vectors to cold storage with tiering and rehydrate on demand.

Phase 3 — SaaS Multi-Region / Multi-Tenant
- Tenant isolation: dedicated schemas or clusters for high-tier customers.
- Global index routing or per-region indices for latency.
- Centralized billing, tenant quotas, throttling.

Operational Practices
- CI/CD with GitOps (ArgoCD); image scanning and vulnerability checks.
- Backup strategy: daily DB dumps, FAISS index snapshots to object storage.
- DR tests: periodic restore rehearsals.
