#include <iostream>
#include <string>
#include <csignal>
#include <thread>
#include <chrono>
#include <iomanip>
#include <sstream>
#include "tcp_server.h"
#include "message_protocol.h"
#include "matcher.h"
#include "resume_parser.h"

// Global server pointer for signal handling
jse::network::TCPServer* g_server = nullptr;

void signal_handler(int signal) {
    std::cout << "\n[Main] Received signal " << signal << ", shutting down..." << std::endl;
    if (g_server) {
        g_server->stop();
    }
}

// Request handler function
jse::protocol::Message handle_job_match_request(const jse::protocol::Message& request) {
    auto start_time = std::chrono::high_resolution_clock::now();
    
    try {
        // Validate message type
        if (request.type != jse::protocol::MessageType::JOB_MATCH_REQUEST) {
            return jse::protocol::MessageBuilder::create_error(
                "unknown",
                jse::protocol::ErrorCode::INVALID_REQUEST_TYPE,
                "Expected JOB_MATCH_REQUEST"
            );
        }
        
        // Extract request data
        std::string request_id = request.payload.value("request_id", "");
        
        if (request_id.empty()) {
            return jse::protocol::MessageBuilder::create_error(
                "",
                jse::protocol::ErrorCode::MISSING_FIELD,
                "request_id is required"
            );
        }
        
        // Extract candidate and job info
        std::string candidate_name = request.payload["candidate"].value("name", "");
        std::string resume_id = request.payload["candidate"].value("resume_id", "");
        
        auto job_obj = request.payload["job"];
        jse::protocol::JobInfo job_info;
        job_info.source = job_obj.value("source", "");
        job_info.source_id = job_obj.value("source_id", "");
        job_info.company_name = job_obj.value("company_name", "");
        job_info.job_title = job_obj.value("job_title", "");
        job_info.job_description = job_obj.value("job_description", "");
        job_info.apply_url = job_obj.value("apply_url", "");
        job_info.posted_date = job_obj.value("posted_date", "");
        
        // Extract keywords
        std::vector<std::string> keywords;
        if (request.payload["candidate"].contains("keywords")) {
            keywords = request.payload["candidate"]["keywords"].get<std::vector<std::string>>();
        }
        
        std::cout << "[Handler] Processing request " << request_id 
                  << " for candidate " << candidate_name 
                  << " (resume: " << resume_id << ")" << std::endl;
        std::cout << "[Handler] Job: " << job_info.job_title 
                  << " at " << job_info.company_name << std::endl;
        
        // Perform matching
        static jse::matching::JobMatcher matcher;
        auto match_result = matcher.match_job(resume_id, job_info, keywords);
        
        // Build response
        jse::protocol::JobMatchResponse response;
        response.request_id = request_id;
        response.confidence_score = match_result.confidence_score;
        response.matched_skills = match_result.matched_skills;
        response.unmatched_required_skills = match_result.missing_skills;
        
        // Determine status based on threshold
        double threshold = 0.70; // Default threshold
        if (match_result.confidence_score >= threshold) {
            response.status = jse::protocol::MatchStatus::MATCHED;
            response.reason = "Job matches candidate profile with sufficient confidence";
        } else {
            response.status = jse::protocol::MatchStatus::REJECTED;
            response.reason = "Confidence score below threshold";
        }
        
        response.reason = match_result.analysis;
        
        auto end_time = std::chrono::high_resolution_clock::now();
        response.processing_time_ms = 
            std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time).count();
        
        // Get current timestamp
        auto now = std::chrono::system_clock::now();
        auto time_t = std::chrono::system_clock::to_time_t(now);
        auto tm = *std::gmtime(&time_t);
        std::ostringstream oss;
        oss << std::put_time(&tm, "%Y-%m-%dT%H:%M:%SZ");
        response.timestamp = oss.str();
        
        std::cout << "[Handler] Response: status=" 
                  << (response.status == jse::protocol::MatchStatus::MATCHED ? "MATCHED" :
                      response.status == jse::protocol::MatchStatus::REJECTED ? "REJECTED" : "ERROR")
                  << ", score=" << response.confidence_score 
                  << ", time=" << response.processing_time_ms << "ms" << std::endl;
        
        return jse::protocol::MessageBuilder::create_job_match_response(response);
        
    } catch (const std::exception& e) {
        std::cerr << "[Handler] Exception: " << e.what() << std::endl;
        return jse::protocol::MessageBuilder::create_error(
            "",
            jse::protocol::ErrorCode::INTERNAL_ERROR,
            std::string("Exception: ") + e.what()
        );
    }
}

jse::protocol::Message request_dispatcher(const jse::protocol::Message& request) {
    switch (request.type) {
        case jse::protocol::MessageType::PING:
            return jse::protocol::MessageBuilder::create_pong();
            
        case jse::protocol::MessageType::JOB_MATCH_REQUEST:
            return handle_job_match_request(request);
            
        case jse::protocol::MessageType::SHUTDOWN:
            return jse::protocol::MessageBuilder::create_shutdown_ack();
            
        default:
            return jse::protocol::MessageBuilder::create_error(
                "",
                jse::protocol::ErrorCode::INVALID_REQUEST_TYPE,
                "Unknown message type"
            );
    }
}

int main(int argc, char* argv[]) {
    int port = 10000;
    
    // Parse command-line arguments
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--port" && i + 1 < argc) {
            port = std::stoi(argv[++i]);
        }
    }
    
    std::cout << "========================================" << std::endl;
    std::cout << "JobSearchEngine - C++ Job Matching Server" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "Port: " << port << std::endl;
    std::cout << "Protocol: TCP with JSON messages" << std::endl;
    std::cout << "Message Framing: Length-prefixed (4-byte big-endian)" << std::endl;
    std::cout << "========================================\n" << std::endl;
    
    try {
        // Create and start server
        jse::network::TCPServer server(port, request_dispatcher);
        g_server = &server;
        
        // Register signal handlers for graceful shutdown
        signal(SIGTERM, signal_handler);
        signal(SIGINT, signal_handler);
        
        server.start();
        
        std::cout << "[Main] Server started successfully" << std::endl;
        std::cout << "[Main] Listening for connections from Go Orchestrator..." << std::endl;
        std::cout << "[Main] Press Ctrl+C to shutdown" << std::endl;
        
        // Keep the server running
        while (server.is_running()) {
            std::this_thread::sleep_for(std::chrono::seconds(1));
        }
        
        std::cout << "[Main] Server shutdown complete" << std::endl;
        return 0;
        
    } catch (const std::exception& e) {
        std::cerr << "[Main] Fatal error: " << e.what() << std::endl;
        return 1;
    }
}
