#pragma once

#include "LLMInterface.h"
#include <string>

// Simple stub LLM used for local testing
class StubLLM : public LLMInterface {
public:
    StubLLM();
    ~StubLLM() override;
    std::string generate(const std::string &prompt) override;
};
