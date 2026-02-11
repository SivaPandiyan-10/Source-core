cmake_minimum_required(VERSION 3.15)
project(personal_ai)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(${CMAKE_SOURCE_DIR}/include)

add_executable(personal_ai
  src/main.cpp
  src/CoreEngine.cpp
  src/StubLLM.cpp
  src/MemoryManager.cpp
  src/StubEmbedding.cpp
  src/DB.cpp
  src/FinancialModule.cpp
  src/VectorStore.cpp
  src/KnowledgeStore.cpp
  src/EmbeddingHttpClient.cpp
  src/OllamaClient.cpp
)

find_package(SQLite3 REQUIRED)
target_link_libraries(personal_ai PRIVATE SQLite::SQLite3)
find_package(CURL REQUIRED)
target_link_libraries(personal_ai PRIVATE CURL::libcurl)
find_library(SODIUM_LIB sodium)
if (SODIUM_LIB)
  target_link_libraries(personal_ai PRIVATE ${SODIUM_LIB})
endif()

install(TARGETS personal_ai RUNTIME DESTINATION bin)
