# -*- coding: utf-8 -*-
"""
MemoryCoreClaw v2.0 数据库迁移脚本

新增功能：
- 决策生命周期管理（status, topic, superseded_by）
- 来源追踪（source, source_confidence, source_detail）
- 待办状态管理（todos 表）
- 决策变更日志（decision_changelog 表）
"""

import sqlite3
from pathlib import Path
from datetime import datetime


def migrate_v2(db_path: str):
    """执行 v2.0 数据库迁移"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"开始迁移数据库: {db_path}")
    print(f"时间: {datetime.now()}")
    
    # ========== 1. facts 表新增字段 ==========
    print("\n[1/4] 升级 facts 表...")
    
    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(facts)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    new_columns = {
        'status': "TEXT DEFAULT 'active' CHECK(status IN ('active', 'superseded', 'cancelled'))",
        'topic': 'TEXT',
        'source': "TEXT DEFAULT 'user' CHECK(source IN ('user', 'compaction', 'system', 'document'))",
        'source_confidence': 'REAL DEFAULT 1.0',
        'superseded_by': 'INTEGER REFERENCES facts(id)',
        'source_detail': 'TEXT',  # JSON
    }
    
    for col_name, col_def in new_columns.items():
        if col_name not in existing_columns:
            try:
                cursor.execute(f'ALTER TABLE facts ADD COLUMN {col_name} {col_def}')
                print(f"  ✅ 添加字段: {col_name}")
            except Exception as e:
                print(f"  ⚠️ 字段 {col_name} 添加失败: {e}")
        else:
            print(f"  ⏭️ 字段已存在: {col_name}")
    
    # 为现有记录设置默认值
    cursor.execute("UPDATE facts SET source = 'user', source_confidence = 1.0 WHERE source IS NULL")
    cursor.execute("UPDATE facts SET status = 'active' WHERE status IS NULL")
    
    # ========== 2. experiences 表新增字段 ==========
    print("\n[2/4] 升级 experiences 表...")
    
    cursor.execute("PRAGMA table_info(experiences)")
    existing_exp_columns = [col[1] for col in cursor.fetchall()]
    
    exp_new_columns = {
        'source': "TEXT DEFAULT 'user' CHECK(source IN ('user', 'compaction', 'system'))",
        'source_confidence': 'REAL DEFAULT 1.0',
        'source_detail': 'TEXT',
    }
    
    for col_name, col_def in exp_new_columns.items():
        if col_name not in existing_exp_columns:
            try:
                cursor.execute(f'ALTER TABLE experiences ADD COLUMN {col_name} {col_def}')
                print(f"  ✅ 添加字段: {col_name}")
            except Exception as e:
                print(f"  ⚠️ 字段 {col_name} 添加失败: {e}")
        else:
            print(f"  ⏭️ 字段已存在: {col_name}")
    
    # 为现有记录设置默认值
    cursor.execute("UPDATE experiences SET source = 'user', source_confidence = 1.0 WHERE source IS NULL")
    
    # ========== 3. 创建 todos 表 ==========
    print("\n[3/4] 创建 todos 表...")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            priority TEXT DEFAULT 'medium' CHECK(priority IN ('high', 'medium', 'low')),
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'done', 'cancelled')),
            source TEXT DEFAULT 'user',
            source_confidence REAL DEFAULT 1.0,
            extraction_id TEXT,
            related_decision_id INTEGER REFERENCES facts(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            done_at TIMESTAMP,
            notes TEXT
        )
    ''')
    print("  ✅ 创建 todos 表")
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_todos_status ON todos(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_todos_priority ON todos(priority)')
    
    # ========== 4. 创建 decision_changelog 表 ==========
    print("\n[4/4] 创建 decision_changelog 表...")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS decision_changelog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            old_decision_id INTEGER NOT NULL REFERENCES facts(id),
            new_decision_id INTEGER REFERENCES facts(id),
            old_content TEXT NOT NULL,
            new_content TEXT NOT NULL,
            topic TEXT,
            change_type TEXT CHECK(change_type IN ('update', 'cancel', 'restore')),
            change_reason TEXT,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            extraction_id TEXT
        )
    ''')
    print("  ✅ 创建 decision_changelog 表")
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_changelog_topic ON decision_changelog(topic)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_changelog_time ON decision_changelog(changed_at)')
    
    # ========== 5. 创建清理任务配置表 ==========
    print("\n[额外] 创建清理配置表...")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cleanup_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            decision_retention_days INTEGER DEFAULT 40,
            todo_done_retention_days INTEGER DEFAULT 180,
            last_cleanup TIMESTAMP
        )
    ''')
    
    # 插入默认配置
    cursor.execute('''
        INSERT OR IGNORE INTO cleanup_config (id, decision_retention_days, todo_done_retention_days)
        VALUES (1, 40, 180)
    ''')
    print("  ✅ 创建 cleanup_config 表")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 50)
    print("✅ 迁移完成！")
    print("=" * 50)
    
    return True


def verify_migration(db_path: str):
    """验证迁移结果"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n验证迁移结果:")
    
    # 检查 facts 表字段
    cursor.execute("PRAGMA table_info(facts)")
    facts_columns = [col[1] for col in cursor.fetchall()]
    print(f"  facts 表字段: {len(facts_columns)} 个")
    
    # 检查新表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    new_tables = ['todos', 'decision_changelog', 'cleanup_config']
    for table in new_tables:
        if table in tables:
            print(f"  ✅ {table} 表存在")
        else:
            print(f"  ❌ {table} 表不存在")
    
    conn.close()
    
    return True


if __name__ == '__main__':
    db_path = os.environ.get("MEMORY_DB_PATH", "memory.db")
    
    # 执行迁移
    migrate_v2(db_path)
    
    # 验证
    verify_migration(db_path)
    
    # 测试写入
    print("\n测试写入...")
    from enhanced_memory import get_enhanced_memory
    mem = get_enhanced_memory(db_path)
    
    # 测试添加待办
    todo_id = mem.add_todo("测试待办", priority="high", source="test")
    print(f"添加待办 ID: {todo_id}")
    
    # 测试获取待办
    todos = mem.get_pending_todos()
    print(f"当前待办: {len(todos)} 条")
    
    # 清理测试数据
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM todos WHERE task = '测试待办'")
    conn.commit()
    conn.close()
    print("测试数据已清理")