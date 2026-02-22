# Security Model (Personal AI Assistant)

Overview
--------
- JWT-based authentication with short-lived access tokens and rotating refresh tokens.
- Per-tenant and per-user authorization with RBAC checks at the API gateway.
- Per-user envelope encryption using Vault/KMS for sensitive documents.
- TLS everywhere (HTTPS for external, mTLS for internal service-to-service).

Key Concepts
------------
- Authentication: `POST /auth/login` issues JWT access token (15m) and refresh token (7d).
- Authorization: API checks `tenant_id` scope and `roles` (user, admin, auditor).
- Encryption: Use envelope encryption; data encrypted with a per-user data key, wrapped by KMS key.
- Secrets: Store credentials and secrets in HashiCorp Vault or cloud KMS.

Service-to-Service Security
---------------------------
- Use mTLS in Kubernetes (Istio) or mutual TLS between containers.
- Short-lived service tokens rotated by job; do not embed static keys in containers.

Data Protection
---------------
- At rest: encrypted DB fields for PII and sensitive blobs encrypted before storage.
- In transit: TLS 1.2+ with strong ciphers.
- Audit: immutable audit logs for sensitive operations, redact PII in logs.

Scraping & Legal
----------------
- Respect robots.txt and site rate-limits.
- Store `robots_status` and optionally honor site-specific opt-outs.

Operational
-----------
- Rate limiting at gateway (per-user, per-tenant) using Redis counters.
- Monitoring for abnormal access patterns and alerts for exfiltration.

Key Rotation & Recovery
-----------------------
- Rotate KMS keys and rewrap data keys via background re-encryption jobs.
- Provide a recovery flow using Vault operators with strict access controls.
