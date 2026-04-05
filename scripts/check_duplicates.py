"""
检查重复记忆

使用方法：
    python scripts/check_duplicates.py

环境变量：
    MEMORY_DB_PATH - 数据库路径
"""
import os
import sys
from pathlib import Path
from collections import Counter

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from memorycoreclaw import SafeMemory

DB_PATH = os.environ.get('MEMORY_DB_PATH', 'memory.db')


def check_duplicates():
    """检查重复的记忆"""
    
    print("=" * 60)
    print("🔍 检查重复记忆")
    print("=" * 60)
    
    mem = SafeMemory(DB_PATH)
    
    # 获取所有事实
    results = mem.recall("", limit=10000)
    
    # 检查内容重复
    contents = [r.get('content', '') for r in results]
    content_counts = Counter(contents)
    
    duplicates = {k: v for k, v in content_counts.items() if v > 1}
    
    if duplicates:
        print(f"\n发现 {len(duplicates)} 条重复内容：")
        for content, count in sorted(duplicates.items(), key=lambda x: -x[1]):
            short = content[:60] + "..." if len(content) > 60 else content
            print(f"  [{count}次] {short}")
    else:
        print("\n✅ 无重复记忆")
    
    print("=" * 60)
    return len(duplicates)


if __name__ == "__main__":
    check_duplicates()
