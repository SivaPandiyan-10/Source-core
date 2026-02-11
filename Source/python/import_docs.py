"""
Import PDF/DOCX/MD files from a directory, extract text, chunk and index using embedding service.
Usage: python python/import_docs.py --dir data/docs --endpoint http://127.0.0.1:8000/embed
"""
import os
import argparse
import sqlite3
import requests
from chunker import chunk_text

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

try:
    import docx
except Exception:
    docx = None

def extract_text(path):
    if path.lower().endswith('.pdf') and PdfReader:
        reader = PdfReader(path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text
    if path.lower().endswith('.docx') and docx:
        d = docx.Document(path)
        return '\n'.join(p.text for p in d.paragraphs)
    # fallback for txt/md
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def embed_text(endpoint, text):
    r = requests.post(endpoint, json={"text": text}, timeout=30)
    r.raise_for_status()
    return r.json().get('embedding', [])

def index_file(db, endpoint, path, chunk_words, overlap):
    text = extract_text(path)
    chunks = chunk_text(text, chunk_words, overlap)
    cur = db.cursor()
    for i,ch in enumerate(chunks):
        tag = f"{os.path.basename(path)}::chunk{i}"
        cur.execute("INSERT INTO knowledge(tag, content) VALUES(?,?)", (tag, ch))
        kid = cur.lastrowid
        emb = embed_text(endpoint, ch)
        if emb:
            cur.execute("INSERT INTO embeddings(knowledge_id, vector_text, metadata) VALUES(?,?,?)", (kid, ','.join(map(str,emb)), os.path.basename(path)))
    db.commit()

def main(args):
    db = sqlite3.connect(args.db)
    for fname in os.listdir(args.dir):
        path = os.path.join(args.dir, fname)
        if not os.path.isfile(path): continue
        print('Indexing', path)
        index_file(db, args.endpoint, path, args.chunk_words, args.overlap)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--dir', required=True)
    p.add_argument('--endpoint', default='http://127.0.0.1:8000/embed')
    p.add_argument('--db', default='personal_ai.db')
    p.add_argument('--chunk-words', type=int, dest='chunk_words', default=200)
    p.add_argument('--overlap', type=int, default=50)
    args = p.parse_args()
    main(args)
