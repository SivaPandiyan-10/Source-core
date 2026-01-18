# JobSearchEngine - Build & Deployment Guide

## Prerequisites

### C++ Server
- **CMake** 3.10 or higher
- **C++17 compatible compiler:** MSVC 2017+, GCC 7+, or Clang 5+
- **nlohmann/json** (header-only library)

### Go Orchestrator
- **Go** 1.21 or higher

---

## Building C++ Server

### Windows (MSVC)

```bash
cd JobSearchEngine
mkdir build
cd build
cmake .. -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release
.\Release\job_matching_engine.exe --port 10000
```

### Linux/macOS

```bash
cd JobSearchEngine
mkdir -p build
cd build
cmake ..
make
./job_matching_engine --port 10000
```

### Install nlohmann/json

```bash
mkdir -p cpp/include/nlohmann
curl -L https://github.com/nlohmann/json/releases/download/v3.11.2/json.hpp \
  -o cpp/include/nlohmann/json.hpp
```

---

## Building Go Orchestrator

```bash
cd JobSearchEngine/go
go mod download
go build -o jobsearch ./cmd/jobsearch
./jobsearch -config ../config/orchestrator.json
```

---

## Running Both Services

### Terminal 1 - C++ Server
```bash
./build/job_matching_engine --port 10000
```

### Terminal 2 - Go Orchestrator
```bash
./go/jobsearch -config config/orchestrator.json
```

---

## Configuration

Edit `config/orchestrator.json`:

```json
{
  "server": {
    "address": "localhost",
    "port": 10000
  },
  "candidate": {
    "name": "Your Name",
    "resume_id": "resume_001",
    "keywords": ["C++", "Python", "AWS", ...]
  },
  "schedule": {
    "fetch_interval": "30s",
    "health_check_interval": "10s",
    "tcp_timeout": "10s"
  },
  "logging": {
    "directory": "logs"
  },
  "platforms": [
    {"name": "linkedin", "enabled": true},
    {"name": "naukri", "enabled": true}
  ]
}
```

---

## Verification

```bash
# Test C++ server is listening
nc -zv localhost 10000

# Check logs for matches
tail -f logs/$(date +%Y-%m-%d).log
```

---

## Troubleshooting

**Port already in use:**
```bash
# Linux/macOS: Kill process
lsof -i :10000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Windows
netstat -ano | findstr :10000
taskkill /PID <PID> /F
```

**nlohmann/json not found:**
```bash
# Ensure file exists at cpp/include/nlohmann/json.hpp
ls -la cpp/include/nlohmann/json.hpp
```

**Go connection refused:**
```bash
# Ensure C++ server is running
ps aux | grep job_matching_engine
```

---
