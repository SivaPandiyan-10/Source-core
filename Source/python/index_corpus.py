"""
Index text files in a directory: chunk, embed via embedding service, and insert into SQLite tables `knowledge` and `embeddings`.

Usage:
 python python/index_corpus.py --dir data/sample_docs --endpoint http://127.0.0.1:8000/embed --db personal_ai.db
"""
import os
import sqlite3
import argparse
import requests
from chunker import chunk_text

def ensure_tables(db):
    cur = db.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS knowledge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tag TEXT,
        content TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS embeddings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        knowledge_id INTEGER,
        vector_text TEXT,
        metadata TEXT
    )''')
    db.commit()

def embed_text(endpoint, text):
    r = requests.post(endpoint, json={"text": text}, timeout=30)
    r.raise_for_status()
    j = r.json()
    return j.get('embedding', [])

def vec_to_csv(v):
    return ','.join(str(x) for x in v)

def index_dir(args):
    db = sqlite3.connect(args.db)
    ensure_tables(db)
    for fname in os.listdir(args.dir):
        path = os.path.join(args.dir, fname)
        if not os.path.isfile(path): continue
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        chunks = chunk_text(text, args.chunk_words, args.overlap)
        for i,ch in enumerate(chunks):
            tag = f"{fname}::chunk{i}"
            cur = db.cursor()
            cur.execute("INSERT INTO knowledge(tag, content) VALUES(?,?)", (tag, ch))
            kid = cur.lastrowid
            emb = embed_text(args.endpoint, ch)
            if emb:
                cur.execute("INSERT INTO embeddings(knowledge_id, vector_text, metadata) VALUES(?,?,?)",
                            (kid, vec_to_csv(emb), fname))
            db.commit()
            print(f"Indexed {tag} (vec_len={len(emb)})")

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--dir', required=True)
    p.add_argument('--endpoint', default='http://127.0.0.1:8000/embed')
    p.add_argument('--db', default='personal_ai.db')
    p.add_argument('--chunk-words', type=int, dest='chunk_words', default=200)
    p.add_argument('--overlap', type=int, default=50)
    args = p.parse_args()
    index_dir(args)
