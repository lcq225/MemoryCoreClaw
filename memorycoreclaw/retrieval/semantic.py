"""
MemoryCoreClaw - Semantic Search Module

Implements semantic similarity search with automatic fallback.

Features:
- Semantic search using embeddings (Ollama bge-m3)
- Automatic fallback to keyword search when embedding unavailable
- Health check for embedding service
- Caching for performance
"""

from typing import List, Dict, Optional, Tuple
import math
import json
import urllib.request
import urllib.error
import sqlite3
from dataclasses import dataclass
from pathlib import Path
import time
import threading


@dataclass
class SearchResult:
    """A search result with similarity score"""
    id: int
    content: str
    score: float
    metadata: Dict
    search_type: str  # 'semantic' or 'keyword'


class EmbeddingService:
    """
    Embedding Service with health check and auto-recovery.
    
    Supports OpenAI-compatible API (Ollama, vLLM, etc.)
    """
    
    def __init__(self, 
                 base_url: str = "http://127.0.0.1:11434/v1",
                 api_key: str = "ollama",
                 model_name: str = "bge-m3",
                 dimensions: int = 1024):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model_name = model_name
        self.dimensions = dimensions
        
        # Health status
        self._is_available = None
        self._last_check_time = 0
        self._check_interval = 60  # Re-check every 60 seconds
        self._lock = threading.Lock()
    
    def is_available(self, force_check: bool = False) -> bool:
        """
        Check if embedding service is available.
        
        Uses cached result unless force_check=True or cache expired.
        """
        with self._lock:
            current_time = time.time()
            
            # Use cached result if valid
            if not force_check and self._is_available is not None:
                if current_time - self._last_check_time < self._check_interval:
                    return self._is_available
            
            # Perform health check
            self._is_available = self._health_check()
            self._last_check_time = current_time
            return self._is_available
    
    def _health_check(self) -> bool:
        """Perform actual health check."""
        try:
            # Try a simple embedding request
            url = f"{self.base_url}/embeddings"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.model_name,
                "input": "test"
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode('utf-8'))
                if 'data' in result and len(result['data']) > 0:
                    return True
            return False
        except Exception as e:
            # Service not available
            return False
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding for text.
        
        Returns None if service unavailable.
        """
        if not self.is_available():
            return None
        
        try:
            url = f"{self.base_url}/embeddings"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.model_name,
                "input": text
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                if 'data' in result and len(result['data']) > 0:
                    return result['data'][0].get('embedding')
            return None
        except Exception as e:
            # Mark as unavailable for next check
            self._is_available = False
            return None
    
    def get_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Get embeddings for multiple texts."""
        if not self.is_available():
            return [None] * len(texts)
        
        try:
            url = f"{self.base_url}/embeddings"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.model_name,
                "input": texts
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                if 'data' in result:
                    # Sort by index to maintain order
                    sorted_data = sorted(result['data'], key=lambda x: x.get('index', 0))
                    return [item.get('embedding') for item in sorted_data]
            return [None] * len(texts)
        except Exception as e:
            self._is_available = False
            return [None] * len(texts)


class SemanticSearch:
    """
    Semantic Search Engine with automatic fallback.
    
    Features:
    - Semantic similarity using embeddings (when available)
    - Fallback to keyword search (when embedding unavailable)
    - Vector storage in database
    - Hybrid search combining both
    """
    
    def __init__(self, 
                 db_path: str,
                 embedding_service: Optional[EmbeddingService] = None):
        """
        Initialize semantic search.
        
        Args:
            db_path: Path to SQLite database
            embedding_service: Optional embedding service (will create default if None)
        """
        self.db_path = db_path
        self.embedding_service = embedding_service or EmbeddingService()
        
        # Ensure embedding cache table exists
        self._init_db()
    
    def _init_db(self):
        """Initialize embedding cache table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create embedding cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embedding_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT NOT NULL,
                memory_id INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(memory_type, memory_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def index(self, memory_type: str, memory_id: int, content: str) -> bool:
        """
        Index a memory for semantic search.
        
        Args:
            memory_type: Type of memory (e.g., 'fact', 'experience')
            memory_id: Memory ID
            content: Memory content
            
        Returns:
            True if indexed successfully, False if embedding unavailable
        """
        if not self.embedding_service.is_available():
            return False
        
        # Get embedding
        embedding = self.embedding_service.get_embedding(content)
        if embedding is None:
            return False
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert to bytes
        import struct
        embedding_bytes = struct.pack(f'{len(embedding)}f', *embedding)
        content_hash = str(hash(content))
        
        cursor.execute('''
            INSERT OR REPLACE INTO embedding_cache 
            (memory_type, memory_id, content_hash, embedding)
            VALUES (?, ?, ?, ?)
        ''', (memory_type, memory_id, content_hash, embedding_bytes))
        
        conn.commit()
        conn.close()
        return True
    
    def search(self, query: str, 
               memory_type: str = 'fact',
               limit: int = 10,
               use_semantic: bool = True) -> List[SearchResult]:
        """
        Search for similar memories.
        
        Automatically falls back to keyword search if semantic unavailable.
        
        Args:
            query: Search query
            memory_type: Type of memory to search
            limit: Maximum results
            use_semantic: Whether to try semantic search first
            
        Returns:
            List of search results
        """
        results = []
        
        # Try semantic search first if enabled and available
        if use_semantic and self.embedding_service.is_available():
            results = self._semantic_search(query, memory_type, limit)
            if results:
                return results
        
        # Fallback to keyword search
        return self._keyword_search(query, memory_type, limit)
    
    def _semantic_search(self, query: str, 
                         memory_type: str, 
                         limit: int) -> List[SearchResult]:
        """Perform semantic search using embeddings."""
        # Get query embedding
        query_embedding = self.embedding_service.get_embedding(query)
        if query_embedding is None:
            return []
        
        # Get all embeddings for this memory type
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ec.memory_id, ec.embedding, m.content, m.importance, m.category
            FROM embedding_cache ec
            JOIN facts m ON ec.memory_id = m.id
            WHERE ec.memory_type = ?
        ''', (memory_type,))
        
        import struct
        
        scores = []
        for row in cursor.fetchall():
            memory_id, embedding_blob, content, importance, category = row
            
            # Unpack embedding
            if embedding_blob is None:
                continue
            
            try:
                embedding = list(struct.unpack(f'{len(embedding_blob)//4}f', embedding_blob))
                score = self._cosine_similarity(query_embedding, embedding)
                scores.append((memory_id, content, score, importance, category))
            except Exception:
                continue
        
        conn.close()
        
        # Sort by score
        scores.sort(key=lambda x: x[2], reverse=True)
        
        results = []
        for memory_id, content, score, importance, category in scores[:limit]:
            results.append(SearchResult(
                id=memory_id,
                content=content,
                score=score,
                metadata={'importance': importance, 'category': category},
                search_type='semantic'
            ))
        
        return results
    
    def _keyword_search(self, query: str, 
                        memory_type: str, 
                        limit: int) -> List[SearchResult]:
        """Perform keyword-based search (fallback)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Use LIKE for simple keyword matching
        query_terms = query.lower().split()
        like_conditions = ' OR '.join(['content LIKE ?' for _ in query_terms])
        like_params = [f'%{term}%' for term in query_terms]
        
        cursor.execute(f'''
            SELECT id, content, importance, category
            FROM facts
            WHERE ({like_conditions})
            ORDER BY importance DESC
            LIMIT ?
        ''', like_params + [limit])
        
        results = []
        for row in cursor.fetchall():
            memory_id, content, importance, category = row
            
            # Calculate simple Jaccard similarity
            content_words = set(content.lower().split())
            query_words = set(query_terms)
            intersection = len(content_words & query_words)
            union = len(content_words | query_words)
            score = intersection / union if union > 0 else 0
            
            # Boost for exact substring match
            if query.lower() in content.lower():
                score += 0.3
            
            results.append(SearchResult(
                id=memory_id,
                content=content,
                score=min(score, 1.0),
                metadata={'importance': importance, 'category': category},
                search_type='keyword'
            ))
        
        conn.close()
        
        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        
        if mag_a == 0 or mag_b == 0:
            return 0
        
        return dot_product / (mag_a * mag_b)
    
    def get_status(self) -> Dict:
        """Get current search status."""
        embedding_available = self.embedding_service.is_available()
        return {
            'embedding_available': embedding_available,
            'search_mode': 'semantic' if embedding_available else 'keyword',
            'model': self.embedding_service.model_name if embedding_available else None,
            'base_url': self.embedding_service.base_url
        }
    
    def rebuild_index(self, memory_type: str = 'fact') -> Tuple[int, int]:
        """
        Rebuild embedding index for all memories of a type.
        
        Returns:
            (success_count, total_count)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, content FROM facts')
        memories = cursor.fetchall()
        conn.close()
        
        success = 0
        total = len(memories)
        
        for memory_id, content in memories:
            if self.index(memory_type, memory_id, content):
                success += 1
        
        return success, total


# Convenience function for quick access
def create_search_engine(db_path: str = None,
                         embedding_config: Dict = None) -> SemanticSearch:
    """
    Create a semantic search engine with configuration.
    
    Args:
        db_path: Database path
        embedding_config: Embedding configuration dict
        
    Returns:
        Configured SemanticSearch instance
    """
    import os
    
    if db_path is None:
        db_path = os.environ.get('MEMORY_DB_PATH', 'memory.db')
    
    if embedding_config is None:
        # Default config for Ollama bge-m3
        embedding_config = {
            'base_url': 'http://127.0.0.1:11434/v1',
            'api_key': 'ollama',
            'model_name': 'bge-m3',
            'dimensions': 1024
        }
    
    embedding_service = EmbeddingService(
        base_url=embedding_config.get('base_url', ''),
        api_key=embedding_config.get('api_key', ''),
        model_name=embedding_config.get('model_name', ''),
        dimensions=embedding_config.get('dimensions', 1024)
    )
    
    return SemanticSearch(db_path, embedding_service)


if __name__ == "__main__":
    # Test the search engine
    print("=" * 60)
    print("Semantic Search Engine Test")
    print("=" * 60)
    
    search = create_search_engine()
    
    # Check status
    status = search.get_status()
    print(f"\n📊 Status:")
    print(f"   Embedding Available: {status['embedding_available']}")
    print(f"   Search Mode: {status['search_mode']}")
    if status['model']:
        print(f"   Model: {status['model']}")
    
    # Test search
    print(f"\n🔍 Testing search...")
    results = search.search("海科", limit=3)
    
    print(f"\n   Found {len(results)} results:")
    for r in results:
        print(f"   [{r.search_type}] Score: {r.score:.3f}")
        print(f"   {r.content[:50]}...")
        print()