#include "../include/resume_parser.h"
#include <algorithm>
#include <sstream>
#include <cctype>
#include <regex>

namespace jobsearch {

ResumeParser::ResumeParser() {
    initialize_keywords();
}

ResumeParser::~ResumeParser() = default;

void ResumeParser::initialize_keywords() {
    // Programming languages
    skill_keywords = {
        "c++", "cpp", "c#", "csharp", "java", "python", "javascript", "typescript",
        "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "scala",
        "r", "matlab", "sql", "plsql", "vbnet", "perl", "groovy",
        
        // Frameworks & Libraries
        "react", "angular", "vue.js", "node.js", "express", "django", "flask",
        "spring", "spring boot", "fastapi", "asp.net", "vue", ".net",
        "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
        
        // Databases
        "sql server", "mysql", "postgresql", "mongodb", "redis", "cassandra",
        "oracle", "sqlite", "firebase", "dynamodb", "elasticsearch",
        
        // Cloud & DevOps
        "aws", "azure", "gcp", "kubernetes", "docker", "jenkins", "gitlab",
        "github", "git", "terraform", "ansible", "cloudformation",
        
        // Big Data & Analytics
        "hadoop", "spark", "hive", "pig", "mapreduce", "hdfs",
        
        // Tools & Other
        "linux", "windows", "macos", "unix", "bash", "shell",
        "git", "svn", "jira", "confluence", "slack",
        "rest", "graphql", "soap", "json", "xml",
        "agile", "scrum", "kanban",
        "machine learning", "deep learning", "nlp", "computer vision",
        "microservices", "monolithic", "api design", "system design",
        "devops", "ci/cd", "continuous integration", "continuous deployment"
    };
    
    // Job roles
    role_keywords = {
        "software engineer", "software developer", "developer", "engineer",
        "senior engineer", "principal engineer", "staff engineer",
        "full stack", "backend", "backend engineer", "backend developer",
        "frontend", "frontend engineer", "frontend developer",
        "mobile developer", "ios developer", "android developer",
        "devops", "devops engineer", "cloud engineer",
        "data engineer", "data scientist", "ml engineer", "machine learning",
        "solutions architect", "architect", "technical architect",
        "tech lead", "engineering manager", "team lead",
        "qa engineer", "quality assurance", "automation engineer",
        "security engineer", "security architect"
    };
    
    // Locations (major tech hubs)
    location_keywords = {
        "san francisco", "bay area", "mountain view", "palo alto", "cupertino",
        "new york", "seattle", "los angeles", "chicago", "boston",
        "austin", "denver", "portland", "phoenix", "miami",
        "london", "berlin", "amsterdam", "paris", "zurich",
        "toronto", "vancouver", "sydney", "bangalore", "hyderabad",
        "mumbai", "delhi", "singapore", "hong kong", "tokyo",
        "remote", "work from home", "distributed", "flexible location"
    };
}

std::unique_ptr<Resume> ResumeParser::parse(
    const std::string& content,
    const std::string& candidate_name) {
    
    if (content.empty() || candidate_name.empty()) {
        return nullptr;
    }
    
    auto resume = std::make_unique<Resume>();
    resume->candidate_name = candidate_name;
    
    // Extract features
    resume->skills = extract_skills(content);
    resume->experience_years = extract_experience_years(content);
    resume->roles = extract_roles(content);
    resume->locations = extract_locations(content);
    
    // Validate
    if (!resume->is_valid()) {
        return nullptr;
    }
    
    return resume;
}

std::vector<std::string> ResumeParser::extract_skills(const std::string& text) {
    std::vector<std::string> found_skills;
    std::string normalized = normalize_text(text);
    
    for (const auto& skill : skill_keywords) {
        if (contains_keyword(normalized, skill)) {
            found_skills.push_back(skill);
        }
    }
    
    // Remove duplicates while preserving order
    std::sort(found_skills.begin(), found_skills.end());
    found_skills.erase(std::unique(found_skills.begin(), found_skills.end()), found_skills.end());
    
    return found_skills;
}

int ResumeParser::extract_experience_years(const std::string& text) {
    std::string normalized = normalize_text(text);
    
    // Try to find patterns like "X years", "X+ years", "X year experience"
    std::regex pattern(R"(\b(\d+)\s*\+?\s*years?)");
    std::smatch match;
    
    if (std::regex_search(text, match, pattern)) {
        try {
            return std::stoi(match[1].str());
        } catch (...) {
            return 0;
        }
    }
    
    return 0;
}

std::vector<std::string> ResumeParser::extract_roles(const std::string& text) {
    std::vector<std::string> found_roles;
    std::string normalized = normalize_text(text);
    
    for (const auto& role : role_keywords) {
        if (contains_keyword(normalized, role)) {
            found_roles.push_back(role);
        }
    }
    
    // Remove duplicates
    std::sort(found_roles.begin(), found_roles.end());
    found_roles.erase(std::unique(found_roles.begin(), found_roles.end()), found_roles.end());
    
    return found_roles;
}

std::vector<std::string> ResumeParser::extract_locations(const std::string& text) {
    std::vector<std::string> found_locations;
    std::string normalized = normalize_text(text);
    
    for (const auto& location : location_keywords) {
        if (contains_keyword(normalized, location)) {
            found_locations.push_back(location);
        }
    }
    
    // Remove duplicates
    std::sort(found_locations.begin(), found_locations.end());
    found_locations.erase(std::unique(found_locations.begin(), found_locations.end()), found_locations.end());
    
    return found_locations;
}

std::string ResumeParser::normalize_text(const std::string& text) {
    std::string result = text;
    
    // Convert to lowercase
    std::transform(result.begin(), result.end(), result.begin(),
                   [](unsigned char c) { return std::tolower(c); });
    
    return result;
}

bool ResumeParser::contains_keyword(const std::string& text, const std::string& keyword) {
    return text.find(keyword) != std::string::npos;
}

void ResumeParser::add_skill_keyword(const std::string& skill) {
    auto normalized = normalize_text(skill);
    if (std::find(skill_keywords.begin(), skill_keywords.end(), normalized) 
        == skill_keywords.end()) {
        skill_keywords.push_back(normalized);
    }
}

void ResumeParser::add_role_keyword(const std::string& role) {
    auto normalized = normalize_text(role);
    if (std::find(role_keywords.begin(), role_keywords.end(), normalized) 
        == role_keywords.end()) {
        role_keywords.push_back(normalized);
    }
}

}  // namespace jobsearch
