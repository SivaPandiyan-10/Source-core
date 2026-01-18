#include "message_protocol.h"
#include <sstream>
#include <chrono>
#include <iomanip>
#include <cstring>

namespace jse {
namespace protocol {

// Helper function to get current timestamp in ISO 8601 format
static std::string get_current_timestamp() {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    auto tm = *std::gmtime(&time_t);
    
    std::ostringstream oss;
    oss << std::put_time(&tm, "%Y-%m-%dT%H:%M:%SZ");
    return oss.str();
}

Message::Message() : type(MessageType::UNKNOWN) {}

Message::Message(MessageType type) : type(type) {}

Message::Message(MessageType type, const json& payload) 
    : type(type), payload(payload) {}

std::string Message::message_type_to_string(MessageType type) {
    switch (type) {
        case MessageType::PING: return "PING";
        case MessageType::PONG: return "PONG";
        case MessageType::JOB_MATCH_REQUEST: return "JOB_MATCH_REQUEST";
        case MessageType::JOB_MATCH_RESPONSE: return "JOB_MATCH_RESPONSE";
        case MessageType::BATCH_JOB_MATCH_REQUEST: return "BATCH_JOB_MATCH_REQUEST";
        case MessageType::BATCH_JOB_MATCH_RESPONSE: return "BATCH_JOB_MATCH_RESPONSE";
        case MessageType::SHUTDOWN: return "SHUTDOWN";
        case MessageType::SHUTDOWN_ACK: return "SHUTDOWN_ACK";
        case MessageType::ERROR: return "ERROR";
        default: return "UNKNOWN";
    }
}

MessageType Message::string_to_message_type(const std::string& str) {
    if (str == "PING") return MessageType::PING;
    if (str == "PONG") return MessageType::PONG;
    if (str == "JOB_MATCH_REQUEST") return MessageType::JOB_MATCH_REQUEST;
    if (str == "JOB_MATCH_RESPONSE") return MessageType::JOB_MATCH_RESPONSE;
    if (str == "BATCH_JOB_MATCH_REQUEST") return MessageType::BATCH_JOB_MATCH_REQUEST;
    if (str == "BATCH_JOB_MATCH_RESPONSE") return MessageType::BATCH_JOB_MATCH_RESPONSE;
    if (str == "SHUTDOWN") return MessageType::SHUTDOWN;
    if (str == "SHUTDOWN_ACK") return MessageType::SHUTDOWN_ACK;
    if (str == "ERROR") return MessageType::ERROR;
    return MessageType::UNKNOWN;
}

std::string Message::serialize() const {
    json msg_json = payload;
    msg_json["type"] = message_type_to_string(type);
    return msg_json.dump();
}

Message Message::deserialize(const std::string& data) {
    try {
        json j = json::parse(data);
        std::string type_str = j.value("type", "UNKNOWN");
        MessageType msg_type = string_to_message_type(type_str);
        return Message(msg_type, j);
    } catch (const std::exception& e) {
        return Message(MessageType::ERROR);
    }
}

std::string Message::frame() const {
    std::string serialized = serialize();
    uint32_t length = static_cast<uint32_t>(serialized.length());
    
    // Convert to big-endian
    uint8_t length_bytes[4];
    length_bytes[0] = (length >> 24) & 0xFF;
    length_bytes[1] = (length >> 16) & 0xFF;
    length_bytes[2] = (length >> 8) & 0xFF;
    length_bytes[3] = length & 0xFF;
    
    std::string result(reinterpret_cast<const char*>(length_bytes), 4);
    result += serialized;
    return result;
}

std::pair<bool, Message> Message::parse_framed(const std::string& raw_data) {
    if (raw_data.length() < 4) {
        return {false, Message(MessageType::ERROR)};
    }
    
    // Parse big-endian length header
    const uint8_t* data = reinterpret_cast<const uint8_t*>(raw_data.data());
    uint32_t length = (static_cast<uint32_t>(data[0]) << 24) |
                     (static_cast<uint32_t>(data[1]) << 16) |
                     (static_cast<uint32_t>(data[2]) << 8) |
                     static_cast<uint32_t>(data[3]);
    
    if (raw_data.length() < 4 + length) {
        return {false, Message(MessageType::ERROR)};
    }
    
    std::string payload_str = raw_data.substr(4, length);
    return {true, deserialize(payload_str)};
}

// MessageBuilder implementations
Message MessageBuilder::create_ping() {
    json payload;
    payload["timestamp"] = get_current_timestamp();
    return Message(MessageType::PING, payload);
}

Message MessageBuilder::create_pong() {
    json payload;
    payload["timestamp"] = get_current_timestamp();
    return Message(MessageType::PONG, payload);
}

Message MessageBuilder::create_job_match_request(const JobMatchRequest& req) {
    json payload;
    payload["request_id"] = req.request_id;
    payload["timestamp"] = req.timestamp;
    
    json candidate_json;
    candidate_json["name"] = req.candidate.name;
    candidate_json["resume_id"] = req.candidate.resume_id;
    candidate_json["keywords"] = req.candidate.keywords;
    payload["candidate"] = candidate_json;
    
    json job_json;
    job_json["source"] = req.job.source;
    job_json["source_id"] = req.job.source_id;
    job_json["company_name"] = req.job.company_name;
    job_json["job_title"] = req.job.job_title;
    job_json["job_description"] = req.job.job_description;
    job_json["apply_url"] = req.job.apply_url;
    job_json["posted_date"] = req.job.posted_date;
    payload["job"] = job_json;
    
    return Message(MessageType::JOB_MATCH_REQUEST, payload);
}

Message MessageBuilder::create_job_match_response(const JobMatchResponse& res) {
    json payload;
    payload["request_id"] = res.request_id;
    payload["status"] = (res.status == MatchStatus::MATCHED ? "MATCHED" :
                         res.status == MatchStatus::REJECTED ? "REJECTED" : "ERROR");
    payload["confidence_score"] = res.confidence_score;
    payload["matched_skills"] = res.matched_skills;
    payload["unmatched_required_skills"] = res.unmatched_required_skills;
    payload["reason"] = res.reason;
    payload["processing_time_ms"] = res.processing_time_ms;
    payload["timestamp"] = res.timestamp;
    
    return Message(MessageType::JOB_MATCH_RESPONSE, payload);
}

Message MessageBuilder::create_error(const std::string& request_id, 
                                    ErrorCode code, 
                                    const std::string& message) {
    json payload;
    payload["request_id"] = request_id;
    
    std::string code_str;
    switch (code) {
        case ErrorCode::INVALID_JSON: code_str = "INVALID_JSON"; break;
        case ErrorCode::MISSING_FIELD: code_str = "MISSING_FIELD"; break;
        case ErrorCode::INTERNAL_ERROR: code_str = "INTERNAL_ERROR"; break;
        case ErrorCode::TIMEOUT: code_str = "TIMEOUT"; break;
        case ErrorCode::INVALID_REQUEST_TYPE: code_str = "INVALID_REQUEST_TYPE"; break;
    }
    
    payload["error_code"] = code_str;
    payload["error_message"] = message;
    payload["timestamp"] = get_current_timestamp();
    
    return Message(MessageType::ERROR, payload);
}

Message MessageBuilder::create_shutdown(const std::string& reason) {
    json payload;
    payload["reason"] = reason;
    payload["timestamp"] = get_current_timestamp();
    return Message(MessageType::SHUTDOWN, payload);
}

Message MessageBuilder::create_shutdown_ack() {
    json payload;
    payload["timestamp"] = get_current_timestamp();
    return Message(MessageType::SHUTDOWN_ACK, payload);
}

} // namespace protocol
} // namespace jse
