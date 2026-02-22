# Build and Run (beta)

This document explains how to build and run the `personal_ai` project on Windows.

Prerequisites
- Install CMake (>= 3.15) and make it available on PATH: https://cmake.org/download/
- Install a C++ toolchain:
  - Option A (recommended): Visual Studio 2022 (Desktop development with C++)
  - Option B: MSYS2/MinGW or other compatible compiler
- Install SQLite3 development files (usually provided with your toolchain). On Windows with Visual Studio, CMake will find SQLite3 if you have a dev package; otherwise install SQLite3 and set `SQLite3_DIR`.
- Install libcurl development libs (CURL). On Windows, installing curl or using vcpkg is recommended.
- Optionally install libsodium if you want encryption features.

Quick build steps (recommended, generator auto-selected)
1. Open a Developer PowerShell for Visual Studio (if using VS). Otherwise ensure your toolchain is on PATH.
2. From the repository root run:

```powershell
cmake -S Source -B build
cmake --build build --config Release
```

3. If the build succeeds, the executable will be in:

- `build/Release/personal_ai.exe` (Visual Studio generator)
- or `build/personal_ai.exe` (single-config generators)

Run
- From PowerShell or Cmd:

```powershell
# optional: point to an Ollama server, otherwise the stub LLM is used
$env:OLLAMA_URL = "http://localhost:11434"
# run the binary
.
# Example Windows path if using default VS config
build\Release\personal_ai.exe
```

Packaging a beta release
1. Create a folder for the beta and copy the exe and required runtime DLLs (Visual C++ runtime) into it.
2. Zip the folder and name it `personal_ai-beta-v0.1.zip`.

Debugging common issues
- "cmake: command not found": install CMake and re-open your terminal.
- Missing SQLite3/CURL: install the development packages or use vcpkg and pass `-DCMAKE_TOOLCHAIN_FILE=path\to\vcpkg.cmake` to `cmake`.
- Linker errors about missing libraries: install corresponding dev libs and ensure CMake finds them.

Notes
- This repository uses CMake and expects C++17.
- If you want I can: 
  - attempt a build here after you confirm CMake is installed, or
  - add a `vcpkg.json` and CMake integration to make dependency setup easier, or
  - produce a ZIP beta inside the repo after a successful local build.

Contact me which of the above you'd like me to do next and I will continue.