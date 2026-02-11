#pragma once
#include "LLMInterface.h"
#include <string>

// Simple Ollama REST client (synchronous) using HTTP POST.
class OllamaClient : public LLMInterface {
public:
    explicit OllamaClient(const std::string &url = "http://127.0.0.1:11434");
    ~OllamaClient() override;
    std::string generate(const std::string &prompt) override;
private:
    std::string url_;
};
