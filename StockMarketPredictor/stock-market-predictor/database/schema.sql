CREATE TABLE IF NOT EXISTS stocks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(16) UNIQUE NOT NULL,
    name VARCHAR(128),
    sector VARCHAR(64),
    exchange VARCHAR(32)
);

CREATE TABLE IF NOT EXISTS stock_prices (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id),
    date DATE NOT NULL,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume FLOAT,
    UNIQUE(stock_id, date)
);

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id),
    prediction_date DATE NOT NULL,
    probability_up FLOAT,
    expected_return FLOAT,
    confidence FLOAT,
    UNIQUE(stock_id, prediction_date)
);

CREATE INDEX IF NOT EXISTS idx_stock_prices_stock_id_date ON stock_prices(stock_id, date);
CREATE INDEX IF NOT EXISTS idx_predictions_stock_id_date ON predictions(stock_id, prediction_date);
