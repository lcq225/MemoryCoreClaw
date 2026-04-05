# -*- coding: utf-8 -*-
"""
任务追踪系统 - 确保任务闭环执行
为每个任务提供状态管理、进度追踪、结果验证
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from functools import wraps

# 配置
MEMORY_DB = r"memory.db"
TASK_DB = r"tasks.db"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"        # 待执行
    RUNNING = "running"       # 执行中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败
    CANCELLED = "cancelled"    # 已取消


@dataclass
class Task:
    """任务"""
    id: str
    name: str
    description: str
    status: str
    created_at: str
    updated_at: str
    completed_at: str = ""
    result: str = ""
    error: str = ""
    progress: int = 0  # 0-100
    tags: str = ""


class TaskTracker:
    """
    任务追踪器
    
    功能：
    - 创建任务并追踪状态
    - 记录进度
    - 验证结果
    - 异常处理
    """
    
    def __init__(self):
        self._init_db()
        self.current_task = None
        
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(TASK_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                updated_at TEXT,
                completed_at TEXT,
                result TEXT,
                error TEXT,
                progress INTEGER DEFAULT 0,
                tags TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_task(self, name: str, description: str = "", 
                    tags: str = "") -> str:
        """创建任务"""
        import uuid
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(TASK_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tasks (id, name, description, status, created_at, updated_at, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (task_id, name, description, TaskStatus.PENDING.value, now, now, tags))
        
        conn.commit()
        conn.close()
        
        self.current_task = task_id
        print(f"\n📋 任务创建: {name} [{task_id}]")
        
        return task_id
    
    def start_task(self, task_id: str):
        """开始任务"""
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(TASK_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tasks SET status = ?, updated_at = ?
            WHERE id = ?
        ''', (TaskStatus.RUNNING.value, now, task_id))
        
        conn.commit()
        conn.close()
        
        print(f"▶️  任务开始: {task_id}")
    
    def update_progress(self, task_id: str, progress: int, message: str = ""):
        """更新进度"""
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(TASK_DB)
        cursor = conn.cursor()
        
        # 构建结果消息
        result = f"[{progress}%] {message}" if message else f"[{progress}%] 进行中"
        
        cursor.execute('''
            UPDATE tasks SET progress = ?, result = ?, updated_at = ?
            WHERE id = ?
        ''', (progress, result, now, task_id))
        
        conn.commit()
        conn.close()
    
    def complete_task(self, task_id: str, result: str = ""):
        """完成任务"""
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(TASK_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tasks SET status = ?, completed_at = ?, result = ?, 
            progress = 100, updated_at = ?
            WHERE id = ?
        ''', (TaskStatus.COMPLETED.value, now, result, now, task_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 任务完成: {task_id}")
        if result:
            print(f"   结果: {result[:100]}")
    
    def fail_task(self, task_id: str, error: str):
        """任务失败"""
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(TASK_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tasks SET status = ?, error = ?, updated_at = ?
            WHERE id = ?
        ''', (TaskStatus.FAILED.value, error[:500], now, task_id))
        
        conn.commit()
        conn.close()
        
        print(f"❌ 任务失败: {task_id}")
        print(f"   错误: {error[:100]}")
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        conn = sqlite3.connect(TASK_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return Task(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                status=row['status'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                completed_at=row['completed_at'] or "",
                result=row['result'] or "",
                error=row['error'] or "",
                progress=row['progress'],
                tags=row['tags'] or ""
            )
        return None
    
    def list_tasks(self, status: str = None, limit: int = 10) -> List[Task]:
        """列出任务"""
        conn = sqlite3.connect(TASK_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status:
            cursor.execute('''
                SELECT * FROM tasks WHERE status = ? 
                ORDER BY updated_at DESC LIMIT ?
            ''', (status, limit))
        else:
            cursor.execute('''
                SELECT * FROM tasks ORDER BY updated_at DESC LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [Task(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            status=row['status'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            completed_at=row['completed_at'] or "",
            result=row['result'] or "",
            error=row['error'] or "",
            progress=row['progress'],
            tags=row['tags'] or ""
        ) for row in rows]
    
    def tracked(self, name: str = None):
        """装饰器：追踪任务执行"""
        def decorator(func: Callable):
            task_name = name or func.__name__
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                tracker = TaskTracker()
                task_id = tracker.create_task(task_name)
                
                try:
                    tracker.start_task(task_id)
                    tracker.update_progress(task_id, 10, "开始执行...")
                    
                    result = func(*args, **kwargs)
                    
                    tracker.update_progress(task_id, 90, "执行完成")
                    tracker.complete_task(task_id, str(result)[:200])
                    
                    return result
                    
                except Exception as e:
                    tracker.fail_task(task_id, str(e))
                    raise
            
            return wrapper
        return decorator
    
    def get_stats(self) -> Dict:
        """获取统计"""
        conn = sqlite3.connect(TASK_DB)
        cursor = conn.cursor()
        
        stats = {}
        
        for status in TaskStatus:
            cursor.execute('''
                SELECT COUNT(*) FROM tasks WHERE status = ?
            ''', (status.value,))
            stats[status.value] = cursor.fetchone()[0]
        
        conn.close()
        
        return stats


# 全局实例
task_tracker = TaskTracker()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="任务追踪系统")
    parser.add_argument("--list", "-l", action="store_true", help="列出任务")
    parser.add_argument("--stats", "-s", action="store_true", help="显示统计")
    parser.add_argument("--running", "-r", action="store_true", help="显示进行中的任务")
    args = parser.parse_args()
    
    tracker = TaskTracker()
    
    if args.stats:
        stats = tracker.get_stats()
        print("\n📊 任务统计")
        print("=" * 40)
        print(f"  待执行: {stats.get('pending', 0)}")
        print(f"  进行中: {stats.get('running', 0)}")
        print(f"  已完成: {stats.get('completed', 0)}")
        print(f"  失败: {stats.get('failed', 0)}")
        print(f"  已取消: {stats.get('cancelled', 0)}")
    
    elif args.running:
        tasks = tracker.list_tasks(TaskStatus.RUNNING.value)
        print("\n🔄 进行中的任务")
        print("=" * 40)
        for t in tasks:
            print(f"  [{t.id}] {t.name} - {t.progress}%")
    
    elif args.list:
        tasks = tracker.list_tasks(limit=10)
        print("\n📋 最近任务")
        print("=" * 40)
        status_emoji = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "cancelled": "🚫"
        }
        for t in tasks:
            emoji = status_emoji.get(t.status, "❓")
            print(f"  {emoji} {t.name} ({t.status}) - {t.progress}%")
    else:
        print("用法:")
        print("  python task_tracker.py --list      # 列出最近任务")
        print("  python task_tracker.py --stats     # 显示统计")
        print("  python task_tracker.py --running    # 显示进行中任务")
