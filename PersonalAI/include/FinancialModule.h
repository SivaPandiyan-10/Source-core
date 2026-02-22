#pragma once

#include <string>

// Minimal financial module API (storage + analytics hooks)
class FinancialModule {
public:
    FinancialModule();
    ~FinancialModule();

    void recordSalary(const std::string &date, double amount);
    void recordExpense(const std::string &date, double amount, const std::string &category);

    // Simple reports
    double getMonthlySavingsRate(const std::string &month) const;
    std::string summary() const;
private:
    struct Impl;
    Impl *impl_;
};
