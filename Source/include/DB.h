#pragma once

#include <string>
#include <sqlite3.h>

class DB {
public:
    explicit DB(const std::string &path);
    ~DB();

    bool exec(const std::string &sql, std::string *err = nullptr);
    bool initializeSchema();

private:
    sqlite3 *db_ = nullptr;
};
