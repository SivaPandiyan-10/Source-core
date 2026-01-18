# JobSearchEngine Go Code: Quick Reference

A beginner's map of the Go codebase with examples and explanations.

---

## Project Structure

```
go/
├── cmd/
│   └── jobsearch/
│       └── main.go              ← START HERE: Entry point, reads config
├── pkg/
│   ├── client/
│   │   └── tcp_client.go        ← Talks to C++ server over TCP
│   ├── logging/
│   │   └── logger.go            ← Saves matched jobs to daily log files
│   ├── orchestrator/
│   │   └── orchestrator.go      ← Main coordinator, fetches jobs and matches them
│   └── platform/
│       └── fetcher.go           ← Gets jobs from LinkedIn, Naukri, etc.
```

### What Each File Does

#### `main.go` - The Starting Point
**What it does:**
- Reads the `config/orchestrator.json` file
- Converts config into settings the orchestrator understands
- Starts the orchestrator
- Handles Ctrl+C shutdown

**When to read it:**
- First, to understand the overall flow
- When you want to change settings (fetch interval, timeouts, etc.)

**Key concepts:**
- Configuration loading from JSON
- Graceful shutdown with signal handling

---

#### `tcp_client.go` - Talk to C++ Server
**What it does:**
- Connects to C++ server at `localhost:10000`
- Sends messages to server (JSON format)
- Receives responses from server
- Reconnects automatically if connection drops

**When to read it:**
- To understand how the Go program talks to C++
- To understand the network protocol (length-prefixed JSON)

**Key concepts:**
- TCP socket connections
- Binary framing (4-byte length + JSON payload)
- Exponential backoff for reconnection
- Timeouts

**Example flow:**
```
1. NewTCPClient("localhost:10000", 30*time.Second)
2. client.Connect(ctx)  ← Opens TCP socket
3. client.SendMessage(jobMatchRequest)  ← Sends JSON over socket
4. client.ReceiveMessage(&response)  ← Receives JSON from socket
5. client.IsConnected()  ← Checks if still connected
```

---

#### `orchestrator.go` - The Main Coordinator
**What it does:**
- Starts 3 background workers (goroutines)
- Periodically fetches jobs from job platforms
- Sends jobs to C++ server for matching
- Logs matched jobs
- Keeps connection to C++ server alive with health checks

**When to read it:**
- To understand the overall job search flow
- To see how different parts work together

**Key components:**

1. **Job Fetching Loop**
   ```
   Every FetchInterval (e.g., 1 hour):
   - Fetch jobs from enabled platforms
   - For each job: send to C++ server for matching
   - Log if it matches
   - Skip jobs we've already processed
   ```

2. **Health Check Loop**
   ```
   Every HealthCheckInterval (e.g., 5 minutes):
   - Ping the C++ server
   - If no response, try to reconnect
   ```

3. **Data Flow**
   ```
   Job Platform → fetchJobsFromPlatforms()
              ↓
   Send to C++ → submitJobForMatching()
              ↓
   Response → Check if matched → Log entry
   ```

**Key concepts:**
- Goroutines running simultaneously
- Message passing between Go and C++
- Deduplication (remembering which jobs we've seen)

---

#### `logger.go` - Save Matched Jobs
**What it does:**
- Creates a new log file each day (logs/YYYY-MM-DD.log)
- Writes job match information to the file
- Counts how many jobs matched today

**When to read it:**
- To understand how logs are organized
- To see Mutex usage (thread-safe file writing)

**File format:**
```
=== JobSearchEngine - Daily Match Log ===
Date: 2024-01-15
=============================================

[2024-01-15 09:30:45] Candidate: John Doe | Company: Google | Job: Backend Engineer | ... | Score: 85.50%
[2024-01-15 10:15:22] Candidate: John Doe | Company: Meta | Job: Infrastructure Engineer | ... | Score: 72.30%
```

**Key concepts:**
- Daily log rotation (new file each day)
- Mutex for thread-safe file access
- Formatted output

---

#### `fetcher.go` - Get Jobs from Platforms
**What it does:**
- Implements job fetching for different platforms
- Currently simulates LinkedIn and Naukri (with demo data)
- In production, would call real APIs or scrapers

**When to read it:**
- To add new job platforms
- To understand the JobInfo structure

**Platform interface:**
```go
FetchJobs(platformName string, keywords []string) → []JobInfo
```

**How to add a new platform:**
1. Create `fetchNewPlatform()` function
2. Add case to FetchJobs() switch statement
3. Return []JobInfo with job data

---

## Data Structures (The Shapes of Data)

### In `main.go`
```go
type Config struct {
    Server struct {
        Address string  // "localhost"
        Port    int     // 10000
    }
    Candidate struct {
        Name     string   // "John Doe"
        ResumeID string   // "john-doe-resume"
        Keywords []string // ["Go", "Python", "Docker"]
    }
    Schedule struct {
        FetchInterval       string // "1h"
        HealthCheckInterval string // "5m"
        TCPTimeout          string // "30s"
    }
    Logging struct {
        Directory string // "logs"
    }
    Platforms []struct {
        Name    string // "linkedin"
        Enabled bool   // true
    }
}
```

### In `tcp_client.go`
```go
type Message struct {
    Type    string          // "PING", "JOB_MATCH_REQUEST", etc.
    Payload json.RawMessage // The actual data (JSON)
}

type TCPClient struct {
    address        string        // Server location
    conn           net.Conn      // The socket connection
    timeout        time.Duration // How long to wait
    reconnectDelay time.Duration // How long between retries
    maxReconnects  int           // How many retries
}
```

### In `orchestrator.go`
```go
type JobMatchRequest struct {
    Type      string        // "JOB_MATCH_REQUEST"
    RequestID string        // Unique ID for this request
    Timestamp string        // When sent (ISO 8601)
    Candidate CandidateInfo // Who we're matching
    Job       JobInfo       // The job to match
}

type JobMatchResponse struct {
    Type                    string   // "JOB_MATCH_RESPONSE"
    Status                  string   // "MATCHED" or "REJECTED"
    ConfidenceScore         float64  // 0.0 to 1.0
    MatchedSkills           []string // ["Go", "Python"]
    UnmatchedRequiredSkills []string // ["Rust"]
    // ... more fields
}

type JobInfo struct {
    Source         string // "linkedin" or "naukri"
    SourceID       string // "job-12345" (unique on that platform)
    CompanyName    string // "Google"
    JobTitle       string // "Senior Backend Engineer"
    JobDescription string // Full job posting text
    ApplyURL       string // Link to apply
    PostedDate     string // When posted (ISO 8601)
}

type CandidateInfo struct {
    Name     string   // "John Doe"
    ResumeID string   // Where to find resume
    Keywords []string // Their skills
}

type Orchestrator struct {
    tcpClient       *TCPClient
    logger          *Logger
    config          *Config
    ctx             context.Context      // For cancellation
    cancel          context.CancelFunc   // To cancel ctx
    wg              sync.WaitGroup       // Wait for goroutines
    processedJobIDs sync.Map             // Cache of seen jobs
    scheduleTicker  *time.Ticker         // Timer for job fetching
    healthCheckTick *time.Ticker         // Timer for health checks
}
```

### In `logger.go`
```go
type LogEntry struct {
    Timestamp       time.Time  // When found
    CandidateName   string     // Who
    CompanyName     string     // Which company
    JobTitle        string     // What job
    ApplyLink       string     // Where to apply
    JobPlatform     string     // Where found
    ConfidenceScore float64    // Match %
    MatchedSkills   []string   // What skills matched
}

type Logger struct {
    logDir     string        // "logs"
    currentDay string        // "2024-01-15"
    file       *os.File      // Currently open file
    mu         sync.Mutex    // Lock for thread-safety
}
```

---

## Important Methods (Functions That Belong to Types)

### TCPClient Methods
```go
client.Connect(ctx)                 // One-time connection attempt
client.ConnectWithRetry(ctx)        // Retry with backoff
client.SendMessage(msg interface{}) // Send JSON to server
client.ReceiveMessage(&response)    // Receive JSON from server
client.IsConnected() bool           // Check if connected
client.Ping() error                 // Health check
client.Close() error                // Close connection
```

### Orchestrator Methods
```go
orch.Start() error                          // Run the orchestrator
orch.Stop()                                 // Stop it
orch.fetchAndProcessJobs()                  // Fetch and match jobs
orch.scheduleJobFetching()                  // Job fetching goroutine
orch.healthCheckWorker()                    // Health check goroutine
orch.submitJobForMatching(job) (bool, error) // Send one job to C++
```

### Logger Methods
```go
logger.LogMatch(entry)  error   // Write a match to log
logger.Close() error            // Close the file
logger.GetMatchCount() (int, error) // Count today's matches
```

---

## The Main Flow (Step by Step)

```
START: User runs `go run cmd/jobsearch/main.go`

1. main() 
   ├─ Load config/orchestrator.json
   ├─ Parse time durations ("1h" → 1 hour)
   └─ Create orchestrator.Config

2. NewOrchestrator(config)
   ├─ Create TCPClient
   ├─ Create Logger
   └─ Create context and timers

3. orch.Start()
   ├─ Connect to C++ server on localhost:10000
   └─ Start 3 goroutines:
      
      GOROUTINE 1: scheduleJobFetching()
      ├─ Every 1 hour (FetchInterval):
      │  ├─ fetchJobsFromPlatforms()
      │  │  ├─ Call platform.FetchJobs("linkedin", keywords)
      │  │  ├─ Call platform.FetchJobs("naukri", keywords)
      │  │  └─ Return all jobs
      │  │
      │  └─ For each job (if not already processed):
      │     ├─ submitJobForMatching(job)
      │     │  ├─ Create JobMatchRequest with job data
      │     │  ├─ tcpClient.SendMessage(request)
      │     │  ├─ tcpClient.ReceiveMessage(response)
      │     │  └─ If MATCHED:
      │     │     └─ logger.LogMatch(entry)
      │     └─ Print result
      
      GOROUTINE 2: healthCheckWorker()
      ├─ Every 5 minutes (HealthCheckInterval):
      │  ├─ If not connected: try to reconnect
      │  └─ If connected: send PING
      
      GOROUTINE 3: handleShutdown()
      └─ Wait for Ctrl+C, then call orch.Stop()

4. orch.Stop()
   ├─ Cancel the context
   └─ This causes all goroutines to exit

5. Clean up
   ├─ Stop timers
   ├─ Wait for goroutines to finish (wg.Wait())
   ├─ Close TCP connection
   └─ Close logger

END
```

---

## Configuration File (config/orchestrator.json)

```json
{
  "server": {
    "address": "localhost",
    "port": 10000
  },
  "candidate": {
    "name": "John Doe",
    "resume_id": "john-doe-resume",
    "keywords": ["Go", "Python", "Docker", "Kubernetes"]
  },
  "schedule": {
    "fetch_interval": "1h",
    "health_check_interval": "5m",
    "tcp_timeout": "30s"
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

### What Each Setting Does
- **server.address/port** - Where the C++ server is running
- **candidate.name/resume_id** - Your information
- **candidate.keywords** - Your skills (for job matching)
- **fetch_interval** - How often to check for new jobs
- **health_check_interval** - How often to ping the server
- **tcp_timeout** - Max wait time for server responses
- **logging.directory** - Where to save log files
- **platforms** - Which job sites to search

---

## TCP Protocol (How Go Talks to C++)

### Message Format
```
[4 bytes: Length] [JSON data]
Length: Big-endian unsigned int
JSON: UTF-8 encoded

Example:
00 00 00 XX | { "type": "PING", ... }
^          ^
|          JSON part
4-byte length
```

### Message Types

**Request from Go:**
```json
{
  "type": "JOB_MATCH_REQUEST",
  "request_id": "req-1234567890",
  "timestamp": "2024-01-15T10:30:00Z",
  "candidate": {
    "name": "John Doe",
    "resume_id": "john-doe-resume",
    "keywords": ["Go", "Python"]
  },
  "job": {
    "source": "linkedin",
    "source_id": "li-job-001",
    "company_name": "Google",
    "job_title": "Backend Engineer",
    "job_description": "...",
    "apply_url": "...",
    "posted_date": "2024-01-15T09:00:00Z"
  }
}
```

**Response from C++:**
```json
{
  "type": "JOB_MATCH_RESPONSE",
  "request_id": "req-1234567890",
  "status": "MATCHED",
  "confidence_score": 0.85,
  "matched_skills": ["Go", "Python"],
  "unmatched_required_skills": ["Rust"],
  "reason": "Candidate has 2/3 required skills",
  "processing_time_ms": 45,
  "timestamp": "2024-01-15T10:30:01Z"
}
```

---

## Common Debugging Questions

### "Why is my job matching not finding anything?"
**Check:**
1. Is the C++ server running? (`telnet localhost 10000`)
2. Are your keywords in the job description? (JobInfo.JobDescription)
3. Is the platform enabled in config? (platforms[].enabled = true)

### "Why are jobs being processed multiple times?"
**Check:**
1. Restart the program (processedJobIDs is cleared)
2. Check that job.SourceID is actually unique per job

### "Why is the log file not being created?"
**Check:**
1. Does logs/ directory exist?
2. Do you have write permissions?
3. Did any jobs actually match? (If no matches, no file)

### "Why is the connection dropping?"
**Check:**
1. Is C++ server still running?
2. Check network connectivity
3. Look at health check logs

---

## How to Add a New Job Platform

**Step 1: Create the fetch function in `platform/fetcher.go`**
```go
func fetchNewPlatformJobs(keywords []string) []orchestrator.JobInfo {
    fmt.Println("[NewPlatform] Fetching jobs...")
    
    jobs := []orchestrator.JobInfo{
        {
            Source: "newplatform",
            SourceID: "np-job-001",
            CompanyName: "Example Corp",
            JobTitle: "Engineer",
            JobDescription: "...",
            ApplyURL: "...",
            PostedDate: time.Now().Format(time.RFC3339),
        },
    }
    
    return jobs
}
```

**Step 2: Add to FetchJobs dispatcher**
```go
func FetchJobs(platformName string, keywords []string) []orchestrator.JobInfo {
    switch platformName {
    case "linkedin":
        return fetchLinkedInJobs(keywords)
    case "naukri":
        return fetchNaukriJobs(keywords)
    case "newplatform":  // ← ADD THIS
        return fetchNewPlatformJobs(keywords)
    default:
        return []orchestrator.JobInfo{}
    }
}
```

**Step 3: Enable in config**
```json
"platforms": [
  {"name": "linkedin", "enabled": true},
  {"name": "naukri", "enabled": true},
  {"name": "newplatform", "enabled": true}
]
```

That's it! Now jobs will be fetched from the new platform.

---

## Tips for Learning

1. **Run the program with `go run cmd/jobsearch/main.go`** and watch the output
2. **Add print statements** to understand what's happening (use `fmt.Println()`)
3. **Check the log files** in logs/ directory to see what matched
4. **Read error messages carefully** - Go errors are usually very helpful
5. **Use the GO_PATTERNS_GUIDE.md** to understand the language features used
6. **Google any unfamiliar function** - Go documentation is excellent

---

## Files You'll Likely Need to Edit

- **config/orchestrator.json** - Change settings
- **go/pkg/platform/fetcher.go** - Add new job sources
- **go/pkg/orchestrator/orchestrator.go** - Change job matching logic
- **go/pkg/logging/logger.go** - Change log format

Everything else rarely needs changes unless you're redesigning the system.

Good luck! 🎯
