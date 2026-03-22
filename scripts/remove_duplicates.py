"""
移除重复记忆

使用方法：
    python scripts/remove_duplicates.py

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


def remove_duplicates():
    """移除重复的记忆（保留最早的一条）"""
    
    print("=" * 60)
    print("🗑️ 移除重复记忆")
    print("=" * 60)
    
    mem = SafeMemory(DB_PATH)
    
    # 获取所有事实
    results = mem.recall("", limit=10000)
    
    # 按内容分组
    content_ids = {}
    for r in results:
        content = r.get('content', '')
        if content not in content_ids:
            content_ids[content] = []
        content_ids[content].append(r.get('id'))
    
    # 找出重复的
    duplicates = {k: v for k, v in content_ids.items() if len(v) > 1}
    
    if not duplicates:
        print("\n✅ 无重复记忆")
        return 0
    
    # 删除重复的（保留第一条）
    removed = 0
    for content, ids in duplicates.items():
        for id in ids[1:]:  # 保留第一条
            mem.delete(id)
            removed += 1
    
    print(f"\n✅ 移除了 {removed} 条重复记忆")
    print(f"   保留了 {len(duplicates)} 条唯一记忆")
    print("=" * 60)
    
    return removed


if __name__ == "__main__":
    remove_duplicates()