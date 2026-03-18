import pandas as pd
import psycopg2
import os

def get_training_data():
    conn = psycopg2.connect(os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/stockdb"))
    df = pd.read_sql("SELECT * FROM stock_prices", conn)
    conn.close()
    return df

def get_latest_data():
    conn = psycopg2.connect(os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/stockdb"))
    df = pd.read_sql("SELECT * FROM stock_prices ORDER BY date DESC LIMIT 180", conn)
    conn.close()
    return df
