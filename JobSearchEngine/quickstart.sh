#!/bin/bash
# Quick start script for JobSearchEngine

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   JobSearchEngine Quick Start                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
echo "[1/5] Checking prerequisites..."
command -v cmake >/dev/null 2>&1 || { echo "❌ CMake not found. Please install CMake."; exit 1; }
command -v go >/dev/null 2>&1 || { echo "❌ Go not found. Please install Go 1.21+."; exit 1; }
echo "✓ Prerequisites OK"
echo ""

# Build C++
echo "[2/5] Building C++ component..."
if [ -d "build" ]; then
    rm -rf build
fi
mkdir -p build
cd build
cmake .. >/dev/null 2>&1
make >/dev/null 2>&1
cd ..
echo "✓ C++ build complete"
echo ""

# Build Go
echo "[3/5] Building Go component..."
cd go
go mod download >/dev/null 2>&1
go build -o ../bin/jobsearch_app ./cmd/jobsearch >/dev/null 2>&1
cd ..
echo "✓ Go build complete"
echo ""

# Verify executables
echo "[4/5] Verifying executables..."
[ -f "bin/jobsearch_engine" ] || { echo "❌ C++ engine not found"; exit 1; }
[ -f "bin/jobsearch_app" ] || { echo "❌ Go app not found"; exit 1; }
echo "✓ Executables verified"
echo ""

# Run test
echo "[5/5] Running test search (john_doe)..."
if [ ! -f "resumes/john_doe.txt" ]; then
    echo "⚠️  Resume file not found: resumes/john_doe.txt"
    echo "   Please add a resume file and try again"
    exit 1
fi

# Run with 1-minute timeout for quick test
timeout 10s ./bin/jobsearch_app --candidate "John Doe" --config config/config.yaml || true
echo ""
echo "✓ Test run completed"
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    Setup Complete! 🎉                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Add your resume to: resumes/your_name.txt"
echo "  2. Edit config: config/config.yaml"
echo "  3. Run: ./bin/jobsearch_app --candidate 'Your Name'"
echo ""
echo "Documentation:"
echo "  - Architecture: cat ARCHITECTURE.md"
echo "  - Build Help:  cat BUILD.md"
echo "  - Deployment:  cat DEPLOYMENT.md"
echo ""
