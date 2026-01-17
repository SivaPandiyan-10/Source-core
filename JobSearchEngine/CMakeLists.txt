cmake_minimum_required(VERSION 3.15)
project(JobSearchEngine VERSION 1.0.0 LANGUAGES CXX)

# C++ Standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wpedantic")

# Output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# Source files for main executable
set(SOURCES
    cpp/src/main.cpp
    cpp/src/resume_parser.cpp
    cpp/src/matcher.cpp
    cpp/src/ipc_handler.cpp
)

# Create main executable
add_executable(jobsearch_engine ${SOURCES})

# Optional: Add support for C++17 features
target_compile_features(jobsearch_engine PRIVATE cxx_std_17)

# Optional: Link against nlohmann/json if available
# find_package(nlohmann_json 3.2.0 QUIET)
# if(nlohmann_json_FOUND)
#     target_link_libraries(jobsearch_engine PRIVATE nlohmann_json::nlohmann_json)
# endif()

# Enable testing
enable_testing()

# Test executable (optional)
# add_executable(test_runner
#     cpp/tests/test_parser.cpp
#     cpp/src/resume_parser.cpp
#     cpp/src/matcher.cpp
#     cpp/src/ipc_handler.cpp
# )
# add_test(NAME Tests COMMAND test_runner)

# Installation
install(TARGETS jobsearch_engine DESTINATION bin)
