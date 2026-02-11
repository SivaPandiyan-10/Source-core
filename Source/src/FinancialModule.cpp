#include "FinancialModule.h"
#include "DB.h"
#include <sstream>
#include <iomanip>
#include <cmath>
#include "EncryptionUtil.h"

struct FinancialModule::Impl {
    Impl() : db("personal_ai.db") { db.initializeSchema(); }
    DB db;
};

FinancialModule::FinancialModule() : impl_(new Impl()) {}
FinancialModule::~FinancialModule() { delete impl_; }

void FinancialModule::recordSalary(const std::string &date, double amount) {
    // use prepared statement via DB wrapper (direct sqlite here)
    sqlite3 *db = nullptr;
    if (sqlite3_open("personal_ai.db", &db) != SQLITE_OK) return;
    const char *sql = "INSERT INTO salaries(date, amount) VALUES(?,?)";
    sqlite3_stmt *stmt = nullptr;
    if (sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr) == SQLITE_OK) {
        sqlite3_bind_text(stmt, 1, date.c_str(), -1, SQLITE_TRANSIENT);
        sqlite3_bind_double(stmt, 2, amount);
        sqlite3_step(stmt);
        sqlite3_finalize(stmt);
    }
    sqlite3_close(db);
}

void FinancialModule::recordExpense(const std::string &date, double amount, const std::string &category) {
    sqlite3 *db = nullptr;
    if (sqlite3_open("personal_ai.db", &db) != SQLITE_OK) return;
    const char *sql = "INSERT INTO expenses(date, amount, category) VALUES(?,?,?)";
    sqlite3_stmt *stmt = nullptr;
    std::string encryptedCategory = EncryptionUtil::encrypt(category);
    if (sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr) == SQLITE_OK) {
        sqlite3_bind_text(stmt, 1, date.c_str(), -1, SQLITE_TRANSIENT);
        sqlite3_bind_double(stmt, 2, amount);
        sqlite3_bind_text(stmt, 3, encryptedCategory.c_str(), -1, SQLITE_TRANSIENT);
        sqlite3_step(stmt);
        sqlite3_finalize(stmt);
    }
    sqlite3_close(db);
}

double FinancialModule::getMonthlySavingsRate(const std::string &month) const {
    // month in YYYY-MM
    double totalSalary = 0.0;
    double totalExpense = 0.0;
    sqlite3 *db = nullptr;
    // quick direct sqlite calls for read queries
    if (sqlite3_open("personal_ai.db", &db) != SQLITE_OK) return 0.0;

    std::string q1 = "SELECT SUM(amount) FROM salaries WHERE date LIKE '" + month + "%' ";
    sqlite3_stmt *stmt = nullptr;
    if (sqlite3_prepare_v2(db, q1.c_str(), -1, &stmt, nullptr) == SQLITE_OK) {
        if (sqlite3_step(stmt) == SQLITE_ROW) totalSalary = sqlite3_column_double(stmt, 0);
        sqlite3_finalize(stmt);
    }

    std::string q2 = "SELECT SUM(amount) FROM expenses WHERE date LIKE '" + month + "%' ";
    if (sqlite3_prepare_v2(db, q2.c_str(), -1, &stmt, nullptr) == SQLITE_OK) {
        if (sqlite3_step(stmt) == SQLITE_ROW) totalExpense = sqlite3_column_double(stmt, 0);
        sqlite3_finalize(stmt);
    }

    sqlite3_close(db);
    if (totalSalary <= 0.0) return 0.0;
    double savings = totalSalary - totalExpense;
    return (savings / totalSalary) * 100.0;
}

std::string FinancialModule::summary() const {
    std::ostringstream out;
    out << "Financial Summary:\n";
    // Simple: report last month savings rate
    // get YYYY-MM of current (naive)
    out << "(Use getMonthlySavingsRate(\"YYYY-MM\") for specific months)";
    return out.str();
}
