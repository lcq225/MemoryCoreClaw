"""
为关系表中的实体自动创建实体定义

使用方法：
    python scripts/create_entities_for_relations.py

环境变量：
    MEMORY_DB_PATH - 数据库路径
"""
import os
import sqlite3
from pathlib import Path

DB_PATH = os.environ.get('MEMORY_DB_PATH', 'memory.db')


def create_entities_for_relations():
    """为关系中的实体创建定义"""
    
    print("=" * 60)
    print("🔗 创建实体定义")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取所有实体
    cursor.execute("""
        SELECT DISTINCT from_entity FROM relations
        UNION
        SELECT DISTINCT to_entity FROM relations
    """)
    entities = set(row[0] for row in cursor.fetchall())
    
    # 获取已存在的实体
    cursor.execute("SELECT name FROM entities")
    existing = set(row[0] for row in cursor.fetchall())
    
    # 创建新实体
    new_entities = entities - existing
    created = 0
    
    for entity in new_entities:
        try:
            cursor.execute("""
                INSERT INTO entities (name, entity_type, importance, access_count)
                VALUES (?, 'auto', 0.5, 0)
            """, (entity,))
            created += 1
        except sqlite3.IntegrityError:
            pass
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ 创建了 {created} 个新实体定义")
    print(f"   总实体数：{len(entities)}")
    print("=" * 60)
    
    return created


if __name__ == "__main__":
    create_entities_for_relations()
