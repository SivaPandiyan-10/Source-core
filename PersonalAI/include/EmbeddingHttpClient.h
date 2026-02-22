#pragma once

#include "EmbeddingService.h"
#include <string>
#include <vector>

// Embedding HTTP client that posts to local Python microservice
class EmbeddingHttpClient : public EmbeddingService {
public:
    EmbeddingHttpClient(const std::string &url = "http://127.0.0.1:8000/embed");
    ~EmbeddingHttpClient() override;
    std::vector<float> embed(const std::string &text) override;
private:
    std::string url_;
};
