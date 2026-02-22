"""
Minimal embedding microservice to run locally.
Requires: pip install -r requirements.txt

Endpoints:
 - POST /embed {"text": "..."} -> {"embedding": [floats]}

This microservice uses sentence-transformers when available.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np

app = FastAPI()

try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception:
    model = None

class EmbedRequest(BaseModel):
    text: str

class EmbedResponse(BaseModel):
    embedding: list

@app.post('/embed', response_model=EmbedResponse)
def embed(req: EmbedRequest):
    if model is None:
        # fallback: simple char-level embedding
        x = np.zeros(8, dtype=float)
        for i, ch in enumerate(req.text[:8]):
            x[i] = ord(ch) / 255.0
        return {"embedding": x.tolist()}
    emb = model.encode(req.text)
    return {"embedding": emb.tolist()}
