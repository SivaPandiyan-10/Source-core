package scheduler

import (
	"fmt"
	"math"
	"math/rand"
	"time"

	"jobsearch/pkg/config"
	"jobsearch/pkg/ipc"
	"jobsearch/pkg/logging"
	"jobsearch/pkg/search"
)

// Scheduler orchestrates job searches and matching
type Scheduler struct {
	candidateName string
	resume        *ipc.Resume
	config        *config.Configuration
	logger        logging.Logger
	ipcClient     *ipc.IPCClient
	searchEngine  *search.SearchEngine
	lastRunTime   time.Time
	retryCount    int
}

// NewScheduler creates a new scheduler
func NewScheduler(
	candidateName string,
	resume *ipc.Resume,
	cfg *config.Configuration,
	logger logging.Logger,
	ipcClient *ipc.IPCClient,
	searchEngine *search.SearchEngine,
) *Scheduler {
	return &Scheduler{
		candidateName: candidateName,
		resume:        resume,
		config:        cfg,
		logger:        logger,
		ipcClient:     ipcClient,
		searchEngine:  searchEngine,
	}
}

// Start begins the main scheduling loop (blocking)
func (s *Scheduler) Start() {
	// Run search immediately on startup
	s.runJobSearch()

	// Create ticker for periodic searches
	interval := time.Duration(s.config.JobSearch.IntervalHours) * time.Hour
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	s.logger.Infof("Scheduler started with interval: %d hours", s.config.JobSearch.IntervalHours)

	for {
		select {
		case <-ticker.C:
			s.runJobSearch()
		}
	}
}

// runJobSearch executes one complete job search cycle
func (s *Scheduler) runJobSearch() {
	s.logger.Infof("Starting job search for candidate: %s", s.candidateName)
	s.lastRunTime = time.Now()

	// Build search keywords from resume
	keywords := s.buildSearchKeywords()
	s.logger.Infof("Search keywords: %v", keywords)

	// Search job portals
	jobs, err := s.searchWithRetry(keywords)
	if err != nil {
		s.logger.Errorf("Job search failed after retries: %v", err)
		return
	}

	if len(jobs) == 0 {
		s.logger.Infof("No jobs found in current search")
		return
	}

	s.logger.Infof("Found %d jobs, matching against resume", len(jobs))

	// Convert search results to IPC format
	var ipcJobs []interface{}
	for _, job := range jobs {
		ipcJobs = append(ipcJobs, map[string]interface{}{
			"id":                        job.ID,
			"title":                     job.Title,
			"company":                   job.Company,
			"location":                  job.Location,
			"description":               job.Description,
			"apply_link":                job.ApplyLink,
			"source":                    job.Source,
			"posted_date":               job.PostedDate,
			"experience_required_years": job.ExperienceRequiredYears,
			"required_skills":           job.RequiredSkills,
		})
	}

	// Match jobs using C++ engine
	matches, err := s.ipcClient.MatchJobs(
		s.resume,
		ipcJobs,
		map[string]interface{}{
			"min_confidence_threshold":     s.config.JobSearch.MinConfidenceThreshold,
			"skill_weight":                 s.config.JobSearch.SkillWeight,
			"experience_weight":            s.config.JobSearch.ExperienceWeight,
			"role_weight":                  s.config.JobSearch.RoleWeight,
			"location_weight":              s.config.JobSearch.LocationWeight,
		},
	)
	if err != nil {
		s.logger.Errorf("Job matching failed: %v", err)
		return
	}

	s.logger.Infof("Matched %d jobs with confidence >= %.2f",
		len(matches), s.config.JobSearch.MinConfidenceThreshold)

	// Log matched jobs
	for i, match := range matches {
		// Find original job for full details
		var company, role, link, source string
		for _, job := range jobs {
			if job.ID == match.JobID {
				company = job.Company
				role = job.Title
				link = job.ApplyLink
				source = job.Source
				break
			}
		}

		jobMatch := &logging.JobMatch{
			Company:         company,
			Role:            role,
			ApplyLink:       link,
			Source:          source,
			ConfidenceScore: match.ConfidenceScore,
			Timestamp:       time.Now(),
			ExperienceMatch: match.ScoreBreakdown["experience_match"],
			SkillMatch:      match.ScoreBreakdown["skill_match"],
			RoleMatch:       match.ScoreBreakdown["role_match"],
			LocationMatch:   match.ScoreBreakdown["location_match"],
		}

		if err := s.logger.LogJobMatch(jobMatch); err != nil {
			s.logger.Errorf("Failed to log job match: %v", err)
		} else {
			s.logger.Debugf("Logged match %d/%d: %s - %s (%.2f)",
				i+1, len(matches), company, role, match.ConfidenceScore)
		}
	}

	s.retryCount = 0  // Reset retry count on success
	s.logger.Infof("Job search cycle completed")
}

// searchWithRetry performs job search with exponential backoff retries
func (s *Scheduler) searchWithRetry(keywords []string) ([]search.JobListing, error) {
	var lastErr error

	for attempt := 0; attempt <= s.config.System.MaxRetries; attempt++ {
		jobs, err := s.searchEngine.SearchForJobs(s.resume, keywords)
		if err == nil {
			return jobs, nil
		}

		lastErr = err
		s.logger.Warnf("Search attempt %d failed: %v", attempt+1, err)

		if attempt < s.config.System.MaxRetries {
			// Calculate backoff with jitter
			backoff := time.Duration(s.config.System.RetryBackoffSeconds) * time.Second
			jitter := time.Duration(rand.Intn(1000)) * time.Millisecond
			sleepTime := backoff + (time.Duration(attempt) * backoff) + jitter

			s.logger.Infof("Retrying in %v...", sleepTime)
			time.Sleep(sleepTime)
		}
	}

	return nil, fmt.Errorf("search failed after %d retries: %w", 
		s.config.System.MaxRetries+1, lastErr)
}

// buildSearchKeywords constructs search keywords from resume
func (s *Scheduler) buildSearchKeywords() []string {
	keywords := make(map[string]bool)

	// Add resume roles
	for _, role := range s.resume.Roles {
		keywords[role] = true
	}

	// Add resume skills (top N most common)
	skillCount := 0
	for _, skill := range s.resume.Skills {
		if skillCount < 10 {  // Limit to 10 skills
			keywords[skill] = true
			skillCount++
		}
	}

	// Add job level indicators
	if s.resume.ExperienceYears >= 10 {
		keywords["Senior"] = true
		keywords["Lead"] = true
	} else if s.resume.ExperienceYears >= 5 {
		keywords["Mid-level"] = true
	}

	// Convert map to slice
	var result []string
	for k := range keywords {
		result = append(result, k)
	}

	return result
}

// Stop gracefully stops the scheduler (future enhancement)
func (s *Scheduler) Stop() {
	s.logger.Info("Scheduler stopping...")
	s.ipcClient.Close()
	s.logger.Close()
}
