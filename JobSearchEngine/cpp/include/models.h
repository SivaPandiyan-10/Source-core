#ifndef JOBSEARCH_MODELS_H
#define JOBSEARCH_MODELS_H

#include <string>
#include <vector>
#include <map>
#include <memory>

namespace jobsearch {

/// Represents a parsed resume with extracted features
struct Resume {
    std::string candidate_name;
    std::vector<std::string> skills;
    int experience_years = 0;
    std::vector<std::string> roles;  // Job titles/roles
    std::vector<std::string> locations;
    std::string industry;
    std::map<std::string, int> skill_frequency;  // Skill occurrence count
    
    /// Return true if resume is valid (has required fields)
    bool is_valid() const {
        return !candidate_name.empty() && !skills.empty() && experience_years > 0;
    }
};

/// Represents a job listing from a portal
struct JobListing {
    std::string id;
    std::string title;
    std::string company;
    std::string location;
    std::string description;
    std::string apply_link;
    std::string source;  // "LinkedIn", "Naukri", etc.
    std::string posted_date;
    int experience_required_years = 0;
    std::vector<std::string> required_skills;
};

/// Represents matching scores and details
struct MatchResult {
    std::string job_id;
    double confidence_score = 0.0;
    
    // Score breakdown
    double skill_match_score = 0.0;
    double experience_match_score = 0.0;
    double role_match_score = 0.0;
    double location_match_score = 0.0;
    
    // Details
    std::vector<std::string> matched_skills;
    std::string explanation;
    
    /// Return true if match meets minimum threshold
    bool passes_threshold(double threshold) const {
        return confidence_score >= threshold;
    }
};

/// Configuration for matching algorithm
struct MatchingConfig {
    double min_confidence_threshold = 0.65;
    double skill_weight = 0.35;
    double experience_weight = 0.30;
    double role_weight = 0.25;
    double location_weight = 0.10;
    int experience_tolerance_years = 1;  // Allow +/- tolerance
    std::vector<std::string> excluded_companies;
    std::vector<std::string> excluded_keywords;
};

}  // namespace jobsearch

#endif  // JOBSEARCH_MODELS_H
