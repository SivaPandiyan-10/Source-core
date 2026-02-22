"""
Knowledge Ingestion Pipeline
Handles local file scanning, PDF/DOCX extraction, RSS feed ingestion, and web crawling
"""

import asyncio
import hashlib
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import aiohttp
import feedparser
import pdfplumber
from docx import Document
import trafilatura  # HTML cleaning
import requests_robots

logger = logging.getLogger(__name__)

# ============================================================================
# LOCAL FILE LOADING
# ============================================================================

class LocalContentLoader:
    """Load and process local files (PDF, DOCX, TXT)"""
    
    SUPPORTED_FORMATS = {'.pdf', '.docx', '.txt', '.md'}
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 250):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    async def scan_folder(self, folder_path: str, recursive: bool = True) -> List[Path]:
        """Scan folder for supported document types"""
        
        folder = Path(folder_path)
        if not folder.exists():
            logger.warning(f"Folder not found: {folder_path}")
            return []
        
        files = []
        pattern = "**/*" if recursive else "*"
        
        for file_path in folder.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_FORMATS:
                files.append(file_path)
        
        logger.info(f"Found {len(files)} documents in {folder_path}")
        return files
    
    async def extract_text(self, file_path: Path) -> str:
        """Extract text from various file formats"""
        
        try:
            if file_path.suffix.lower() == '.pdf':
                return await self._extract_pdf(file_path)
            elif file_path.suffix.lower() == '.docx':
                return await self._extract_docx(file_path)
            elif file_path.suffix.lower() in {'.txt', '.md'}:
                return await self._extract_text(file_path)
            else:
                logger.warning(f"Unsupported format: {file_path.suffix}")
                return ""
        
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""
    
    async def _extract_pdf(self, file_path: Path) -> str:
        """Extract text from PDF"""
        
        text = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
        
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
        
        return "\n".join(text)
    
    async def _extract_docx(self, file_path: Path) -> str:
        """Extract text from DOCX"""
        
        text = []
        try:
            doc = Document(file_path)
            for para in doc.paragraphs:
                if para.text.strip():
                    text.append(para.text)
        
        except Exception as e:
            logger.error(f"DOCX extraction error: {e}")
        
        return "\n".join(text)
    
    async def _extract_text(self, file_path: Path) -> str:
        """Extract text from plain text files"""
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        
        except Exception as e:
            logger.error(f"Text extraction error: {e}")
            return ""
    
    def chunk_text(self, text: str, doc_id: str) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks"""
        
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            
            if chunk_text.strip():
                chunks.append({
                    "id": f"{doc_id}_chunk_{len(chunks)}",
                    "text": chunk_text,
                    "token_count": len(chunk_words),
                    "sequence": len(chunks)
                })
        
        return chunks


# ============================================================================
# WEB CONTENT LOADER (RSS & Crawling)
# ============================================================================

class WebContentLoader:
    """Fetch and process RSS feeds and web content"""
    
    def __init__(self, timeout: int = 10, respect_robots_txt: bool = True):
        self.timeout = timeout
        self.respect_robots_txt = respect_robots_txt
        self.headers = {
            "User-Agent": "PersonalAI/1.0 (+https://example.com/bot)"
        }
    
    async def fetch_rss_feeds(self, feeds: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Fetch articles from RSS feeds"""
        
        articles = []
        
        for feed in feeds:
            try:
                feed_url = feed.get("url")
                feed_name = feed.get("name", feed_url)
                category = feed.get("category", "general")
                source_weight = feed.get("source_weight", 0.8)
                
                logger.info(f"Fetching RSS feed: {feed_name}")
                
                # Parse RSS
                parsed = feedparser.parse(feed_url)
                
                if parsed.status != 200:
                    logger.warning(f"Failed to fetch {feed_name}, status: {parsed.status}")
                    continue
                
                for entry in parsed.entries[:100]:  # Limit to 100 entries per feed
                    article = {
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "description": entry.get("summary", ""),
                        "published_date": self._parse_date(entry.get("published", "")),
                        "author": entry.get("author", ""),
                        "feed_name": feed_name,
                        "feed_url": feed_url,
                        "category": category,
                        "source_weight": source_weight,
                        "url_hash": hashlib.sha256(entry.get("link", "").encode()).hexdigest()
                    }
                    
                    articles.append(article)
                
                logger.info(f"Fetched {len(parsed.entries)} articles from {feed_name}")
            
            except Exception as e:
                logger.error(f"Error fetching RSS {feed.get('url', 'unknown')}: {e}")
        
        return articles
    
    async def crawl_article(self, url: str) -> Optional[str]:
        """Crawl and extract article body from URL"""
        
        try:
            # Check robots.txt
            if self.respect_robots_txt and not self._can_fetch(url):
                logger.warning(f"robots.txt disallows: {url}")
                return None
            
            # Fetch article
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=self.headers) as resp:
                    if resp.status != 200:
                        logger.warning(f"Failed to fetch {url}: {resp.status}")
                        return None
                    
                    html = await resp.text()
            
            # Extract main content using trafilatura
            extracted = trafilatura.extract(html)
            
            if not extracted:
                logger.warning(f"Could not extract content from {url}")
            
            return extracted
        
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse various date formats"""
        
        if not date_str:
            return datetime.utcnow()
        
        try:
            # Try common formats
            for fmt in ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%a, %d %b %Y %H:%M:%S"]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            return datetime.utcnow()
        
        except Exception as e:
            logger.warning(f"Could not parse date: {date_str}")
            return datetime.utcnow()
    
    def _can_fetch(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt"""
        
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            robots = requests_robots.load_robots(robots_url)
            
            user_agent = "PersonalAI"
            return robots.is_allowed(user_agent, parsed.path)
        
        except Exception as e:
            logger.warning(f"Error checking robots.txt: {e}")
            return True  # Default: allow if can't check


# ============================================================================
# DEDUPLICATION
# ============================================================================

class Deduplicator:
    """Handle content deduplication"""
    
    def __init__(self):
        self.content_hashes = set()
        self.url_hashes = set()
    
    def hash_content(self, content: str) -> str:
        """Compute content hash"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def hash_url(self, url: str) -> str:
        """Compute URL hash"""
        return hashlib.sha256(url.encode()).hexdigest()
    
    async def is_duplicate_content(self, content: str) -> bool:
        """Check if content is duplicate"""
        
        content_hash = self.hash_content(content)
        
        if content_hash in self.content_hashes:
            return True
        
        self.content_hashes.add(content_hash)
        return False
    
    async def is_duplicate_url(self, url: str) -> bool:
        """Check if URL was already ingested"""
        
        url_hash = self.hash_url(url)
        
        if url_hash in self.url_hashes:
            return True
        
        self.url_hashes.add(url_hash)
        return False


# ============================================================================
# RANKING & FILTERING
# ============================================================================

class RankingService:
    """Compute ranking signals for retrieved documents"""
    
    @staticmethod
    def compute_recency_score(published_date: datetime) -> float:
        """Compute recency boost (1.0 = today, decays over time)"""
        
        days_old = (datetime.utcnow() - published_date).days
        
        # Exponential decay: newer = higher score
        # At 7 days: 0.5, at 30 days: 0.1
        recency = 1.0 / (1.0 + days_old / 7.0)
        
        return recency
    
    @staticmethod
    def compute_hybrid_score(
        relevance_score: float,
        recency_score: float,
        source_weight: float,
        weights: Dict[str, float] = None
    ) -> float:
        """
        Compute hybrid ranking score:
        0.7 * relevance + 0.2 * recency + 0.1 * source
        """
        
        if weights is None:
            weights = {
                "relevance": 0.70,
                "recency": 0.20,
                "source": 0.10
            }
        
        score = (
            weights["relevance"] * relevance_score +
            weights["recency"] * recency_score +
            weights["source"] * source_weight
        )
        
        return score


# ============================================================================
# INGESTION PIPELINE
# ============================================================================

class IngestionPipeline:
    """Main ingestion orchestrator"""
    
    def __init__(self, embedding_client, vector_store, database):
        self.local_loader = LocalContentLoader()
        self.web_loader = WebContentLoader()
        self.deduplicator = Deduplicator()
        self.ranking_service = RankingService()
        self.embedding_client = embedding_client
        self.vector_store = vector_store
        self.database = database
    
    async def ingest_local_folder(self, user_id: str, folder_path: str) -> Dict[str, Any]:
        """Ingest all documents from a local folder"""
        
        logger.info(f"Starting local folder ingestion: {folder_path}")
        
        stats = {
            "documents": 0,
            "chunks": 0,
            "tokens": 0,
            "duplicates": 0,
            "errors": 0
        }
        
        # Scan folder
        files = await self.local_loader.scan_folder(folder_path)
        
        for file_path in files:
            try:
                # Extract text
                text = await self.local_loader.extract_text(file_path)
                
                if not text.strip():
                    logger.warning(f"No text extracted from {file_path}")
                    continue
                
                # Check for duplicate
                if await self.deduplicator.is_duplicate_content(text):
                    logger.info(f"Duplicate document skipped: {file_path.name}")
                    stats["duplicates"] += 1
                    continue
                
                # Create document record
                doc_id = hashlib.sha256(f"{user_id}{file_path}".encode()).hexdigest()[:16]
                
                # Chunk document
                chunks = self.local_loader.chunk_text(text, doc_id)
                
                # Embed and store chunks
                for chunk in chunks:
                    try:
                        embedding = await self.embedding_client.embed(chunk["text"])
                        
                        # Store in vector database
                        vector_id = await self.vector_store.add_vector(
                            user_id=user_id,
                            doc_id=doc_id,
                            chunk_id=chunk["id"],
                            embedding=embedding,
                            metadata={
                                "title": file_path.name,
                                "source_type": "local_upload",
                                "sequence": chunk["sequence"],
                                "tokens": chunk["token_count"]
                            }
                        )
                        
                        stats["chunks"] += 1
                        stats["tokens"] += chunk["token_count"]
                    
                    except Exception as e:
                        logger.error(f"Error embedding chunk: {e}")
                        stats["errors"] += 1
                
                stats["documents"] += 1
                logger.info(f"Ingested {file_path.name}: {len(chunks)} chunks")
            
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                stats["errors"] += 1
        
        logger.info(f"Local ingestion complete: {stats}")
        return stats
    
    async def ingest_news_feeds(self, user_id: str, feeds: List[Dict[str, str]]) -> Dict[str, Any]:
        """Ingest news articles from RSS feeds"""
        
        logger.info(f"Starting news feed ingestion for user {user_id}")
        
        stats = {
            "articles": 0,
            "chunks": 0,
            "tokens": 0,
            "duplicates": 0,
            "crawl_errors": 0
        }
        
        # Fetch RSS feeds
        articles = await self.web_loader.fetch_rss_feeds(feeds)
        
        for article in articles:
            try:
                # Check URL deduplication
                if await self.deduplicator.is_duplicate_url(article["url"]):
                    logger.debug(f"Duplicate URL skipped: {article['url']}")
                    stats["duplicates"] += 1
                    continue
                
                # Crawl full article
                body_content = await self.web_loader.crawl_article(article["url"])
                
                if not body_content:
                    logger.warning(f"Could not extract content from {article['url']}")
                    stats["crawl_errors"] += 1
                    continue
                
                # Chunk article
                doc_id = article["url_hash"]
                chunk_text = body_content
                
                # For web content, create single or few chunks
                chunks = self.local_loader.chunk_text(chunk_text, doc_id)
                
                # Embed and store
                for chunk in chunks:
                    try:
                        embedding = await self.embedding_client.embed(chunk["text"])
                        
                        recency_score = self.ranking_service.compute_recency_score(
                            article["published_date"]
                        )
                        
                        vector_id = await self.vector_store.add_vector(
                            user_id=user_id,
                            doc_id=doc_id,
                            chunk_id=chunk["id"],
                            embedding=embedding,
                            metadata={
                                "title": article["title"],
                                "source_type": "rss_feed",
                                "source_url": article["url"],
                                "source_weight": article["source_weight"],
                                "published_date": article["published_date"].isoformat(),
                                "recency_score": recency_score,
                                "feed_name": article["feed_name"],
                                "category": article["category"]
                            }
                        )
                        
                        stats["chunks"] += 1
                        stats["tokens"] += chunk["token_count"]
                    
                    except Exception as e:
                        logger.error(f"Error embedding article chunk: {e}")
                
                stats["articles"] += 1
            
            except Exception as e:
                logger.error(f"Error processing article: {e}")
        
        logger.info(f"News ingestion complete: {stats}")
        return stats


# ============================================================================
# SCHEDULED INGESTION
# ============================================================================

class ScheduledIngestionService:
    """Manage scheduled ingestion tasks"""
    
    def __init__(self, pipeline: IngestionPipeline):
        self.pipeline = pipeline
        self.tasks = {}
    
    async def schedule_daily_news_ingestion(self, user_id: str, feeds: List[Dict[str, str]], hour: int = 2):
        """Schedule daily news ingestion at specified hour (UTC)"""
        
        logger.info(f"Scheduling daily news ingestion for user {user_id} at {hour}:00 UTC")
        
        # TODO: Implement using APScheduler or Celery
        # For now, this is a placeholder
        
        async def ingest_job():
            while True:
                now = datetime.utcnow()
                next_run = now.replace(hour=hour, minute=0, second=0)
                
                if now > next_run:
                    next_run += timedelta(days=1)
                
                sleep_seconds = (next_run - now).total_seconds()
                await asyncio.sleep(sleep_seconds)
                
                logger.info(f"Running scheduled news ingestion for {user_id}")
                await self.pipeline.ingest_news_feeds(user_id, feeds)
        
        task = asyncio.create_task(ingest_job())
        self.tasks[user_id] = task
        
        return task
