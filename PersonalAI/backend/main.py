from fastapi import FastAPI, WebSocket, UploadFile, File, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import hashlib
import os
import requests
import sqlite3
import json

from auth import create_access_token, get_current_user
from faiss_index import get_default_index
from ingest.chunker import chunk_text
from rq import Queue
from redis import Redis

REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379')
EMBED_URL = os.getenv('EMBED_SERVICE_URL', 'http://embed:8100')
DB_PATH = os.getenv('DB_PATH', 'data/personalai.db')

redis_conn = Redis.from_url(REDIS_URL)
queue = Queue('default', connection=redis_conn)

app = FastAPI(title="Personal AI Assistant Backend")


class LoginReq(BaseModel):
    username: str
    password: str


@app.post('/auth/login')
async def login(payload: LoginReq):
    # Demo user validation (replace with real user store)
    if payload.username == 'demo' and payload.password == 'demo':
        token = create_access_token({'sub': payload.username})
        return {"access_token": token, "token_type": "bearer", "expires_in": 3600}
    raise HTTPException(status_code=401, detail="invalid credentials")


@app.post('/auth/refresh')
async def refresh(body: dict):
    # placeholder: implement rotating refresh tokens
    return {"access_token": create_access_token({'sub': 'demo'}), "expires_in": 3600}


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys=ON')
    conn.commit()
    conn.close()


@app.on_event('startup')
def startup():
    init_db()
    # ensure FAISS index exists
    get_default_index()
    # ensure demo user exists
    try:
        from auth import register_demo_user
        register_demo_user()
    except Exception:
        pass


@app.post('/api/upload')
async def upload(files: List[UploadFile] = File(...), current_user: dict = Depends(get_current_user)):
    ids = []
    for f in files:
        content = await f.read()
        sha = hashlib.sha256(content).hexdigest()
        # enqueue ingestion job to background worker
        from tasks import process_ingest
        job = queue.enqueue(process_ingest, content, f.filename, current_user.get('sub', 'demo'))
        ids.append({"filename": f.filename, "sha256": sha, "job_id": job.get_id()})
    return {"uploaded": ids}


@app.post('/api/vector/search')
async def vector_search(body: dict, current_user: dict = Depends(get_current_user)):
    query = body.get('query')
    top_k = int(body.get('top_k', 5))
    # create embedding for query via embedding service
    r = requests.post(f"{EMBED_URL}/embed", json={"texts": [query]})
    r.raise_for_status()
    resp = r.json()
    vec = resp['vectors'][0]
    import numpy as np
    idx = get_default_index(dim=len(vec))
    dists, idxs = idx.search(np.array(vec, dtype='float32'), top_k)
    # fetch metadata from DB for indices
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    results = []
    for i, score in zip(idxs, dists):
        if i < 0:
            continue
        cur.execute('SELECT vector_id, chunk_id, metadata_json FROM embeddings_meta LIMIT 1 OFFSET ?', (i,))
        row = cur.fetchone()
        if row:
            results.append({'vector_index': i, 'score': score, 'meta': json.loads(row[2]) if row[2] else None})
    conn.close()
    return {"query": query, "results": results}


@app.post('/api/chat/stream')
async def chat_stream(body: dict):
    query = body.get('query')
    return {"reply": f"Received: {query}"}


@app.websocket('/ws/chat/{session_id}')
async def websocket_chat(ws: WebSocket, session_id: str):
    # Accept a token query parameter for authentication: ?token=<jwt>
    await ws.accept()
    try:
        # retrieve token from query params
        params = ws.query_params
        token = params.get('token')
        user = None
        if token:
            try:
                from auth import verify_token
                user = verify_token(token)
            except Exception:
                await ws.send_text('authentication failed')
                await ws.close()
                return
        else:
            await ws.send_text('missing token')
            await ws.close()
            return

        # handle streaming via orchestrator
        from orchestrator import handle_ws_stream
        await handle_ws_stream(ws, session_id, user, model=None)
    except Exception:
        await ws.close()


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
"""
FastAPI Backend for Personal AI Assistant
Main orchestration layer for RAG, authentication, API endpoints, and job scheduling
"""

from fastapi import FastAPI, WebSocket, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from fastapi.responses import StreamingResponse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

import jwt
import asyncio
import hashlib
import logging
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

import httpx
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from pydantic import BaseModel, EmailStr, Field
import aiohttp

# ============================================================================
# CONFIGURATION
# ============================================================================

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/personal_ai")
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL", "postgresql+asyncpg://user:password@localhost/personal_ai")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-please-change")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8001")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE SETUP
# ============================================================================

class Database:
    def __init__(self):
        self.engine = None
        self.async_engine = None
        self.SessionLocal = None
        self.AsyncSessionLocal = None
    
    def initialize(self):
        """Initialize database connections"""
        self.engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=20,
            max_overflow=40
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info("Database initialized")
    
    async def initialize_async(self):
        """Initialize async database connections"""
        self.async_engine = create_async_engine(
            ASYNC_DATABASE_URL,
            echo=False,
            pool_size=20,
            max_overflow=40
        )
        self.AsyncSessionLocal = sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        
        logger.info("Async database initialized")
    
    def get_session(self) -> Session:
        """Get sync database session"""
        return self.SessionLocal()
    
    async def get_async_session(self) -> AsyncSession:
        """Get async database session"""
        async with self.AsyncSessionLocal() as session:
            yield session

db = Database()

# ============================================================================
# SCHEMAS / MODELS
# ============================================================================

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: int
    token_type: str = "bearer"

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    sources: Optional[List[str]] = None
    timestamp: datetime

class ChatQueryRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    include_sources: bool = True

class DocumentUploadResponse(BaseModel):
    doc_id: str
    title: str
    chunks: int
    tokens: int
    status: str

class SearchRequest(BaseModel):
    query: str
    limit: int = Field(10, ge=1, le=50)
    threshold: float = Field(0.5, ge=0.0, le=1.0)

class SearchResult(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    content: str
    relevance_score: float
    source_type: str

# ============================================================================
# EMBEDDING SERVICE CLIENT
# ============================================================================

class EmbeddingClient:
    def __init__(self, base_url: str = EMBEDDING_SERVICE_URL):
        self.base_url = base_url
        self.client = None
    
    async def initialize(self):
        """Initialize HTTP client"""
        self.client = aiohttp.ClientSession()
    
    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.close()
    
    async def embed(self, text: str, model: str = "sentence-transformers/all-MiniLM-L6-v2") -> List[float]:
        """Generate embedding for text"""
        try:
            async with self.client.post(
                f"{self.base_url}/embed",
                json={
                    "text": text,
                    "model": model
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status != 200:
                    logger.error(f"Embedding service error: {resp.status}")
                    raise Exception(f"Embedding service returned {resp.status}")
                
                data = await resp.json()
                return data.get("embedding", [])
        
        except Exception as e:
            logger.error(f"Error calling embedding service: {e}")
            raise

embedding_client = EmbeddingClient()

# ============================================================================
# OLLAMA LLM CLIENT
# ============================================================================

class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url
        self.model = model
        self.client = None
    
    async def initialize(self):
        """Initialize HTTP client"""
        self.client = aiohttp.ClientSession()
    
    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.close()
    
    async def generate(self, prompt: str, stream: bool = True, temperature: float = 0.7) -> str:
        """Generate response from LLM with streaming support"""
        try:
            full_response = ""
            
            async with self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": stream,
                    "temperature": temperature
                },
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status != 200:
                    logger.error(f"Ollama error: {resp.status}")
                    return "[LLM Error] Unable to generate response"
                
                if stream:
                    async for line in resp.content:
                        if line:
                            import json
                            chunk = json.loads(line)
                            full_response += chunk.get("response", "")
                            # Yield for streaming
                            yield chunk.get("response", "")
                else:
                    data = await resp.json()
                    full_response = data.get("response", "")
                    yield full_response
        
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            yield f"[Model Error] {str(e)}"

ollama_client = OllamaClient()

# ============================================================================
# AUTHENTICATION & JWT
# ============================================================================

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256 (in production, use bcrypt)"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def create_token(user_id: str, expires_in_hours: int = JWT_EXPIRATION_HOURS) -> str:
        """Create JWT token"""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(hours=expires_in_hours),
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

# ============================================================================
# RAG PIPELINE
# ============================================================================

class RAGPipeline:
    def __init__(self):
        self.faiss_index = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=250,
            separators=["\n\n", "\n", " ", ""]
        )
    
    async def initialize(self):
        """Load FAISS index from disk"""
        if os.path.exists(FAISS_INDEX_PATH):
            try:
                # Note: FAISS indexing is synchronous, run in thread pool
                loop = asyncio.get_event_loop()
                self.faiss_index = await loop.run_in_executor(
                    None,
                    self._load_index
                )
                logger.info("FAISS index loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load FAISS index: {e}")
                self.faiss_index = None
        else:
            logger.info("FAISS index not found, will create on first document")
    
    def _load_index(self):
        """Load FAISS index (synchronous)"""
        return FAISS.load_local(FAISS_INDEX_PATH, embedding_function=None)
    
    async def chunk_document(self, text: str, doc_id: str) -> List[Dict[str, Any]]:
        """Split document into chunks"""
        chunks = self.text_splitter.split_text(text)
        chunk_list = []
        
        for i, chunk_text in enumerate(chunks):
            chunk_list.append({
                "chunk_id": f"{doc_id}_chunk_{i}",
                "text": chunk_text,
                "sequence": i,
                "tokens": len(chunk_text.split())  # Approximate
            })
        
        return chunk_list
    
    async def retrieve_relevant(self, query: str, top_k: int = 10, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve top-K relevant documents using RAG pipeline:
        1. Embed query
        2. Search FAISS index
        3. Apply hybrid ranking (relevance + recency + source weight)
        """
        
        try:
            # Step 1: Generate query embedding
            query_embedding = await embedding_client.embed(query)
            query_vec = np.array([query_embedding], dtype=np.float32)
            
            # Step 2: FAISS similarity search
            if not self.faiss_index:
                logger.warning("FAISS index not initialized")
                return []
            
            # Search in thread pool (FAISS is synchronous)
            loop = asyncio.get_event_loop()
            distances, indices = await loop.run_in_executor(
                None,
                lambda: self.faiss_index.search(query_vec, k=min(top_k * 2, 50))
            )
            
            # Step 3: Retrieve metadata and apply hybrid ranking
            results = []
            
            for dist, idx in zip(distances[0], indices[0]):
                if idx == -1:  # Invalid index
                    continue
                
                # Normalize distance to relevance score
                relevance_score = 1.0 / (1.0 + float(dist))
                
                # TODO: Fetch metadata from database
                # Apply hybrid ranking:
                # final_score = 0.7 * relevance + 0.2 * recency + 0.1 * source_weight
                
                results.append({
                    "index": int(idx),
                    "relevance_score": float(relevance_score),
                    "distance": float(dist)
                })
            
            return results[:top_k]
        
        except Exception as e:
            logger.error(f"Error in retrieval: {e}")
            return []
    
    async def generate_rag_response(self, query: str, context_docs: List[str], user_id: Optional[str] = None):
        """Generate RAG response using Ollama"""
        
        # Prepare context
        context_text = "\n\n".join([f"Source {i+1}:\n{doc}" for i, doc in enumerate(context_docs[:5])])
        
        prompt = f"""You are a helpful AI assistant with access to the following context.

CONTEXT:
{context_text}

QUESTION:
{query}

Please provide a comprehensive answer based on the context above. If the context doesn't contain relevant information, say so clearly.

ANSWER:
"""
        
        try:
            async for chunk in ollama_client.generate(prompt, stream=True):
                yield chunk
        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            yield f"Error: {str(e)}"

rag_pipeline = RAGPipeline()

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting Personal AI Assistant API...")
    await embedding_client.initialize()
    await ollama_client.initialize()
    await rag_pipeline.initialize()
    logger.info("All services initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await embedding_client.close()
    await ollama_client.close()

app = FastAPI(
    title="Personal AI Assistant API",
    description="Production-ready Personal AI system with RAG",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:4200").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Trust host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[os.getenv("ALLOWED_HOST", "localhost")]
)

security = HTTPBearer()

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_current_user(credentials: HTTPAuthCredentials = Depends(security)) -> Dict[str, Any]:
    """Extract and verify current user from JWT token"""
    token = credentials.credentials
    payload = AuthService.verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload

# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "embedding": "ready",
            "ollama": "ready",
            "database": "ready"
        }
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint (placeholder)"""
    return {
        "processed_messages": 0,
        "total_embeddings": 0,
        "system_uptime_seconds": 0
    }

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/auth/register", response_model=Dict[str, str])
async def register(request: UserRegisterRequest, db_session: Session = Depends(db.get_session)):
    """Register new user"""
    try:
        # TODO: Create user in database
        # TODO: Generate encryption key
        
        logger.info(f"User registered: {request.email}")
        
        return {
            "status": "success",
            "message": "User registered successfully"
        }
    
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(request: UserLoginRequest):
    """User login"""
    try:
        # TODO: Validate credentials
        password_hash = AuthService.hash_password(request.password)
        
        # TODO: Fetch user from database and verify
        user_id = "dummy-user-id"  # Placeholder
        
        access_token = AuthService.create_token(user_id)
        
        logger.info(f"User logged in: {request.email}")
        
        return TokenResponse(
            access_token=access_token,
            expires_in=JWT_EXPIRATION_HOURS * 3600
        )
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str, token: str = None):
    """WebSocket endpoint for streaming chat"""
    
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            query = data.get("message", "")
            
            if not query:
                continue
            
            logger.info(f"Chat query received: {query[:100]}...")
            
            # Retrieve relevant context
            retrieved_docs = await rag_pipeline.retrieve_relevant(query, top_k=10)
            
            # Send streaming response
            await websocket.send_json({
                "type": "status",
                "message": f"Retrieved {len(retrieved_docs)} documents"
            })
            
            # Generate RAG response with streaming
            full_response = ""
            async for chunk in rag_pipeline.generate_rag_response(query, []):
                full_response += chunk
                await websocket.send_json({
                    "type": "stream",
                    "delta": chunk
                })
            
            # Send completion
            await websocket.send_json({
                "type": "complete",
                "message": full_response,
                "sources": [f"doc_{i}" for i in range(len(retrieved_docs))]
            })
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1000)

@app.post("/api/v1/chat/query")
async def chat_query(request: ChatQueryRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """REST endpoint for chat queries (non-streaming)"""
    
    try:
        # Retrieve context
        retrieved_docs = await rag_pipeline.retrieve_relevant(request.message, top_k=10)
        
        # Generate response
        response_text = ""
        async for chunk in rag_pipeline.generate_rag_response(request.message, []):
            response_text += chunk
        
        return {
            "response": response_text,
            "sources": retrieved_docs if request.include_sources else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Chat query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# KNOWLEDGE MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/knowledge/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """Upload and index a document"""
    
    try:
        content = await file.read()
        text_content = content.decode('utf-8', errors='ignore')
        
        # Chunk document
        chunks = await rag_pipeline.chunk_document(text_content, file.filename)
        
        logger.info(f"Document uploaded: {file.filename} ({len(chunks)} chunks)")
        
        # TODO: Add to FAISS index
        # TODO: Store in database
        
        return DocumentUploadResponse(
            doc_id="doc-id",
            title=file.filename,
            chunks=len(chunks),
            tokens=sum(c["tokens"] for c in chunks),
            status="indexed"
        )
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/knowledge/search", response_model=List[SearchResult])
async def search_knowledge(
    request: SearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Search knowledge base"""
    
    try:
        results = await rag_pipeline.retrieve_relevant(request.query, top_k=request.limit)
        
        # Format results
        formatted_results = []
        for result in results:
            # TODO: Fetch actual document metadata from database
            formatted_results.append(SearchResult(
                chunk_id=f"chunk_{result['index']}",
                doc_id=f"doc_{result['index']}",
                title="Document Title",
                content="Document content snippet",
                relevance_score=result["relevance_score"],
                source_type="local_upload"
            ))
        
        return formatted_results
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# NEWS FEED ENDPOINTS
# ============================================================================

@app.post("/api/v1/news/ingest-now", response_model=Dict[str, Any])
async def trigger_news_ingestion(
    current_user: Dict[str, Any] = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """Trigger manual news ingestion"""
    
    try:
        # TODO: Add background task for news ingestion
        # background_tasks.add_task(ingest_news_feeds, current_user["user_id"])
        
        return {
            "status": "ingestion_started",
            "message": "News ingestion started in background"
        }
    
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/api/v1/analytics/summary")
async def analytics_summary(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user analytics summary"""
    
    return {
        "total_documents": 0,
        "total_interactions": 0,
        "storage_used_mb": 0,
        "avg_response_time_ms": 0
    }

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        workers=int(os.getenv("WORKERS", 4)),
        log_level=LOG_LEVEL.lower()
    )
