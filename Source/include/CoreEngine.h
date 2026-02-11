#pragma once

#include <memory>
#include <string>

class CoreEngineImpl;

class CoreEngine {
public:
    CoreEngine();
    ~CoreEngine();

    // Starts a simple CLI loop
    void runCLI();

private:
    std::unique_ptr<CoreEngineImpl> impl_;
};
