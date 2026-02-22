#pragma once

#include <string>
#include <vector>

// Very small memory manager API (short-term + long-term hooks)
class MemoryManager {
public:
    MemoryManager();
    ~MemoryManager();

    void addSessionNote(const std::string &note);
    std::vector<std::string> getSessionNotes() const;

    void addLongTermNote(const std::string &tag, const std::string &content);
    std::vector<std::pair<std::string, std::string>> queryLongTerm(const std::string &query) const;

private:
    struct Impl;
    Impl *impl_;
};
