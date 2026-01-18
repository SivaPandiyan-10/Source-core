cmake_minimum_required(VERSION 3.10)
project(JobSearchEngine)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Enable testing
enable_testing()

# Add include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/cpp/include)

# Source files for the C++ server
set(SERVER_SOURCES
    cpp/src/main.cpp
    cpp/src/message_protocol.cpp
    cpp/src/tcp_server.cpp
    cpp/src/matcher.cpp
    cpp/src/resume_parser.cpp
)

# Create executable
add_executable(job_matching_engine ${SERVER_SOURCES})

# Platform-specific libraries
if(WIN32)
    target_link_libraries(job_matching_engine ws2_32)
elseif(UNIX)
    target_link_libraries(job_matching_engine pthread)
endif()

# Required: nlohmann/json header-only library
# Download from: https://github.com/nlohmann/json/releases
# Place in cpp/include/nlohmann/

# Check if nlohmann/json is available
if(NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/cpp/include/nlohmann/json.hpp")
    message(WARNING "nlohmann/json not found. Please download and place it in cpp/include/nlohmann/")
endif()

# Compiler flags for better warnings and optimization
if(MSVC)
    target_compile_options(job_matching_engine PRIVATE /W4 /O2)
else()
    target_compile_options(job_matching_engine PRIVATE -Wall -Wextra -O2)
endif()

# Installation
install(TARGETS job_matching_engine DESTINATION bin)

# Print summary
message(STATUS "====================================")
message(STATUS "JobSearchEngine - C++ Server Build")
message(STATUS "====================================")
message(STATUS "Target: job_matching_engine")
message(STATUS "C++ Standard: C++17")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
if(WIN32)
    message(STATUS "Platform: Windows")
elseif(UNIX)
    message(STATUS "Platform: Unix/Linux")
endif()
message(STATUS "====================================")
