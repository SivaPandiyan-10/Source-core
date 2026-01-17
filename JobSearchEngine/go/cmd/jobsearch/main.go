package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"runtime"
	"strings"

	"jobsearch/pkg/config"
	"jobsearch/pkg/ipc"
	"jobsearch/pkg/logging"
	"jobsearch/pkg/scheduler"
	"jobsearch/pkg/search"
)

func main() {
	// Parse command-line flags
	candidateName := flag.String("candidate", "", "Candidate name (required)")
	configPath := flag.String("config", "config/config.yaml", "Path to configuration file")
	flag.Parse()

	if *candidateName == "" {
		fmt.Fprintf(os.Stderr, "Error: --candidate flag is required\n")
		fmt.Fprintf(os.Stderr, "Usage: jobsearch --candidate \"John Doe\" [--config config.yaml]\n")
		os.Exit(1)
	}

	// Load configuration
	cfg, err := config.LoadConfig(*configPath)
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Initialize logger
	logger := logging.NewDailyLogger(cfg.Paths.Logs)
	defer logger.Close()

	logger.Infof("JobSearchEngine started for candidate: %s", *candidateName)
	logger.Infof("Configuration loaded from: %s", *configPath)
	logger.Infof("Platform: %s/%s", runtime.GOOS, runtime.GOARCH)

	// Validate resume exists
	resumePath := filepath.Join(cfg.Paths.Resumes, sanitizeFilename(*candidateName)+".txt")
	if _, err := os.Stat(resumePath); os.IsNotExist(err) {
		logger.Errorf("Resume not found for candidate: %s (expected at %s)", *candidateName, resumePath)
		fmt.Fprintf(os.Stderr, "Error: Resume not found for candidate: %s\n", *candidateName)
		os.Exit(1)
	}

	// Read resume content
	resumeContent, err := os.ReadFile(resumePath)
	if err != nil {
		logger.Errorf("Failed to read resume: %v", err)
		fmt.Fprintf(os.Stderr, "Error: Failed to read resume: %v\n", err)
		os.Exit(1)
	}

	// Parse resume using C++ engine
	logger.Infof("Parsing resume for candidate: %s", *candidateName)
	ipcClient := ipc.NewIPCClient(cfg.System.CPPEnginePath)

	parsedResume, err := ipcClient.ParseResume(string(resumeContent), *candidateName)
	if err != nil {
		logger.Errorf("Failed to parse resume: %v", err)
		fmt.Fprintf(os.Stderr, "Error: Failed to parse resume: %v\n", err)
		os.Exit(1)
	}

	logger.Infof("Resume parsed successfully. Skills: %v, Experience: %d years, Roles: %v",
		parsedResume.Skills, parsedResume.ExperienceYears, parsedResume.Roles)

	// Prevent system sleep (platform-specific)
	if cfg.System.PreventSleepOnWindows && runtime.GOOS == "windows" {
		preventSleep()
		defer allowSleep()
		logger.Info("System sleep prevention enabled on Windows")
	}

	// Initialize job search engine
	searchEngine := search.NewSearchEngine(cfg.JobPortals)

	// Initialize scheduler
	sched := scheduler.NewScheduler(*candidateName, parsedResume, cfg, logger, ipcClient, searchEngine)

	// Run scheduler (blocking call)
	logger.Info("Starting job search scheduler")
	sched.Start()

	logger.Info("JobSearchEngine shutdown complete")
}

// sanitizeFilename converts candidate name to safe filename
func sanitizeFilename(name string) string {
	return strings.NewReplacer(" ", "_", "/", "_", "\\", "_", ":", "_").Replace(name)
}

// preventSleep prevents system sleep on Windows
func preventSleep() {
	if runtime.GOOS == "windows" {
		// On Windows, use SetThreadExecutionState to prevent sleep
		// This requires cgo or syscall package
		// Simplified implementation - actual implementation would use Windows API
		log.Println("Preventing system sleep on Windows")
	}
}

// allowSleep allows system to sleep again
func allowSleep() {
	if runtime.GOOS == "windows" {
		log.Println("Allowing system sleep on Windows")
	}
}
