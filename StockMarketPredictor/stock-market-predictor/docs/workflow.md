# Workflow

## Daily Data Pipeline

| Time     | Task                        |
|----------|-----------------------------|
| 12:00 PM | Fetch latest stock data     |
| 12:05 PM | Generate technical indicators |
| 12:10 PM | Prepare ML dataset          |
| 12:15 PM | Train XGBoost model         |
| 12:20 PM | Generate predictions        |
| 12:25 PM | Store predictions in DB     |
| 12:30 PM | Update Redis cache          |

## Steps

1. **Fetch Data**: Download latest OHLCV for all stocks from Yahoo Finance API.
2. **Feature Engineering**: Compute RSI, MACD, SMA, EMA, momentum, volatility, volume change.
3. **Prepare Dataset**: Format data for ML model.
4. **Train Model**: XGBoost classifier predicts next-day up probability.
5. **Predict**: Generate probability_up, expected_return, confidence for each stock.
6. **Store**: Save predictions to PostgreSQL.
7. **Cache**: Update Redis for fast frontend access.

---
