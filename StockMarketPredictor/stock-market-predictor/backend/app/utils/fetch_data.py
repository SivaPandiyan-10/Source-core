import yfinance as yf
import pandas as pd
import psycopg2
import os
from datetime import datetime, timedelta

STOCK_LIST = ["AAPL", "MSFT", "GOOGL"]  # Replace with 5000+ symbols in production

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/stockdb")

conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

def fetch_and_store(symbol):
    end = datetime.now()
    start = end - timedelta(days=180)
    df = yf.download(symbol, start=start, end=end)
    for idx, row in df.iterrows():
        cursor.execute("""
            INSERT INTO stock_prices (stock_id, date, open, high, low, close, volume)
            VALUES ((SELECT id FROM stocks WHERE symbol=%s), %s, %s, %s, %s, %s, %s)
            ON CONFLICT (stock_id, date) DO UPDATE SET open=EXCLUDED.open, high=EXCLUDED.high, low=EXCLUDED.low, close=EXCLUDED.close, volume=EXCLUDED.volume;
        """, (symbol, idx.date(), row['Open'], row['High'], row['Low'], row['Close'], row['Volume']))
    conn.commit()

def main():
    for symbol in STOCK_LIST:
        fetch_and_store(symbol)
    print("Stock data updated.")

if __name__ == "__main__":
    main()
