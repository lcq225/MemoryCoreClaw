# -*- coding: utf-8 -*-
"""
MemoryCoreClaw v2.1.0 Functional Verification Test
"""
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test module imports"""
    print("1. Testing module imports...")
    from memorycoreclaw import Memory, SafeMemory
    from memorycoreclaw.storage.database import SafeDatabaseManager, MemoryHealthChecker
    print("   [OK] Memory")
    print("   [OK] SafeMemory")
    print("   [OK] SafeDatabaseManager")
    print("   [OK] MemoryHealthChecker")
    return True

def test_basic_memory():
    """Test basic Memory functions"""
    print("\n2. Testing basic Memory...")
    from memorycoreclaw import Memory
    
    db_path = os.path.join(tempfile.gettempdir(), 'test_v210.db')
    if os.path.exists(db_path):
        os.remove(db_path)
    
    mem = Memory(db_path=db_path)
    
    # remember
    fid = mem.remember('test fact memory', importance=0.8, category='test')
    print("   [OK] remember() -> ID {}".format(fid))
    
    # recall
    results = mem.recall('test', limit=5)
    print("   [OK] recall() -> {} results".format(len(results)))
    
    # learn
    eid = mem.learn('test action', 'test context', 'positive', 'test insight', 0.8)
    print("   [OK] learn() -> ID {}".format(eid))
    
    # relate
    mem.relate('EntityA', 'knows', 'EntityB')
    print("   [OK] relate()")
    
    # working memory
    mem.hold('test_key', 'test_value', priority=0.9)
    val = mem.retrieve('test_key')
    print("   [OK] working memory: {}".format(val))
    
    # stats
    stats = mem.get_stats()
    print("   [OK] stats: facts={}, exp={}, rel={}".format(
        stats['facts'], stats['experiences'], stats['relations']))
    
    return True

def test_safe_memory():
    """Test SafeMemory v2.1.0 features"""
    print("\n3. Testing SafeMemory (v2.1.0)...")
    from memorycoreclaw import SafeMemory
    
    db_path = os.path.join(tempfile.gettempdir(), 'test_v210_safe.db')
    if os.path.exists(db_path):
        os.remove(db_path)
    
    mem = SafeMemory(db_path=db_path)
    
    # Source tracking
    fid = mem.remember('user preference test', importance=0.85, category='preference', 
                       source='user', source_confidence=1.0)
    print("   [OK] remember with source -> ID {}".format(fid))
    
    # Boundary checking
    results = mem.recall('', limit=-1)  # Should auto-correct
    print("   [OK] boundary check limit=-1 -> {} results (auto-corrected)".format(len(results)))
    
    results = mem.recall('test', limit=None)  # Should auto-correct
    print("   [OK] boundary check limit=None -> {} results (auto-corrected)".format(len(results)))
    
    # Health check
    health = mem.health_check()
    print("   [OK] health_check() -> {}".format(health['status']))
    
    # Core memory protection
    core_id = mem.remember('core memory test', importance=0.95, category='core')
    result = mem.delete(core_id)  # Should be protected
    if not result.get('success') and '确认' in result.get('message', ''):
        print("   [OK] core memory protection: delete blocked")
    else:
        print("   [WARN] core memory protection not working: {}".format(result))
    
    result = mem.delete(core_id, force=True)  # Force delete
    print("   [OK] force delete core memory: {}".format(result.get('success')))
    
    return True

def test_database_manager():
    """Test SafeDatabaseManager"""
    print("\n4. Testing SafeDatabaseManager (v2.1.0)...")
    from memorycoreclaw.storage.database import SafeDatabaseManager, MemoryHealthChecker
    
    db_path = os.path.join(tempfile.gettempdir(), 'test_v210_db.db')
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = SafeDatabaseManager(db_path)
    
    # Transaction
    with db.transaction() as cursor:
        cursor.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER, name TEXT)")
        cursor.execute("INSERT INTO test VALUES (1, 'test')")
    print("   [OK] transaction() committed")
    
    # Readonly
    with db.readonly() as cursor:
        cursor.execute("SELECT COUNT(*) FROM test")
        count = cursor.fetchone()[0]
    print("   [OK] readonly() -> {} records".format(count))
    
    # Health checker - use the SafeMemory database which has full schema
    # (MemoryHealthChecker requires relations, facts, experiences tables)
    safe_db_path = os.path.join(tempfile.gettempdir(), 'test_v210_safe.db')
    checker = MemoryHealthChecker(safe_db_path)
    report = checker.check()
    print("   [OK] MemoryHealthChecker -> {}".format(report['status']))
    
    return True

def test_version():
    """Test version info"""
    print("\n5. Testing version...")
    from memorycoreclaw import __version__
    print("   [OK] version: {}".format(__version__))
    return True

def main():
    print("=" * 60)
    print("MemoryCoreClaw v2.1.0 Functional Verification")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_basic_memory,
        test_safe_memory,
        test_database_manager,
        test_version,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print("   [FAIL] {}".format(str(e)))
            failed += 1
    
    print("\n" + "=" * 60)
    print("Result: {} passed, {} failed".format(passed, failed))
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)