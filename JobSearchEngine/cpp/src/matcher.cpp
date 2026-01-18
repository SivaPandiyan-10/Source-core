#include "matcher.h"
#include <algorithm>
#include <cctype>
#include <sstream>

namespace jse {
namespace matching {

JobMatcher::JobMatcher() : match_threshold_(0.70) {}

std::vector<MatchResult> JobMatcher::match_jobs(
    const Resume& resume,
    const std::vector<JobListing>& jobs) {
    
    std::vector<MatchResult> results;
    
    for (const auto& job : jobs) {
        if (should_filter_out(job)) {
            continue;
        }
        
        auto result = match_job(resume, job);
        if (result.passes_threshold(config_.min_confidence_threshold)) {
            results.push_back(result);
        }
    }
    
    // Sort by confidence score (descending)
    std::sort(results.begin(), results.end(),
              [](const MatchResult& a, const MatchResult& b) {
                  return a.confidence_score > b.confidence_score;
              });
    
    return results;
}

MatchResult JobMatcher::match_job(const Resume& resume, const JobListing& job) {
    MatchResult result;
    result.job_id = job.id;
    
    // Calculate individual match scores
    result.skill_match_score = calculate_skill_match(resume, job);
    result.experience_match_score = calculate_experience_match(resume, job);
    result.role_match_score = calculate_role_match(resume, job);
    result.location_match_score = calculate_location_match(resume, job);
    
    // Calculate weighted confidence score
    result.confidence_score = calculate_confidence(
        result.skill_match_score,
        result.experience_match_score,
        result.role_match_score,
        result.location_match_score
    );
    
    // Find matched skills for explanation
    for (const auto& resume_skill : resume.skills) {
        for (const auto& job_skill : job.required_skills) {
            if (string_contains(normalize_string(job_skill), normalize_string(resume_skill))) {
                result.matched_skills.push_back(resume_skill);
                break;
            }
        }
    }
    
    // Generate explanation
    if (result.confidence_score >= 0.80) {
        result.explanation = "Excellent match with strong skills and experience alignment";
    } else if (result.confidence_score >= 0.65) {
        result.explanation = "Good match with relevant skills and experience";
    } else if (result.confidence_score >= 0.50) {
        result.explanation = "Moderate match with some relevant skills";
    } else {
        result.explanation = "Weak match";
    }
    
    return result;
}

void JobMatcher::set_config(const MatchingConfig& config) {
    config_ = config;
}

const MatchingConfig& JobMatcher::get_config() const {
    return config_;
}

double JobMatcher::calculate_skill_match(
    const Resume& resume,
    const JobListing& job) {
    
    if (job.required_skills.empty() || resume.skills.empty()) {
        return 0.5;  // Neutral score if data is incomplete
    }
    
    int matched_count = 0;
    for (const auto& resume_skill : resume.skills) {
        for (const auto& job_skill : job.required_skills) {
            if (string_contains(normalize_string(job_skill), normalize_string(resume_skill)) ||
                string_contains(normalize_string(resume_skill), normalize_string(job_skill))) {
                matched_count++;
                break;
            }
        }
    }
    
    // Score = (matched skills) / (required skills)
    double score = static_cast<double>(matched_count) / job.required_skills.size();
    return std::min(1.0, score);
}

double JobMatcher::calculate_experience_match(
    const Resume& resume,
    const JobListing& job) {
    
    int resume_exp = resume.experience_years;
    int job_exp = job.experience_required_years;
    
    if (job_exp == 0) {
        return 0.8;  // No requirement specified, neutral/positive score
    }
    
    int diff = std::abs(resume_exp - job_exp);
    
    if (diff <= config_.experience_tolerance_years) {
        return 1.0;
    } else if (diff <= config_.experience_tolerance_years * 2) {
        return 0.8;
    } else if (resume_exp >= job_exp) {
        return 0.6;  // Overqualified but acceptable
    } else {
        return std::max(0.0, 0.4 - (diff * 0.1));  // Underqualified
    }
}

double JobMatcher::calculate_role_match(
    const Resume& resume,
    const JobListing& job) {
    
    std::string normalized_job_title = normalize_string(job.title);
    
    int matched_roles = 0;
    for (const auto& resume_role : resume.roles) {
        if (string_contains(normalized_job_title, normalize_string(resume_role))) {
            matched_roles++;
        }
    }
    
    if (!resume.roles.empty()) {
        double score = static_cast<double>(matched_roles) / resume.roles.size();
        return std::min(1.0, score * 1.2);  // Boost score slightly
    }
    
    return 0.5;
}

double JobMatcher::calculate_location_match(
    const Resume& resume,
    const JobListing& job) {
    
    // Check if job is remote or matches preferred locations
    std::string normalized_location = normalize_string(job.location);
    
    if (string_contains(normalized_location, "remote") ||
        string_contains(normalized_location, "work from home") ||
        string_contains(normalized_location, "distributed")) {
        return 1.0;  // Remote is always a good match
    }
    
    // Check if location matches resume preferences
    for (const auto& pref_location : resume.locations) {
        if (string_contains(normalized_location, normalize_string(pref_location))) {
            return 1.0;
        }
    }
    
    // Location mismatch - return lower score
    if (resume.locations.empty()) {
        return 0.7;  // No location preference specified
    }
    
    return 0.3;  // Location preference not met
}

bool JobMatcher::should_filter_out(const JobListing& job) const {
    // Check excluded companies
    for (const auto& excluded_company : config_.excluded_companies) {
        if (string_contains(normalize_string(job.company), normalize_string(excluded_company))) {
            return true;
        }
    }
    
    // Check excluded keywords
    std::string normalized_desc = normalize_string(job.description);
    for (const auto& excluded_keyword : config_.excluded_keywords) {
        if (string_contains(normalized_desc, normalize_string(excluded_keyword))) {
            return true;
        }
    }
    
    return false;
}

double JobMatcher::calculate_confidence(
    double skill, double exp, double role, double location) const {
    
    return (skill * config_.skill_weight +
            exp * config_.experience_weight +
            role * config_.role_weight +
            location * config_.location_weight);
}

bool JobMatcher::string_contains(
    const std::string& haystack,
    const std::string& needle) {
    
    return haystack.find(needle) != std::string::npos;
}

std::string JobMatcher::normalize_string(const std::string& str) {
    std::string result = str;
    
    // Convert to lowercase
    std::transform(result.begin(), result.end(), result.begin(),
                   [](unsigned char c) { return std::tolower(c); });
    
    return result;
}

}  // namespace jobsearch
