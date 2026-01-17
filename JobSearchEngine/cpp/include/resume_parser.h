#ifndef JOBSEARCH_RESUME_PARSER_H
#define JOBSEARCH_RESUME_PARSER_H

#include "models.h"
#include <string>
#include <vector>
#include <memory>

namespace jobsearch {

class ResumeParser {
public:
    ResumeParser();
    ~ResumeParser();
    
    /// Parse resume content and extract features
    /// Returns nullptr if parsing fails
    std::unique_ptr<Resume> parse(const std::string& content, const std::string& candidate_name);
    
    /// Extract skills from text (keyword-based)
    std::vector<std::string> extract_skills(const std::string& text);
    
    /// Extract experience years from text
    int extract_experience_years(const std::string& text);
    
    /// Extract job roles/titles from text
    std::vector<std::string> extract_roles(const std::string& text);
    
    /// Extract location preferences from text
    std::vector<std::string> extract_locations(const std::string& text);
    
    /// Normalize text (lowercase, remove punctuation, etc.)
    static std::string normalize_text(const std::string& text);
    
    /// Add custom skill keywords for detection
    void add_skill_keyword(const std::string& skill);
    
    /// Add custom role keywords for detection
    void add_role_keyword(const std::string& role);

private:
    std::vector<std::string> skill_keywords;
    std::vector<std::string> role_keywords;
    std::vector<std::string> location_keywords;
    
    /// Load default skill and role keywords
    void initialize_keywords();
    
    /// Extract years from text (e.g., "5 years experience" -> 5)
    int parse_years_from_text(const std::string& text);
    
    /// Case-insensitive string find
    bool contains_keyword(const std::string& text, const std::string& keyword);
};

}  // namespace jobsearch

#endif  // JOBSEARCH_RESUME_PARSER_H
