#pragma once

#include <string>

// Abstract interface for LLM integrations (Ollama, local LLMs)
class LLMInterface {
public:
    virtual ~LLMInterface() = default;
    // Synchronous simple generation (implementations may stream)
    virtual std::string generate(const std::string &prompt) = 0;
};
