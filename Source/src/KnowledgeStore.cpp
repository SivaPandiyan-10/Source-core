#include "KnowledgeStore.h"
#include "EmbeddingService.h"
#include "VectorStore.h"
#include <sqlite3.h>
#include <sstream>
#include <iostream>

struct KnowledgeStore::Impl {
    EmbeddingService *embed = nullptr;
    VectorStore *vstore = nullptr;
    sqlite3 *db = nullptr;
    Impl(EmbeddingService *e, VectorStore *v) : embed(e), vstore(v) {
        if (sqlite3_open("personal_ai.db", &db) != SQLITE_OK) db = nullptr;
        const char *sql = R"SQL(
CREATE TABLE IF NOT EXISTS knowledge (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tag TEXT,
  content TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
)SQL";
        char *err = nullptr;
        if (db) sqlite3_exec(db, sql, nullptr, nullptr, &err);
        if (err) sqlite3_free(err);
    }
    ~Impl() { if (db) sqlite3_close(db); }
};

KnowledgeStore::KnowledgeStore(EmbeddingService *embedSvc, VectorStore *vstore) : impl_(new Impl(embedSvc, vstore)) {}
KnowledgeStore::~KnowledgeStore() { delete impl_; }

int KnowledgeStore::addKnowledge(const std::string &tag, const std::string &content) {
    if (!impl_ || !impl_->db) return -1;
    sqlite3_stmt *stmt = nullptr;
    const char *sql = "INSERT INTO knowledge(tag, content) VALUES(?,?)";
    if (sqlite3_prepare_v2(impl_->db, sql, -1, &stmt, nullptr) != SQLITE_OK) return -1;
    sqlite3_bind_text(stmt, 1, tag.c_str(), -1, SQLITE_TRANSIENT);
    // encrypt content at rest
    std::string enc = EncryptionUtil::encrypt(content);
    sqlite3_bind_text(stmt, 2, enc.c_str(), -1, SQLITE_TRANSIENT);
    if (sqlite3_step(stmt) != SQLITE_DONE) {
        sqlite3_finalize(stmt);
        return -1;
    }
    sqlite3_finalize(stmt);
    int id = (int)sqlite3_last_insert_rowid(impl_->db);
    // generate embedding and store in vector store
    if (impl_->embed && impl_->vstore) {
        auto vec = impl_->embed->embed(content);
        impl_->vstore->upsertVector(id, vec, tag);
    }
    return id;
}

bool KnowledgeStore::updateKnowledge(int id, const std::string &tag, const std::string &content) {
    if (!impl_ || !impl_->db) return false;
    sqlite3_stmt *stmt = nullptr;
    const char *sql = "UPDATE knowledge SET tag = ?, content = ? WHERE id = ?";
    if (sqlite3_prepare_v2(impl_->db, sql, -1, &stmt, nullptr) != SQLITE_OK) return false;
    sqlite3_bind_text(stmt, 1, tag.c_str(), -1, SQLITE_TRANSIENT);
    std::string enc = EncryptionUtil::encrypt(content);
    sqlite3_bind_text(stmt, 2, enc.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_int(stmt, 3, id);
    bool ok = (sqlite3_step(stmt) == SQLITE_DONE);
    sqlite3_finalize(stmt);
    if (ok && impl_->embed && impl_->vstore) {
        auto vec = impl_->embed->embed(content);
        impl_->vstore->upsertVector(id, vec, tag);
    }
    return ok;
}

bool KnowledgeStore::deleteKnowledge(int id) {
    if (!impl_ || !impl_->db) return false;
    sqlite3_stmt *stmt = nullptr;
    const char *sql = "DELETE FROM knowledge WHERE id = ?";
    if (sqlite3_prepare_v2(impl_->db, sql, -1, &stmt, nullptr) != SQLITE_OK) return false;
    sqlite3_bind_int(stmt, 1, id);
    bool ok = (sqlite3_step(stmt) == SQLITE_DONE);
    sqlite3_finalize(stmt);
    return ok;
}

std::vector<std::pair<int, std::string>> KnowledgeStore::searchByTag(const std::string &tag) {
    std::vector<std::pair<int, std::string>> out;
    if (!impl_ || !impl_->db) return out;
    sqlite3_stmt *stmt = nullptr;
    const char *sql = "SELECT id, content FROM knowledge WHERE tag LIKE ?";
    if (sqlite3_prepare_v2(impl_->db, sql, -1, &stmt, nullptr) != SQLITE_OK) return out;
    std::string like = "%" + tag + "%";
    sqlite3_bind_text(stmt, 1, like.c_str(), -1, SQLITE_TRANSIENT);
    while (sqlite3_step(stmt) == SQLITE_ROW) {
        int id = sqlite3_column_int(stmt, 0);
        const unsigned char *ct = sqlite3_column_text(stmt, 1);
        std::string enc = ct ? reinterpret_cast<const char*>(ct) : "";
        std::string content = EncryptionUtil::decrypt(enc);
        out.emplace_back(id, content);
    }
    sqlite3_finalize(stmt);
    return out;
}

std::vector<std::tuple<int, std::string, float>> KnowledgeStore::retrieveRelevant(const std::string &query, int k) {
    std::vector<std::tuple<int, std::string, float>> out;
    if (!impl_ || !impl_->embed || !impl_->vstore || !impl_->db) return out;
    auto qvec = impl_->embed->embed(query);
    auto results = impl_->vstore->query(qvec, k);
    // fetch content for each id
    sqlite3_stmt *stmt = nullptr;
    const char *sql = "SELECT content FROM knowledge WHERE id = ?";
    if (sqlite3_prepare_v2(impl_->db, sql, -1, &stmt, nullptr) != SQLITE_OK) return out;
    for (auto &p : results) {
        int id = p.first;
        float score = p.second;
        sqlite3_reset(stmt);
        sqlite3_bind_int(stmt, 1, id);
        if (sqlite3_step(stmt) == SQLITE_ROW) {
            const unsigned char *ct = sqlite3_column_text(stmt, 0);
            std::string enc = ct ? reinterpret_cast<const char*>(ct) : "";
            std::string content = EncryptionUtil::decrypt(enc);
            out.emplace_back(id, content, score);
        }
    }
    sqlite3_finalize(stmt);
    return out;
}
