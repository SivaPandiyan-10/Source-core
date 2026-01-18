#ifndef MESSAGE_PROTOCOL_H
#define MESSAGE_PROTOCOL_H

#include <string>
#include <vector>
#include <cstdint>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

namespace jse {
namespace protocol {

// Message type enumeration
enum class MessageType {
    PING,
    PONG,
    JOB_MATCH_REQUEST,
    JOB_MATCH_RESPONSE,
    BATCH_JOB_MATCH_REQUEST,
    BATCH_JOB_MATCH_RESPONSE,
    SHUTDOWN,
    SHUTDOWN_ACK,
    ERROR,
    UNKNOWN
};

// Job match status
enum class MatchStatus {
    MATCHED,
    REJECTED,
    ERROR
};

// Error codes
enum class ErrorCode {
    INVALID_JSON,
    MISSING_FIELD,
    INTERNAL_ERROR,
    TIMEOUT,
    INVALID_REQUEST_TYPE
};

// Structures for message payloads
struct Candidate {
    std::string name;
    std::string resume_id;
    std::vector<std::string> keywords;
};

struct JobInfo {
    std::string source;
    std::string source_id;
    std::string company_name;
    std::string job_title;
    std::string job_description;
    std::string apply_url;
    std::string posted_date;
};

struct JobMatchRequest {
    std::string request_id;
    std::string timestamp;
    Candidate candidate;
    JobInfo job;
};

struct JobMatchResponse {
    std::string request_id;
    MatchStatus status;
    double confidence_score;
    std::vector<std::string> matched_skills;
    std::vector<std::string> unmatched_required_skills;
    std::string reason;
    int64_t processing_time_ms;
    std::string timestamp;
};

struct ErrorMessage {
    std::string request_id;
    ErrorCode error_code;
    std::string error_message;
    std::string timestamp;
};

// Message class with framing and serialization
class Message {
public:
    MessageType type;
    json payload;

    Message();
    explicit Message(MessageType type);
    Message(MessageType type, const json& payload);

    // Serialization
    std::string serialize() const;
    
    // Deserialization
    static Message deserialize(const std::string& data);

    // Framing (adds length prefix)
    std::string frame() const;
    
    // Parsing framed message
    static std::pair<bool, Message> parse_framed(const std::string& raw_data);

    // Helper methods
    static std::string message_type_to_string(MessageType type);
    static MessageType string_to_message_type(const std::string& str);
};

// Message builder utility
class MessageBuilder {
public:
    static Message create_ping();
    static Message create_pong();
    static Message create_job_match_request(const JobMatchRequest& req);
    static Message create_job_match_response(const JobMatchResponse& res);
    static Message create_error(const std::string& request_id, 
                                ErrorCode code, 
                                const std::string& message);
    static Message create_shutdown(const std::string& reason = "");
    static Message create_shutdown_ack();
};

} // namespace protocol
} // namespace jse

#endif // MESSAGE_PROTOCOL_H
