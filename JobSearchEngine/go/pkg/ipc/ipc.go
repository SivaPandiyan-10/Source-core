package ipc

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
)

// ===== DATA STRUCTURES =====
// These structs define the shape of data we send and receive

// ParseResumeRequest - What we send to C++ to parse a resume
type ParseResumeRequest struct {
	Command       string `json:"command"`        // What action to perform (e.g., "parse_resume")
	Content       string `json:"content"`        // The resume text content
	CandidateName string `json:"candidate_name"` // Name of the person
}

// Resume - The result after parsing a resume
type Resume struct {
	Candidate       string   `json:"candidate"`        // Person's name
	Skills          []string `json:"skills"`           // List of skills found
	ExperienceYears int      `json:"experience_years"` // Years of experience
	Roles           []string `json:"roles"`            // Job titles/roles
	Locations       []string `json:"locations"`        // Locations worked
	Industry        string   `json:"industry"`         // Industry type
}

// IPCResponse - Response we get from C++ engine
type IPCResponse struct {
	Status  string        `json:"status"`            // "success" or "error"
	Resume  *Resume       `json:"resume,omitempty"`  // Resume data (if applicable)
	Message string        `json:"message,omitempty"` // Error or info message
	Matches []MatchResult `json:"matches,omitempty"` // Matched jobs (if applicable)
}

// MatchResult - A single job match result
type MatchResult struct {
	JobID           string   `json:"job_id"`           // Job's unique ID
	ConfidenceScore float64  `json:"confidence_score"` // Score from 0.0 to 1.0
	MatchedSkills   []string `json:"matched_skills"`   // Skills that matched
	Explanation     string   `json:"explanation"`      // Why it matched/didn't
}

// ===== IPC CLIENT =====
// This manages communication with the C++ engine

// IPCClient - Handles talking to the C++ engine process
type IPCClient struct {
	enginePath string         // Where the C++ executable is located
	cmd        *exec.Cmd      // The running C++ process
	stdin      io.WriteCloser // Where we send data TO C++
	stdout     io.ReadCloser  // Where we receive data FROM C++
}

// ===== CONSTRUCTOR & SETUP =====

// NewIPCClient - Creates a new IPC client
// Parameters:
//
//	enginePath - Where the C++ executable is located (e.g., "./bin/engine")
//
// Returns: A new IPCClient ready to use
func NewIPCClient(enginePath string) *IPCClient {
	return &IPCClient{
		enginePath: enginePath,
	}
}

// Start - Launches the C++ engine process
// This starts the actual C++ executable and creates communication pipes
func (c *IPCClient) Start() error {
	// If no path provided, try to find the executable
	if c.enginePath == "" {
		c.enginePath = findCPPEngine()
	}

	// Create a new command to run the C++ engine
	c.cmd = exec.Command(c.enginePath)

	// Create a pipe for sending data TO C++
	stdin, err := c.cmd.StdinPipe()
	if err != nil {
		return fmt.Errorf("failed to create input pipe: %w", err)
	}

	// Create a pipe for receiving data FROM C++
	stdout, err := c.cmd.StdoutPipe()
	if err != nil {
		return fmt.Errorf("failed to create output pipe: %w", err)
	}

	c.stdin = stdin
	c.stdout = stdout

	// Actually start the C++ process
	if err := c.cmd.Start(); err != nil {
		return fmt.Errorf("failed to start C++ engine: %w", err)
	}

	fmt.Println("[IPCClient] C++ engine started successfully")
	return nil
}

// ===== PUBLIC METHODS =====

// ParseResume - Ask C++ to parse resume content
// Parameters:
//
//	content - The resume text (as a string)
//	candidateName - The person's name
//
// Returns: Parsed resume data or an error
func (c *IPCClient) ParseResume(content, candidateName string) (*Resume, error) {
	// Start the engine if not already running
	if c.cmd == nil {
		if err := c.Start(); err != nil {
			return nil, err
		}
	}

	// Build the request to send
	request := ParseResumeRequest{
		Command:       "parse_resume",
		Content:       content,
		CandidateName: candidateName,
	}

	// Send the request to C++
	data, _ := json.Marshal(request)
	if _, err := c.stdin.Write(append(data, '\n')); err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}

	// Read the response from C++
	var response IPCResponse
	decoder := json.NewDecoder(c.stdout)
	if err := decoder.Decode(&response); err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	// Check if C++ reported an error
	if response.Status != "success" {
		return nil, fmt.Errorf("C++ error: %s", response.Message)
	}

	// Return the parsed resume
	return response.Resume, nil
}

// MatchJobs - Ask C++ to match jobs against a resume
// Parameters:
//
//	resume - The candidate's resume data
//	jobs - List of jobs to match
//	config - Configuration settings
//
// Returns: List of matching jobs or an error
func (c *IPCClient) MatchJobs(resume *Resume, jobs interface{}, config interface{}) ([]MatchResult, error) {
	// Build the request
	matchRequest := map[string]interface{}{
		"command": "match_jobs",
		"resume":  resume,
		"jobs":    jobs,
		"config":  config,
	}

	// Send to C++
	data, _ := json.Marshal(matchRequest)
	if _, err := c.stdin.Write(append(data, '\n')); err != nil {
		return nil, fmt.Errorf("failed to send match request: %w", err)
	}

	// Read response
	var response IPCResponse
	decoder := json.NewDecoder(c.stdout)
	if err := decoder.Decode(&response); err != nil {
		return nil, fmt.Errorf("failed to read match response: %w", err)
	}

	// Check for errors
	if response.Status != "success" {
		return nil, fmt.Errorf("C++ match error: %s", response.Message)
	}

	// Return the matches
	return response.Matches, nil
}

// Close - Cleanly shutdown the C++ engine
// Always call this when done to avoid zombie processes
func (c *IPCClient) Close() error {
	// Close the input pipe
	if c.stdin != nil {
		c.stdin.Close()
	}

	// Kill the C++ process
	if c.cmd != nil && c.cmd.Process != nil {
		c.cmd.Process.Kill()
	}

	fmt.Println("[IPCClient] C++ engine stopped")
	return nil
}

// ===== HELPER FUNCTIONS =====

// findCPPEngine - Try to locate the C++ executable in common locations
func findCPPEngine() string {
	// List of places to look for the executable
	possibleLocations := []string{
		"./bin/jobsearch_engine",
		"./jobsearch_engine",
		"/usr/local/bin/jobsearch_engine",
		"/usr/bin/jobsearch_engine",
	}

	// Check each location
	for _, location := range possibleLocations {
		if _, err := os.Stat(location); err == nil {
			// File exists!
			fmt.Printf("[IPCClient] Found engine at: %s\n", location)
			return location
		}
	}

	// If not found in any common location, assume it's in the system PATH
	fmt.Println("[IPCClient] Engine not found in common locations, assuming it's in PATH")
	return "jobsearch_engine"
}
