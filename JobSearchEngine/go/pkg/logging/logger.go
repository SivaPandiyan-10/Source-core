package logging

import (
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// JobMatch represents a matched job entry for logging
type JobMatch struct {
	Company          string
	Role             string
	ApplyLink        string
	Source           string
	ConfidenceScore  float64
	Timestamp        time.Time
	ExperienceMatch  float64
	SkillMatch       float64
	RoleMatch        float64
	LocationMatch    float64
}

// Logger interface for logging operations
type Logger interface {
	Info(msg string)
	Infof(format string, args ...interface{})
	Warn(msg string)
	Warnf(format string, args ...interface{})
	Error(msg string)
	Errorf(format string, args ...interface{})
	Debugf(format string, args ...interface{})
	LogJobMatch(match *JobMatch) error
	Close() error
}

// DailyLogger creates daily log files and rotates them
type DailyLogger struct {
	logDir        string
	currentDate   string
	file          *os.File
	mu            sync.Mutex
	deduplicator  *Deduplicator
}

// Deduplicator prevents duplicate job entries
type Deduplicator struct {
	seen map[string]bool
	mu   sync.Mutex
}

// NewDailyLogger creates a new daily logger
func NewDailyLogger(logDir string) *DailyLogger {
	// Create log directory if it doesn't exist
	if err := os.MkdirAll(logDir, 0755); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to create log directory: %v\n", err)
	}

	return &DailyLogger{
		logDir:       logDir,
		deduplicator: NewDeduplicator(),
	}
}

// NewDeduplicator creates a new deduplicator
func NewDeduplicator() *Deduplicator {
	return &Deduplicator{
		seen: make(map[string]bool),
	}
}

// isDuplicate checks if a job has already been logged
func (d *Deduplicator) isDuplicate(company, role, link string) bool {
	d.mu.Lock()
	defer d.mu.Unlock()

	key := fmt.Sprintf("%s|%s|%s", company, role, link)
	if d.seen[key] {
		return true
	}

	d.seen[key] = true
	return false
}

// ensureFileOpen ensures the log file is open for the current date
func (l *DailyLogger) ensureFileOpen() error {
	l.mu.Lock()
	defer l.mu.Unlock()

	today := time.Now().Format("2006-01-02")

	// If file is already open for today, return
	if l.file != nil && l.currentDate == today {
		return nil
	}

	// Close previous file if open
	if l.file != nil {
		l.file.Close()
	}

	// Open or create today's log file
	logPath := filepath.Join(l.logDir, today+".log")
	file, err := os.OpenFile(logPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return fmt.Errorf("failed to open log file: %w", err)
	}

	l.file = file
	l.currentDate = today

	return nil
}

// Info logs an info message
func (l *DailyLogger) Info(msg string) {
	l.Infof("%s", msg)
}

// Infof logs a formatted info message
func (l *DailyLogger) Infof(format string, args ...interface{}) {
	l.ensureFileOpen()
	timestamp := time.Now().Format("2006-01-02 15:04:05")
	msg := fmt.Sprintf("[%s] [INFO] %s\n", timestamp, fmt.Sprintf(format, args...))

	l.mu.Lock()
	if l.file != nil {
		l.file.WriteString(msg)
	}
	l.mu.Unlock()

	// Also print to stdout
	fmt.Print(msg)
}

// Warn logs a warning message
func (l *DailyLogger) Warn(msg string) {
	l.Warnf("%s", msg)
}

// Warnf logs a formatted warning message
func (l *DailyLogger) Warnf(format string, args ...interface{}) {
	l.ensureFileOpen()
	timestamp := time.Now().Format("2006-01-02 15:04:05")
	msg := fmt.Sprintf("[%s] [WARN] %s\n", timestamp, fmt.Sprintf(format, args...))

	l.mu.Lock()
	if l.file != nil {
		l.file.WriteString(msg)
	}
	l.mu.Unlock()

	// Also print to stderr
	fmt.Fprint(os.Stderr, msg)
}

// Error logs an error message
func (l *DailyLogger) Error(msg string) {
	l.Errorf("%s", msg)
}

// Errorf logs a formatted error message
func (l *DailyLogger) Errorf(format string, args ...interface{}) {
	l.ensureFileOpen()
	timestamp := time.Now().Format("2006-01-02 15:04:05")
	msg := fmt.Sprintf("[%s] [ERROR] %s\n", timestamp, fmt.Sprintf(format, args...))

	l.mu.Lock()
	if l.file != nil {
		l.file.WriteString(msg)
	}
	l.mu.Unlock()

	// Also print to stderr
	fmt.Fprint(os.Stderr, msg)
}

// Debugf logs a formatted debug message
func (l *DailyLogger) Debugf(format string, args ...interface{}) {
	l.ensureFileOpen()
	timestamp := time.Now().Format("2006-01-02 15:04:05")
	msg := fmt.Sprintf("[%s] [DEBUG] %s\n", timestamp, fmt.Sprintf(format, args...))

	l.mu.Lock()
	if l.file != nil {
		l.file.WriteString(msg)
	}
	l.mu.Unlock()

	// Also print to stdout
	fmt.Print(msg)
}

// LogJobMatch logs a matched job with deduplication
func (l *DailyLogger) LogJobMatch(match *JobMatch) error {
	// Check for duplicates
	if l.deduplicator.isDuplicate(match.Company, match.Role, match.ApplyLink) {
		l.Infof("Skipping duplicate job: %s - %s", match.Company, match.Role)
		return nil
	}

	l.ensureFileOpen()

	timestamp := match.Timestamp.Format("2006-01-02 15:04:05")
	scoreStr := fmt.Sprintf("%.2f", match.ConfidenceScore)

	// Format: [timestamp] Company | Role | Link | Source | Score | Breakdown
	entry := fmt.Sprintf(
		"[%s] %s | %s | %s | %s | %s | Skill:%.2f Exp:%.2f Role:%.2f Loc:%.2f\n",
		timestamp,
		match.Company,
		match.Role,
		match.ApplyLink,
		match.Source,
		scoreStr,
		match.SkillMatch,
		match.ExperienceMatch,
		match.RoleMatch,
		match.LocationMatch,
	)

	l.mu.Lock()
	if l.file != nil {
		_, err := l.file.WriteString(entry)
		l.mu.Unlock()
		if err != nil {
			return fmt.Errorf("failed to write log entry: %w", err)
		}
	} else {
		l.mu.Unlock()
		return fmt.Errorf("log file is not open")
	}

	// Also print to stdout
	fmt.Print(entry)

	return nil
}

// Close closes the logger and flushes pending writes
func (l *DailyLogger) Close() error {
	l.mu.Lock()
	defer l.mu.Unlock()

	if l.file != nil {
		l.file.Sync()
		return l.file.Close()
	}

	return nil
}
