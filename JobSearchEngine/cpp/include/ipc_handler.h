#ifndef JOBSEARCH_IPC_HANDLER_H
#define JOBSEARCH_IPC_HANDLER_H

#include "models.h"
#include <string>
#include <vector>
#include <memory>

// Forward declare nlohmann json (rapidjson alternative for production)
namespace nlohmann {
    class json;
}

namespace jobsearch {

/// Handles JSON-based IPC communication with Go orchestrator
class IPCHandler {
public:
    IPCHandler();
    ~IPCHandler();
    
    /// Read and parse JSON request from stdin
    std::string read_request();
    
    /// Send JSON response to stdout
    void send_response(const std::string& response);
    
    /// Parse resume parsing request from JSON
    /// Returns: { "command": "parse_resume", "content": "...", "candidate_name": "..." }
    static bool parse_resume_request(
        const std::string& json_str,
        std::string& out_content,
        std::string& out_candidate_name
    );
    
    /// Create JSON response for parsed resume
    static std::string create_resume_response(const Resume& resume);
    
    /// Parse job matching request from JSON
    /// Returns: { "command": "match_jobs", "resume": {...}, "jobs": [...], "config": {...} }
    static bool parse_match_request(
        const std::string& json_str,
        Resume& out_resume,
        std::vector<JobListing>& out_jobs,
        MatchingConfig& out_config
    );
    
    /// Create JSON response for match results
    static std::string create_match_response(const std::vector<MatchResult>& results);
    
    /// Create JSON error response
    static std::string create_error_response(const std::string& message);

private:
    /// Helper to safely read from stdin
    std::string read_line();
};

}  // namespace jobsearch

#endif  // JOBSEARCH_IPC_HANDLER_H
