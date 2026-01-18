package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"jobsearch/pkg/orchestrator"
)

// ===== CONFIGURATION STRUCTURE =====

// Config - What we read from the JSON configuration file
// This defines all the settings needed to run the job search
type Config struct {
	Server struct {
		Address string `json:"address"` // Server IP (e.g., "localhost")
		Port    int    `json:"port"`    // Server port (e.g., 10000)
	} `json:"server"`
	Candidate struct {
		Name     string   `json:"name"`      // Your name
		ResumeID string   `json:"resume_id"` // Where to find your resume
		Keywords []string `json:"keywords"`  // Your skills
	} `json:"candidate"`
	Schedule struct {
		FetchInterval       string `json:"fetch_interval"`        // How often to search for jobs (e.g., "1h")
		HealthCheckInterval string `json:"health_check_interval"` // How often to check server (e.g., "5m")
		TCPTimeout          string `json:"tcp_timeout"`           // How long to wait for TCP responses (e.g., "30s")
	} `json:"schedule"`
	Logging struct {
		Directory string `json:"directory"` // Where to save log files
	} `json:"logging"`
	Platforms []struct {
		Name    string `json:"name"`    // Platform name (e.g., "linkedin")
		Enabled bool   `json:"enabled"` // Should we search this platform?
	} `json:"platforms"`
}

// ===== MAIN ENTRY POINT =====

// main - The starting point of the program
// Reads configuration, sets up the orchestrator, and starts the job search
func main() {
	// Parse command-line arguments
	configFile := flag.String("config", "config/orchestrator.json", "Configuration file path")
	flag.Parse()

	// Step 1: Load configuration from JSON file
	config, err := loadConfig(*configFile)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to load configuration: %v\n", err)
		os.Exit(1)
	}

	// Step 2: Parse time durations from config
	// These are strings like "1h", "5m", "30s" that need to be converted to Go duration objects
	fetchInterval, err := time.ParseDuration(config.Schedule.FetchInterval)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Invalid fetch interval: %v\n", err)
		os.Exit(1)
	}

	healthCheckInterval, err := time.ParseDuration(config.Schedule.HealthCheckInterval)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Invalid health check interval: %v\n", err)
		os.Exit(1)
	}

	tcpTimeout, err := time.ParseDuration(config.Schedule.TCPTimeout)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Invalid TCP timeout: %v\n", err)
		os.Exit(1)
	}

	// Step 3: Convert platform configs from JSON format to internal format
	var platforms []orchestrator.PlatformConfig
	for _, p := range config.Platforms {
		platforms = append(platforms, orchestrator.PlatformConfig{
			Name:    p.Name,
			Enabled: p.Enabled,
		})
	}

	// Step 4: Build the orchestrator configuration
	orchConfig := &orchestrator.Config{
		ServerAddress:       fmt.Sprintf("%s:%d", config.Server.Address, config.Server.Port),
		CandidateName:       config.Candidate.Name,
		ResumeID:            config.Candidate.ResumeID,
		ResumeKeywords:      config.Candidate.Keywords,
		FetchInterval:       fetchInterval,
		HealthCheckInterval: healthCheckInterval,
		TCPTimeout:          tcpTimeout,
		LogDir:              config.Logging.Directory,
		Platforms:           platforms,
	}

	// Step 5: Create the orchestrator
	orch, err := orchestrator.NewOrchestrator(orchConfig)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to create orchestrator: %v\n", err)
		os.Exit(1)
	}

	// Step 6: Handle Ctrl+C gracefully
	// When user presses Ctrl+C, we want to stop cleanly instead of crashing
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	// This goroutine waits for Ctrl+C and tells orchestrator to stop
	go func() {
		<-sigChan
		orch.Stop()
	}()

	// Step 7: Start the orchestrator
	// This runs the main job search loop
	if err := orch.Start(); err != nil {
		fmt.Fprintf(os.Stderr, "Orchestrator error: %v\n", err)
		os.Exit(1)
	}
}

// ===== HELPER FUNCTIONS =====

// loadConfig - Reads and parses the JSON configuration file
// Parameters:
//
//	filename - Path to the config file (e.g., "config/orchestrator.json")
//
// Returns: Parsed configuration, or error if file can't be read/parsed
func loadConfig(filename string) (*Config, error) {
	// Read the entire file
	data, err := os.ReadFile(filename)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}

	// Parse the JSON
	var config Config
	if err := json.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("failed to parse config: %w", err)
	}

	return &config, nil
}
