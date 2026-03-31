# -*- coding: utf-8 -*-
"""
记忆清理脚本

功能：
- 清理 40 天前的 superseded 决策
- 清理半年前完成的待办
- 输出清理统计

使用：
    python cleanup_memory.py [--db-path PATH] [--dry-run]
    
参数：
    --db-path: 数据库路径（默认：D:\CoPaw\.copaw\.agent-memory\memory.db）
    --dry-run: 仅显示将要清理的内容，不实际删除
"""
import argparse
import sqlite3
from datetime import datetime
from pathlib import Path


def cleanup_memory(db_path: str, dry_run: bool = False) -> dict:
    """
    清理旧记忆记录
    
    Args:
        db_path: 数据库路径
        dry_run: 是否仅模拟运行
        
    Returns:
        清理统计
    """
    print(f"\n{'=' * 60}")
    print(f"记忆清理 {'[DRY RUN]' if dry_run else ''}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库: {db_path}")
    print(f"{'=' * 60}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取清理配置
    cursor.execute('SELECT decision_retention_days, todo_done_retention_days, last_cleanup FROM cleanup_config WHERE id = 1')
    config = cursor.fetchone()
    
    if config:
        decision_days = config[0]
        todo_days = config[1]
        last_cleanup = config[2]
    else:
        decision_days = 40
        todo_days = 180
        last_cleanup = None
    
    print(f"\n配置:")
    print(f"  - 决策保留: {decision_days} 天")
    print(f"  - 已完成待办保留: {todo_days} 天")
    print(f"  - 上次清理: {last_cleanup or '从未'}")
    
    result = {
        "dry_run": dry_run,
        "decision_days": decision_days,
        "todo_days": todo_days,
        "deleted_decisions": 0,
        "deleted_todos": 0,
    }
    
    # 1. 查找要清理的旧决策
    print(f"\n[1] 检查旧决策...")
    cursor.execute('''
        SELECT id, content, updated_at
        FROM facts 
        WHERE category = 'decision' 
        AND status = 'superseded' 
        AND updated_at IS NOT NULL
        AND datetime(updated_at) < datetime('now', '-' || ? || ' days')
    ''', (decision_days,))
    
    old_decisions = cursor.fetchall()
    print(f"  发现 {len(old_decisions)} 条可清理的旧决策")
    
    if old_decisions and dry_run:
        print(f"  示例:")
        for row in old_decisions[:3]:
            print(f"    - ID={row[0]}: {row[1][:50]}... (更新于 {row[2]})")
    
    # 2. 查找要清理的已完成待办
    print(f"\n[2] 检查已完成待办...")
    cursor.execute('''
        SELECT id, task, done_at
        FROM todos 
        WHERE status = 'done' 
        AND done_at IS NOT NULL
        AND datetime(done_at) < datetime('now', '-' || ? || ' days')
    ''', (todo_days,))
    
    old_todos = cursor.fetchall()
    print(f"  发现 {len(old_todos)} 条可清理的已完成待办")
    
    if old_todos and dry_run:
        print(f"  示例:")
        for row in old_todos[:3]:
            print(f"    - ID={row[0]}: {row[1][:50]}... (完成于 {row[2]})")
    
    # 3. 执行清理（非 dry-run 模式）
    if not dry_run:
        # 清理旧决策
        cursor.execute('''
            DELETE FROM facts 
            WHERE category = 'decision' 
            AND status = 'superseded' 
            AND updated_at IS NOT NULL
            AND datetime(updated_at) < datetime('now', '-' || ? || ' days')
        ''', (decision_days,))
        result["deleted_decisions"] = cursor.rowcount
        
        # 清理已完成待办
        cursor.execute('''
            DELETE FROM todos 
            WHERE status = 'done' 
            AND done_at IS NOT NULL
            AND datetime(done_at) < datetime('now', '-' || ? || ' days')
        ''', (todo_days,))
        result["deleted_todos"] = cursor.rowcount
        
        # 更新清理时间
        cursor.execute('UPDATE cleanup_config SET last_cleanup = CURRENT_TIMESTAMP WHERE id = 1')
        
        conn.commit()
        
        print(f"\n✅ 清理完成:")
        print(f"  - 删除旧决策: {result['deleted_decisions']} 条")
        print(f"  - 删除已完成待办: {result['deleted_todos']} 条")
    else:
        print(f"\n⚠️ DRY RUN 模式 - 未实际删除")
        print(f"  - 将删除旧决策: {len(old_decisions)} 条")
        print(f"  - 将删除已完成待办: {len(old_todos)} 条")
    
    # 4. 输出当前统计
    print(f"\n[统计]")
    
    cursor.execute('SELECT COUNT(*) FROM facts')
    print(f"  - 事实总数: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM facts WHERE category = 'decision' AND status = 'active'")
    print(f"  - 有效决策: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM facts WHERE category = 'decision' AND status = 'superseded'")
    print(f"  - 已废弃决策: {cursor.fetchone()[0]}")
    
    cursor.execute('SELECT COUNT(*) FROM experiences')
    print(f"  - 教训总数: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM todos WHERE status IN ('pending', 'in_progress')")
    print(f"  - 待办: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM todos WHERE status = 'done'")
    print(f"  - 已完成待办: {cursor.fetchone()[0]}")
    
    conn.close()
    
    print(f"\n{'=' * 60}")
    
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='记忆清理脚本')
    parser.add_argument('--db-path', default=r'D:\CoPaw\.copaw\.agent-memory\memory.db', help='数据库路径')
    parser.add_argument('--dry-run', action='store_true', help='仅模拟运行，不实际删除')
    
    args = parser.parse_args()
    
    cleanup_memory(args.db_path, args.dry_run)