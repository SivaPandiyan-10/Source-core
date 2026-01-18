package platform

import (
	"fmt"
	"time"

	"jobsearch/pkg/orchestrator"
)

// ===== PLATFORM DISPATCHER =====

// FetchJobs - Gets jobs from the specified job platform
// This is a dispatcher function that routes to the right platform
// Parameters:
//
//	platformName - Which platform to fetch from ("linkedin", "naukri", etc.)
//	keywords - Search keywords/skills (e.g., ["Go", "Docker", "Kubernetes"])
//
// Returns: List of job postings
func FetchJobs(platformName string, keywords []string) []orchestrator.JobInfo {
	// Route to the correct platform
	switch platformName {
	case "linkedin":
		return fetchLinkedInJobs(keywords)
	case "naukri":
		return fetchNaukriJobs(keywords)
	default:
		fmt.Printf("[Platform] Unknown platform: %s\n", platformName)
		return []orchestrator.JobInfo{}
	}
}

// ===== LINKEDIN JOB FETCHER =====

// fetchLinkedInJobs - Simulates fetching jobs from LinkedIn
// In a real system, this would call LinkedIn's API or use a web scraper
// For this demo, we return sample job data that represents what LinkedIn would return
// Parameters:
//
//	keywords - What to search for (not used in demo, but would filter results in production)
//
// Returns: List of jobs found on LinkedIn
func fetchLinkedInJobs(keywords []string) []orchestrator.JobInfo {
	fmt.Println("[LinkedIn] Fetching jobs...")

	// Demo: These would come from LinkedIn's API in production
	// In real code, you would filter these by keywords parameter
	jobs := []orchestrator.JobInfo{
		{
			Source:         "linkedin",                           // Where this job came from
			SourceID:       "li-job-001",                         // Unique ID on LinkedIn
			CompanyName:    "Google",                             // Company posting the job
			JobTitle:       "Senior Software Engineer - Backend", // Job position title
			JobDescription: "We are looking for a Senior Software Engineer with expertise in C++, System Design, and Distributed Systems. Experience with AWS is a plus.",
			ApplyURL:       "https://linkedin.com/jobs/view/senior-backend-engineer-google", // Link to apply
			PostedDate:     time.Now().Add(-24 * time.Hour).Format(time.RFC3339),            // When posted
		},
		{
			Source:         "linkedin",
			SourceID:       "li-job-002",
			CompanyName:    "Meta",
			JobTitle:       "Software Engineer - Infrastructure",
			JobDescription: "Looking for talented engineers proficient in C++, Python, and DevOps. Must have strong understanding of TCP/IP networking.",
			ApplyURL:       "https://linkedin.com/jobs/view/infrastructure-engineer-meta",
			PostedDate:     time.Now().Add(-12 * time.Hour).Format(time.RFC3339),
		},
	}

	fmt.Printf("[LinkedIn] Found %d jobs\n", len(jobs))
	return jobs
}

// ===== NAUKRI JOB FETCHER =====

// fetchNaukriJobs - Simulates fetching jobs from Naukri (Indian job site)
// In a real system, this would call Naukri's API or scraper
// For this demo, we return sample job data that represents what Naukri would return
// Parameters:
//
//	keywords - What to search for (not used in demo, but would filter results in production)
//
// Returns: List of jobs found on Naukri
func fetchNaukriJobs(keywords []string) []orchestrator.JobInfo {
	fmt.Println("[Naukri] Fetching jobs...")

	// Demo: These would come from Naukri's API in production
	// In real code, you would filter these by keywords parameter
	jobs := []orchestrator.JobInfo{
		{
			Source:         "naukri",                    // Where this job came from
			SourceID:       "nk-job-001",                // Unique ID on Naukri
			CompanyName:    "Microsoft India",           // Company posting the job
			JobTitle:       "Cloud Solutions Architect", // Job position title
			JobDescription: "Seeking Cloud Solutions Architect with expertise in Azure, C#, and System Architecture. Experience with Docker and Kubernetes preferred.",
			ApplyURL:       "https://www.naukri.com/job/cloud-solutions-architect", // Link to apply
			PostedDate:     time.Now().Format(time.RFC3339),                        // When posted
		},
		{
			Source:         "naukri",
			SourceID:       "nk-job-002",
			CompanyName:    "TCS",
			JobTitle:       "Senior DevOps Engineer",
			JobDescription: "TCS is hiring Senior DevOps Engineers with strong background in Linux, CI/CD, Kubernetes, and cloud platforms.",
			ApplyURL:       "https://www.naukri.com/job/senior-devops-engineer",
			PostedDate:     time.Now().Add(-48 * time.Hour).Format(time.RFC3339),
		},
	}

	fmt.Printf("[Naukri] Found %d jobs\n", len(jobs))
	return jobs
}
