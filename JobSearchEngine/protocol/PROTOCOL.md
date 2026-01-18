# JobSearchEngine - TCP Communication Protocol

## Overview
- **Transport Layer**: TCP/IP
- **Port**: 10000
- **Message Format**: JSON
- **Encoding**: UTF-8
- **Message Framing**: Length-prefixed (4-byte big-endian length header)

## Message Framing

All messages follow this structure:
```
[4 bytes: Message Length (Big-Endian)][JSON Payload]
```

**Example**: 
- Message: `{"type":"PING"}`
- Length: 15 bytes
- Wire format: `0x0000000F` + `{"type":"PING"}`

---

## Message Types

### 1. PING (Keep-Alive)
**Direction**: Bi-directional  
**Purpose**: Connection health check

**Request**:
```json
{
  "type": "PING",
  "timestamp": "2026-01-18T10:30:00Z"
}
```

**Response**:
```json
{
  "type": "PONG",
  "timestamp": "2026-01-18T10:30:00Z"
}
```

---

### 2. JOB_MATCH_REQUEST (Go → C++)
**Direction**: Go Client → C++ Server  
**Purpose**: Request job matching against resume profiles

**Request**:
```json
{
  "type": "JOB_MATCH_REQUEST",
  "request_id": "req-20260118-001",
  "timestamp": "2026-01-18T10:30:00Z",
  "candidate": {
    "name": "John Doe",
    "resume_id": "resume_001",
    "keywords": ["C++", "System Design", "Python", "AWS"]
  },
  "job": {
    "source": "linkedin",
    "source_id": "job_12345",
    "company_name": "Tech Corp Inc",
    "job_title": "Senior Backend Engineer",
    "job_description": "We are looking for a Senior Backend Engineer with...",
    "apply_url": "https://linkedin.com/jobs/view/12345",
    "posted_date": "2026-01-16T00:00:00Z"
  }
}
```

**Response**:
```json
{
  "type": "JOB_MATCH_RESPONSE",
  "request_id": "req-20260118-001",
  "status": "MATCHED",
  "confidence_score": 0.87,
  "matched_skills": ["C++", "System Design"],
  "unmatched_required_skills": [],
  "reason": "Strong match: Core skills (C++, System Design) found. 87% confidence",
  "processing_time_ms": 45,
  "timestamp": "2026-01-18T10:30:01Z"
}
```

**Status Codes**:
- `MATCHED`: Job meets minimum threshold (default: 70%)
- `REJECTED`: Job below threshold
- `ERROR`: Processing error

---

### 3. BATCH_JOB_MATCH_REQUEST (Optional - Optimization)
**Direction**: Go Client → C++ Server  
**Purpose**: Submit multiple jobs in a single request

**Request**:
```json
{
  "type": "BATCH_JOB_MATCH_REQUEST",
  "batch_id": "batch-20260118-001",
  "timestamp": "2026-01-18T10:30:00Z",
  "jobs": [
    {
      "request_id": "req-001",
      "candidate": { ... },
      "job": { ... }
    },
    {
      "request_id": "req-002",
      "candidate": { ... },
      "job": { ... }
    }
  ]
}
```

**Response**:
```json
{
  "type": "BATCH_JOB_MATCH_RESPONSE",
  "batch_id": "batch-20260118-001",
  "results": [
    {
      "request_id": "req-001",
      "status": "MATCHED",
      "confidence_score": 0.85,
      ...
    },
    {
      "request_id": "req-002",
      "status": "REJECTED",
      "confidence_score": 0.45,
      ...
    }
  ],
  "timestamp": "2026-01-18T10:30:02Z"
}
```

---

### 4. SHUTDOWN (Either Direction)
**Purpose**: Graceful shutdown signal

**Request**:
```json
{
  "type": "SHUTDOWN",
  "reason": "Server restart",
  "timestamp": "2026-01-18T10:30:00Z"
}
```

**Response**:
```json
{
  "type": "SHUTDOWN_ACK",
  "timestamp": "2026-01-18T10:30:00Z"
}
```

---

## Error Handling

**Generic Error Response**:
```json
{
  "type": "ERROR",
  "request_id": "req-20260118-001",
  "error_code": "INVALID_JSON",
  "error_message": "Failed to parse JSON payload",
  "timestamp": "2026-01-18T10:30:01Z"
}
```

**Error Codes**:
- `INVALID_JSON`: Malformed JSON
- `MISSING_FIELD`: Required field missing
- `INTERNAL_ERROR`: Server-side error
- `TIMEOUT`: Request processing timeout
- `INVALID_REQUEST_TYPE`: Unknown message type

---

## Connection Lifecycle

1. **Go connects to C++ on port 10000**
2. **Optional**: Both send PING to verify connection
3. **Go sends JOB_MATCH_REQUEST(s)**
4. **C++ responds with JOB_MATCH_RESPONSE**
5. **Go processes ACK and logs if MATCHED**
6. **Repeat steps 3-5 periodically**
7. **On shutdown**: SHUTDOWN message sent, ACK received, connection closed

---

## Resilience Patterns

### Reconnection Logic
- Go detects connection loss
- Waits with exponential backoff (1s, 2s, 4s, 8s, max 60s)
- Attempts reconnection every interval
- Resumes job processing after successful reconnection

### Message Timeout
- C++ processes each request within 5 seconds (configurable)
- Go awaits response with 10-second timeout
- On timeout, request is marked failed and can be retried

### Duplicate Prevention
- Go maintains a local cache of processed job IDs
- Jobs already sent are not re-sent

---

## Configuration Parameters

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `PORT` | 10000 | TCP listening port |
| `MATCH_THRESHOLD` | 0.70 | Confidence score threshold |
| `REQUEST_TIMEOUT` | 5000ms | C++ request processing timeout |
| `RESPONSE_TIMEOUT` | 10000ms | Go response wait timeout |
| `RECONNECT_BACKOFF_MAX` | 60s | Max backoff interval |
| `BATCH_SIZE` | 10 | Max jobs per batch request |

---
