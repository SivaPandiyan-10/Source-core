package config

import (
	"fmt"
	"os"

	"gopkg.in/yaml.v3"
)

// Configuration represents the entire application configuration
type Configuration struct {
	JobSearch  JobSearchConfig  `yaml:"job_search"`
	JobPortals JobPortalsConfig `yaml:"job_portals"`
	Filters    FilterConfig     `yaml:"filters"`
	Paths      PathsConfig      `yaml:"paths"`
	System     SystemConfig     `yaml:"system"`
}

// JobSearchConfig contains job search settings
type JobSearchConfig struct {
	Enabled                    bool    `yaml:"enabled"`
	IntervalHours              int     `yaml:"interval_hours"`
	MinConfidenceThreshold     float64 `yaml:"min_confidence_threshold"`
	SkillWeight                float64 `yaml:"skill_weight"`
	ExperienceWeight           float64 `yaml:"experience_weight"`
	RoleWeight                 float64 `yaml:"role_weight"`
	LocationWeight             float64 `yaml:"location_weight"`
	ExperienceToleranceYears   int     `yaml:"experience_tolerance_years"`
}

// JobPortalsConfig contains job portal configurations
type JobPortalsConfig struct {
	LinkedIn LinkedInConfig `yaml:"linkedin"`
	Naukri   NaukriConfig   `yaml:"naukri"`
}

// LinkedInConfig contains LinkedIn-specific settings
type LinkedInConfig struct {
	Enabled                bool `yaml:"enabled"`
	SearchKeywordsResume   bool `yaml:"search_keywords_from_resume"`
	RateLimitPerHour       int  `yaml:"rate_limit_requests_per_hour"`
	RequestTimeoutSeconds  int  `yaml:"request_timeout_seconds"`
}

// NaukriConfig contains Naukri-specific settings
type NaukriConfig struct {
	Enabled                bool `yaml:"enabled"`
	SearchKeywordsResume   bool `yaml:"search_keywords_from_resume"`
	RateLimitPerHour       int  `yaml:"rate_limit_requests_per_hour"`
	RequestTimeoutSeconds  int  `yaml:"request_timeout_seconds"`
	BaseURL                string `yaml:"base_url"`
}

// FilterConfig contains filtering settings
type FilterConfig struct {
	ExperienceToleranceYears int      `yaml:"experience_tolerance_years"`
	PreferredLocations       []string `yaml:"preferred_locations"`
	ExcludedCompanies        []string `yaml:"excluded_companies"`
	ExcludedKeywords         []string `yaml:"excluded_keywords"`
}

// PathsConfig contains file path configurations
type PathsConfig struct {
	Resumes       string `yaml:"resumes"`
	Logs          string `yaml:"logs"`
	Cache         string `yaml:"cache"`
	CPPEnginePath string `yaml:"cpp_engine_path"`
}

// SystemConfig contains system-level configurations
type SystemConfig struct {
	PreventSleepOnWindows bool   `yaml:"prevent_sleep_on_windows"`
	LogLevel              string `yaml:"log_level"`
	MaxRetries            int    `yaml:"max_retries"`
	RetryBackoffSeconds   int    `yaml:"retry_backoff_seconds"`
	CPPEnginePath         string
}

// LoadConfig loads configuration from YAML file
func LoadConfig(path string) (*Configuration, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}

	cfg := &Configuration{}
	if err := yaml.Unmarshal(data, cfg); err != nil {
		return nil, fmt.Errorf("failed to parse config file: %w", err)
	}

	// Set defaults if not specified
	if cfg.JobSearch.IntervalHours == 0 {
		cfg.JobSearch.IntervalHours = 6
	}
	if cfg.JobSearch.MinConfidenceThreshold == 0 {
		cfg.JobSearch.MinConfidenceThreshold = 0.65
	}
	if cfg.JobSearch.SkillWeight == 0 {
		cfg.JobSearch.SkillWeight = 0.35
	}
	if cfg.JobSearch.ExperienceWeight == 0 {
		cfg.JobSearch.ExperienceWeight = 0.30
	}
	if cfg.JobSearch.RoleWeight == 0 {
		cfg.JobSearch.RoleWeight = 0.25
	}
	if cfg.JobSearch.LocationWeight == 0 {
		cfg.JobSearch.LocationWeight = 0.10
	}

	if cfg.Paths.Resumes == "" {
		cfg.Paths.Resumes = "./resumes"
	}
	if cfg.Paths.Logs == "" {
		cfg.Paths.Logs = "./logs"
	}
	if cfg.Paths.Cache == "" {
		cfg.Paths.Cache = "./cache"
	}

	if cfg.System.LogLevel == "" {
		cfg.System.LogLevel = "INFO"
	}
	if cfg.System.MaxRetries == 0 {
		cfg.System.MaxRetries = 3
	}
	if cfg.System.RetryBackoffSeconds == 0 {
		cfg.System.RetryBackoffSeconds = 30
	}

	// Set C++ engine path (will be set by main)
	cfg.System.CPPEnginePath = cfg.Paths.CPPEnginePath

	return cfg, nil
}

// Validate checks if configuration is valid
func (c *Configuration) Validate() error {
	if c.Paths.Resumes == "" {
		return fmt.Errorf("resumes path is required")
	}
	if c.Paths.Logs == "" {
		return fmt.Errorf("logs path is required")
	}
	if !c.JobSearch.Enabled {
		return fmt.Errorf("job_search must be enabled")
	}
	if c.JobSearch.IntervalHours < 1 {
		return fmt.Errorf("job_search interval must be at least 1 hour")
	}

	// Validate weights sum to approximately 1.0
	weights := c.JobSearch.SkillWeight +
		c.JobSearch.ExperienceWeight +
		c.JobSearch.RoleWeight +
		c.JobSearch.LocationWeight
	if weights < 0.95 || weights > 1.05 {
		return fmt.Errorf("matching weights should sum to 1.0, got %.2f", weights)
	}

	return nil
}
