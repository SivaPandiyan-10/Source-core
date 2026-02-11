#pragma once

#include <string>
#include <vector>

// Thin interface to an embedding provider (usually a Python microservice)
class EmbeddingService {
public:
    virtual ~EmbeddingService() = default;
    virtual std::vector<float> embed(const std::string &text) = 0;
};
