# Deployment Guide & Operations Manual

## Quick Start: Local Development

### Prerequisites
```bash
# System requirements
- Docker & Docker Compose
- Node.js 18+
- Python 3.10+
- PostgreSQL 14+
- Redis
- Ollama (local LLM)
```

### 1. Clone & Setup

```bash
git clone https://github.com/your-org/personal-ai.git
cd personal-ai

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
ng build  # or ng serve for dev

# C++ Core
cd ../core
cmake -B build
ninja -C build

# Python Microservices
cd ../embeddings
pip install -r requirements.txt
python embedding_service.py
```

### 2. Environment Variables

Create `.env` file in project root:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/personal_ai
ASYNC_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/personal_ai

# API
API_HOST=0.0.0.0
API_PORT=8000
JWT_SECRET=your-super-secret-key-change-me
MASTER_KEY=your-master-encryption-key

# LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Embedding Service
EMBEDDING_SERVICE_URL=http://localhost:8001

# Storage
FAISS_INDEX_PATH=./data/faiss_index

# CORS
CORS_ORIGINS=http://localhost:4200,http://localhost:8080

# Logging
LOG_LEVEL=INFO
```

### 3. Database Setup

```bash
# Create PostgreSQL database
psql -U postgres
CREATE DATABASE personal_ai;
\q

# Apply schema
psql -U postgres -d personal_ai -f sql/production_schema.sql

# Or with Docker
docker run -d \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=personal_ai \
  -p 5432:5432 \
  postgres:15
```

### 4. Start Services

```bash
# Terminal 1: Redis
docker run -d -p 6379:6379 redis:latest

# Terminal 2: PostgreSQL (if not running)
docker run -d -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=personal_ai \
  postgres:15

# Terminal 3: Ollama (local LLM)
ollama serve

# Terminal 4: Embedding Service
cd embeddings && python embedding_service.py

# Terminal 5: C++ Core
./core/build/personal_ai.exe  # or ./core/build/personal_ai on Linux

# Terminal 6: FastAPI Backend
cd backend && python main.py

# Terminal 7: Angular Frontend
cd frontend && ng serve
```

**Access Application:**
- Frontend: http://localhost:4200
- API Docs: http://localhost:8000/docs
- Embedding Service: http://localhost:8001/docs

---

## Docker Compose Deployment

Create `docker-compose.yml`:

```yaml
version: '3.9'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: personal_ai
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/production_schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0:11434

  embedding-service:
    build:
      context: ./embeddings
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    environment:
      - MODEL=sentence-transformers/all-MiniLM-L6-v2
      - DEVICE=cpu  # or 'cuda' for GPU
    depends_on:
      postgres:
        condition: service_healthy

  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/personal_ai
      - ASYNC_DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/personal_ai
      - JWT_SECRET=change-me-in-production
      - EMBEDDING_SERVICE_URL=http://embedding-service:8001
      - OLLAMA_BASE_URL=http://ollama:11434
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      embedding-service:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - api
    volumes:
      - ./frontend/nginx.conf:/etc/nginx/nginx.conf:ro

volumes:
  postgres_data:
  ollama_data:
```

**Start:**
```bash
docker-compose up -d

# Monitor
docker-compose logs -f
```

---

## Kubernetes Deployment (Production)

### Helm Chart Structure

```
helm-charts/
├── Chart.yaml
├── values.yaml
├── values-prod.yaml
├── templates/
│   ├── deployment-api.yaml
│   ├── deployment-embeddings.yaml
│   ├── deployment-scheduler.yaml
│   ├── service-api.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── hpa.yaml
│   └── pdb.yaml
└── charts/
    ├── postgresql/
    ├── redis/
    └── milvus/
```

### Deploy to AWS EKS

```bash
# Create cluster
aws eks create-cluster \
  --name personal-ai-prod \
  --role-arn arn:aws:iam::ACCOUNT:role/eks-service-role \
  --resources-vpc-config subnetIds=subnet-xxx,subnet-yyy

# Add node group
aws eks create-nodegroup \
  --cluster-name personal-ai-prod \
  --nodegroup-name prod-nodes \
  --scaling-config minSize=3,maxSize=30,desiredSize=5 \
  --node-role arn:aws:iam::ACCOUNT:role/NodeInstanceRole

# Get kubeconfig
aws eks update-kubeconfig \
  --name personal-ai-prod \
  --region us-east-1

# Install ingress controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  -n ingress-nginx \
  --create-namespace

# Deploy Personal AI
helm install personal-ai ./helm-charts \
  --namespace personal-ai \
  --create-namespace \
  --values helm-charts/values-prod.yaml \
  --set image.repository=YOUR_REGISTRY/personal-ai \
  --set image.tag=v1.0.0

# Check deployment
kubectl get pods -n personal-ai
kubectl get svc -n personal-ai
```

### Helm Values (values-prod.yaml)

```yaml
global:
  environment: production
  domain: personal-ai.example.com

api:
  replicaCount: 3
  image:
    repository: YOUR_REGISTRY/personal-ai-api
    tag: v1.0.0
    pullPolicy: IfNotPresent
  
  resources:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 2000m
      memory: 2Gi
  
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 20
    targetCPUUtilizationPercentage: 70

embeddings:
  replicaCount: 2
  image:
    repository: YOUR_REGISTRY/personal-ai-embeddings
    tag: v1.0.0
  
  resources:
    requests:
      cpu: 1000m
      memory: 2Gi
    limits:
      cpu: 2000m
      memory: 4Gi
  
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10

postgresql:
  enabled: true
  auth:
    username: personal_ai
    password: CHANGE_ME
    database: personal_ai
  
  primary:
    persistence:
      enabled: true
      size: 50Gi
  
  replica:
    replicaCount: 2
    persistence:
      enabled: true
      size: 50Gi

redis:
  enabled: true
  replica:
    replicaCount: 2

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: personal-ai.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: personal-ai-tls
      hosts:
        - personal-ai.example.com
```

---

## Monitoring & Observability

### Prometheus Setup

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'personal-ai-api'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: personal-ai-api
      - source_labels: [__meta_kubernetes_pod_container_port_name]
        action: keep
        regex: metrics

  - job_name: 'personal-ai-embeddings'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: personal-ai-embeddings

alert_rules:
  - alert: HighAPILatency
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
    for: 5m
    annotations:
      summary: "High API latency detected"

  - alert: DatabaseConnectionPoolExhausted
    expr: pg_stat_activity_count > 90
    for: 3m
    annotations:
      summary: "Database connection pool nearly exhausted"

  - alert: VectorStorageHighMemory
    expr: process_resident_memory_bytes{job="milvus"} > 4e9
    for: 5m
```

### Grafana Dashboards

Key metrics to track:
- API response time (p50, p95, p99)
- Chat completion latency (embedding + retrieval + LLM)
- Vector database query time
- Concurrent users
- Error rates
- Document ingestion rate
- Cache hit ratio
- Database connection pool usage

### Logging Stack (ELK)

```yaml
# elasticsearch
image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
environment:
  - discovery.type=single-node
  - "ES_JAVA_OPTS=-Xms512m -Xmx512m"

# logstash
input {
  tcp { port => 5000 format => "json" }
}
filter {
  mutate { add_field => { "[@metadata][index_name]" => "personal-ai-%{+YYYY.MM.dd}" } }
}
output {
  elasticsearch { hosts => ["elasticsearch:9200"] }
}

# kibana
environment:
  - ELASTICSEARCH_HOSTS=["http://elasticsearch:9200"]
```

---

## Scaling Guide

### Horizontal Scaling Strategy

**Level 1: Single Server (100 users, 10GB documents)**
- Everything on one machine
- SQLite + FAISS
- Cost: ~$50/month

**Level 2: Distributed Services (1K users, 1TB documents)**
- API cluster (3 instances)
- Separate DB (PostgreSQL replica)
- Redis cache layer
- Milvus vector DB
- Cost: ~$500/month

**Level 3: Multi-Region (10K+ users)**
- Global load balancer
- Regional Kubernetes clusters
- Cross-region replication
- CDN for static assets
- Cost: $5-10K/month

### Auto-Scaling Configuration

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: personal-ai-api
  minReplicas: 3
  maxReplicas: 30
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "1k"
```

---

## Security Hardening

### TLS/SSL

```bash
# Let's Encrypt with cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml

# ClusterIssuer
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-key
    solvers:
      - http01:
          ingress:
            class: nginx
```

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: personal-ai-network-policy
spec:
  podSelector:
    matchLabels:
      app: personal-ai-api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: ingress-nginx
      ports:
        - protocol: TCP
          port: 8000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
```

### Secret Management (HashiCorp Vault)

```bash
# Install Vault
helm repo add hashicorp https://helm.releases.hashicorp.com
helm install vault hashicorp/vault \
  --namespace vault \
  --create-namespace

# Store secrets
vault kv put secret/personal-ai/prod \
  db_password="..." \
  jwt_secret="..." \
  master_key="..."

# Kubernetes auth
vault auth enable kubernetes
vault write auth/kubernetes/config \
  token_reviewer_jwt=@/var/run/secrets/kubernetes.io/serviceaccount/token \
  kubernetes_host="https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```

---

## Backup & Disaster Recovery

### Database Backups

```bash
# Automated daily backup
#  cron job
0 2 * * * pg_dump personal_ai | gzip > /backups/personal_ai_$(date +\%Y\%m\%d).sql.gz

# Full backup to S3
aws s3 cp /backups/personal_ai_*.sql.gz s3://my-backup-bucket/

# Point-in-time recovery
pg_restore -d personal_ai /backups/personal_ai_20260222.sql.gz
```

### FAISS Index Backup

```bash
# Daily snapshot
tar -czf /backups/faiss_index_$(date +\%Y\%m\%d).tar.gz ./data/faiss_index/

# Push to S3
aws s3 cp /backups/faiss_index_*.tar.gz s3://my-backup-bucket/
```

### Disaster Recovery Plan

```
RTO (Recovery Time Objective): 1 hour
RPO (Recovery Point Objective): 1 hour (daily backups + transaction logs)

Recovery Steps:
1. Spin up standby cluster in secondary region
2. Restore PostgreSQL from latest backup
3. Sync vector index from S3
4. Point DNS to secondary cluster
5. Verify with smoke tests
6. Begin investigations on primary
```

---

## Performance Tuning

### Database Optimization

```sql
-- Analyze query plans
EXPLAIN ANALYZE SELECT * FROM chunk_vectors 
  WHERE user_id = 'xxx' 
  LIMIT 10;

-- Create indexes for hot queries
CREATE INDEX idx_chunk_vectors_user_recency 
  ON chunk_vectors(user_id, created_at DESC) 
  INCLUDE (relevance_baseline);

-- Partition large tables by user_id
CREATE TABLE chunk_vectors_2026_q1 PARTITION OF chunk_vectors
  FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');
```

### Cache Strategy

```
Level 1: Redis (session tokens, rate limits) — TTL: 24h
Level 2: In-process cache (LRU) — Size: 100MB, TTL: 1h
Level 3: CDN (assets, static) — TTL: 7 days

Cache Key Patterns:
- user:{user_id}:session
- embedding:{text_hash}  (cache embedding computations)
- search:{query_hash}:{user_id}  (cache search results)
```

### Query Optimization

```python
# Batch vector operations
def batch_embed(texts, batch_size=32):
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        embeddings = embedding_service.embed_batch(batch)
        yield embeddings

# Use FAISS batch search
def batch_search(queries, k=10):
    query_vectors = embedding_service.embed_batch(queries)
    distances, indices = faiss_index.search(query_vectors, k)
    return list(zip(distances, indices))
```

---

## Maintenance & Updates

### Zero-Downtime Deployment

```bash
# Rolling update strategy
kubectl set image deployment/personal-ai-api \
  personal-ai-api=my-registry/personal-ai-api:v1.1.0 \
  --record

# Monitor rollout
kubectl rollout status deployment/personal-ai-api

# Rollback if needed
kubectl rollout undo deployment/personal-ai-api
```

### Database Migrations

```bash
# Using Alembic for Python
alembic init migrations
alembic revision --autogenerate -m "Add new column"
alembic upgrade head

# Kubernetes pre-deploy job
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
spec:
  template:
    spec:
      containers:
        - name: migrate
          image: my-registry/personal-ai-api:v1.1.0
          command: ["alembic", "upgrade", "head"]
      restartPolicy: Never
```

---

## Troubleshooting

### Common Issues

**High Latency in Vector Searches**
```bash
# Check FAISS index size
ls -lh data/faiss_index/

# Rebuild FAISS if corrupted
python -m scripts.rebuild_faiss

# Monitor Milvus performance
kubectl exec -it milvus-0 -- milvus_cmd check_index
```

**Memory Leaks in Embedding Service**
```bash
# Monitor process
watch -n 1 'ps aux | grep embedding_service'

# Profile memory
python -m memory_profiler embedding_service.py
```

**Database Connection Pool Issues**
```sql
-- Check connections
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;

-- Kill hung connections
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE usename = 'personal_ai' AND state = 'idle' AND query_start < now() - INTERVAL '1 hour';
```

---

## Cost Optimization

### AWS Pricing Breakdown (10K users, 1M documents)

```
EC2 Instances (EKS nodes): $2,000/month
  - 5 on-demand + auto-scale to 30 spot instances

RDS PostgreSQL:
  - db.r6i.2xlarge (memory-optimized): $1,500/month
  - Automated backups: $150/month

ElastiCache Redis (cluster mode):
  - cache.r6g.xlarge: $500/month

Milvus VectorDB (managed): $800/month

Data Transfer:
  - Inter-region replication: $100/month
  - CloudFront CDN: $200/month

Total: ~$5,250/month at scale

Cost Reduction:
- Use Spot instances → 60% savings
- Reserved instances (1yr) → 40% savings
- Auto-scale down during off-peak → 20% savings
```

---

## Production Checklist

- [ ] SSL/TLS certificates configured
- [ ] Database backups automated and tested
- [ ] Monitoring & alerting active
- [ ] Rate limiting enabled
- [ ] Authentication & MFA working
- [ ] Logging centralized (ELK)
- [ ] Security scanning (SAST/DAST)
- [ ] Load testing completed
- [ ] Disaster recovery drilled
- [ ] Documentation up-to-date
- [ ] On-call schedule established
- [ ] Incident response plan ready
