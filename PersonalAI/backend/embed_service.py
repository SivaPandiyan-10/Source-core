from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np

app = FastAPI(title='Embedding Microservice')


class EmbReq(BaseModel):
    texts: List[str]
    model: str = 'all-MiniLM-L6-v2'


@app.on_event('startup')
def load_model():
    global _model
    _model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


@app.post('/embed')
def embed(req: EmbReq):
    if not req.texts:
        raise HTTPException(status_code=400, detail='no texts provided')
    vectors = _model.encode(req.texts, show_progress_bar=False, convert_to_numpy=True)
    # Convert to list for JSON serializable
    return {"model": req.model, "dim": vectors.shape[1], "vectors": vectors.tolist()}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('embed_service:app', host='0.0.0.0', port=8100)
