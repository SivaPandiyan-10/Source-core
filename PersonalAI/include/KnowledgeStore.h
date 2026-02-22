#pragma once

#include <string>
#include <vector>

class EmbeddingService;
class VectorStore;

class KnowledgeStore {
public:
    KnowledgeStore(EmbeddingService *embedSvc, VectorStore *vstore);
    ~KnowledgeStore();

    // CRUD
    int addKnowledge(const std::string &tag, const std::string &content);
    bool updateKnowledge(int id, const std::string &tag, const std::string &content);
    bool deleteKnowledge(int id);
    std::vector<std::pair<int, std::string>> searchByTag(const std::string &tag);

    // RAG retrieve: returns list of (id, content, score)
    std::vector<std::tuple<int, std::string, float>> retrieveRelevant(const std::string &query, int k = 5);

private:
    struct Impl;
    Impl *impl_;
};
