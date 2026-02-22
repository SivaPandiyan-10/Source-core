#include "StubLLM.h"
#include <string>

StubLLM::StubLLM() {}
StubLLM::~StubLLM() = default;

std::string StubLLM::generate(const std::string &prompt) {
    // Very small local stub - echo + suggestion
    return "(stub) I received: " + prompt + "\n[Hint] Try: 'Show my monthly savings rate'";
}
