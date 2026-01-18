# JobSearchEngine - Architecture & Design Documentation

## Executive Summary

JobSearchEngine is a production-ready, distributed job matching system consisting of:
1. **C++ TCP Server** - Job Matching Engine with resume analysis and scoring
2. **Go TCP Client** - Job Orchestrator that fetches jobs and coordinates matching

Both services communicate exclusively via TCP sockets over a structured JSON protocol on port 10000.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  Go Job Orchestrator                    │
│  - Job Platform Integration (LinkedIn, Naukri, etc.)    │
│  - Job Search & Collection                              │
│  - TCP Client (Reconnection Management)                 │
│  - Daily Logging of Matched Jobs                        │
└──────────────────────────┬──────────────────────────────┘
                           │
                    TCP Port 10000
              Length-Prefixed JSON Protocol
                           │
┌──────────────────────────▼──────────────────────────────┐
│             C++ Job Matching Engine                     │
│  - TCP Server (Thread-Safe Socket Handling)             │
│  - Resume Profile Management                           │
│  - Resume Parsing & Skill Extraction                    │
│  - Job-Resume Matching Engine                           │
│  - Confidence Score Calculation                         │
└─────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

### C++ Job Matching Engine (TCP Server)

**Responsibilities:**
- Listen on TCP port 10000 indefinitely
- Accept connections from Go orchestrator
- Parse incoming job-matching requests
- Maintain resume profile repository
- Extract resume features (skills, experience, certifications)
- Perform skill-based matching against job descriptions
- Calculate confidence scores
- Return structured responses
- Handle multiple concurrent connections via threading

**Key Features:**
- Multi-threaded request handling (one thread per client)
- Non-blocking socket I/O
- Graceful shutdown handling
- Signal-based lifecycle management
- Comprehensive logging

---

### Go Job Orchestrator (TCP Client)

**Responsibilities:**
- Connect to C++ TCP server
- Fetch jobs from multiple platforms (LinkedIn, Naukri, custom)
- Deduplicate jobs to prevent re-submission
- Submit jobs to C++ server for matching
- Receive and process matching responses
- Log matched jobs (score >= threshold) to daily log files
- Maintain connection and auto-reconnect on failure
- Perform periodic health checks

**Key Features:**
- Exponential backoff reconnection logic
- Connection health monitoring
- Job deduplication via local cache
- Daily log rotation
- Configurable fetch intervals
- Platform plugin architecture

---

## Communication Protocol

### Message Transport

**Frame Format:**
```
[4 bytes: Length (Big-Endian)] [JSON Payload]
```

### Request-Response Flow

**Job Matching Request (Go → C++):**
```json
{
  "type": "JOB_MATCH_REQUEST",
  "request_id": "req-001",
  "timestamp": "2026-01-18T10:30:00Z",
  "candidate": {
    "name": "John Doe",
    "resume_id": "resume_001",
    "keywords": ["C++", "System Design"]
  },
  "job": {
    "source": "linkedin",
    "source_id": "job_123",
    "company_name": "Tech Corp",
    "job_title": "Senior Engineer",
    "job_description": "...",
    "apply_url": "https://...",
    "posted_date": "2026-01-16T00:00:00Z"
  }
}
```

**Job Matching Response (C++ → Go):**
```json
{
  "type": "JOB_MATCH_RESPONSE",
  "request_id": "req-001",
  "status": "MATCHED",
  "confidence_score": 0.87,
  "matched_skills": ["C++"],
  "unmatched_required_skills": ["Rust"],
  "reason": "Strong match",
  "processing_time_ms": 45,
  "timestamp": "2026-01-18T10:30:01Z"
}
```

---

## Matching Algorithm

1. **Extract Required Skills:** Parse job description for keyword matches
2. **Find Matches:** Compare resume skills against required skills
3. **Calculate Score:** Matched / Required skills ratio
4. **Determine Status:** Score >= 0.70 = MATCHED, else REJECTED
5. **Log Result:** Only MATCHED jobs are logged to daily files

---

## Logging System

### Daily Log Format

**File:** `logs/YYYY-MM-DD.log`

```
=== JobSearchEngine - Daily Match Log ===
Date: 2026-01-18
=============================================

[2026-01-18 10:30:15] Candidate: John Doe | Company: Tech Corp | Job: Senior Engineer | Platform: linkedin | Score: 87.00% | Skills: [C++] | Apply: https://...
```

---

## Resilience Patterns

### Reconnection Logic

- Exponential backoff: 1s → 2s → 4s → ... → 60s (max)
- Health checks every 10 seconds
- Auto-reconnect on failure

### Job Deduplication

- Track processed job IDs in memory
- Prevent duplicate submissions
- Reset cache per session (not persistent)

---

## Configuration

### C++ Server
```bash
./job_matching_engine --port 10000
```

### Go Orchestrator
File: `config/orchestrator.json`
```json
{
  "server": {"address": "localhost", "port": 10000},
  "candidate": {"name": "John", "resume_id": "resume_001", "keywords": [...]},
  "schedule": {"fetch_interval": "30s", "health_check_interval": "10s"},
  "logging": {"directory": "logs"},
  "platforms": [{"name": "linkedin", "enabled": true}]
}
```

---

## Build & Run

### C++ Server
```bash
cd JobSearchEngine
mkdir build && cd build
cmake ..
cmake --build . --config Release
./job_matching_engine --port 10000
```

### Go Orchestrator
```bash
cd JobSearchEngine/go
go build -o jobsearch ./cmd/jobsearch
./jobsearch -config ../config/orchestrator.json
```

---

## Error Handling

| Scenario | Action |
|----------|--------|
| Invalid JSON | Return ERROR response |
| Missing field | Return ERROR response |
| Processing timeout | Return ERROR response |
| Connection lost | Go: Retry with backoff |
| Job parse error | Go: Log, skip, continue |

---

## Future Enhancements

- TLS encryption for secure communication
- Authentication/authorization tokens
- Advanced ML-based matching
- Distributed server deployment
- Admin dashboard UI
- Prometheus metrics export
- LinkedIn API direct integration

---
