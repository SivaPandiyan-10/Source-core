import asyncio
import json
from typing import List, Dict, Any, Optional
import httpx
import sqlite3
from faiss_index import get_default_index
from llm.ollama_client import async_stream_generate
from ingest.chunker import chunk_text
import os

EMBED_URL = os.getenv('EMBED_SERVICE_URL', 'http://embed:8100')
DB_PATH = os.getenv('DB_PATH', 'data/personalai.db')


def hybrid_rerank(similarities: List[float], metas: List[Dict[str, Any]]) -> List[float]:
    # Simple linear combination: similarity + recency_score * 0.1 + source_weight * 0.1
    scores = []
    for sim, meta in zip(similarities, metas):
        rec = meta.get('recency_score') or 0.0
        sw = meta.get('source_weight') or 0.0
        scores.append(sim + 0.1 * rec + 0.1 * sw)
    return scores


def build_prompt(retrieved: List[Dict[str, Any]], user_query: str) -> str:
    system = "You are a helpful assistant. Use the provided context to answer accurately."
    ctx = []
    for r in retrieved:
        m = r.get('meta') or {}
        txt = m.get('text') or m.get('excerpt') or m.get('content') or m.get('summary') or ''
        ctx.append(f"Source: {m.get('filename','unknown')}, Content: {txt[:800]}")
    context_block = '\n\n'.join(ctx)
    prompt = f"{system}\n\nContext:\n{context_block}\n\nUser: {user_query}\nAssistant:"
    return prompt


async def retrieve_for_query(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    # call embedding service
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{EMBED_URL}/embed", json={"texts": [query]})
        r.raise_for_status()
        resp = r.json()
    vec = resp['vectors'][0]
    import numpy as np
    idx = get_default_index(dim=len(vec))
    dists, idxs = idx.search(np.array(vec, dtype='float32'), top_k)

    # map offsets to metadata
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    results = []
    for offset, score in zip(idxs, dists):
        if offset < 0:
            continue
        cur.execute('SELECT metadata_json FROM embeddings_meta WHERE vector_offset = ?', (offset,))
        row = cur.fetchone()
        meta = json.loads(row[0]) if row and row[0] else {}
        results.append({'offset': int(offset), 'score': float(score), 'meta': meta})
    conn.close()
    return results


async def handle_ws_stream(ws, session_id: str, user: Dict[str, Any], model: Optional[str] = None):
    # Receive a single message (user query) and stream back tokens
    data = await ws.receive_text()
    query = data
    retrieved = await retrieve_for_query(query, top_k=6)
    # prepare meta list for reranking
    metas = [r['meta'] for r in retrieved]
    sims = [r['score'] for r in retrieved]
    scores = hybrid_rerank(sims, metas)
    # sort by hybrid score
    combined = sorted(zip(retrieved, scores), key=lambda x: x[1], reverse=True)
    retrieved_sorted = [c[0] for c in combined]
    prompt = build_prompt(retrieved_sorted, query)

    # stream tokens from LLM
    async for chunk in async_stream_generate(prompt, model=model):
        await ws.send_text(chunk)
