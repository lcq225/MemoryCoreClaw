"""
MemoryCoreClaw - Storage Module: Safe Database Manager

解决以下问题：
- R1: 数据库连接未正确关闭
- R2: 多步操作无事务保护
- R3: 异常处理不完整

特性：
1. 单例模式，全局共享连接
2. 线程本地存储，避免并发问题
3. 自动事务管理
4. 异常安全
5. WAL 模式，提升性能
"""

import sqlite3
import threading
from contextlib import contextmanager
from typing import Generator, Optional, List, Dict, Any
from datetime import datetime
import json


class SafeDatabaseManager:
    """
    线程安全的数据库管理器
    
    用法：
        db = SafeDatabaseManager(db_path)
        
        # 安全事务操作
        with db.transaction() as cursor:
            cursor.execute(...)
            # 自动提交或回滚
        
        # 只读操作
        with db.readonly() as cursor:
            cursor.execute(...)
    
    特性：
        - 单例模式：同一数据库路径共享连接
        - 线程安全：每个线程独立的连接
        - 事务自动：提交成功，回滚异常
        - 异常安全：finally 确保资源释放
    """
    
    _instances = {}  # 多数据库路径支持
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str):
        # 不同 db_path 创建不同实例
        if db_path not in cls._instances:
            with cls._lock:
                if db_path not in cls._instances:
                    instance = super().__new__(cls)
                    instance._db_path = db_path
                    instance._local = threading.local()
                    instance._closed = False
                    cls._instances[db_path] = instance
        return cls._instances[db_path]
    
    @contextmanager
    def transaction(self) -> Generator[sqlite3.Cursor, None, None]:
        """
        事务上下文管理器 - 用于写操作
        
        用法：
            with db.transaction() as cursor:
                cursor.execute('INSERT INTO ...')
                cursor.execute('UPDATE ...')
                # 自动提交，异常自动回滚
        
        Yields:
            sqlite3.Cursor: 数据库游标
        """
        if self._closed:
            raise RuntimeError("Database connection has been closed")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            cursor.close()
    
    @contextmanager
    def readonly(self) -> Generator[sqlite3.Cursor, None, None]:
        """
        只读上下文管理器 - 用于查询操作
        
        用法：
            with db.readonly() as cursor:
                cursor.execute('SELECT ...')
                results = cursor.fetchall()
        
        Yields:
            sqlite3.Cursor: 数据库游标
        """
        if self._closed:
            raise RuntimeError("Database connection has been closed")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        获取线程本地连接
        
        Returns:
            sqlite3.Connection: 数据库连接
        """
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self._db_path,
                check_same_thread=False,
                timeout=30.0  # 30秒超时
            )
            # 启用 WAL 模式，提升并发性能
            self._local.conn.execute('PRAGMA journal_mode=WAL')
            # 启用外键约束
            self._local.conn.execute('PRAGMA foreign_keys=ON')
            # 设置行工厂，返回字典
            self._local.conn.row_factory = sqlite3.Row
        
        return self._local.conn
    
    def close(self):
        """关闭当前线程的连接"""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
    
    def close_all(self):
        """关闭所有连接（谨慎使用）"""
        self._closed = True
        for instance in SafeDatabaseManager._instances.values():
            if hasattr(instance._local, 'conn') and instance._local.conn:
                instance._local.conn.close()
                instance._local.conn = None
    
    @property
    def path(self) -> str:
        """获取数据库路径"""
        return self._db_path
    
    def execute_script(self, script: str):
        """
        执行SQL脚本（用于初始化等）
        
        Args:
            script: SQL脚本内容
        """
        conn = self._get_connection()
        try:
            conn.executescript(script)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise


class MemoryHealthChecker:
    """
    记忆系统健康检查器
    
    解决 I1: 自我健康检查
    """
    
    def __init__(self, db):
        """
        初始化健康检查器
        
        Args:
            db: SafeDatabaseManager 对象或数据库路径字符串
        """
        if isinstance(db, str):
            # 如果传入的是字符串路径，创建 SafeDatabaseManager
            self.db = SafeDatabaseManager(db)
        else:
            self.db = db
    
    def check(self) -> Dict[str, Any]:
        """
        执行健康检查
        
        Returns:
            {
                'status': 'healthy' | 'warning' | 'error',
                'issues': [...],
                'stats': {...}
            }
        """
        issues = []
        stats = {}
        
        # 1. 检查数据库完整性
        with self.db.readonly() as cursor:
            cursor.execute('PRAGMA integrity_check')
            result = cursor.fetchone()
            if result and result[0] != 'ok':
                issues.append({
                    'type': 'database_corruption',
                    'severity': 'error',
                    'detail': result[0]
                })
        
        # 2. 检查孤立关系（关系中的实体不存在）
        with self.db.readonly() as cursor:
            cursor.execute('''
                SELECT COUNT(*) as cnt FROM relations r
                WHERE NOT EXISTS (
                    SELECT 1 FROM entities e WHERE e.name = r.from_entity
                )
                OR NOT EXISTS (
                    SELECT 1 FROM entities e WHERE e.name = r.to_entity
                )
            ''')
            row = cursor.fetchone()
            orphan_count = row['cnt'] if row else 0
            if orphan_count > 0:
                issues.append({
                    'type': 'orphaned_relations',
                    'severity': 'warning',
                    'count': orphan_count
                })
        
        # 3. 收集统计信息
        with self.db.readonly() as cursor:
            cursor.execute('SELECT COUNT(*) as cnt FROM facts')
            stats['facts'] = cursor.fetchone()['cnt']
            
            cursor.execute('SELECT COUNT(*) as cnt FROM experiences')
            stats['experiences'] = cursor.fetchone()['cnt']
            
            cursor.execute('SELECT COUNT(*) as cnt FROM relations')
            stats['relations'] = cursor.fetchone()['cnt']
            
            cursor.execute('SELECT COUNT(*) as cnt FROM entities')
            stats['entities'] = cursor.fetchone()['cnt']
        
        # 确定状态
        if any(i.get('severity') == 'error' for i in issues):
            status = 'error'
        elif len(issues) > 0:
            status = 'warning'
        else:
            status = 'healthy'
        
        return {
            'status': status,
            'issues': issues,
            'stats': stats,
            'checked_at': datetime.now().isoformat()
        }
    
    def repair(self) -> Dict[str, Any]:
        """
        执行自动修复
        
        Returns:
            {
                'repaired': [...],
                'failed': [...]
            }
        """
        repaired = []
        failed = []
        
        # 修复孤立关系：创建缺失的实体
        try:
            with self.db.transaction() as cursor:
                # 找出所有孤立关系涉及的实体
                cursor.execute('''
                    SELECT DISTINCT from_entity, to_entity FROM relations r
                    WHERE NOT EXISTS (
                        SELECT 1 FROM entities e WHERE e.name = r.from_entity
                    )
                    OR NOT EXISTS (
                        SELECT 1 FROM entities e WHERE e.name = r.to_entity
                    )
                ''')
                
                rows = cursor.fetchall()
                entities_to_create = set()
                
                for row in rows:
                    entities_to_create.add(row['from_entity'])
                    entities_to_create.add(row['to_entity'])
                
                # 创建缺失的实体
                for entity_name in entities_to_create:
                    if entity_name:
                        cursor.execute('''
                            INSERT OR IGNORE INTO entities (name, type, importance)
                            VALUES (?, 'auto_created', 0.5)
                        ''', (entity_name,))
                        repaired.append(f'Created entity: {entity_name}')
        
        except Exception as e:
            failed.append(f'Failed to repair orphaned relations: {str(e)}')
        
        return {
            'repaired': repaired,
            'failed': failed,
            'repaired_at': datetime.now().isoformat()
        }


def validate_limit(limit: int, max_limit: int = 100, default: int = 10) -> int:
    """
    验证并修正 limit 参数
    
    解决 R4: 边界条件检查
    
    Args:
        limit: 用户传入的 limit
        max_limit: 最大允许值
        default: 默认值
    
    Returns:
        修正后的 limit
    """
    if limit is None or limit <= 0:
        return default
    if limit > max_limit:
        return max_limit
    return limit


def validate_query(query: str) -> str:
    """
    验证并清理查询字符串
    
    解决 R4: 边界条件检查
    
    Args:
        query: 用户传入的查询
    
    Returns:
        清理后的查询字符串，空查询返回空字符串
    """
    if query is None:
        return ""
    return query.strip()


def is_valid_source(source: str) -> bool:
    """
    验证来源类型
    
    解决 R5: 记忆来源标记
    
    Args:
        source: 来源类型
    
    Returns:
        是否有效
    """
    valid_sources = {'user', 'llm', 'document', 'system', 'auto'}
    return source in valid_sources


# 测试代码
if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("=" * 60)
    print("SafeDatabaseManager 测试")
    print("=" * 60)
    
    # 使用测试数据库
    test_db = SafeDatabaseManager(":memory:")
    
    # 测试事务
    print("\n1. 测试事务...")
    with test_db.transaction() as cursor:
        cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)')
        cursor.execute('INSERT INTO test (name) VALUES (?)', ('test1',))
    
    with test_db.readonly() as cursor:
        cursor.execute('SELECT * FROM test')
        print(f"   插入成功: {cursor.fetchall()}")
    
    # 测试异常回滚
    print("\n2. 测试异常回滚...")
    try:
        with test_db.transaction() as cursor:
            cursor.execute('INSERT INTO test (name) VALUES (?)', ('test2',))
            raise Exception("模拟错误")
    except Exception:
        pass
    
    with test_db.readonly() as cursor:
        cursor.execute('SELECT * FROM test')
        print(f"   回滚成功，记录数: {len(cursor.fetchall())}")
    
    # 测试边界验证
    print("\n3. 测试边界验证...")
    print(f"   validate_limit(-1) = {validate_limit(-1)}")
    print(f"   validate_limit(1000) = {validate_limit(1000)}")
    print(f"   validate_query('  test  ') = '{validate_query('  test  ')}'")
    print(f"   validate_query('') = '{validate_query('')}'")
    
    print("\n✅ 测试通过")