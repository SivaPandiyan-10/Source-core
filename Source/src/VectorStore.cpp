#include "VectorStore.h"
#include <sqlite3.h>
#include <sstream>
#include <iostream>
#include <cmath>

struct VectorStore::Impl {
    sqlite3 *db = nullptr;
    Impl(const std::string &path) {
        if (sqlite3_open(path.c_str(), &db) != SQLITE_OK) {
            std::cerr << "VectorStore: failed to open DB\n";
            db = nullptr;
            return;
        }
        const char *sql = R"SQL(
CREATE TABLE IF NOT EXISTS embeddings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  knowledge_id INTEGER,
  vector_text TEXT,
  metadata TEXT
);
)SQL";
        char *err = nullptr;
        sqlite3_exec(db, sql, nullptr, nullptr, &err);
        if (err) sqlite3_free(err);
    }
    ~Impl() { if (db) sqlite3_close(db); }
};

VectorStore::VectorStore(const std::string &dbpath) : impl_(new Impl(dbpath)) {}
VectorStore::~VectorStore() { delete impl_; }

static std::string vecToCsv(const std::vector<float> &v) {
    std::ostringstream ss;
    for (size_t i = 0; i < v.size(); ++i) {
        if (i) ss << ",";
        ss << v[i];
    }
    return ss.str();
}

static std::vector<float> csvToVec(const std::string &s) {
    std::vector<float> v;
    std::istringstream is(s);
    std::string tok;
    while (std::getline(is, tok, ',')) v.push_back(std::stof(tok));
    return v;
}

bool VectorStore::upsertVector(int knowledgeId, const std::vector<float> &vec, const std::string &metadata) {
    if (!impl_ || !impl_->db) return false;
    std::string csv = vecToCsv(vec);
    sqlite3_stmt *stmt = nullptr;
    const char *sql = "INSERT INTO embeddings(knowledge_id, vector_text, metadata) VALUES(?,?,?)";
    if (sqlite3_prepare_v2(impl_->db, sql, -1, &stmt, nullptr) != SQLITE_OK) return false;
    sqlite3_bind_int(stmt, 1, knowledgeId);
    sqlite3_bind_text(stmt, 2, csv.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 3, metadata.c_str(), -1, SQLITE_TRANSIENT);
    bool ok = (sqlite3_step(stmt) == SQLITE_DONE);
    sqlite3_finalize(stmt);
    return ok;
}

static float cosineSim(const std::vector<float> &a, const std::vector<float> &b) {
    if (a.empty() || b.empty()) return 0.0f;
    float num = 0.0f, da = 0.0f, db = 0.0f;
    size_t n = std::min(a.size(), b.size());
    for (size_t i = 0; i < n; ++i) {
        num += a[i] * b[i];
        da += a[i] * a[i];
        db += b[i] * b[i];
    }
    if (da <= 0.0f || db <= 0.0f) return 0.0f;
    return num / (std::sqrt(da) * std::sqrt(db));
}

std::vector<std::pair<int, float>> VectorStore::query(const std::vector<float> &vec, int k) const {
    std::vector<std::pair<int, float>> results;
    if (!impl_ || !impl_->db) return results;
    const char *sql = "SELECT knowledge_id, vector_text FROM embeddings";
    sqlite3_stmt *stmt = nullptr;
    if (sqlite3_prepare_v2(impl_->db, sql, -1, &stmt, nullptr) != SQLITE_OK) return results;
    while (sqlite3_step(stmt) == SQLITE_ROW) {
        int kid = sqlite3_column_int(stmt, 0);
        const unsigned char *vt = sqlite3_column_text(stmt, 1);
        if (!vt) continue;
        std::string csv(reinterpret_cast<const char*>(vt));
        auto v2 = csvToVec(csv);
        float score = cosineSim(vec, v2);
        results.emplace_back(kid, score);
    }
    sqlite3_finalize(stmt);
    std::sort(results.begin(), results.end(), [](auto &a, auto &b){ return a.second > b.second; });
    if ((int)results.size() > k) results.resize(k);
    return results;
}
