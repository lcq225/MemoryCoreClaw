#!/usr/bin/env python3
"""
MemoryCoreClaw - Standalone Tests

Run: python tests/standalone_test.py
"""

import tempfile
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_import():
    """Test that we can import the package"""
    from memorycoreclaw import Memory
    assert Memory is not None
    print("✅ test_import")


def test_create_memory():
    """Test creating a memory instance"""
    from memorycoreclaw import Memory
    
    temp_dir = tempfile.gettempdir()
    temp_db = os.path.join(temp_dir, "test_memory.db")
    
    if os.path.exists(temp_db):
        os.unlink(temp_db)
    
    try:
        mem = Memory(db_path=temp_db)
        assert mem is not None
        print("✅ test_create_memory")
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def test_remember_recall():
    """Test storing and recalling a fact"""
    from memorycoreclaw import Memory
    
    temp_dir = tempfile.gettempdir()
    temp_db = os.path.join(temp_dir, "test_remember.db")
    
    if os.path.exists(temp_db):
        os.unlink(temp_db)
    
    try:
        mem = Memory(db_path=temp_db)
        
        mem_id = mem.remember("Alice works at TechCorp", importance=0.8)
        assert mem_id > 0
        
        results = mem.recall("Alice")
        assert len(results) > 0
        assert "Alice" in results[0]['content']
        
        print("✅ test_remember_recall")
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def test_learn():
    """Test learning a lesson"""
    from memorycoreclaw import Memory
    
    temp_dir = tempfile.gettempdir()
    temp_db = os.path.join(temp_dir, "test_learn.db")
    
    if os.path.exists(temp_db):
        os.unlink(temp_db)
    
    try:
        mem = Memory(db_path=temp_db)
        
        lesson_id = mem.learn(
            action="Deployed without testing",
            context="Production release",
            outcome="negative",
            insight="Always test before deploying",
            importance=0.9
        )
        assert lesson_id > 0
        
        lessons = mem.get_lessons()
        assert len(lessons) > 0
        
        print("✅ test_learn")
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def test_relate():
    """Test creating and getting relations"""
    from memorycoreclaw import Memory
    
    temp_dir = tempfile.gettempdir()
    temp_db = os.path.join(temp_dir, "test_relate.db")
    
    if os.path.exists(temp_db):
        os.unlink(temp_db)
    
    try:
        mem = Memory(db_path=temp_db)
        
        rel_id = mem.relate("Alice", "works_at", "TechCorp")
        assert rel_id > 0
        
        relations = mem.get_relations("Alice")
        assert len(relations) > 0
        
        print("✅ test_relate")
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def test_working_memory():
    """Test working memory"""
    from memorycoreclaw import Memory
    
    temp_dir = tempfile.gettempdir()
    temp_db = os.path.join(temp_dir, "test_working.db")
    
    if os.path.exists(temp_db):
        os.unlink(temp_db)
    
    try:
        mem = Memory(db_path=temp_db)
        
        mem.hold("test_key", "test_value", priority=0.8)
        value = mem.retrieve("test_key")
        assert value == "test_value"
        
        print("✅ test_working_memory")
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def test_stats():
    """Test getting statistics"""
    from memorycoreclaw import Memory
    
    temp_dir = tempfile.gettempdir()
    temp_db = os.path.join(temp_dir, "test_stats.db")
    
    if os.path.exists(temp_db):
        os.unlink(temp_db)
    
    try:
        mem = Memory(db_path=temp_db)
        
        mem.remember("Test fact")
        mem.learn("Action", "Context", "neutral", "Insight")
        mem.relate("A", "knows", "B")
        
        stats = mem.get_stats()
        assert stats['facts'] >= 1
        assert stats['experiences'] >= 1
        assert stats['relations'] >= 1
        
        print("✅ test_stats")
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def test_export():
    """Test exporting memory"""
    from memorycoreclaw import Memory
    
    temp_dir = tempfile.gettempdir()
    temp_db = os.path.join(temp_dir, "test_export.db")
    
    if os.path.exists(temp_db):
        os.unlink(temp_db)
    
    try:
        mem = Memory(db_path=temp_db)
        
        mem.remember("Test fact for export")
        mem.relate("Alice", "works_at", "TechCorp")
        
        data = mem.export()
        assert 'facts' in data
        assert 'relations' in data
        assert len(data['facts']) > 0
        
        print("✅ test_export")
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


if __name__ == "__main__":
    print("=" * 50)
    print("MemoryCoreClaw Standalone Tests")
    print("=" * 50)
    
    test_import()
    test_create_memory()
    test_remember_recall()
    test_learn()
    test_relate()
    test_working_memory()
    test_stats()
    test_export()
    
    print("=" * 50)
    print("All tests passed!")
    print("=" * 50)