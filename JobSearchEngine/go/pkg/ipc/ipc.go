package ipc

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
)

// ParseResumeRequest is the request to parse a resume
type ParseResumeRequest struct {
	Command       string `json:"command"`
	Content       string `json:"content"`
	CandidateName string `json:"candidate_name"`
}

// Resume represents parsed resume data
type Resume struct {
	Candidate       string   `json:"candidate"`
	Skills          []string `json:"skills"`
	ExperienceYears int      `json:"experience_years"`
	Roles           []string `json:"roles"`
	Locations       []string `json:"locations"`
	Industry        string   `json:"industry"`
}

// IPCResponse is a generic response from C++ engine
type IPCResponse struct {
	Status  string          `json:"status"`
	Resume  *Resume         `json:"resume,omitempty"`
	Message string          `json:"message,omitempty"`
	Matches []MatchResult   `json:"matches,omitempty"`
}

// MatchResult represents a job match result
type MatchResult struct {
	JobID              string                 `json:"job_id"`
	ConfidenceScore    float64                `json:"confidence_score"`
	ScoreBreakdown     map[string]float64     `json:"score_breakdown"`
	MatchedSkills      []string               `json:"matched_skills"`
	Explanation        string                 `json:"explanation"`
}

// IPCClient handles communication with the C++ engine
type IPCClient struct {
	enginePath string
	cmd        *exec.Cmd
	stdin      io.WriteCloser
	stdout     io.ReadCloser
}

// NewIPCClient creates a new IPC client
func NewIPCClient(enginePath string) *IPCClient {
	return &IPCClient{
		enginePath: enginePath,
	}
}

// Start starts the C++ subprocess
func (c *IPCClient) Start() error {
	if c.enginePath == "" {
		// Try common locations
		c.enginePath = findCPPEngine()
	}

	c.cmd = exec.Command(c.enginePath)

	stdin, err := c.cmd.StdinPipe()
	if err != nil {
		return fmt.Errorf("failed to create stdin pipe: %w", err)
	}

	stdout, err := c.cmd.StdoutPipe()
	if err != nil {
		return fmt.Errorf("failed to create stdout pipe: %w", err)
	}

	c.stdin = stdin
	c.stdout = stdout

	if err := c.cmd.Start(); err != nil {
		return fmt.Errorf("failed to start C++ engine: %w", err)
	}

	return nil
}

// ParseResume sends a resume parsing request
func (c *IPCClient) ParseResume(content, candidateName string) (*Resume, error) {
	if c.cmd == nil {
		if err := c.Start(); err != nil {
			return nil, err
		}
	}

	request := ParseResumeRequest{
		Command:       "parse_resume",
		Content:       content,
		CandidateName: candidateName,
	}

	// Send request
	data, _ := json.Marshal(request)
	if _, err := c.stdin.Write(append(data, '\n')); err != nil {
		return nil, fmt.Errorf("failed to send parse_resume request: %w", err)
	}

	// Read response
	var response IPCResponse
	decoder := json.NewDecoder(c.stdout)
	if err := decoder.Decode(&response); err != nil {
		return nil, fmt.Errorf("failed to read parse_resume response: %w", err)
	}

	if response.Status != "success" {
		return nil, fmt.Errorf("parse_resume failed: %s", response.Message)
	}

	return response.Resume, nil
}

// MatchJobs sends a job matching request
func (c *IPCClient) MatchJobs(resume *Resume, jobs interface{}, config interface{}) ([]MatchResult, error) {
	matchRequest := map[string]interface{}{
		"command": "match_jobs",
		"resume":  resume,
		"jobs":    jobs,
		"config":  config,
	}

	// Send request
	data, _ := json.Marshal(matchRequest)
	if _, err := c.stdin.Write(append(data, '\n')); err != nil {
		return nil, fmt.Errorf("failed to send match_jobs request: %w", err)
	}

	// Read response
	var response IPCResponse
	decoder := json.NewDecoder(c.stdout)
	if err := decoder.Decode(&response); err != nil {
		return nil, fmt.Errorf("failed to read match_jobs response: %w", err)
	}

	if response.Status != "success" {
		return nil, fmt.Errorf("match_jobs failed: %s", response.Message)
	}

	return response.Matches, nil
}

// Close closes the IPC connection and subprocess
func (c *IPCClient) Close() error {
	if c.stdin != nil {
		c.stdin.Close()
	}
	if c.cmd != nil && c.cmd.Process != nil {
		c.cmd.Process.Kill()
	}
	return nil
}

// findCPPEngine tries to locate the C++ engine executable
func findCPPEngine() string {
	// Try common locations
	locations := []string{
		"./bin/jobsearch_engine",
		"./jobsearch_engine",
		"/usr/local/bin/jobsearch_engine",
		"/usr/bin/jobsearch_engine",
	}

	for _, loc := range locations {
		if _, err := os.Stat(loc); err == nil {
			return loc
		}
	}

	return "jobsearch_engine"  // Assume it's in PATH
}
