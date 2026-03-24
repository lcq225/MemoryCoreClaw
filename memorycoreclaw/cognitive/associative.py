"""
MemoryCoreClaw - Associative Memory Module

Implements divergent (spreading activation) and convergent (aggregation) memory.

Human Memory Pattern:
1. Divergent: One trigger → Activate entire knowledge network
   Example: "Company" → John, City, Department...

2. Convergent: Multiple clues → Identify core entity
   Example: "BLUF style" + "IT" + "City" → John

Design Questions:
- When to diverge? When user mentions an entity
- When to converge? When multiple clues appear, need to identify core
- Divergence depth? 1-hop, 2-hop, 3-hop?
- Convergence threshold? How many clues to aggregate?
"""

from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import sqlite3
import math


@dataclass
class ActivatedNode:
    """A node activated during spreading activation."""
    entity: str
    score: float
    depth: int
    path: List[str]
    relation_type: str = ""


@dataclass
class ConvergenceResult:
    """Result of convergent memory aggregation."""
    entity: str
    score: float
    evidence: List[Dict]
    confidence: float


class AssociativeMemory:
    """
    Associative Memory Engine.
    
    Implements two key patterns:
    1. Divergent Memory: Spreading activation from one entity
    2. Convergent Memory: Multiple clues converging to core
    
    Algorithm Details:
    
    Divergent (Spreading Activation):
    - Start from seed entity
    - BFS traverse relation graph
    - Score decays with depth (activation strength)
    - Relation weight affects propagation
    
    Convergent (Evidence Aggregation):
    - Start from multiple clues
    - Find entities connected to each clue
    - Aggregate scores from all paths
    - Higher score = more likely the target
    """
    
    # Relation weights for spreading activation
    RELATION_WEIGHTS = {
        # Identity relations (high weight)
        'is_a': 0.9,
        'type_of': 0.9,
        'instance_of': 0.9,
        
        # Strong relations
        'works_at': 0.8,
        'manages': 0.8,
        'reports_to': 0.8,
        'located_in': 0.8,
        'part_of': 0.8,
        
        # Medium relations
        'knows': 0.6,
        'collaborates_with': 0.6,
        'related_to': 0.6,
        'associated_with': 0.6,
        
        # Weak relations
        'similar_to': 0.4,
        'mentioned_with': 0.3,
    }
    
    # Default weight for unknown relations
    DEFAULT_WEIGHT = 0.5
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def _get_relation_weight(self, relation_type: str) -> float:
        """Get weight for a relation type."""
        return self.RELATION_WEIGHTS.get(relation_type, self.DEFAULT_WEIGHT)
    
    def diverge(self, 
                seed: str,
                max_depth: int = 3,
                min_score: float = 0.1,
                max_nodes: int = 20) -> List[ActivatedNode]:
        """
        Divergent memory: Spreading activation from a seed entity.
        
        Args:
            seed: Starting entity
            max_depth: Maximum traversal depth
            min_score: Minimum activation score to include
            max_nodes: Maximum nodes to return
            
        Returns:
            List of activated nodes, sorted by score
            
        Algorithm:
            1. Start from seed with score 1.0
            2. BFS traverse relations
            3. Score = prev_score * relation_weight * depth_decay
            4. Decay factor: 0.7^depth (exponential decay)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        activated = {}
        queue = deque([(seed, 1.0, 0, [seed])])
        visited = {seed}
        
        while queue:
            current, score, depth, path = queue.popleft()
            
            # Check depth limit
            if depth > max_depth:
                continue
            
            # Record activation
            if current != seed:  # Don't include seed itself
                if current not in activated or activated[current].score < score:
                    activated[current] = ActivatedNode(
                        entity=current,
                        score=score,
                        depth=depth,
                        path=path
                    )
            
            # Find all relations from current entity
            cursor.execute('''
                SELECT to_entity, relation_type FROM relations
                WHERE from_entity = ?
            ''', (current,))
            
            for to_entity, relation_type in cursor.fetchall():
                if to_entity in visited:
                    continue
                
                visited.add(to_entity)
                
                # Calculate new score
                relation_weight = self._get_relation_weight(relation_type)
                depth_decay = math.pow(0.7, depth + 1)  # Exponential decay
                new_score = score * relation_weight * depth_decay
                
                # Only propagate if score is above threshold
                if new_score >= min_score:
                    new_path = path + [to_entity]
                    queue.append((to_entity, new_score, depth + 1, new_path))
        
        # Also check reverse relations
        queue = deque([(seed, 1.0, 0, [seed])])
        visited_reverse = {seed}
        
        while queue:
            current, score, depth, path = queue.popleft()
            
            if depth > max_depth:
                continue
            
            cursor.execute('''
                SELECT from_entity, relation_type FROM relations
                WHERE to_entity = ?
            ''', (current,))
            
            for from_entity, relation_type in cursor.fetchall():
                if from_entity in visited_reverse:
                    continue
                
                visited_reverse.add(from_entity)
                
                relation_weight = self._get_relation_weight(relation_type)
                depth_decay = math.pow(0.7, depth + 1)
                new_score = score * relation_weight * depth_decay
                
                if new_score >= min_score:
                    if from_entity not in activated or activated[from_entity].score < new_score:
                        activated[from_entity] = ActivatedNode(
                            entity=from_entity,
                            score=new_score,
                            depth=depth + 1,
                            path=path + [from_entity]
                        )
                    
                    queue.append((from_entity, new_score, depth + 1, path + [from_entity]))
        
        conn.close()
        
        # Sort by score and limit
        results = sorted(activated.values(), key=lambda x: x.score, reverse=True)
        return results[:max_nodes]
    
    def converge(self,
                 clues: List[str],
                 min_evidence: int = 2,
                 min_score: float = 0.3) -> List[ConvergenceResult]:
        """
        Convergent memory: Multiple clues aggregating to core entities.
        
        Args:
            clues: List of clue entities
            min_evidence: Minimum number of clues pointing to entity
            min_score: Minimum aggregation score
            
        Returns:
            List of convergence results, sorted by score
            
        Algorithm:
            1. For each clue, find connected entities (1-hop)
            2. Aggregate scores from all clues
            3. Entity with highest aggregate = most likely target
            4. Confidence = evidence_count / total_clues
        """
        if not clues:
            return []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Track which entities are connected to which clues
        entity_evidence = defaultdict(list)  # entity -> list of (clue, score, relation)
        
        for clue in clues:
            # Find entities connected FROM clue
            cursor.execute('''
                SELECT to_entity, relation_type FROM relations
                WHERE from_entity = ?
            ''', (clue,))
            
            for to_entity, relation_type in cursor.fetchall():
                weight = self._get_relation_weight(relation_type)
                entity_evidence[to_entity].append({
                    'clue': clue,
                    'score': weight,
                    'relation': relation_type,
                    'direction': 'forward'
                })
            
            # Find entities connected TO clue
            cursor.execute('''
                SELECT from_entity, relation_type FROM relations
                WHERE to_entity = ?
            ''', (clue,))
            
            for from_entity, relation_type in cursor.fetchall():
                weight = self._get_relation_weight(relation_type)
                entity_evidence[from_entity].append({
                    'clue': clue,
                    'score': weight,
                    'relation': relation_type,
                    'direction': 'reverse'
                })
        
        conn.close()
        
        # Calculate aggregation scores
        results = []
        for entity, evidence_list in entity_evidence.items():
            if len(evidence_list) < min_evidence:
                continue
            
            # Aggregate score: sum of evidence scores
            aggregate_score = sum(e['score'] for e in evidence_list)
            
            # Normalize by max possible score
            max_possible = len(clues) * 1.0  # Max weight is 1.0
            normalized_score = aggregate_score / max_possible
            
            if normalized_score >= min_score:
                confidence = len(evidence_list) / len(clues)
                results.append(ConvergenceResult(
                    entity=entity,
                    score=normalized_score,
                    evidence=evidence_list,
                    confidence=confidence
                ))
        
        # Sort by score
        results.sort(key=lambda x: (x.score, x.confidence), reverse=True)
        return results
    
    def smart_recall(self,
                     query: str,
                     mode: str = 'auto') -> Dict:
        """
        Smart recall that automatically chooses between diverge and converge.
        
        Args:
            query: User query
            mode: 'auto', 'diverge', or 'converge'
            
        Returns:
            Dict with mode used and results
            
        Auto Mode Logic:
            1. Extract entities from query
            2. If 1 entity → diverge (learn about this entity)
            3. If 2+ entities → converge (find common connection)
            4. If no entities → fall back to keyword search
        """
        # Extract entities from query (simplified)
        # In production, use NER or LLM
        entities = self._extract_entities(query)
        
        if mode == 'auto':
            if len(entities) == 1:
                mode = 'diverge'
            elif len(entities) >= 2:
                mode = 'converge'
            else:
                return {
                    'mode': 'keyword',
                    'entities': [],
                    'results': []
                }
        
        if mode == 'diverge' and entities:
            results = self.diverge(entities[0])
            return {
                'mode': 'diverge',
                'seed': entities[0],
                'results': [
                    {
                        'entity': r.entity,
                        'score': r.score,
                        'depth': r.depth,
                        'path': r.path
                    }
                    for r in results
                ]
            }
        
        elif mode == 'converge' and len(entities) >= 2:
            results = self.converge(entities)
            return {
                'mode': 'converge',
                'clues': entities,
                'results': [
                    {
                        'entity': r.entity,
                        'score': r.score,
                        'confidence': r.confidence,
                        'evidence_count': len(r.evidence)
                    }
                    for r in results
                ]
            }
        
        return {
            'mode': 'none',
            'entities': entities,
            'results': []
        }
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        Extract entities from text.
        
        Simplified version - in production use NER or LLM.
        """
        # Get all known entities from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM entities')
        known_entities = {row[0].lower() for row in cursor.fetchall()}
        conn.close()
        
        # Simple matching
        text_lower = text.lower()
        found = []
        for entity in known_entities:
            if entity in text_lower:
                found.append(entity)
        
        return found


# Integration with Memory class
def add_associative_methods():
    """
    Add associative memory methods to Memory class.
    
    Usage:
        mem = Memory()
        
        # Divergent: Learn about an entity
        network = mem.associate("John")
        
        # Convergent: Who connects these clues?
        results = mem.aggregate(["Company", "BLUF style", "City"])
        
        # Smart: Auto-choose based on query
        results = mem.smart_recall("Tell me about John")
    """
    pass


if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    # Example usage - replace with your database path
    db_path = "path/to/your/memory.db"
    
    print("=" * 60)
    print("Associative Memory Test")
    print("=" * 60)
    
    print("\nPlease set db_path to your memory database to run tests.")
    print("\nExample usage:")
    print("  am = AssociativeMemory(db_path)")
    print("  results = am.diverge('EntityName', max_depth=2)")
    print("  results = am.converge(['Clue1', 'Clue2'])")