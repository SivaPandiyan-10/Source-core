#pragma once

#include <string>
#include <vector>
#include <utility>

// Simple on-disk vector store backed by SQLite: stores id -> vector (as CSV text) and metadata
class VectorStore {
public:
    explicit VectorStore(const std::string &dbpath = "personal_ai.db");
    ~VectorStore();

    // Store a vector for a knowledge id
    bool upsertVector(int knowledgeId, const std::vector<float> &vec, const std::string &metadata = "");

    // Retrieve top-k by cosine similarity (returns pair<knowledgeId, score>)
    std::vector<std::pair<int, float>> query(const std::vector<float> &vec, int k = 5) const;

private:
    struct Impl;
    Impl *impl_;
};
