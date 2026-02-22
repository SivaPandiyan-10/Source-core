import sqlite3
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext

DB_PATH = os.getenv('DB_PATH', 'data/personalai.db')
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _ensure_db():
    d = os.path.dirname(DB_PATH)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def create_user(email: str, password: str):
    _ensure_db()
    h = pwd_context.hash(password)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO users(email, pw_hash, created_at) VALUES (?, ?, ?)', (email, h, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def verify_user(email: str, password: str) -> bool:
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT pw_hash FROM users WHERE email = ?', (email,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    return pwd_context.verify(password, row[0])


def store_refresh_token(token: str, email: str, expires_minutes: int = 7 * 24 * 60):
    _ensure_db()
    issued = datetime.utcnow()
    expires = issued + timedelta(minutes=expires_minutes)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT OR REPLACE INTO refresh_tokens(token, user_email, issued_at, expires_at) VALUES (?, ?, ?, ?)',
                (token, email, issued.isoformat(), expires.isoformat()))
    conn.commit()
    conn.close()


def validate_refresh_token(token: str) -> bool:
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT expires_at FROM refresh_tokens WHERE token = ?', (token,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    expires = datetime.fromisoformat(row[0])
    return datetime.utcnow() < expires
