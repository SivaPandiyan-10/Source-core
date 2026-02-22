# Personal AI Assistant (C++ core)

This repository contains a privacy-first, local-first scaffold for a personal AI assistant with a C++ core and a small Python embedding microservice.

# Quick start (build minimal CLI):

```bash
# From repository root
mkdir build && cd build
cmake ..
cmake --build . --config Release
./personal_ai
```

Install dependencies (Linux / macOS):

```bash
# Debian/Ubuntu example
sudo apt install build-essential cmake libsqlite3-dev libcurl4-openssl-dev libsodium-dev
```

Run embedding microservice (optional, recommended for better embeddings):

```bash
python -m pip install -r python/requirements.txt
uvicorn python.embedding_service:app --port 8000 --reload
```

To enable Ollama integration, set `OLLAMA_URL`, for example:

```bash
export OLLAMA_URL="http://127.0.0.1:11434"
```

Windows demo (PowerShell)

```powershell
# 1) Run the setup helper to see missing deps
PowerShell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1

# 2) Start the embedding service in a separate shell
python -m pip install -r python/requirements.txt
python -m uvicorn python.embedding_service:app --port 8000

# 3) Index the sample corpus
python python/index_corpus.py --dir data/sample_docs --endpoint http://127.0.0.1:8000/embed --db personal_ai.db

# 4) Build and run the C++ CLI (see build steps above)
mkdir build; cd build; cmake ..; cmake --build . --config Release
./personal_ai

# Or run the demo runner script to automate steps 2-4 (when available)
PowerShell -ExecutionPolicy Bypass -File .\scripts\run_demo.ps1
```

```bash
python -m pip install -r python/requirements.txt
uvicorn python.embedding_service:app --port 8000 --reload
```

What's included:
- `include/` core headers
- `src/` minimal implementations and CLI
- `python/` embedding microservice
- `sql/schema.sql` database schema
- `docs/` architecture, RAG notes, prompts
