#!/usr/bin/env python3
"""
MemoryCoreClaw - Basic Usage Example

Demonstrates the simplified Memory API.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memorycoreclaw import Memory


def main():
    # Create a memory instance
    print("=== MemoryCoreClaw Example ===\n")
    
    # Use a temporary database for this example
    import tempfile
    import os
    temp_dir = tempfile.gettempdir()
    temp_db = os.path.join(temp_dir, "memorycoreclaw_example.db")
    
    # Clean up if exists
    if os.path.exists(temp_db):
        os.unlink(temp_db)
    
    try:
        mem = Memory(db_path=temp_db)
        
        # ===== Store Facts =====
        print("Storing facts...")
        mem.remember("Alice works at TechCorp", importance=0.8, tags=["person", "work"])
        mem.remember("Alice knows Python", importance=0.7, tags=["person", "skill"])
        mem.remember("Bob is Alice's manager", importance=0.6, tags=["person", "work"])
        mem.remember("TechCorp uses Python and Go", importance=0.5, tags=["company", "tech"])
        
        # ===== Store Lessons =====
        print("Storing lessons...")
        mem.learn(
            action="Deployed without testing",
            context="Production release on Friday",
            outcome="negative",
            insight="Never deploy on Friday without testing",
            importance=0.9
        )
        
        mem.learn(
            action="Documented API before coding",
            context="New feature development",
            outcome="positive",
            insight="Documentation-first approach improves design",
            importance=0.8
        )
        
        # ===== Create Relations =====
        print("Creating relations...")
        mem.relate("Alice", "works_at", "TechCorp")
        mem.relate("Alice", "knows", "Bob")
        mem.relate("Bob", "manages", "Alice")
        mem.relate("TechCorp", "uses", "Python")
        
        # ===== Search Memories =====
        print("\nSearching memories...")
        results = mem.recall("Alice")
        print(f"  Found {len(results)} memories about 'Alice':")
        for r in results[:3]:
            print(f"    - {r['content']}")
        
        # ===== Get Relations =====
        print("\nGetting relations for 'Alice'...")
        relations = mem.get_relations("Alice")
        for rel in relations:
            print(f"    {rel['from_entity']} --[{rel['relation_type']}]--> {rel['to_entity']}")
        
        # ===== Get Lessons =====
        print("\nLearned lessons:")
        lessons = mem.get_lessons()
        for i, lesson in enumerate(lessons, 1):
            print(f"  {i}. {lesson['insight']}")
        
        # ===== Working Memory =====
        print("\nUsing working memory...")
        mem.hold("current_task", "Writing documentation", priority=0.9)
        mem.hold("temp_data", {"key": "value"}, ttl=60)
        
        task = mem.retrieve("current_task")
        print(f"  Current task: {task}")
        
        # ===== Statistics =====
        print("\nMemory statistics:")
        stats = mem.get_stats()
        print(f"  Facts: {stats['facts']}")
        print(f"  Lessons: {stats['experiences']}")
        print(f"  Relations: {stats['relations']}")
        print(f"  Entities: {stats['entities']}")
        
        # ===== Export =====
        print("\nExporting memory...")
        data = mem.export()
        print(f"  Exported {len(data.get('facts', []))} facts")
        print(f"  Exported {len(data.get('experiences', []))} lessons")
        print(f"  Exported {len(data.get('relations', []))} relations")
        
    finally:
        # Clean up
        if os.path.exists(temp_db):
            os.unlink(temp_db)
    
    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()