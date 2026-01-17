# Development Notes and Future Enhancements

## Current Implementation Status

### Completed Components

#### C++ Resume Engine ✅
- [x] Resume data model structures
- [x] Resume parser with keyword extraction
- [x] Job matching engine with confidence scoring
- [x] IPC handler for JSON communication
- [x] Main event loop with stdin/stdout processing
- [x] CMake build system
- [x] Thread-safe singleton patterns
- [x] Comprehensive error handling

#### Go Orchestration Layer ✅
- [x] CLI argument parsing
- [x] Configuration management (YAML parsing)
- [x] Daily logger with deduplication
- [x] Scheduler with configurable intervals
- [x] Job portal search interface
- [x] Rate limiting implementation
- [x] IPC client for subprocess communication
- [x] Go module structure with dependencies
- [x] Exponential backoff retry logic
- [x] Platform-specific code (Windows/Linux)

#### Infrastructure & Docs ✅
- [x] Architecture documentation
- [x] Build instructions for all platforms
- [x] Deployment guide (systemd, Docker, Kubernetes)
- [x] Sample resumes and log files
- [x] Configuration templates
- [x] README with quick start guide
- [x] Folder structure scaffolding

---

## Known Limitations & TODOs

### Phase 1: Core (Current)
- [x] Basic resume parsing via keywords
- [x] Weighted job matching algorithm
- [x] File-based logging
- [x] Daily scheduling

### Phase 2: Portal Integration (Recommended Next)
- [ ] LinkedIn API integration (requires OAuth2)
- [ ] Naukri web scraping (with Selenium/Chromedp)
- [ ] Indeed.com integration
- [ ] Glassdoor integration
- [ ] Stack Overflow Jobs integration

### Phase 3: Advanced Features (Future)
- [ ] REST API for job status queries
- [ ] Web dashboard for visualizing matches
- [ ] Email notifications for high-scoring matches
- [ ] Candidate profile improvement suggestions
- [ ] Job trend analysis and insights
- [ ] Machine learning-based job quality scoring
- [ ] Resume version management
- [ ] Multi-candidate support
- [ ] OAuth2 for secure credential storage

### Phase 4: Infrastructure
- [ ] Proper database backend (PostgreSQL)
- [ ] Cache layer (Redis)
- [ ] Message queue (RabbitMQ/Kafka)
- [ ] Distributed tracing (Jaeger)
- [ ] Metrics collection (Prometheus)
- [ ] Centralized logging (ELK stack)

---

## Implementation Details for Future Phases

### LinkedIn Integration

```cpp
// cpp/src/linkedin_api.cpp (future)
class LinkedInAPI {
public:
    LinkedInAPI(const std::string& api_key);
    std::vector<JobListing> search(const std::vector<std::string>& keywords);
    
private:
    std::string api_key_;
    HttpClient client_;
    RateLimiter limiter_;
};
```

### Naukri Web Scraping

```go
// go/pkg/search/naukri.go (enhancement)
type NaukriScraper struct {
    client *chromedp.Browser
    limiter *RateLimiter
}

func (ns *NaukriScraper) SearchWithBrowser(keywords []string) ([]JobListing, error) {
    // Use Chromedp for JavaScript-heavy sites
    // Implement politeness delays
    // Handle pagination
}
```

### REST API

```go
// go/pkg/api/handler.go (future)
func (h *Handler) GetMatches(w http.ResponseWriter, r *http.Request) {
    // GET /api/candidate/{id}/matches
    // GET /api/candidate/{id}/matches/{jobId}
    // POST /api/candidate/{id}/feedback
}
```

### Database Schema

```sql
-- PostgreSQL schema (future)
CREATE TABLE candidates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    resume_path VARCHAR(512),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE job_matches (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id),
    job_id VARCHAR(256),
    company VARCHAR(256),
    role VARCHAR(256),
    source VARCHAR(50),
    confidence_score FLOAT,
    applied BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_candidate_date ON job_matches(candidate_id, created_at);
CREATE INDEX idx_job_id ON job_matches(job_id);
```

---

## Code Quality Improvements

### Testing Framework Setup

```cpp
// cpp/tests/test_parser.cpp (incomplete)
#include <gtest/gtest.h>
#include "../include/resume_parser.h"

class ResumeParserTest : public ::testing::Test {
protected:
    jobsearch::ResumeParser parser;
};

TEST_F(ResumeParserTest, ParseValidResume) {
    std::string resume = "10 years C++ experience...";
    auto parsed = parser.parse(resume, "John Doe");
    ASSERT_NE(parsed, nullptr);
    EXPECT_EQ(parsed->experience_years, 10);
    EXPECT_FALSE(parsed->skills.empty());
}
```

```go
// go/pkg/scheduler/scheduler_test.go (incomplete)
func TestBuildSearchKeywords(t *testing.T) {
    resume := &ipc.Resume{
        Roles: []string{"Engineer", "Architect"},
        Skills: []string{"Go", "C++"},
        ExperienceYears: 10,
    }
    
    sched := &Scheduler{resume: resume}
    keywords := sched.buildSearchKeywords()
    
    assert.Contains(t, keywords, "Engineer")
    assert.True(t, len(keywords) > 0)
}
```

### Performance Optimization Notes

1. **C++ Parser**
   - Use trie data structure for keyword matching (vs linear search)
   - Implement SIMD for string comparison
   - Cache compiled regex patterns

2. **Go Scheduler**
   - Connection pooling for HTTP requests
   - Concurrent job matching (goroutine pool)
   - In-memory cache for recently seen jobs

3. **IPC Communication**
   - Consider gRPC for better performance
   - Implement bidirectional streaming for large job batches
   - Add compression for resume content

---

## Security Enhancements (Production)

1. **Authentication**
   - OAuth2 for portal integrations
   - API key management via HashiCorp Vault
   - TLS certificate validation

2. **Data Protection**
   - Encrypt resume data at rest
   - Use secure channels for IPC (Unix sockets, not pipes)
   - Implement audit logging

3. **API Security**
   - Rate limiting per client
   - DDoS protection (if exposing API)
   - Input validation and sanitization

4. **Code Security**
   - Buffer overflow protection (Rust alternative for critical paths)
   - Memory leak detection (valgrind in CI)
   - Dependency vulnerability scanning

---

## Configuration Schema Extension

Future enhancements to `config.yaml`:

```yaml
# Advanced matching
matching:
  use_ml_model: false  # Future: enable ML-based scoring
  ml_model_path: "./models/scoring_model.pb"
  custom_weights:
    senior_preference: true
    specialization: "System Design"

# Database (future)
database:
  enabled: false
  type: "postgresql"
  connection_string: "${DB_CONN_STRING}"

# API (future)
api:
  enabled: false
  port: 8080
  auth_enabled: true
  tls_cert: "./certs/cert.pem"
  tls_key: "./certs/key.pem"

# Notifications (future)
notifications:
  email:
    enabled: false
    smtp_server: "smtp.gmail.com"
    from_address: "${EMAIL_FROM}"
  slack:
    enabled: false
    webhook_url: "${SLACK_WEBHOOK}"
  mobile:
    enabled: false
    push_service: "firebase"
```

---

## Platform-Specific Enhancements

### Windows (Sleep Prevention)
```cpp
// cpp/src/windows_sleep.cpp (future)
#ifdef _WIN32
#include <windows.h>

class WindowsSleepPrevention {
public:
    void enable() {
        SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED);
    }
    
    void disable() {
        SetThreadExecutionState(ES_CONTINUOUS);
    }
};
#endif
```

### Linux (Daemon Mode)
```go
// go/pkg/daemon/daemon.go (future)
func BecomeDaemon() error {
    // Fork process
    // Close file descriptors
    // Change working directory
    // Create new session/process group
}
```

### macOS (Launch Agent)
```xml
<!-- ~/Library/LaunchAgents/com.jobsearch.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jobsearch</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/jobsearch_app</string>
        <string>--candidate</string>
        <string>John Doe</string>
    </array>
    <key>StartInterval</key>
    <integer>21600</integer>
    <key>StandardOutPath</key>
    <string>/var/log/jobsearch.log</string>
</dict>
</plist>
```

---

## Metrics to Track

### Application Metrics
- Jobs searched per cycle
- Jobs matched per cycle
- Average confidence score
- Search latency
- Parse latency
- Match latency

### System Metrics
- CPU usage
- Memory usage
- Disk usage (logs)
- Network I/O
- Process uptime

### Business Metrics
- Top matching companies
- Most common roles
- Skill demand trends
- Location distribution

---

## References and Resources

- [C++17 Standard Library](https://en.cppreference.com/)
- [Go Best Practices](https://golang.org/doc/effective_go)
- [Google Test Framework](https://github.com/google/googletest)
- [Protocol Buffers](https://developers.google.com/protocol-buffers) (for future IPC)
- [gRPC](https://grpc.io/) (for future performance)

---

## Maintenance Schedule

- **Daily**: Monitor logs for errors, check service status
- **Weekly**: Review job matching statistics, update excluded companies
- **Monthly**: Archive old logs, analyze trends, update resume if needed
- **Quarterly**: Update job portal integrations, review configuration
- **Annually**: Update dependencies, security audit, performance review

---

**Document last updated: 2025-01-17**
