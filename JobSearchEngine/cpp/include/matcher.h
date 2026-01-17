#ifndef JOBSEARCH_MATCHER_H
#define JOBSEARCH_MATCHER_H

#include "models.h"
#include <vector>
#include <memory>

namespace jobsearch {

class JobMatcher {
public:
    explicit JobMatcher(const MatchingConfig& config = MatchingConfig());
    ~JobMatcher();
    
    /// Match multiple jobs against a resume
    /// Returns only jobs with confidence score >= config.min_confidence_threshold
    std::vector<MatchResult> match_jobs(
        const Resume& resume,
        const std::vector<JobListing>& jobs
    );
    
    /// Match a single job against a resume
    MatchResult match_job(const Resume& resume, const JobListing& job);
    
    /// Update matching configuration
    void set_config(const MatchingConfig& config);
    
    /// Get current configuration
    const MatchingConfig& get_config() const;

private:
    MatchingConfig config_;
    
    /// Calculate skill match score [0, 1]
    double calculate_skill_match(
        const Resume& resume,
        const JobListing& job
    );
    
    /// Calculate experience match score [0, 1]
    double calculate_experience_match(
        const Resume& resume,
        const JobListing& job
    );
    
    /// Calculate role match score [0, 1]
    double calculate_role_match(
        const Resume& resume,
        const JobListing& job
    );
    
    /// Calculate location match score [0, 1]
    double calculate_location_match(
        const Resume& resume,
        const JobListing& job
    );
    
    /// Check if job should be filtered out (company blacklist, keywords, etc.)
    bool should_filter_out(const JobListing& job) const;
    
    /// Calculate weighted confidence score
    double calculate_confidence(
        double skill, double exp, double role, double location
    ) const;
    
    /// Case-insensitive string comparison
    static bool string_contains(
        const std::string& haystack,
        const std::string& needle
    );
    
    /// Normalize string for comparison
    static std::string normalize_string(const std::string& str);
};

}  // namespace jobsearch

#endif  // JOBSEARCH_MATCHER_H
