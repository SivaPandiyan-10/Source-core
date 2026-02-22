"""
FAISS service: builds an ANN index from embeddings in `personal_ai.db` and serves query endpoint.
Run: uvicorn python.faiss_service:app --port 9000
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import numpy as np
import faiss
import os

app = FastAPI()
INDEX_PATH = "faiss.index"

class QueryRequest(BaseModel):
    embedding: list
    k: int = 5

def load_embeddings_from_db(dbpath="personal_ai.db"):
    db = sqlite3.connect(dbpath)
    cur = db.cursor()
    cur.execute("SELECT knowledge_id, vector_text FROM embeddings")
    rows = cur.fetchall()
    ids = []
    vecs = []
    for kid, vtxt in rows:
        if not vtxt: continue
        arr = np.fromstring(vtxt, sep=',', dtype=np.float32)
        ids.append(int(kid))
        vecs.append(arr)
    db.close()
    if not vecs:
        return np.zeros((0,)), []
    # pad vectors to same dim
    dim = max(v.size for v in vecs)
    mat = np.zeros((len(vecs), dim), dtype=np.float32)
    for i,v in enumerate(vecs): mat[i, :v.size] = v
    return mat, ids

def build_index(dbpath="personal_ai.db"):
    mat, ids = load_embeddings_from_db(dbpath)
    if mat.shape[0] == 0:
        raise RuntimeError("No embeddings found")
    # normalize for cosine via inner product
    faiss.normalize_L2(mat)
    dim = mat.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(mat)
    faiss.write_index(index, INDEX_PATH)
    # store ids mapping
    with open("faiss_ids.txt", "w") as f:
        for idv in ids: f.write(str(idv) + "\n")
    return len(ids)

def load_index():
    if not os.path.exists(INDEX_PATH):
        raise RuntimeError("Index not found; call /rebuild first")
    index = faiss.read_index(INDEX_PATH)
    ids = []
    with open("faiss_ids.txt", "r") as f:
        for line in f: ids.append(int(line.strip()))
    return index, ids

@app.post("/rebuild")
def rebuild():
    try:
        count = build_index()
        return {"status": "ok", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
def query(req: QueryRequest):
    try:
        q = np.array(req.embedding, dtype=np.float32)
        faiss.normalize_L2(q.reshape(1, -1))
        index, ids = load_index()
        D, I = index.search(q.reshape(1, -1), req.k)
        res = []
        for dist, idx in zip(D[0], I[0]):
            if idx < 0 or idx >= len(ids): continue
            res.append({"knowledge_id": ids[idx], "score": float(dist)})
        return {"results": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
