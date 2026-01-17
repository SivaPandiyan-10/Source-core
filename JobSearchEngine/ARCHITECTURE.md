# JobSearchEngine - Architecture Documentation

## Executive Summary

JobSearchEngine is a production-grade, multi-language utility that continuously searches for job openings matching candidate profiles. It leverages C++ for high-performance resume parsing and matching, and Go for orchestration, scheduling, and web interactions. The system is designed for 24/7 operation with graceful error handling, rate limiting, and cross-platform support.

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Go Orchestration Layer                    │
│  (Main CLI, Scheduling, Web Search, Logging, Service Mgmt)  │
└─────────────────┬───────────────────────────────────────────┘
                  │
        ┌─────────┴──────────┬──────────────┬──────────────┐
        │                    │              │              │
        v                    v              v              v
   ┌─────────┐      ┌──────────────┐  ┌──────────┐  ┌──────────┐
   │Scheduler│      │Resume Parser │  │Web Search│  │  Logger  │
   │  (Go)   │      │   Engine(C++)│  │  (Go)    │  │   (Go)   │
   └─────────┘      └──────────────┘  └──────────┘  └──────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        v                                       v
   ┌──────────────┐                  ┌──────────────────┐
   │Resume Storage│                  │Matching Engine   │
   │  (JSON)      │                  │  (C++)           │
   └──────────────┘                  └──────────────────┘
```

---

## Component Breakdown

### 1. **Go Orchestration Layer** (Main Process)
**Responsibility**: CLI interface, coordination, scheduling, web interactions, logging.

#### Key Components:
- **CLI Handler** (`go/cmd/jobsearch/main.go`)
  - Parses command-line arguments: `--candidate "Name" --config "config.yaml"`
  - Validates candidate name against resume repository
  - Spawns C++ resume engine as subprocess
  - Initializes scheduling and job search loops

- **Scheduler** (`go/pkg/scheduler/scheduler.go`)
  - Manages periodic job search execution (configurable interval, default 6h)
  - Maintains deduplication cache to prevent duplicate entries
  - Implements exponential backoff for retries on network failures
  - Respects platform rate limits for job search APIs

- **Web Search Engine** (`go/pkg/search/searcher.go`)
  - Abstracts job portal integrations (LinkedIn, Naukri, extensible)
  - Keyword-based search with configurable filters
  - Implements scraping logic with rate limiting (backoff, user-agent rotation)
  - Returns standardized JobListing struct to matching engine

- **Logger** (`go/pkg/logging/logger.go`)
  - Writes matched jobs to daily log files (`logs/YYYY-MM-DD.log`)
  - Formats log entries with company, role, link, source, confidence score, timestamp
  - Appends to existing logs, no overwrites
  - Thread-safe logging with buffered writes

- **IPC Handler** (`go/pkg/ipc/ipc.go`)
  - Communicates with C++ resume engine via JSON over stdin/stdout
  - Passes resume metadata and job listings for matching
  - Handles subprocess lifecycle and error recovery

- **Configuration Manager** (`go/pkg/config/config.go`)
  - Loads and validates YAML/JSON configuration
  - Manages job site URLs, search intervals, thresholds, paths
  - Provides runtime configuration updates without restart (future)

### 2. **C++ Resume Engine** (Subprocess)
**Responsibility**: Resume parsing, feature extraction, job matching, confidence scoring.

#### Key Components:
- **Resume Parser** (`cpp/src/resume_parser.cpp`)
  - Extracts skills, experience, role keywords, location preferences from plain text resumes
  - Normalizes text (case-insensitive, punctuation handling)
  - Builds searchable index of resume features
  - Supports TXT, DOCX (via text extraction), PDF (via text extraction)

- **Matching Engine** (`cpp/src/matcher.cpp`)
  - Compares job descriptions against resume features
  - Calculates confidence scores based on:
    - Skill overlap percentage
    - Experience level alignment
    - Role relevance scoring
    - Location / remote preferences
  - Applies configurable filters (min confidence threshold)
  - Only returns jobs above confidence threshold

- **Data Models** (`cpp/include/models.h`)
  - `Resume`: parsed resume with features and metadata
  - `JobListing`: standardized job data from portals
  - `MatchResult`: matching score with detailed breakdown
  - `Configuration`: matching thresholds and rules

---

## Data Flow Diagram

```
1. User Execution
   └─> Go CLI: --candidate "John Doe" --config config.yaml

2. Resume Loading & Validation
   └─> Go validates candidate name against resumes/ directory
   └─> Reads resume file (resumes/john_doe.txt or similar)

3. Resume Parsing
   └─> Go spawns C++ engine as subprocess
   └─> Sends resume content via IPC (JSON format)
   └─> C++ parser extracts: skills, experience, roles, locations
   └─> Returns parsed metadata to Go

4. Periodic Job Search
   └─> Scheduler triggers every N hours
   └─> Go search module queries job portals (LinkedIn API, Naukri scraping, etc.)
   └─> Collects job listings: title, company, link, description, location
   └─> Filters by configured keywords/locations

5. Job Matching
   └─> Go sends job listings + parsed resume to C++ matcher
   └─> C++ calculates confidence scores for each job
   └─> Returns matches with scores > threshold

6. Logging & Output
   └─> Go receives matched jobs from C++
   └─> Deduplicates against existing logs
   └─> Writes to logs/YYYY-MM-DD.log
   └─> Output format: [timestamp] Company | Role | Link | Source | Score

7. Sleep Handling
   └─> On Windows: Uses SetThreadExecutionState to prevent sleep
   └─> On Linux: Daemon mode with periodic wake-up checks
   └─> Resumes operation after system wake-up

8. Long-Running Loop
   └─> Scheduler sleeps until next interval
   └─> Repeats steps 4-7
```

---

## IPC Protocol (Go ↔ C++)

### Resume Parsing Request
```json
{
  "command": "parse_resume",
  "content": "John Doe\n10 years experience in Software Engineering...",
  "candidate_name": "John Doe"
}
```

### Resume Parsing Response
```json
{
  "status": "success",
  "resume": {
    "candidate": "John Doe",
    "skills": ["C++", "Go", "Python", "System Design"],
    "experience_years": 10,
    "roles": ["Software Engineer", "Architect", "Lead Developer"],
    "locations": ["San Francisco", "Remote"],
    "industry": "Technology"
  }
}
```

### Job Matching Request
```json
{
  "command": "match_jobs",
  "resume": { "skills": [...], "experience_years": 10, ... },
  "jobs": [
    {
      "id": "job_123",
      "title": "Senior Software Engineer",
      "company": "TechCorp",
      "location": "San Francisco",
      "description": "Looking for C++ expert with 8+ years experience...",
      "link": "https://...",
      "source": "LinkedIn"
    }
  ],
  "config": {
    "min_confidence_threshold": 0.65,
    "skill_weight": 0.35,
    "experience_weight": 0.30,
    "role_weight": 0.25,
    "location_weight": 0.10
  }
}
```

### Job Matching Response
```json
{
  "status": "success",
  "matches": [
    {
      "job_id": "job_123",
      "confidence_score": 0.85,
      "score_breakdown": {
        "skill_match": 0.90,
        "experience_match": 0.85,
        "role_match": 0.75,
        "location_match": 1.0
      },
      "matched_skills": ["C++", "System Design"],
      "explanation": "Strong skill and experience alignment"
    }
  ]
}
```

---

## Configuration Structure

**config/config.yaml**:
```yaml
job_search:
  enabled: true
  interval_hours: 6
  min_confidence_threshold: 0.65

job_portals:
  linkedin:
    enabled: true
    search_keywords_from_resume: true
    rate_limit_requests_per_hour: 30
  
  naukri:
    enabled: true
    search_keywords_from_resume: true
    rate_limit_requests_per_hour: 20

filters:
  experience_tolerance_years: 1
  preferred_locations:
    - "San Francisco"
    - "Remote"
  excluded_companies: []
  excluded_keywords: ["Intern", "Trainee"]

paths:
  resumes: "./resumes"
  logs: "./logs"
  cache: "./cache"

system:
  prevent_sleep_on_windows: true
  log_level: "INFO"
  max_retries: 3
  retry_backoff_seconds: 30
```

---

## Folder Structure

```
JobSearchEngine/
├── cpp/                          # C++ Resume Engine
│   ├── CMakeLists.txt           # Build configuration
│   ├── include/
│   │   ├── models.h             # Data structures
│   │   ├── resume_parser.h      # Resume extraction
│   │   ├── matcher.h            # Job matching
│   │   └── ipc_handler.h        # Go communication
│   ├── src/
│   │   ├── main.cpp             # Entry point (subprocess)
│   │   ├── resume_parser.cpp    # Resume parsing logic
│   │   ├── matcher.cpp          # Matching algorithm
│   │   ├── ipc_handler.cpp      # IPC communication
│   │   └── utils.cpp            # Utilities (text processing, etc.)
│   └── tests/
│       ├── test_parser.cpp      # Parser unit tests
│       ├── test_matcher.cpp     # Matcher unit tests
│       └── CMakeLists.txt
│
├── go/                           # Go Orchestration Layer
│   ├── go.mod                   # Go module definition
│   ├── go.sum                   # Dependency lock file
│   ├── cmd/jobsearch/
│   │   └── main.go              # CLI entry point
│   └── pkg/
│       ├── scheduler/
│       │   ├── scheduler.go     # Job scheduling logic
│       │   ├── deduplicator.go  # Duplicate prevention
│       │   └── scheduler_test.go
│       ├── search/
│       │   ├── searcher.go      # Job portal integration
│       │   ├── linkedin.go      # LinkedIn implementation
│       │   ├── naukri.go        # Naukri implementation
│       │   └── search_test.go
│       ├── logging/
│       │   ├── logger.go        # Log writing
│       │   └── logger_test.go
│       ├── config/
│       │   ├── config.go        # Configuration management
│       │   └── config_test.go
│       └── ipc/
│           ├── ipc.go           # Go-C++ communication
│           └── ipc_test.go
│
├── config/
│   └── config.yaml              # Configuration template
│
├── resumes/
│   ├── john_doe.txt             # Example resume
│   └── jane_smith.txt
│
├── logs/                         # Daily log files created here
│   └── 2025-01-17.log
│
├── docs/
│   ├── ARCHITECTURE.md          # This file
│   ├── BUILD.md                 # Build instructions
│   ├── DEPLOYMENT.md            # Deployment guide
│   └── API.md                   # IPC API documentation
│
├── Makefile                     # Convenient build targets
├── .gitignore
├── README.md                    # Project overview
└── LICENSE
```

---

## Technology Choices & Rationale

| Component | Tech | Rationale |
|-----------|------|-----------|
| CLI & Orchestration | Go | Excellent concurrency, quick startup, cross-platform |
| Resume Parsing & Matching | C++ | High performance, memory efficiency, complex algorithms |
| Configuration | YAML | Human-readable, widely supported |
| Resume Storage | Plain text + metadata | Lightweight, portable, privacy-friendly |
| IPC Protocol | JSON over stdin/stdout | Language-agnostic, debuggable, standard |
| Logging | File-based (daily rotation) | Simple, queryable, no external dependencies |
| Job Source APIs | HTTP (web scraping + APIs) | Real-time data, flexible integration |
| Database | None (file-based cache) | Simplicity, zero dependencies, easy deployment |

---

## Error Handling & Resilience

1. **Network Failures**: Exponential backoff, configurable retry count
2. **Rate Limiting**: Respect API/portal rate limits, queue jobs with delays
3. **Resume Not Found**: Graceful exit with informative error message
4. **Subprocess Failure**: Log error, restart on next scheduler tick
5. **Log Write Failures**: Queue entries in memory, retry on next interval
6. **Configuration Errors**: Validate on startup, use safe defaults

---

## Security & Privacy Considerations

1. **No Credentials Stored**: Job portal access uses public APIs or authenticated sessions only during runtime
2. **Resume Data**: Stored locally only, never uploaded without consent
3. **Rate Limiting**: Respect portals' ToS, avoid aggressive scraping
4. **User-Agent Rotation**: Rotate user agents to avoid blocking
5. **Timeouts**: Implement request timeouts (30s default) to prevent hanging
6. **Logging**: No sensitive data (passwords, tokens) in logs

---

## Future Extensibility

- **New Job Portals**: Implement `JobPortal` interface in Go search layer
- **Advanced Matching**: Plug in ML models for better scoring
- **Database Backend**: Replace file-based logging with optional DB
- **REST API**: Expose status, logs, matching results via HTTP
- **Web Dashboard**: Real-time job matches, configuration management
- **Mobile Notifications**: Alert candidates of high-confidence matches

---

## Performance Targets

- **Resume Parsing**: < 100ms for typical resume (< 2000 words)
- **Job Matching**: < 50ms per job listing
- **Log Writing**: < 10ms per entry
- **Memory Footprint**: < 50MB (Go + C++ combined)
- **Scheduling Overhead**: < 1% CPU during idle periods

---

## Compliance & Standards

- **Cross-Platform**: Windows (x86_64) and Linux (x86_64, ARM64)
- **Standards**: POSIX for Linux, Windows API for sleep prevention
- **Build System**: CMake (C++), Go Modules (Go)
- **Testing**: Google Test (C++), built-in testing (Go)
- **Documentation**: Markdown, inline code comments
