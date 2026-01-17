#include "../include/ipc_handler.h"
#include <iostream>
#include <sstream>
#include <regex>

// Using nlohmann/json for production-grade JSON handling
// Include path: #include <nlohmann/json.hpp>
// For this implementation, we'll use a simplified JSON builder

namespace jobsearch {

IPCHandler::IPCHandler() = default;

IPCHandler::~IPCHandler() = default;

std::string IPCHandler::read_request() {
    std::string line;
    if (std::getline(std::cin, line)) {
        return line;
    }
    return "";
}

void IPCHandler::send_response(const std::string& response) {
    std::cout << response << std::endl;
    std::cout.flush();
}

bool IPCHandler::parse_resume_request(
    const std::string& json_str,
    std::string& out_content,
    std::string& out_candidate_name) {
    
    // Simple JSON parsing (in production, use nlohmann/json)
    // This is a basic implementation for illustration
    
    // Look for "content" field
    std::regex content_regex(R"("content"\s*:\s*"([^"]*)")");
    std::smatch content_match;
    if (std::regex_search(json_str, content_match, content_regex)) {
        out_content = content_match[1].str();
    }
    
    // Look for "candidate_name" field
    std::regex name_regex(R"("candidate_name"\s*:\s*"([^"]*)")");
    std::smatch name_match;
    if (std::regex_search(json_str, name_match, name_regex)) {
        out_candidate_name = name_match[1].str();
    }
    
    return !out_content.empty() && !out_candidate_name.empty();
}

std::string IPCHandler::create_resume_response(const Resume& resume) {
    std::ostringstream ss;
    
    ss << "{"
       << "\"status\":\"success\","
       << "\"resume\":{"
       << "\"candidate\":\"" << resume.candidate_name << "\","
       << "\"skills\":[";
    
    for (size_t i = 0; i < resume.skills.size(); ++i) {
        if (i > 0) ss << ",";
        ss << "\"" << resume.skills[i] << "\"";
    }
    
    ss << "],"
       << "\"experience_years\":" << resume.experience_years << ","
       << "\"roles\":[";
    
    for (size_t i = 0; i < resume.roles.size(); ++i) {
        if (i > 0) ss << ",";
        ss << "\"" << resume.roles[i] << "\"";
    }
    
    ss << "],"
       << "\"locations\":[";
    
    for (size_t i = 0; i < resume.locations.size(); ++i) {
        if (i > 0) ss << ",";
        ss << "\"" << resume.locations[i] << "\"";
    }
    
    ss << "]"
       << "}";  // End resume object
    
    ss << "}";  // End root object
    
    return ss.str();
}

bool IPCHandler::parse_match_request(
    const std::string& json_str,
    Resume& out_resume,
    std::vector<JobListing>& out_jobs,
    MatchingConfig& out_config) {
    
    // In production, use a proper JSON library
    // This is a simplified implementation
    
    // Parse resume skills
    std::regex skills_regex(R"("skills"\s*:\s*\[(.*?)\])");
    std::smatch skills_match;
    if (std::regex_search(json_str, skills_match, skills_regex)) {
        std::string skills_str = skills_match[1].str();
        std::regex skill_item(R"("([^"]+)")");
        
        auto skills_begin = std::sregex_iterator(skills_str.begin(), skills_str.end(), skill_item);
        auto skills_end = std::sregex_iterator();
        
        for (auto it = skills_begin; it != skills_end; ++it) {
            out_resume.skills.push_back((*it)[1].str());
        }
    }
    
    // Parse experience years
    std::regex exp_regex(R"("experience_years"\s*:\s*(\d+))");
    std::smatch exp_match;
    if (std::regex_search(json_str, exp_match, exp_regex)) {
        out_resume.experience_years = std::stoi(exp_match[1].str());
    }
    
    // Parse config threshold
    std::regex threshold_regex(R"("min_confidence_threshold"\s*:\s*([\d.]+))");
    std::smatch threshold_match;
    if (std::regex_search(json_str, threshold_match, threshold_regex)) {
        out_config.min_confidence_threshold = std::stod(threshold_match[1].str());
    }
    
    return !out_resume.skills.empty();
}

std::string IPCHandler::create_match_response(const std::vector<MatchResult>& results) {
    std::ostringstream ss;
    
    ss << "{"
       << "\"status\":\"success\","
       << "\"matches\":[";
    
    for (size_t i = 0; i < results.size(); ++i) {
        const auto& result = results[i];
        
        if (i > 0) ss << ",";
        
        ss << "{"
           << "\"job_id\":\"" << result.job_id << "\","
           << "\"confidence_score\":" << result.confidence_score << ","
           << "\"score_breakdown\":{"
           << "\"skill_match\":" << result.skill_match_score << ","
           << "\"experience_match\":" << result.experience_match_score << ","
           << "\"role_match\":" << result.role_match_score << ","
           << "\"location_match\":" << result.location_match_score
           << "},"
           << "\"matched_skills\":[";
        
        for (size_t j = 0; j < result.matched_skills.size(); ++j) {
            if (j > 0) ss << ",";
            ss << "\"" << result.matched_skills[j] << "\"";
        }
        
        ss << "],"
           << "\"explanation\":\"" << result.explanation << "\""
           << "}";
    }
    
    ss << "]"
       << "}";
    
    return ss.str();
}

std::string IPCHandler::create_error_response(const std::string& message) {
    std::ostringstream ss;
    ss << "{\"status\":\"error\",\"message\":\"" << message << "\"}";
    return ss.str();
}

}  // namespace jobsearch
