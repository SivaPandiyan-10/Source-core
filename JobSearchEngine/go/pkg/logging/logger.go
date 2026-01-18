package logging

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// ===== DATA STRUCTURES =====

// LogEntry - Information about a single matched job
// This data gets written to the daily log file
type LogEntry struct {
	Timestamp       time.Time  // When the match was found
	CandidateName   string     // Who we're matching for
	CompanyName     string     // Which company posted the job
	JobTitle        string     // The position title
	ApplyLink       string     // URL to apply
	JobPlatform     string     // Where we found it (e.g., LinkedIn, Naukri)
	ConfidenceScore float64    // Match percentage (0.0 to 1.0)
	MatchedSkills   []string   // Which skills matched
}

// ===== LOGGER =====

// Logger - Handles writing job matches to daily log files
// Each day gets its own log file (YYYY-MM-DD.log format)
// Uses Mutex to make sure multiple goroutines can log at the same time safely
type Logger struct {
	logDir     string        // Directory where logs are stored
	currentDay string        // Which day's file is currently open (YYYY-MM-DD)
	file       *os.File      // The currently open log file
	mu         sync.Mutex    // Prevents multiple goroutines from writing simultaneously
}

// ===== CONSTRUCTOR =====

// NewLogger - Creates a new logger
// Parameters:
//   logDir - Directory where daily log files will be stored
// Returns: A new Logger, or error if directory can't be created
func NewLogger(logDir string) (*Logger, error) {
	// Create the log directory if it doesn't exist
	if err := os.MkdirAll(logDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create log directory: %w", err)
	}

	return &Logger{
		logDir: logDir,
	}, nil
}

// ===== LOGGING OPERATIONS =====

// LogMatch - Writes a job match to the daily log file
// Automatically creates a new file if the date changes
// Parameters:
//   entry - The job match information to log
// Returns: Error if writing fails
func (l *Logger) LogMatch(entry LogEntry) error {
	// Lock the mutex to prevent other goroutines from writing at the same time
	// This ensures our log file doesn't get corrupted
	l.mu.Lock()
	defer l.mu.Unlock()

	// Format the date (YYYY-MM-DD)
	currentDay := entry.Timestamp.Format("2006-01-02")
	
	// If the date changed, close the old file and open a new one
	if currentDay != l.currentDay {
		// Close the old file if it's open
		if l.file != nil {
			l.file.Close()
		}

		// Build the filename: logs/2024-01-15.log
		filename := filepath.Join(l.logDir, currentDay+".log")
		
		// Open the file for writing (create if doesn't exist, append if it does)
		file, err := os.OpenFile(filename, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
		if err != nil {
			return fmt.Errorf("failed to open log file: %w", err)
		}

		l.file = file
		l.currentDay = currentDay

		// Write a header if the file is brand new (empty)
		stat, _ := os.Stat(filename)
		if stat.Size() == 0 {
			fmt.Fprintf(l.file, "=== JobSearchEngine - Daily Match Log ===\n")
			fmt.Fprintf(l.file, "Date: %s\n", currentDay)
			fmt.Fprintf(l.file, "=============================================\n\n")
		}
	}

	// Format the timestamp
	timestamp := entry.Timestamp.Format("2006-01-02 15:04:05")
	
	// Convert the list of skills to a string (e.g., "Go, Python, Docker")
	skillsStr := strings.Join(entry.MatchedSkills, ", ")

	// Build the log line with all the information
	logLine := fmt.Sprintf(
		"[%s] Candidate: %s | Company: %s | Job: %s | Platform: %s | Score: %.2f%% | Skills: [%s] | Apply: %s\n",
		timestamp,
		entry.CandidateName,
		entry.CompanyName,
		entry.JobTitle,
		entry.JobPlatform,
		entry.ConfidenceScore*100,  // Convert 0.85 to 85%
		skillsStr,
		entry.ApplyLink,
	)

	// Write the line to the file
	if _, err := l.file.WriteString(logLine); err != nil {
		return fmt.Errorf("failed to write log entry: %w", err)
	}

	// Make sure it's written to disk (not just buffered)
	return l.file.Sync()
}

// Close - Closes the logger and finishes all pending writes
// Always call this when done to cleanup
// Returns: Error if closing fails
func (l *Logger) Close() error {
	l.mu.Lock()
	defer l.mu.Unlock()

	if l.file != nil {
		return l.file.Close()
	}
	return nil
}

// ===== STATISTICS =====

// GetMatchCount - Counts how many matches we logged today
// Returns: The number of log entries for today (or 0 if no file yet)
func (l *Logger) GetMatchCount() (int, error) {
	l.mu.Lock()
	defer l.mu.Unlock()

	// Get today's date
	currentDay := time.Now().Format("2006-01-02")
	filename := filepath.Join(l.logDir, currentDay+".log")

	// Read the entire log file
	content, err := os.ReadFile(filename)
	if err != nil {
		// If the file doesn't exist, we have 0 matches
		if os.IsNotExist(err) {
			return 0, nil
		}
		return 0, err
	}

	// Count how many lines contain job matches
	// (header lines start with "===", dates start with "Date:", or are empty)
	logContent := string(content)
	matches := 0
	
	for _, line := range strings.Split(logContent, "\n") {
		// Skip empty lines and header lines
		if len(line) == 0 || strings.HasPrefix(line, "=") || strings.HasPrefix(line, "Date:") {
			continue
		}
		
		// Any other line is a log entry, so count it
		if len(line) > 0 {
			matches++
		}
	}

	return matches, nil
}

	// Count lines that are log entries (not headers)
	lines := strings.Split(string(content), "\n")
	count := 0
	for _, line := range lines {
		if strings.HasPrefix(line, "[") && strings.Contains(line, "] Candidate:") {
			count++
		}
	}

	return count, nil
}
