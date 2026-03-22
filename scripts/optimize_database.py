"""
优化记忆数据库

功能：
- 清理孤立记录
- 修复记忆强度
- 补充实体定义

使用方法：
    python scripts/optimize_database.py

环境变量：
    MEMORY_DB_PATH - 数据库路径（默认：memory.db）
"""
import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(os.environ.get('MEMORY_DB_PATH', 'memory.db'))


def optimize_database():
    """优化数据库"""
    
    print("=" * 60)
    print("🔧 MemoryCoreClaw 数据库优化")
    print("=" * 60)
    print(f"\n数据库路径: {DB_PATH}\n")
    
    if not DB_PATH.exists():
        print("❌ 数据库文件不存在")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    changes = []
    
    # 1. 清理孤立的关系记录
    print("🔍 检查孤立关系记录...")
    cursor.execute("""
        DELETE FROM relations 
        WHERE id NOT IN (
            SELECT r.id FROM relations r
            LEFT JOIN entities e1 ON r.from_entity = e1.name
            LEFT JOIN entities e2 ON r.to_entity = e2.name
            WHERE e1.id IS NOT NULL OR e2.id IS NOT NULL
        )
    """)
    if cursor.rowcount > 0:
        changes.append(f"清理孤立关系：{cursor.rowcount} 条")
        print(f"   清理 {cursor.rowcount} 条孤立关系")
    else:
        print("   ✅ 无孤立关系")
    
    # 2. 修复记忆强度
    print("🔍 检查记忆强度...")
    cursor.execute("""
        SELECT f.id FROM facts f
        LEFT JOIN memory_strength ms ON ms.memory_id = f.id AND ms.memory_type = 'fact'
        WHERE ms.id IS NULL
    """)
    missing_strength = cursor.fetchall()
    for (fact_id,) in missing_strength:
        cursor.execute("""
            INSERT INTO memory_strength (memory_type, memory_id, base_strength, current_strength)
            VALUES ('fact', ?, 0.5, 0.5)
        """, (fact_id,))
    if missing_strength:
        changes.append(f"补充记忆强度：{len(missing_strength)} 条")
        print(f"   补充 {len(missing_strength)} 条记忆强度")
    else:
        print("   ✅ 记忆强度完整")
    
    # 3. 补充实体定义
    print("🔍 检查实体定义...")
    cursor.execute("""
        SELECT DISTINCT from_entity FROM relations
        UNION
        SELECT DISTINCT to_entity FROM relations
    """)
    entities_in_relations = set(row[0] for row in cursor.fetchall())
    
    cursor.execute("SELECT name FROM entities")
    existing_entities = set(row[0] for row in cursor.fetchall())
    
    new_entities = entities_in_relations - existing_entities
    for entity in new_entities:
        cursor.execute("""
            INSERT INTO entities (name, entity_type, importance, access_count)
            VALUES (?, 'auto', 0.5, 0)
        """, (entity,))
    
    if new_entities:
        changes.append(f"补充实体定义：{len(new_entities)} 条")
        print(f"   补充 {len(new_entities)} 个实体定义")
    else:
        print("   ✅ 实体定义完整")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    if changes:
        print("优化完成：")
        for change in changes:
            print(f"  ✅ {change}")
    else:
        print("✅ 数据库已是最优状态")
    print("=" * 60)


if __name__ == "__main__":
    optimize_database()