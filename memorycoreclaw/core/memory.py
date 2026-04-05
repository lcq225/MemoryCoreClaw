"""
MemoryCoreClaw - Unified Memory Interface

Simple API for human-brain-inspired memory management.
"""

from typing import Optional, List, Dict, Any
from .engine import MemoryEngine, MemoryLayer, Emotion


class Memory:
    """
    Unified memory interface for AI agents.
    
    Features:
    - Layered memory (core/important/normal)
    - Forgetting curve (Ebbinghaus model)
    - Contextual memory triggers
    - Working memory (limited capacity)
    - Relation learning
    - Semantic search
    
    Example:
        mem = Memory()
        
        # Remember
        mem.remember("Alice works at TechCorp", importance=0.8)
        
        # Recall
        results = mem.recall("Alice")
        
        # Relations
        mem.relate("Alice", "works_at", "TechCorp")
        network = mem.associate("Alice")
        
        # Context trigger
        mem.recall_by_context(people=["Alice"])
        
        # Working memory
        mem.hold("task", "processing", priority=0.9)
    """
    
    def __init__(self, db_path: Optional[str] = None, session_id: Optional[str] = None):
        """
        Initialize memory system.
        
        Args:
            db_path: Database path (default: ~/.memorycoreclaw/memory.db)
            session_id: Session identifier for working memory isolation
        """
        self.core = MemoryEngine(db_path)
        self.session_id = session_id or "default"
        
        # Lazy load cognitive modules
        self._forgetting = None
        self._contextual = None
        self._working = None
        self._semantic = None
    
    @property
    def forgetting(self):
        """Lazy load forgetting curve engine."""
        if self._forgetting is None:
            from ..cognitive.forgetting import ForgettingCurve
            self._forgetting = ForgettingCurve(self.core.db_path)
        return self._forgetting
    
    @property
    def contextual(self):
        """Lazy load contextual memory engine."""
        if self._contextual is None:
            from ..cognitive.contextual import ContextualMemory
            self._contextual = ContextualMemory(self.core.db_path)
        return self._contextual
    
    @property
    def working(self):
        """Lazy load working memory engine."""
        if self._working is None:
            from ..cognitive.working_memory import WorkingMemory
            self._working = WorkingMemory(self.core.db_path, self.session_id)
        return self._working
    
    @property
    def semantic(self):
        """Lazy load semantic search engine."""
        if self._semantic is None:
            from ..retrieval.semantic import create_search_engine
            self._semantic = create_search_engine(self.core.db_path)
        return self._semantic
    
    @property
    def associative(self):
        """Lazy load associative memory engine."""
        if getattr(self, '_associative', None) is None:
            from ..cognitive.associative import AssociativeMemory
            self._associative = AssociativeMemory(self.core.db_path)
        return self._associative
    
    # ==================== Core Operations ====================
    
    def remember(self, content: str, 
                 importance: float = 0.5,
                 category: str = "general",
                 emotion: str = "neutral",
                 tags: Optional[List[str]] = None) -> int:
        """
        Store a fact in memory.
        
        Args:
            content: The fact content
            importance: 0-1, higher = more important (core >= 0.9)
            category: Memory category
            emotion: positive/negative/neutral/milestone
            tags: Optional tags for categorization
            
        Returns:
            Memory ID
        """
        return self.core.remember(
            content=content,
            importance=importance,
            category=category,
            emotion=emotion,
            tags=tags or []
        )
    
    def recall(self, query: str, limit: int = 5, use_semantic: bool = True) -> List[Dict[str, Any]]:
        """
        Search memories by keyword or semantic similarity.
        
        Automatically uses semantic search when embedding service available,
        falls back to keyword search otherwise.
        
        Args:
            query: Search query
            limit: Maximum results
            use_semantic: Whether to try semantic search first
            
        Returns:
            List of matching memories
        """
        # Try semantic search first
        if use_semantic:
            try:
                semantic_results = self.semantic.search(query, memory_type='fact', limit=limit)
                if semantic_results:
                    # Convert SearchResult to dict format
                    results = []
                    for r in semantic_results:
                        results.append({
                            'id': r.id,
                            'content': r.content,
                            'score': r.score,
                            'importance': r.metadata.get('importance', 0.5),
                            'category': r.metadata.get('category', 'general'),
                            'search_type': r.search_type
                        })
                    return results
            except Exception:
                pass  # Fall through to keyword search
        
        # Fallback to keyword search
        results = self.core.recall(query, limit)
        
        # Enhance results with forgetting curve
        for r in results:
            r['retention'] = self.forgetting.calculate_retention(
                days_since_access=r.get('days_old', 0),
                importance=r.get('importance', 0.5)
            )
        
        return results
    
    def recall_by_category(self, category: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search memories by category.
        
        Args:
            category: Category to filter by (e.g., 'preference', 'config', 'milestone')
            limit: Maximum results
            
        Returns:
            List of matching memories
        """
        return self.core.recall_by_category(category, limit)
    
    def recall_by_importance(self, min_importance: float = 0.7, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search memories by minimum importance.
        
        Args:
            min_importance: Minimum importance threshold (0-1)
            limit: Maximum results
            
        Returns:
            List of matching memories
        """
        return self.core.recall_by_importance(min_importance, limit)
    
    def learn(self, action: str, context: str, 
              outcome: str, insight: str,
              importance: float = 0.7) -> int:
        """
        Learn from experience (lesson learned).
        
        Args:
            action: What was done
            context: The situation
            outcome: positive/negative/neutral
            insight: What was learned
            importance: Lesson importance
            
        Returns:
            Lesson ID
        """
        return self.core.learn(
            action=action,
            context=context,
            outcome=outcome,
            insight=insight,
            importance=importance
        )
    
    def get_lessons(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get all learned lessons.
        
        Args:
            limit: Maximum number of lessons to return
            
        Returns:
            List of lessons
        """
        return self.core.get_lessons(limit)
    
    def relate(self, entity1: str, relation: str, entity2: str,
               evidence: Optional[str] = None) -> int:
        """
        Create a relation between entities.
        
        Args:
            entity1: Source entity
            relation: Relation type (works_at, knows, prefers, etc.)
            entity2: Target entity
            evidence: Optional evidence/source
            
        Returns:
            Relation ID
        """
        return self.core.relate(entity1, relation, entity2, evidence)
    
    def get_relations(self, entity: str) -> List[Dict[str, Any]]:
        """
        Get all relations for an entity.
        
        Args:
            entity: Entity name
            
        Returns:
            List of relations
        """
        return self.core.get_relations(entity)
    
    def associate(self, entity: str, depth: int = 2) -> Dict[str, Any]:
        """
        Get association network for an entity.
        
        Args:
            entity: Central entity
            depth: How many hops to traverse
            
        Returns:
            Association network with entities and relations
        """
        return self.core.associate(entity, depth)
    
    # ==================== Associative Memory ====================
    
    def diverge(self, seed: str, max_depth: int = 3, min_score: float = 0.1) -> List[Dict[str, Any]]:
        """
        Divergent memory: Spread activation from a seed entity.
        
        Activates the entire knowledge network from one trigger point.
        Like human memory: "Enterprise" → User A, City A, Industry...
        
        Args:
            seed: Starting entity
            max_depth: Maximum traversal depth (default 3)
            min_score: Minimum activation score to include
            
        Returns:
            List of activated entities with scores and paths
        """
        results = self.associative.diverge(seed, max_depth, min_score)
        return [
            {
                'entity': r.entity,
                'score': r.score,
                'depth': r.depth,
                'path': r.path,
                'relation_type': r.relation_type
            }
            for r in results
        ]
    
    def converge(self, clues: List[str], min_evidence: int = 2) -> List[Dict[str, Any]]:
        """
        Convergent memory: Multiple clues aggregating to core entity.
        
        Like human reasoning: "BLUF" + "IT" + "City A" → User A
        
        Args:
            clues: List of clue entities
            min_evidence: Minimum number of clues pointing to entity
            
        Returns:
            List of converged entities with scores and evidence
        """
        results = self.associative.converge(clues, min_evidence)
        return [
            {
                'entity': r.entity,
                'score': r.score,
                'confidence': r.confidence,
                'evidence': r.evidence
            }
            for r in results
        ]
    
    def smart_recall(self, query: str) -> Dict[str, Any]:
        """
        Smart recall that automatically chooses between diverge and converge.
        
        - 1 entity in query → diverge (learn about this entity)
        - 2+ entities in query → converge (find common connection)
        - No entities → keyword search
        
        Args:
            query: User query
            
        Returns:
            Dict with mode used and results
        """
        return self.associative.smart_recall(query)
    
    # ==================== Contextual Memory ====================
    
    def recall_by_context(self, 
                          people: Optional[List[str]] = None,
                          location: Optional[str] = None,
                          emotion: Optional[str] = None,
                          activity: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Recall memories triggered by context.
        
        Args:
            people: People mentioned
            location: Current location
            emotion: Current emotion
            activity: Current activity
            
        Returns:
            List of contextually relevant memories
        """
        return self.contextual.recall_by_context(
            people=people,
            location=location,
            emotion=emotion,
            activity=activity
        )
    
    def bind_context(self, memory_id: int,
                     people: Optional[List[str]] = None,
                     location: Optional[str] = None,
                     emotion: Optional[str] = None,
                     activity: Optional[str] = None):
        """
        Bind context to a memory for future triggering.
        
        Args:
            memory_id: Memory ID
            people: Related people
            location: Location context
            emotion: Emotional context
            activity: Activity context
        """
        self.contextual.bind_context(
            memory_id=memory_id,
            people=people,
            location=location,
            emotion=emotion,
            activity=activity
        )
    
    # ==================== Working Memory ====================
    
    def hold(self, key: str, value: Any, 
             priority: float = 0.5, ttl: Optional[int] = None):
        """
        Store item in working memory (limited capacity).
        
        Args:
            key: Item key
            value: Item value
            priority: Priority (higher = more likely to keep)
            ttl: Time-to-live in seconds
        """
        self.working.add(key, value, priority, ttl_seconds=ttl)
    
    def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve item from working memory.
        
        Args:
            key: Item key
            
        Returns:
            Item value or None if not found
        """
        return self.working.get(key)
    
    def forget(self, key: str):
        """Remove item from working memory."""
        self.working.remove(key)
    
    # ==================== Maintenance ====================
    
    def apply_forgetting(self):
        """Apply forgetting curve to all memories."""
        self.forgetting.apply_forgetting_curve()
    
    def consolidate(self):
        """
        Run memory consolidation:
        - Apply forgetting curve
        - Clean up expired items
        - Update importance scores
        """
        self.apply_forgetting()
        self.working.cleanup_expired()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        stats = self.core.get_stats()
        stats['working_memory'] = {
            'used': self.working.used,
            'capacity': self.working.capacity
        }
        stats['search'] = self.semantic.get_status()
        return stats
    
    # ==================== Export ====================
    
    def export(self, format: str = "json", path: Optional[str] = None) -> Dict:
        """
        Export memories to file.
        
        Args:
            format: Export format (json/markdown)
            path: Output path (auto-generated if None)
            
        Returns:
            Export data dict or markdown string
        """
        from ..utils.export import MemoryExporter
        exporter = MemoryExporter(self.core)
        
        if format == "markdown":
            return exporter.export_markdown(path)
        else:
            return exporter.export_json(path)
    
    def visualize(self, path: Optional[str] = None) -> str:
        """
        Generate knowledge graph visualization.
        
        Args:
            path: Output HTML path
            
        Returns:
            HTML file path
        """
        from ..utils.visualization import MemoryVisualizer
        viz = MemoryVisualizer(self.core.db_path)
        return viz.generate_knowledge_graph(path)
    
    # ==================== CRUD ====================
    
    def delete(self, memory_id: int):
        """Delete a memory by ID."""
        self.core.delete_fact(memory_id)
    
    def update(self, memory_id: int, **kwargs):
        """Update a memory."""
        self.core.update_fact(memory_id, **kwargs)


def get_memory(db_path: str = None, session_id: str = None) -> Memory:
    """
    Get or create a Memory instance.
    
    Args:
        db_path: Database path (default: ~/.memorycoreclaw/memory.db)
        session_id: Session identifier
    
    Returns:
        Memory instance
    """
    return Memory(db_path=db_path, session_id=session_id)
