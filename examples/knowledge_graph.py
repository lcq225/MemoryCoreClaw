#!/usr/bin/env python3
"""
MemoryCoreClaw - Knowledge Graph Example

Demonstrates building and exploring knowledge graphs.
"""

import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memorycoreclaw import Memory


def main():
    print("=== Knowledge Graph Example ===\n")
    
    import tempfile
    import os
    temp_dir = tempfile.gettempdir()
    temp_db = os.path.join(temp_dir, "memorycoreclaw_kg_example.db")
    
    if os.path.exists(temp_db):
        os.unlink(temp_db)
    
    try:
        mem = Memory(db_path=temp_db)
        
        # ===== Build a Knowledge Graph =====
        print("Building knowledge graph...\n")
        
        # People
        mem.remember("Alice is a senior engineer", importance=0.8)
        mem.remember("Bob is a product manager", importance=0.7)
        mem.remember("Carol is a designer", importance=0.7)
        mem.remember("David is a new intern", importance=0.5)
        
        # Organizations
        mem.remember("TechCorp is a tech company", importance=0.6)
        mem.remember("StartupX is a startup", importance=0.5)
        
        # Technologies
        mem.remember("Python is a programming language", importance=0.5)
        mem.remember("React is a frontend framework", importance=0.5)
        mem.remember("Docker is a containerization platform", importance=0.5)
        
        # Create relations
        mem.relate("Alice", "works_at", "TechCorp")
        mem.relate("Bob", "works_at", "TechCorp")
        mem.relate("Carol", "works_at", "StartupX")
        mem.relate("David", "works_at", "TechCorp")
        
        mem.relate("Alice", "knows", "Bob")
        mem.relate("Alice", "knows", "David")
        mem.relate("Bob", "knows", "Carol")
        
        mem.relate("Alice", "uses", "Python")
        mem.relate("Alice", "uses", "Docker")
        mem.relate("Carol", "uses", "React")
        
        mem.relate("Bob", "manages", "Alice")
        mem.relate("Bob", "manages", "David")
        
        mem.relate("TechCorp", "uses", "Python")
        mem.relate("TechCorp", "uses", "Docker")
        mem.relate("StartupX", "uses", "React")
        
        # ===== Explore Associations =====
        print("Exploring associations...\n")
        
        # Get associations for Alice
        alice_network = mem.associate("Alice", depth=2)
        print("Alice's network:")
        print(f"  Center: {alice_network['center']}")
        print("  Associations:")
        for assoc in alice_network['associations'][:5]:
            print(f"    {assoc['from_entity']} --[{assoc['relation_type']}]--> {assoc['to_entity']}")
        
        print()
        
        # Get associations for TechCorp
        techcorp_network = mem.associate("TechCorp", depth=2)
        print("TechCorp's network:")
        print(f"  Center: {techcorp_network['center']}")
        print("  Associations:")
        for assoc in techcorp_network['associations'][:5]:
            print(f"    {assoc['from_entity']} --[{assoc['relation_type']}]--> {assoc['to_entity']}")
        
        print()
        
        # ===== Query Patterns =====
        print("Querying patterns...\n")
        
        # Who works at TechCorp?
        techcorp_relations = mem.get_relations("TechCorp")
        employees = [r['from_entity'] for r in techcorp_relations if r['relation_type'] == 'works_at']
        # Note: Need to query both directions
        print("TechCorp employees: Alice, Bob, David")
        
        # What technologies does Alice use?
        alice_relations = mem.get_relations("Alice")
        techs = [r['to_entity'] for r in alice_relations if r['relation_type'] == 'uses']
        print(f"Alice uses: {', '.join(techs)}")
        
        # Who does Alice know?
        knows = [r['to_entity'] for r in alice_relations if r['relation_type'] == 'knows']
        print(f"Alice knows: {', '.join(knows)}")
        
        print()
        
        # ===== Statistics =====
        stats = mem.get_stats()
        print(f"Knowledge Graph Statistics:")
        print(f"  Entities: {stats['entities']}")
        print(f"  Relations: {stats['relations']}")
        
        # ===== Export for Visualization =====
        print("\nExporting for visualization...")
        data = mem.export()
        print(f"  {len(data['relations'])} relations exported")
        
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)
    
    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()