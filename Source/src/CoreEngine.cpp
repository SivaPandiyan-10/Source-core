#include "CoreEngine.h"
#include "StubLLM.h"
#include "MemoryManager.h"
#include "FinancialModule.h"
#include "EmbeddingHttpClient.h"
#include "VectorStore.h"
#include "KnowledgeStore.h"
#include <iostream>
#include <memory>

struct CoreEngineImpl {
    CoreEngineImpl() {
        // choose LLM implementation based on environment
        const char *ollama = std::getenv("OLLAMA_URL");
        if (ollama && std::string(ollama).size() > 0) {
            llm = std::make_unique<OllamaClient>(std::string(ollama));
        } else {
            llm = std::make_unique<StubLLM>();
        }
        embedClient = std::make_unique<EmbeddingHttpClient>();
        vstore = std::make_unique<VectorStore>("personal_ai.db");
        knowledge = std::make_unique<KnowledgeStore>(embedClient.get(), vstore.get());
    }
    std::unique_ptr<LLMInterface> llm;
    std::unique_ptr<EmbeddingHttpClient> embedClient;
    std::unique_ptr<VectorStore> vstore;
    std::unique_ptr<KnowledgeStore> knowledge;
    MemoryManager mem;
    FinancialModule finance;
};

CoreEngine::CoreEngine() : impl_(new CoreEngineImpl()) {}
CoreEngine::~CoreEngine() = default;

void CoreEngine::runCLI() {
    std::cout << "Personal AI Assistant (minimal CLI)\n";
    while (true) {
        std::cout << "\nSelect: 1=chat 2=record expense 3=summary 0=exit > ";
        int choice;
        if (!(std::cin >> choice)) break;
        std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
        if (choice == 0) break;
        if (choice == 1) {
            std::string prompt;
            std::cout << "Prompt: ";
            std::getline(std::cin, prompt);
            auto out = impl_->llm->generate(prompt);
            std::cout << "LLM> " << out << "\n";
            impl_->mem.addSessionNote(prompt);
        } else if (choice == 2) {
            std::string date, cat;
            double amt;
            std::cout << "Date(YYYY-MM): ";
            std::getline(std::cin, date);
            std::cout << "Amount: ";
            std::cin >> amt;
            std::cin.ignore();
            std::cout << "Category: ";
            std::getline(std::cin, cat);
            impl_->finance.recordExpense(date, amt, cat);
            std::cout << "Recorded.\n";
        } else if (choice == 3) {
            std::cout << impl_->finance.summary() << "\n";
        } else if (choice == 4) {
            std::string tag, content;
            std::cout << "Tag: ";
            std::getline(std::cin, tag);
            std::cout << "Content: ";
            std::getline(std::cin, content);
            int id = impl_->knowledge->addKnowledge(tag, content);
            std::cout << "Knowledge added id=" << id << "\n";
        } else if (choice == 5) {
            std::string q;
            std::cout << "Query: ";
            std::getline(std::cin, q);
            auto res = impl_->knowledge->retrieveRelevant(q, 5);
            std::cout << "Top results:\n";
            for (auto &t : res) {
                int id; std::string content; float score;
                std::tie(id, content, score) = t;
                std::cout << "[" << id << "] (" << score << ") " << content << "\n";
            }
        }
    }
}
