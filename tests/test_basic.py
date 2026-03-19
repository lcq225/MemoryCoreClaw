"""
MemoryCoreClaw - Basic Tests

Run: pytest tests/test_basic.py -v
"""

import pytest
import tempfile
import os
from pathlib import Path

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMemoryEngine:
    """Test MemoryEngine basic operations"""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            yield f.name
        os.unlink(f.name)
    
    def test_import(self):
        """Test that we can import the package"""
        from memorycoreclaw import Memory
        assert Memory is not None
    
    def test_create_memory(self, temp_db):
        """Test creating a memory instance"""
        from memorycoreclaw import Memory
        mem = Memory(db_path=temp_db)
        assert mem is not None
    
    def test_remember(self, temp_db):
        """Test storing a fact"""
        from memorycoreclaw import Memory
        mem = Memory(db_path=temp_db)
        
        mem_id = mem.remember("Alice works at TechCorp", importance=0.8)
        assert mem_id > 0
    
    def test_recall(self, temp_db):
        """Test recalling a fact"""
        from memorycoreclaw import Memory
        mem = Memory(db_path=temp_db)
        
        mem.remember("Alice works at TechCorp", importance=0.8)
        results = mem.recall("Alice")
        
        assert len(results) > 0
        assert "Alice" in results[0]['content']
    
    def test_learn(self, temp_db):
        """Test learning a lesson"""
        from memorycoreclaw import Memory
        mem = Memory(db_path=temp_db)
        
        lesson_id = mem.learn(
            action="Deployed without testing",
            context="Production release",
            outcome="negative",
            insight="Always test before deploying",
            importance=0.9
        )
        assert lesson_id > 0
    
    def test_get_lessons(self, temp_db):
        """Test getting lessons"""
        from memorycoreclaw import Memory
        mem = Memory(db_path=temp_db)
        
        mem.learn("Action", "Context", "negative", "Insight")
        lessons = mem.get_lessons()
        
        assert len(lessons) > 0
    
    def test_relate(self, temp_db):
        """Test creating a relation"""
        from memorycoreclaw import Memory
        mem = Memory(db_path=temp_db)
        
        rel_id = mem.relate("Alice", "works_at", "TechCorp")
        assert rel_id > 0
    
    def test_get_relations(self, temp_db):
        """Test getting relations"""
        from memorycoreclaw import Memory
        mem = Memory(db_path=temp_db)
        
        mem.relate("Alice", "works_at", "TechCorp")
        relations = mem.get_relations("Alice")
        
        assert len(relations) > 0
    
    def test_get_stats(self, temp_db):
        """Test getting statistics"""
        from memorycoreclaw import Memory
        mem = Memory(db_path=temp_db)
        
        mem.remember("Test fact")
        mem.learn("Action", "Context", "neutral", "Insight")
        mem.relate("A", "knows", "B")
        
        stats = mem.get_stats()
        assert stats['facts'] >= 1
        assert stats['experiences'] >= 1
        assert stats['relations'] >= 1


class TestCognitive:
    """Test cognitive modules"""
    
    def test_forgetting_curve(self):
        """Test forgetting curve calculation"""
        from memorycoreclaw.cognitive import ForgettingCurve
        
        fc = ForgettingCurve()
        
        # Test retention calculation
        retention = fc.calculate_retention(1, 0.8)  # 1 day, strength 0.8
        assert 0 < retention <= 1
        
        # Test retention decreases over time
        retention_1d = fc.calculate_retention(1, 0.8)
        retention_30d = fc.calculate_retention(30, 0.8)
        assert retention_1d > retention_30d
    
    def test_working_memory(self):
        """Test working memory"""
        from memorycoreclaw.cognitive import WorkingMemory
        
        wm = WorkingMemory(capacity=5)
        
        # Test hold and retrieve
        wm.hold("key1", "value1")
        assert wm.retrieve("key1") == "value1"
        
        # Test capacity limit
        for i in range(10):
            wm.hold(f"key{i}", f"value{i}", priority=i/10)
        
        assert len(wm.items) <= 5
    
    def test_heuristic(self):
        """Test heuristic engine"""
        from memorycoreclaw.cognitive import HeuristicEngine
        
        he = HeuristicEngine()
        
        schemas = he.recognize("Why did this happen? How can I fix it?")
        assert len(schemas) > 0
        assert 'problem_solving' in [s.name for s in schemas]


class TestRetrieval:
    """Test retrieval modules"""
    
    def test_semantic_search(self):
        """Test semantic search"""
        from memorycoreclaw.retrieval import SemanticSearch
        
        ss = SemanticSearch()
        
        # Index documents
        ss.index(1, "Alice works at TechCorp")
        ss.index(2, "Bob works at StartupX")
        ss.index(3, "Python is a programming language")
        
        # Search
        results = ss.search("Alice")
        assert len(results) > 0
    
    def test_ontology(self):
        """Test ontology engine"""
        from memorycoreclaw.retrieval import OntologyEngine
        
        ont = OntologyEngine()
        
        # Test relation inference
        rel, conf = ont.infer_relation("Alice", "TechCorp Inc")
        assert rel == 'works_at'
        
        # Test inverse
        inverse = ont.get_inverse('works_at')
        assert inverse == 'employs'


class TestMemoryAPI:
    """Test simplified Memory API"""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            yield f.name
        os.unlink(f.name)
    
    def test_memory_api(self, temp_db):
        """Test Memory API"""
        from memorycoreclaw import Memory
        
        mem = Memory(db_path=temp_db)
        
        # Test remember
        mem.remember("Alice is a Python developer", importance=0.8, tags=["person", "skill"])
        
        # Test recall
        results = mem.recall("Alice")
        assert len(results) > 0
        
        # Test learn
        mem.learn(
            action="Forgot to backup",
            context="Before upgrade",
            outcome="negative",
            insight="Always backup before upgrades",
            importance=0.9
        )
        
        # Test relate
        mem.relate("Alice", "knows", "Bob")
        
        # Test get_stats
        stats = mem.get_stats()
        assert isinstance(stats, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])