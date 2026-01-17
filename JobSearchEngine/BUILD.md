# JobSearchEngine Build Instructions

## Prerequisites

### Windows
- Visual Studio 2019 or later (with C++ tools)
- CMake 3.15+
- Go 1.21+
- Git
- PowerShell or Command Prompt

### Linux
- GCC 9+ or Clang 10+
- CMake 3.15+
- Go 1.21+
- Git
- Bash

## Building C++ Component

### Windows (Visual Studio)

```powershell
cd JobSearchEngine
mkdir build
cd build
cmake ..
cmake --build . --config Release
```

Output: `bin/jobsearch_engine.exe`

### Linux / macOS

```bash
cd JobSearchEngine
mkdir build
cd build
cmake ..
make
```

Output: `bin/jobsearch_engine`

## Building Go Component

### Windows & Linux

```bash
cd JobSearchEngine/go
go mod download
go build -o ../bin/jobsearch_app ./cmd/jobsearch
```

Output: `bin/jobsearch_app` (or `.exe` on Windows)

## Complete Build Script

### build.ps1 (Windows PowerShell)

```powershell
# Create build directory
if (!(Test-Path "build")) { mkdir build }
cd build

# Build C++
cmake ..
cmake --build . --config Release

# Build Go
cd ..\go
go mod download
go build -o ..\bin\jobsearch_app .\cmd\jobsearch

echo "Build complete!"
echo "C++ engine: ..\bin\jobsearch_engine.exe"
echo "Go app: ..\bin\jobsearch_app.exe"
```

### build.sh (Linux/macOS Bash)

```bash
#!/bin/bash
set -e

echo "Building JobSearchEngine..."

# Build C++
mkdir -p build
cd build
cmake ..
make
cd ..

# Build Go
cd go
go mod download
go build -o ../bin/jobsearch_app ./cmd/jobsearch
cd ..

echo "Build complete!"
echo "C++ engine: bin/jobsearch_engine"
echo "Go app: bin/jobsearch_app"
```

## Running the Application

### Basic Usage

```bash
./bin/jobsearch_app --candidate "John Doe" --config config/config.yaml
```

### On Windows

```powershell
.\bin\jobsearch_app.exe --candidate "John Doe" --config config\config.yaml
```

### With Custom Config

```bash
./bin/jobsearch_app --candidate "Jane Smith" --config ./custom_config.yaml
```

## Verify Installation

### Test C++ Engine

```bash
# Linux/macOS
echo '{"command":"parse_resume","content":"10 years C++ experience","candidate_name":"Test"}' | \
./bin/jobsearch_engine

# Windows (PowerShell)
'{"command":"parse_resume","content":"10 years C++ experience","candidate_name":"Test"}' | \
.\bin\jobsearch_engine.exe
```

### Test Go App

```bash
# Check help
./bin/jobsearch_app --help

# Run with john_doe resume
./bin/jobsearch_app --candidate "John Doe"
```

## Directory Structure After Build

```
JobSearchEngine/
├── bin/
│   ├── jobsearch_engine       # C++ executable
│   └── jobsearch_app          # Go executable
├── build/                     # CMake build directory
│   ├── CMakeFiles/
│   ├── CMakeCache.txt
│   └── Makefile (or .sln on Windows)
├── cpp/
├── go/
│   ├── go.sum
│   └── go.mod
└── config/
    └── config.yaml
```

## Troubleshooting

### C++ Build Issues

**Error: "cmake not found"**
- Install CMake: https://cmake.org/download/
- Add to PATH

**Error: "C++ compiler not found"**
- Windows: Install Visual Studio
- Linux: `sudo apt-get install build-essential`
- macOS: `xcode-select --install`

### Go Build Issues

**Error: "go: not found"**
- Install Go 1.21+: https://golang.org/dl/
- Add to PATH

**Error: "module not found"**
```bash
cd JobSearchEngine/go
go mod tidy
go mod download
```

### Runtime Issues

**Error: "Resume not found"**
- Ensure resume exists in `resumes/john_doe.txt` (matches candidate name)
- Check config paths: `config.yaml`

**Error: "C++ engine not found"**
- Ensure C++ binary is compiled and in `bin/` directory
- Check `cpp_engine_path` in `config.yaml`

**Error: "Port already in use"**
- The application doesn't use network ports - check for file lock issues
- Restart the application

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/build.yml`:

```yaml
name: Build

on: [push, pull_request]

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - name: Install CMake
        run: |
          if [ "$RUNNER_OS" == "Linux" ]; then
            sudo apt-get install -y cmake
          else
            brew install cmake
          fi
        shell: bash
      - name: Build
        run: |
          mkdir build && cd build
          cmake .. && make
          cd ../go && go build -o ../bin/jobsearch_app ./cmd/jobsearch
        shell: bash
      - name: Test
        run: |
          go test ./...
```

## Performance Notes

- **First run:** May take 10-30 seconds (C++ engine initialization, resume parsing)
- **Subsequent runs:** 2-5 seconds per search cycle
- **Memory usage:** ~50-100 MB
- **Disk usage:** Logs grow ~10 KB per 100 matched jobs

## Deployment

### Docker Deployment

```dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY . .

RUN apk add --no-cache cmake build-base
RUN cd go && go build -o /app/bin/jobsearch_app ./cmd/jobsearch
RUN mkdir -p build && cd build && cmake .. && make

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/bin /app/bin
COPY --from=builder /app/config /app/config
COPY --from=builder /app/resumes /app/resumes

ENTRYPOINT ["/app/bin/jobsearch_app"]
```

Build and run:
```bash
docker build -t jobsearch:latest .
docker run --name jobsearch jobsearch:latest --candidate "John Doe"
```
