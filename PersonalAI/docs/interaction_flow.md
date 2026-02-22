**Example Interaction Flow**

1. User: "What's my savings rate for 2026-01?"
2. CoreEngine: Detects intent `finance.query_savings` (lightweight intent classifier or prompt pattern).
3. CoreEngine queries `FinancialModule::getMonthlySavingsRate("2026-01")` and returns result.

RAG example:
1. User: "How did I plan the X project last year?"
2. CoreEngine calls `KnowledgeStore::retrieveRelevant(query, k=5)` -> gets top 3 chunks.
3. Injects chunks into the LLM prompt and calls `LLMInterface::generate()`.
4. Returns summarized answer and stores the user query into short-term memory.
