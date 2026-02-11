**Architecture Overview**

- **Core Engine:** Orchestrates modules, loads config, provides CLI and optional web interface.
- **LLM Interface Layer:** Abstracts model calls (Ollama REST, local LLM). Supports streaming and model switching.
- **Embedding Interface Layer:** Talks to Python microservice for embeddings or local C++ embedder.
- **Memory Manager:** Short-term (session) + long-term (persistent SQLite + vector store).
- **Knowledge Store:** CRUD operations for notes, tagged entries, files.
- **Financial Module:** Records salary/expense/investment; exposes analytics API.
- **RAG Layer:** Chunking, embeddings, vector store, retrieval and prompt injection.

See `diagrams/class_diagram.puml` for a quick class diagram.
