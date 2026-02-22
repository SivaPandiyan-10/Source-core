import faiss
import numpy as np
import os
import threading

_lock = threading.Lock()

class FaissIndex:
    def __init__(self, dim: int = 1536, index_path: str = 'data/faiss.index'):
        self.dim = dim
        self.index_path = index_path
        self._ensure_dir()
        self._load_or_create()

    def _ensure_dir(self):
        d = os.path.dirname(self.index_path)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)

    def _load_or_create(self):
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                return
            except Exception:
                pass
        # use IndexFlatIP with normalized vectors for cosine
        self.index = faiss.IndexFlatIP(self.dim)

    def _persist(self):
        faiss.write_index(self.index, self.index_path)

    def add(self, vectors: np.ndarray):
        # vectors shape: (N, dim)
        assert vectors.ndim == 2 and vectors.shape[1] == self.dim
        with _lock:
            # normalize for cosine similarity
            faiss.normalize_L2(vectors)
            # If index supports ntotal, record start offset
            try:
                start = int(self.index.ntotal)
            except Exception:
                start = 0
            self.index.add(vectors)
            self._persist()
            # return list of offsets for the added vectors
            return list(range(start, start + vectors.shape[0]))

    def search(self, query_vec: np.ndarray, top_k: int = 5):
        # query_vec shape: (dim,) or (1, dim)
        q = np.array(query_vec, dtype='float32')
        if q.ndim == 1:
            q = q.reshape(1, -1)
        faiss.normalize_L2(q)
        with _lock:
            distances, indices = self.index.search(q, top_k)
        return distances[0].tolist(), indices[0].tolist()


_default_index = None

def get_default_index(dim=1536):
    global _default_index
    if _default_index is None:
        _default_index = FaissIndex(dim=dim)
    return _default_index
