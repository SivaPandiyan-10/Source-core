package orchestrator

import (
	"context"
	"fmt"
	"sync"
	"time"

	"jobsearch/pkg/client"
	"jobsearch/pkg/logging"
	"jobsearch/pkg/platform"
)

// ===== MESSAGE TYPES =====
// These structs match the C++ server protocol

// JobMatchRequest - What we send to the C++ server
// Asks: "Does this job match my candidate's skills?"
type JobMatchRequest struct {
	Type      string        `json:"type"`       // "JOB_MATCH_REQUEST"
	RequestID string        `json:"request_id"` // Unique ID for this request
	Timestamp string        `json:"timestamp"`  // When we sent it
	Candidate CandidateInfo `json:"candidate"`  // Who we're matching
	Job       JobInfo       `json:"job"`        // The job to match against
}

// JobMatchResponse - What the C++ server sends back
// Tells us: "Here's how well the job matches"
type JobMatchResponse struct {
	Type                    string   `json:"type"`                      // "JOB_MATCH_RESPONSE"
	RequestID               string   `json:"request_id"`                // Same ID as the request
	Status                  string   `json:"status"`                    // "MATCHED" or "REJECTED"
	ConfidenceScore         float64  `json:"confidence_score"`          // 0.0 to 1.0
	MatchedSkills           []string `json:"matched_skills"`            // Which skills matched
	UnmatchedRequiredSkills []string `json:"unmatched_required_skills"` // Which skills didn't match
	Reason                  string   `json:"reason"`                    // Why it matched/didn't
	ProcessingTimeMs        int64    `json:"processing_time_ms"`        // How long it took
	Timestamp               string   `json:"timestamp"`                 // When C++ processed it
}

// CandidateInfo - Information about the person we're finding jobs for
type CandidateInfo struct {
	Name     string   `json:"name"`      // Candidate's name
	ResumeID string   `json:"resume_id"` // ID to find their resume
	Keywords []string `json:"keywords"`  // Their skills (Go, Python, etc.)
}

// JobInfo - Information about a job posting
type JobInfo struct {
	Source         string `json:"source"`          // Where it came from (LinkedIn, Naukri)
	SourceID       string `json:"source_id"`       // Job ID from that platform
	CompanyName    string `json:"company_name"`    // Company name
	JobTitle       string `json:"job_title"`       // Job position
	JobDescription string `json:"job_description"` // Job details
	ApplyURL       string `json:"apply_url"`       // Link to apply
	PostedDate     string `json:"posted_date"`     // When it was posted
}

// ===== CONFIGURATION =====

// Config - Settings for the orchestrator
type Config struct {
	ServerAddress       string           // Where C++ server is (e.g., localhost:10000)
	CandidateName       string           // Who we're finding jobs for
	ResumeID            string           // Where to find their resume
	ResumeKeywords      []string         // Their skills
	FetchInterval       time.Duration    // How often to fetch new jobs (e.g., 1 hour)
	HealthCheckInterval time.Duration    // How often to ping the server (e.g., 5 minutes)
	TCPTimeout          time.Duration    // How long to wait for TCP responses
	LogDir              string           // Where to save match logs
	Platforms           []PlatformConfig // Which job sites to search
}

// PlatformConfig - Which job platform to use
type PlatformConfig struct {
	Name    string // "linkedin", "naukri", etc.
	Enabled bool   // Should we search this platform?
}

// ===== ORCHESTRATOR MAIN CLASS =====

// Orchestrator - Main coordinator that manages the entire job search
// This repeatedly:
// 1. Fetches jobs from job platforms
// 2. Sends them to C++ server for matching
// 3. Logs matches
// 4. Keeps connection to C++ server alive
type Orchestrator struct {
	// Connection to C++ server
	tcpClient *client.TCPClient

	// Logging matches to files
	logger *logging.Logger

	// Configuration
	config *Config

	// Context and cancellation (for graceful shutdown)
	ctx    context.Context
	cancel context.CancelFunc

	// Goroutine synchronization
	wg sync.WaitGroup

	// Remember which jobs we've already processed
	// Maps: jobID -> true (if we've seen it)
	processedJobIDs sync.Map

	// Periodic timers
	scheduleTicker  *time.Ticker // Triggers job fetching
	healthCheckTick *time.Ticker // Triggers server health checks
}

// ===== CONSTRUCTOR =====

// NewOrchestrator - Creates a new orchestrator
// Parameters:
//
//	config - Configuration for how to run
//
// Returns: A new orchestrator, or error if setup fails
func NewOrchestrator(config *Config) (*Orchestrator, error) {
	// Create the logger (will make log directory if needed)
	logger, err := logging.NewLogger(config.LogDir)
	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	// Create a context we can cancel later (for shutdown)
	ctx, cancel := context.WithCancel(context.Background())

	return &Orchestrator{
		tcpClient:       client.NewTCPClient(config.ServerAddress, config.TCPTimeout),
		logger:          logger,
		config:          config,
		ctx:             ctx,
		cancel:          cancel,
		scheduleTicker:  time.NewTicker(config.FetchInterval),
		healthCheckTick: time.NewTicker(config.HealthCheckInterval),
	}, nil
}

// ===== MAIN OPERATIONS =====

// Start - Begins the orchestration process
// This is the main entry point - runs until Stop() is called
// Returns: Error if startup fails
func (o *Orchestrator) Start() error {
	// Print startup banner
	fmt.Println("========================================")
	fmt.Println("JobSearchEngine - Go Job Orchestrator")
	fmt.Println("========================================")
	fmt.Printf("Server: %s\n", o.config.ServerAddress)
	fmt.Printf("Candidate: %s (Resume ID: %s)\n", o.config.CandidateName, o.config.ResumeID)
	fmt.Printf("Fetch Interval: %v\n", o.config.FetchInterval)
	fmt.Printf("Health Check Interval: %v\n", o.config.HealthCheckInterval)
	fmt.Println("========================================\n")

	// Connect to C++ server
	if err := o.tcpClient.ConnectWithRetry(o.ctx); err != nil {
		return fmt.Errorf("failed to connect to server: %w", err)
	}

	// Start background workers (these run concurrently)
	o.wg.Add(3)
	go o.scheduleJobFetching() // Fetches jobs on a schedule
	go o.healthCheckWorker()   // Checks if connection is alive
	go o.handleShutdown()      // Waits for shutdown signal

	fmt.Println("[Orchestrator] Started successfully")
	fmt.Println("[Orchestrator] Press Ctrl+C to shutdown")

	// Wait for all goroutines to finish (they stop when ctx.Done() happens)
	<-o.ctx.Done()

	// Cleanup resources
	o.scheduleTicker.Stop()
	o.healthCheckTick.Stop()
	o.wg.Wait()
	o.tcpClient.Close()

	fmt.Println("[Orchestrator] Shutdown complete")
	return nil
}

// Stop - Gracefully stops the orchestrator
// Calling this will cause Start() to return
func (o *Orchestrator) Stop() {
	fmt.Println("[Orchestrator] Stopping...")
	o.cancel()
}

// ===== JOB FETCHING & PROCESSING =====

// scheduleJobFetching - Runs in a goroutine, periodically fetches jobs
// Fetches immediately on startup, then every FetchInterval
func (o *Orchestrator) scheduleJobFetching() {
	defer o.wg.Done()

	// Fetch immediately
	o.fetchAndProcessJobs()

	// Then fetch on a timer
	for {
		select {
		case <-o.ctx.Done():
			// We're shutting down
			return
		case <-o.scheduleTicker.C:
			// Timer fired, fetch more jobs
			o.fetchAndProcessJobs()
		}
	}
}

// fetchAndProcessJobs - Main work function
// Fetches jobs from all platforms, then sends each to C++ for matching
func (o *Orchestrator) fetchAndProcessJobs() {
	fmt.Println("[Orchestrator] Fetching jobs...")

	// Step 1: Get all available jobs from enabled platforms
	jobs := o.fetchJobsFromPlatforms()
	fmt.Printf("[Orchestrator] Fetched %d jobs\n", len(jobs))

	// Step 2: Process each job
	processedCount := 0
	matchedCount := 0

	for _, job := range jobs {
		// Skip if we already processed this exact job
		jobKey := job.SourceID
		if _, exists := o.processedJobIDs.Load(jobKey); exists {
			continue
		}

		// Remember that we've processed this job
		// (so we don't check it again next time)
		o.processedJobIDs.Store(jobKey, true)

		// Send to C++ server for matching
		if matched, err := o.submitJobForMatching(job); err != nil {
			fmt.Printf("[Orchestrator] Error processing job %s: %v\n", jobKey, err)
		} else if matched {
			matchedCount++
		}

		processedCount++
	}

	fmt.Printf("[Orchestrator] Processed %d jobs, %d matches\n", processedCount, matchedCount)
}

// fetchJobsFromPlatforms - Fetches jobs from all enabled job platforms
// Returns: List of all jobs found
func (o *Orchestrator) fetchJobsFromPlatforms() []JobInfo {
	var allJobs []JobInfo

	// Loop through each configured platform
	for _, platformCfg := range o.config.Platforms {
		// Skip disabled platforms
		if !platformCfg.Enabled {
			continue
		}

		// Fetch jobs from this platform
		jobs := platform.FetchJobs(platformCfg.Name, o.config.ResumeKeywords)
		allJobs = append(allJobs, jobs...)
	}

	return allJobs
}

// submitJobForMatching - Sends a job to the C++ server
// The C++ server will analyze if it matches the candidate
// Returns: true if job matched, false otherwise
func (o *Orchestrator) submitJobForMatching(job JobInfo) (bool, error) {
	// Make sure we're still connected
	if !o.tcpClient.IsConnected() {
		if err := o.tcpClient.ConnectWithRetry(o.ctx); err != nil {
			return false, fmt.Errorf("not connected to server: %w", err)
		}
	}

	// Step 1: Build the request to send to C++
	req := JobMatchRequest{
		Type:      "JOB_MATCH_REQUEST",
		RequestID: fmt.Sprintf("req-%d", time.Now().UnixNano()),
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		Candidate: CandidateInfo{
			Name:     o.config.CandidateName,
			ResumeID: o.config.ResumeID,
			Keywords: o.config.ResumeKeywords,
		},
		Job: job,
	}

	// Step 2: Send the request over TCP
	if err := o.tcpClient.SendMessage(req); err != nil {
		return false, fmt.Errorf("failed to send request: %w", err)
	}

	// Step 3: Receive the response from C++
	var response JobMatchResponse
	if err := o.tcpClient.ReceiveMessage(&response); err != nil {
		return false, fmt.Errorf("failed to receive response: %w", err)
	}

	// Step 4: If it matched, log it
	if response.Status == "MATCHED" {
		logEntry := logging.LogEntry{
			Timestamp:       time.Now(),
			CandidateName:   o.config.CandidateName,
			CompanyName:     job.CompanyName,
			JobTitle:        job.JobTitle,
			ApplyLink:       job.ApplyURL,
			JobPlatform:     job.Source,
			ConfidenceScore: response.ConfidenceScore,
			MatchedSkills:   response.MatchedSkills,
		}

		if err := o.logger.LogMatch(logEntry); err != nil {
			fmt.Printf("[Orchestrator] Warning: Failed to log match: %v\n", err)
		}

		fmt.Printf("[Orchestrator] MATCHED: %s at %s (Score: %.2f%%)\n",
			job.JobTitle, job.CompanyName, response.ConfidenceScore*100)

		return true, nil
	}

	// No match
	fmt.Printf("[Orchestrator] REJECTED: %s at %s (Score: %.2f%%)\n",
		job.JobTitle, job.CompanyName, response.ConfidenceScore*100)

	return false, nil
}

// ===== HEALTH CHECKING =====

// healthCheckWorker - Runs in a goroutine, monitors server connection
// On a timer, pings the server to make sure it's still responding
func (o *Orchestrator) healthCheckWorker() {
	defer o.wg.Done()

	for {
		select {
		case <-o.ctx.Done():
			// We're shutting down
			return
		case <-o.healthCheckTick.C:
			// Time to check health
			if !o.tcpClient.IsConnected() {
				fmt.Println("[HealthCheck] Connection lost, attempting to reconnect...")
				if err := o.tcpClient.ConnectWithRetry(o.ctx); err != nil {
					fmt.Printf("[HealthCheck] Reconnection failed: %v\n", err)
				} else {
					fmt.Println("[HealthCheck] Reconnected successfully")
				}
			} else {
				// Try to ping the server
				if err := o.tcpClient.Ping(); err != nil {
					fmt.Printf("[HealthCheck] Ping failed: %v, reconnecting...\n", err)
					if err := o.tcpClient.ConnectWithRetry(o.ctx); err != nil {
						fmt.Printf("[HealthCheck] Reconnection failed: %v\n", err)
					}
				}
			}
		}
	}
}

// ===== SHUTDOWN HANDLING =====

// handleShutdown - Runs in a goroutine, just waits for shutdown
// When ctx.Done() happens, this goroutine finishes
func (o *Orchestrator) handleShutdown() {
	defer o.wg.Done()
	<-o.ctx.Done()
}
