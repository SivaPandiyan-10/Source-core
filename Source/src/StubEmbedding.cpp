#include "EmbeddingService.h"
#include <vector>
#include <string>

class StubEmbedding : public EmbeddingService {
public:
    StubEmbedding() {}
    ~StubEmbedding() override = default;
    std::vector<float> embed(const std::string &text) override {
        // Return a tiny deterministic pseudo-embedding
        std::vector<float> v(8, 0.0f);
        for (size_t i = 0; i < text.size() && i < v.size(); ++i) v[i] = float((unsigned char)text[i]) / 255.0f;
        return v;
    }
};
