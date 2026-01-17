@echo off
REM Quick start script for JobSearchEngine on Windows

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                   JobSearchEngine Quick Start                   ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Check prerequisites
echo [1/5] Checking prerequisites...
where cmake >nul 2>&1
if errorlevel 1 (
    echo ❌ CMake not found. Please install CMake.
    exit /b 1
)
where go >nul 2>&1
if errorlevel 1 (
    echo ❌ Go not found. Please install Go 1.21+.
    exit /b 1
)
echo ✓ Prerequisites OK
echo.

REM Build C++
echo [2/5] Building C++ component...
if exist "build" rmdir /s /q build
mkdir build
cd build
cmake .. >nul 2>&1
cmake --build . --config Release >nul 2>&1
cd ..
if errorlevel 1 (
    echo ❌ C++ build failed
    exit /b 1
)
echo ✓ C++ build complete
echo.

REM Build Go
echo [3/5] Building Go component...
cd go
call go mod download >nul 2>&1
call go build -o ..\bin\jobsearch_app.exe .\cmd\jobsearch >nul 2>&1
cd ..
if errorlevel 1 (
    echo ❌ Go build failed
    exit /b 1
)
echo ✓ Go build complete
echo.

REM Verify executables
echo [4/5] Verifying executables...
if not exist "bin\jobsearch_engine.exe" (
    echo ❌ C++ engine not found
    exit /b 1
)
if not exist "bin\jobsearch_app.exe" (
    echo ❌ Go app not found
    exit /b 1
)
echo ✓ Executables verified
echo.

REM Check resume
echo [5/5] Checking resume file...
if not exist "resumes\john_doe.txt" (
    echo ⚠️  Resume file not found: resumes\john_doe.txt
    echo    Please add a resume file and try again
    exit /b 1
)
echo ✓ Resume file found
echo.

echo ╔════════════════════════════════════════════════════════════════╗
echo ║                    Setup Complete! 🎉                           ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo Next steps:
echo   1. Add your resume to: resumes\your_name.txt
echo   2. Edit config: config\config.yaml
echo   3. Run: .\bin\jobsearch_app.exe --candidate "Your Name"
echo.
echo Documentation:
echo   - Architecture: type ARCHITECTURE.md
echo   - Build Help:  type BUILD.md
echo   - Deployment:  type DEPLOYMENT.md
echo.
