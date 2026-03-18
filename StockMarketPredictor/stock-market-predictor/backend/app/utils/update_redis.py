import redis
import psycopg2
import os
import json

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/stockdb")

r = redis.Redis.from_url(REDIS_URL)
conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

cursor.execute("SELECT s.symbol, p.probability_up, p.expected_return, p.confidence, sp.volume FROM predictions p JOIN stocks s ON p.stock_id = s.id JOIN stock_prices sp ON sp.stock_id = s.id AND sp.date = p.prediction_date;")
rows = cursor.fetchall()

for row in rows:
    symbol, probability_up, expected_return, confidence, volume = row
    r.set(f"prediction:{symbol}", json.dumps({
        "probability_up": probability_up,
        "expected_return": expected_return,
        "confidence": confidence,
        "volume": volume
    }))

print("Redis cache updated.")
