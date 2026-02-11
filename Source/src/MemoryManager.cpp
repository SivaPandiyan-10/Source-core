#include "MemoryManager.h"
#include <vector>
#include <string>
#include <mutex>
#include <fstream>

struct MemoryManager::Impl {
    std::vector<std::string> session;
    std::vector<std::pair<std::string, std::string>> longterm;
    std::mutex mu;
};

MemoryManager::MemoryManager() : impl_(new Impl()) {}
MemoryManager::~MemoryManager() { delete impl_; }

void MemoryManager::addSessionNote(const std::string &note) {
    std::lock_guard<std::mutex> lk(impl_->mu);
    impl_->session.push_back(note);
}

std::vector<std::string> MemoryManager::getSessionNotes() const {
    std::lock_guard<std::mutex> lk(impl_->mu);
    return impl_->session;
}

void MemoryManager::addLongTermNote(const std::string &tag, const std::string &content) {
    std::lock_guard<std::mutex> lk(impl_->mu);
    impl_->longterm.emplace_back(tag, content);
}

std::vector<std::pair<std::string, std::string>> MemoryManager::queryLongTerm(const std::string &query) const {
    std::lock_guard<std::mutex> lk(impl_->mu);
    // Naive substring match
    std::vector<std::pair<std::string, std::string>> out;
    for (auto &p : impl_->longterm) {
        if (p.first.find(query) != std::string::npos || p.second.find(query) != std::string::npos)
            out.push_back(p);
    }
    return out;
}
