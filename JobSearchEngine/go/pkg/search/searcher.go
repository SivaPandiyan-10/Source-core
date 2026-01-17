package search

import (
	"fmt"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"

	"jobsearch/pkg/config"
	"jobsearch/pkg/ipc"
)

// JobListing represents a job posting from a portal
type JobListing struct {
	ID                      string
	Title                   string
	Company                 string
	Location                string
	Description             string
	ApplyLink               string
	Source                  string
	PostedDate              string
	ExperienceRequiredYears int
	RequiredSkills          []string
}

// SearchEngine manages job search across multiple portals
type SearchEngine struct {
	config     *config.JobPortalsConfig
	client     *http.Client
	limiter    *RateLimiter
	mu         sync.Mutex
}

// RateLimiter implements request rate limiting
type RateLimiter struct {
	linkedInRequests map[time.Time]int
	naukriRequests   map[time.Time]int
	mu               sync.Mutex
}

// NewSearchEngine creates a new search engine
func NewSearchEngine(cfg *config.JobPortalsConfig) *SearchEngine {
	return &SearchEngine{
		config: cfg,
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
		limiter: &RateLimiter{
			linkedInRequests: make(map[time.Time]int),
			naukriRequests:   make(map[time.Time]int),
		},
	}
}

// SearchForJobs searches across configured job portals
func (se *SearchEngine) SearchForJobs(resume *ipc.Resume, keywords []string) ([]JobListing, error) {
	var results []JobListing
	var wg sync.WaitGroup
	var mu sync.Mutex
	errChan := make(chan error, 2)

	// Search LinkedIn if enabled
	if se.config.LinkedIn.Enabled {
		wg.Add(1)
		go func() {
			defer wg.Done()
			jobs, err := se.searchLinkedIn(keywords)
			if err != nil {
				errChan <- fmt.Errorf("LinkedIn search failed: %w", err)
				return
			}
			mu.Lock()
			results = append(results, jobs...)
			mu.Unlock()
		}()
	}

	// Search Naukri if enabled
	if se.config.Naukri.Enabled {
		wg.Add(1)
		go func() {
			defer wg.Done()
			jobs, err := se.searchNaukri(keywords)
			if err != nil {
				errChan <- fmt.Errorf("Naukri search failed: %w", err)
				return
			}
			mu.Lock()
			results = append(results, jobs...)
			mu.Unlock()
		}()
	}

	wg.Wait()
	close(errChan)

	// Return first error if any
	for err := range errChan {
		return results, err
	}

	return results, nil
}

// searchLinkedIn searches for jobs on LinkedIn
func (se *SearchEngine) searchLinkedIn(keywords []string) ([]JobListing, error) {
	// Rate limit check
	if !se.limiter.canMakeLinkedInRequest(se.config.LinkedIn.RateLimitPerHour) {
		return nil, fmt.Errorf("LinkedIn rate limit exceeded")
	}

	se.limiter.recordLinkedInRequest()

	var jobs []JobListing

	// In production, use LinkedIn API (requires authentication)
	// For now, simulate search with basic HTTP GET
	// This is a simplified implementation - real implementation would use proper API

	searchURL := fmt.Sprintf("https://www.linkedin.com/jobs/search/?keywords=%s",
		url.QueryEscape(strings.Join(keywords, " ")))

	req, _ := http.NewRequest("GET", searchURL, nil)
	req.Header.Set("User-Agent", getRandomUserAgent())

	// In production: implement proper LinkedIn API integration
	// For now, return empty results as placeholder
	return jobs, nil
}

// searchNaukri searches for jobs on Naukri
func (se *SearchEngine) searchNaukri(keywords []string) ([]JobListing, error) {
	// Rate limit check
	if !se.limiter.canMakeNaukriRequest(se.config.Naukri.RateLimitPerHour) {
		return nil, fmt.Errorf("Naukri rate limit exceeded")
	}

	se.limiter.recordNaukriRequest()

	var jobs []JobListing

	// Build search URL with keywords
	searchURL := fmt.Sprintf("%s/jobs?keywords=%s",
		se.config.Naukri.BaseURL,
		url.QueryEscape(strings.Join(keywords, " ")))

	req, _ := http.NewRequest("GET", searchURL, nil)
	req.Header.Set("User-Agent", getRandomUserAgent())

	// In production: implement proper Naukri scraping with politeness delays
	// For now, return empty results as placeholder
	return jobs, nil
}

// canMakeLinkedInRequest checks if we can make another LinkedIn request
func (rl *RateLimiter) canMakeLinkedInRequest(ratePerHour int) bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	oneHourAgo := now.Add(-1 * time.Hour)

	// Count requests in the last hour
	count := 0
	for t := range rl.linkedInRequests {
		if t.After(oneHourAgo) {
			count += rl.linkedInRequests[t]
		}
	}

	return count < ratePerHour
}

// recordLinkedInRequest records a LinkedIn request
func (rl *RateLimiter) recordLinkedInRequest() {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	rl.linkedInRequests[now]++

	// Clean up old entries
	oneHourAgo := now.Add(-1 * time.Hour)
	for t := range rl.linkedInRequests {
		if t.Before(oneHourAgo) {
			delete(rl.linkedInRequests, t)
		}
	}
}

// canMakeNaukriRequest checks if we can make another Naukri request
func (rl *RateLimiter) canMakeNaukriRequest(ratePerHour int) bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	oneHourAgo := now.Add(-1 * time.Hour)

	// Count requests in the last hour
	count := 0
	for t := range rl.naukriRequests {
		if t.After(oneHourAgo) {
			count += rl.naukriRequests[t]
		}
	}

	return count < ratePerHour
}

// recordNaukriRequest records a Naukri request
func (rl *RateLimiter) recordNaukriRequest() {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	rl.naukriRequests[now]++

	// Clean up old entries
	oneHourAgo := now.Add(-1 * time.Hour)
	for t := range rl.naukriRequests {
		if t.Before(oneHourAgo) {
			delete(rl.naukriRequests, t)
		}
	}
}

// getRandomUserAgent returns a random user agent
func getRandomUserAgent() string {
	userAgents := []string{
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
	}

	return userAgents[int(time.Now().UnixNano())%len(userAgents)]
}
