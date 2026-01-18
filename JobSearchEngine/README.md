# JobSearchEngine - Production-Ready Job Matching System

A highly efficient, distributed job matching system using **C++ TCP server** and **Go TCP client** for real-time job discovery and matching.

## Quick Start

```bash
# Terminal 1: Start C++ Server
cd JobSearchEngine
mkdir build && cd build
cmake .. && cmake --build . --config Release
./job_matching_engine --port 10000

# Terminal 2: Start Go Orchestrator
cd JobSearchEngine/go
go build -o jobsearch ./cmd/jobsearch
./jobsearch -config ../config/orchestrator.json
```

---

## Architecture

```
Go Orchestrator (TCP Client)
├── Job Platform Integration (LinkedIn, Naukri)
├── Job Fetching & Deduplication
├── TCP Client with Auto-Reconnect
└── Daily Logging of Matches
    │
    └─── TCP Port 10000 (JSON Protocol)
    │
C++ Matching Engine (TCP Server)
├── Socket Server (Multi-threaded)
├── Resume Profile Management
├── Resume Parsing & Skill Extraction
├── Job-Resume Matching Algorithm
└── Confidence Score Calculation
```

---

## Features

### ✅ Core Capabilities

- **TCP Socket Communication**: Length-prefixed JSON protocol
- **Resume Matching**: Skill-based confidence scoring
- **Multi-threaded Server**: Handles concurrent connections
- **Auto-reconnection**: Exponential backoff with health checks
- **Daily Logging**: Automatic log rotation (logs/YYYY-MM-DD.log)
- **Job Deduplication**: Prevents duplicate submissions
- **Cross-platform**: Windows & Linux support

### ✅ Production-Ready

- Graceful shutdown handling
- Signal-based lifecycle management
- Comprehensive error handling
- Thread-safe operations
- No external dependencies (Go uses stdlib only)
- Clear separation of concerns

---

## Project Structure

```
JobSearchEngine/
├── protocol/
│   └── PROTOCOL.md               # TCP message protocol specification
├── cpp/
│   ├── include/                  # C++ headers
│   │   ├── message_protocol.h   # TCP message definitions
│   │   ├── tcp_server.h         # Socket server
│   │   ├── matcher.h            # Matching engine
│   │   └── resume_parser.h      # Resume parsing
│   └── src/                      # C++ implementations
│       ├── main.cpp
│       ├── message_protocol.cpp
│       ├── tcp_server.cpp
│       ├── matcher.cpp
│       └── resume_parser.cpp
├── go/
│   ├── cmd/jobsearch/
│   │   └── main.go               # Orchestrator entry point
│   ├── pkg/
│   │   ├── client/
│   │   │   └── tcp_client.go    # TCP client implementation
│   │   ├── orchestrator/
│   │   │   └── orchestrator.go  # Main orchestration logic
│   │   ├── platform/
│   │   │   └── fetcher.go       # Job platform integration
│   │   └── logging/
│   │       └── logger.go        # Daily log management
│   └── go.mod
├── config/
│   └── orchestrator.json         # Go configuration file
├── logs/
│   └── 2026-01-18.log            # Sample daily log
├── CMakeLists.txt                # C++ build configuration
├── ARCHITECTURE.md               # Detailed design documentation
├── BUILD.md                      # Build and deployment guide
└── README.md                     # This file
```

---

## Message Protocol

### Request (Go → C++)

```json
{
  "type": "JOB_MATCH_REQUEST",
  "request_id": "req-001",
  "timestamp": "2026-01-18T10:30:00Z",
  "candidate": {
    "name": "John Doe",
    "resume_id": "resume_001",
    "keywords": ["C++", "System Design", "Python"]
  },
  "job": {
    "source": "linkedin",
    "source_id": "job_123",
    "company_name": "Tech Corp",
    "job_title": "Senior Engineer",
    "job_description": "Looking for C++ engineer...",
    "apply_url": "https://linkedin.com/jobs/123",
    "posted_date": "2026-01-16T00:00:00Z"
  }
}
```

### Response (C++ → Go)

```json
{
  "type": "JOB_MATCH_RESPONSE",
  "request_id": "req-001",
  "status": "MATCHED",
  "confidence_score": 0.87,
  "matched_skills": ["C++", "System Design"],
  "unmatched_required_skills": ["Rust"],
  "reason": "Strong match: Core skills found",
  "processing_time_ms": 45,
  "timestamp": "2026-01-18T10:30:01Z"
}
```

---

## Daily Log Format

**File:** `logs/YYYY-MM-DD.log`

```
=== JobSearchEngine - Daily Match Log ===
Date: 2026-01-18
=============================================

[2026-01-18 10:30:15] Candidate: John Doe | Company: Tech Corp | Job: Senior Engineer | Platform: linkedin | Score: 87.00% | Skills: [C++] | Apply: https://linkedin.com/jobs/123
[2026-01-18 11:45:22] Candidate: John Doe | Company: Microsoft | Job: Architect | Platform: naukri | Score: 92.00% | Skills: [C++, Azure] | Apply: https://naukri.com/job/456
```

**Logged:** Only MATCHED jobs (confidence score >= 0.70)

---

## Configuration

### C++ Server

```bash
./job_matching_engine --port 10000
```

Command-line options:
- `--port <number>` - TCP port (default: 10000)

### Go Orchestrator

Edit `config/orchestrator.json`:

```json
{
  "server": {
    "address": "localhost",
    "port": 10000
  },
  "candidate": {
    "name": "Your Name",
    "resume_id": "resume_001",
    "keywords": ["C++", "Python", "AWS"]
  },
  "schedule": {
    "fetch_interval": "30s",
    "health_check_interval": "10s",
    "tcp_timeout": "10s"
  },
  "logging": {
    "directory": "logs"
  },
  "platforms": [
    {"name": "linkedin", "enabled": true},
    {"name": "naukri", "enabled": true}
  ]
}
```

---

## Building & Running

### Prerequisites

**C++ Server:**
- CMake 3.10+
- C++17 compiler
- nlohmann/json header library

**Go Orchestrator:**
- Go 1.21+

### Build C++ Server

```bash
# Windows
cd JobSearchEngine && mkdir build && cd build
cmake .. -G "Visual Studio 17 2022"
cmake --build . --config Release
.\Release\job_matching_engine.exe --port 10000

# Linux/macOS
cd JobSearchEngine && mkdir build && cd build
cmake ..
make
./job_matching_engine --port 10000
```

### Build Go Orchestrator

```bash
cd JobSearchEngine/go
go build -o jobsearch ./cmd/jobsearch
./jobsearch -config ../config/orchestrator.json
```

### Run Both Services

**Terminal 1:**
```bash
./build/job_matching_engine --port 10000
# Output:
# JobSearchEngine - C++ Job Matching Server
# Port: 10000
# [Main] Server started successfully
```

**Terminal 2:**
```bash
./go/jobsearch -config config/orchestrator.json
# Output:
# JobSearchEngine - Go Job Orchestrator
# ...
# [Orchestrator] Started successfully
```

---

## Matching Algorithm

1. **Extract Skills** - Parse job description for skill keywords
2. **Compare** - Match resume skills against required skills
3. **Score** - Calculate: matched_skills / required_skills
4. **Decide** - If score >= 0.70: MATCHED, else REJECTED
5. **Log** - Write MATCHED jobs to daily log

**Example:**
```
Resume: [C++, Python, AWS, Docker]
Job Description: "C++ engineer with AWS experience"
Required Skills: [C++, AWS]
Matched: [C++, AWS]
Score: 2/2 = 1.00 (100%)
Status: MATCHED ✓ (logged)
```

---

## Resilience & Reconnection

### Connection Loss Handling

```
Connection Lost
  ↓
Wait 1s, Retry
  ↓
If failed: Wait 2s, Retry
  ↓
Continue: 1s → 2s → 4s → 8s → 16s → 32s → 60s (max)
  ↓
Resume job processing on success
```

### Job Deduplication

- In-memory cache of processed job IDs
- Prevents duplicate submissions within session
- Cache resets on restart (set to persistent DB for production)

### Health Checks

- PING/PONG every 10 seconds
- Auto-reconnect on failure
- Transparent to job processing

---

## Error Handling

| Scenario | C++ Action | Go Action |
|----------|-----------|----------|
| Invalid JSON | Return ERROR | Log, skip job |
| Missing field | Return ERROR | Log, skip job |
| Socket timeout | Close connection | Reconnect |
| Processing failure | Return ERROR | Log, continue |

---

## Performance

| Metric | Value |
|--------|-------|
| Message Overhead | 4 bytes (length prefix only) |
| Avg. Processing Time | ~50ms per job |
| Max Concurrent Connections | Unlimited (thread per client) |
| Reconnect Latency | 1-60s (exponential backoff) |
| Daily Log Size | ~100KB (varies) |

---

## Monitoring

### C++ Server Output

```
[Main] Server started successfully
[TCPServer] Listening on port 10000
[ClientHandler] Client connected
[Handler] Processing request req-001
[Handler] Response: status=MATCHED, score=0.87
[ClientHandler] Client disconnected
```

### Go Orchestrator Output

```
[Orchestrator] Fetching jobs...
[LinkedIn] Found 5 jobs
[Orchestrator] Processing job job_123
[Orchestrator] MATCHED: Senior Engineer at Tech Corp (Score: 87.00%)
[HealthCheck] Ping successful
```

### Log Files

Check matched jobs:
```bash
tail -f logs/$(date +%Y-%m-%d).log
```

---

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed design, components, and workflow
- [BUILD.md](BUILD.md) - Complete build and deployment instructions
- [protocol/PROTOCOL.md](protocol/PROTOCOL.md) - TCP message protocol specification

---

## Troubleshooting

### Port Already in Use

```bash
# Find and kill process
lsof -i :10000 | grep LISTEN | awk '{print $2}' | xargs kill -9  # macOS/Linux
netstat -ano | findstr :10000  # Windows
```

### C++ Build Fails

```bash
# Install nlohmann/json
mkdir -p cpp/include/nlohmann
curl -L https://github.com/nlohmann/json/releases/download/v3.11.2/json.hpp \
  -o cpp/include/nlohmann/json.hpp
```

### Go Connection Refused

```bash
# Ensure C++ server is running
ps aux | grep job_matching_engine  # macOS/Linux
Get-Process | grep job_matching_engine  # Windows
```

### No Jobs Matched

- Check candidate keywords match job descriptions
- Verify job descriptions contain skill keywords
- Consider lowering match threshold (if < 0.70 required)

---

## Future Enhancements

- TLS/SSL encryption for secure communication
- Authentication and authorization tokens
- ML-based job relevance scoring
- Resume PDF/DOCX parsing
- Direct LinkedIn API integration
- Distributed server deployment
- Admin dashboard UI
- Prometheus metrics export
- Email notifications for matches

---

## License

[LICENSE](LICENSE)

---

## Contributing

Contributions welcome! Please ensure:
- Code follows production quality standards
- Tests pass before submission
- Documentation is updated
- Commit messages are descriptive

---

## Contact & Support

For issues, questions, or suggestions:
1. Check [ARCHITECTURE.md](ARCHITECTURE.md) for design details
2. Review [BUILD.md](BUILD.md) for build issues
3. Check troubleshooting section above
4. Open an issue with detailed information

---

**Last Updated:** January 18, 2026
**Status:** Production-Ready
