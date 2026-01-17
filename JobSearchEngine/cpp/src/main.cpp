#include "../include/resume_parser.h"
#include "../include/matcher.h"
#include "../include/ipc_handler.h"
#include <iostream>
#include <string>
#include <vector>

using namespace jobsearch;

int main(int argc, char* argv[]) {
    try {
        IPCHandler ipc;
        ResumeParser parser;
        JobMatcher matcher;
        
        // Main event loop: Read requests from Go orchestrator via stdin
        while (true) {
            std::string request = ipc.read_request();
            
            if (request.empty()) {
                break;  // EOF or error
            }
            
            // Determine command type
            if (request.find("parse_resume") != std::string::npos) {
                // Parse resume request
                std::string content, candidate_name;
                
                if (IPCHandler::parse_resume_request(request, content, candidate_name)) {
                    auto resume = parser.parse(content, candidate_name);
                    
                    if (resume && resume->is_valid()) {
                        std::string response = IPCHandler::create_resume_response(*resume);
                        ipc.send_response(response);
                    } else {
                        std::string error = IPCHandler::create_error_response(
                            "Failed to parse resume or invalid resume data");
                        ipc.send_response(error);
                    }
                } else {
                    std::string error = IPCHandler::create_error_response(
                        "Invalid parse_resume request format");
                    ipc.send_response(error);
                }
            } 
            else if (request.find("match_jobs") != std::string::npos) {
                // Match jobs request
                Resume resume;
                std::vector<JobListing> jobs;
                MatchingConfig config;
                
                if (IPCHandler::parse_match_request(request, resume, jobs, config)) {
                    matcher.set_config(config);
                    auto results = matcher.match_jobs(resume, jobs);
                    
                    std::string response = IPCHandler::create_match_response(results);
                    ipc.send_response(response);
                } else {
                    std::string error = IPCHandler::create_error_response(
                        "Invalid match_jobs request format");
                    ipc.send_response(error);
                }
            }
            else {
                std::string error = IPCHandler::create_error_response(
                    "Unknown command in request");
                ipc.send_response(error);
            }
        }
        
    } catch (const std::exception& e) {
        std::cerr << "Fatal error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}
