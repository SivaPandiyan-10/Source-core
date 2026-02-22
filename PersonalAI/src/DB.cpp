#include "DB.h"
#include <fstream>
#include <sstream>
#include <iostream>

DB::DB(const std::string &path) {
    if (sqlite3_open(path.c_str(), &db_) != SQLITE_OK) {
        std::cerr << "Failed to open DB: " << sqlite3_errmsg(db_) << "\n";
        sqlite3_close(db_);
        db_ = nullptr;
    }
}

DB::~DB() {
    if (db_) sqlite3_close(db_);
}

bool DB::exec(const std::string &sql, std::string *err) {
    if (!db_) return false;
    char *errmsg = nullptr;
    int rc = sqlite3_exec(db_, sql.c_str(), nullptr, nullptr, &errmsg);
    if (rc != SQLITE_OK) {
        if (err) *err = errmsg ? errmsg : "unknown";
        sqlite3_free(errmsg);
        return false;
    }
    return true;
}

bool DB::initializeSchema() {
    if (!db_) return false;
    const char *sql = R"SQL(
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS salaries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER REFERENCES users(id),
  date TEXT NOT NULL,
  amount REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS expenses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER REFERENCES users(id),
  date TEXT NOT NULL,
  amount REAL NOT NULL,
  category TEXT
);

)SQL";

    std::string error;
    return exec(sql, &error);
}
