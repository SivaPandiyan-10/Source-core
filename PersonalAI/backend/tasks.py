import sqlite3
import os
import json
import requests
import numpy as np
from ingest.chunker import chunk_text
from faiss_index import get_default_index

DB_PATH = os.getenv('DB_PATH', 'data/personalai.db')
EMBED_URL = os.getenv('EMBED_SERVICE_URL', 'http://embed:8100')


def _ensure_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys=ON')
    conn.commit()
    conn.close()


def process_ingest(file_bytes: bytes, filename: str, owner_id: str):
    """Background job: extract text, chunk, embed, and upsert vectors into FAISS and metadata table."""
    _ensure_db()
    text = None
    try:
        text = file_bytes.decode('utf-8')
    except Exception:
        # fallback: treat as binary and skip
        text = ''

    chunks = chunk_text(text, chunk_size=500, overlap=100)
    texts = [c[2] for c in chunks if c[2].strip()]
    if not texts:
        return {'status': 'empty'}

    # call embedding service in batches
    r = requests.post(f"{EMBED_URL}/embed", json={"texts": texts})
    r.raise_for_status()
    resp = r.json()
    vectors = resp['vectors']
    dim = resp['dim']
    arr = np.array(vectors, dtype='float32')

    # upsert into FAISS and capture offsets
    idx = get_default_index(dim=dim)
    offsets = idx.add(arr)

    # write metadata rows into embeddings_meta (append) with vector_offset
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for i, chunk in enumerate(chunks):
        meta = {'filename': filename, 'chunk_index': chunk[0], 'owner': owner_id}
        vector_id = f"{filename}-{i}"
        vector_offset = offsets[i] if i < len(offsets) else None
        cur.execute('INSERT OR REPLACE INTO embeddings_meta(vector_id, chunk_id, tenant_id, model, dim, source, vector_offset, metadata_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    (vector_id, None, None, resp.get('model', ''), dim, 'upload', vector_offset, json.dumps(meta)))
    conn.commit()
    conn.close()
    return {'status': 'ok', 'chunks': len(texts)}
