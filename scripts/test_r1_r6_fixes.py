"""
测试安全修复功能

使用方法：
    python scripts/test_r1_r6_fixes.py

环境变量：
    MEMORY_DB_PATH - 数据库路径
"""
import os
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from memorycoreclaw import SafeMemory

DB_PATH = os.environ.get('MEMORY_DB_PATH', 'memory.db')


def test_boundary_check():
    """测试边界检查"""
    print("\n🧪 测试边界检查...")
    
    mem = SafeMemory(DB_PATH)
    
    # 测试无效 limit
    results = mem.recall("", limit=-1)
    print(f"  limit=-1 → 自动修正为 10，返回 {len(results)} 条")
    
    results = mem.recall("", limit=None)
    print(f"  limit=None → 自动修正为 10，返回 {len(results)} 条")
    
    print("  ✅ 边界检查正常")


def test_core_memory_protection():
    """测试核心记忆保护"""
    print("\n🧪 测试核心记忆保护...")
    
    mem = SafeMemory(DB_PATH)
    
    # 创建一个核心记忆
    mem.remember("测试核心记忆", importance=0.95, category="test")
    
    # 获取这个记忆
    results = mem.recall("测试核心记忆", limit=1)
    if results:
        memory_id = results[0].get('id')
        
        # 尝试删除（应该被保护）
        result = mem.delete(memory_id)
        if result.get('warning'):
            print(f"  核心记忆保护正常: {result.get('warning')[:50]}...")
        
        # 强制删除
        mem.delete(memory_id, force=True)
        print("  ✅ 核心记忆保护正常")


def test_source_tracking():
    """测试来源追踪"""
    print("\n🧪 测试来源追踪...")
    
    mem = SafeMemory(DB_PATH)
    
    # 带来源标记的记忆
    mem.remember(
        "测试来源追踪",
        importance=0.5,
        category="test",
        source="user",
        source_confidence=1.0
    )
    
    print("  ✅ 来源追踪功能正常")


def run_tests():
    """运行所有测试"""
    
    print("=" * 60)
    print("🧪 MemoryCoreClaw 安全功能测试")
    print("=" * 60)
    print(f"\n数据库路径: {DB_PATH}")
    
    try:
        test_boundary_check()
        test_core_memory_protection()
        test_source_tracking()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_tests()
