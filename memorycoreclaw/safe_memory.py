"""
MemoryCoreClaw - Safe Memory Engine Wrapper

整合所有安全修复：
- R1: 数据库连接管理
- R2: 事务边界保护
- R3: 异常处理完善
- R4: 边界条件检查
- R5: 记忆来源标记
- R6: 防误删除机制

用法：
    from safe_memory import SafeMemory
    
    mem = SafeMemory(db_path)
    
    # 带来源的记忆存储
    mem.remember("Mr Lee 喜欢高效沟通", source="user")
    
    # 带边界检查的检索
    results = mem.recall("", limit=-1)  # 自动修正为默认值
    
    # 带保护的删除
    mem.delete(1)  # 核心记忆需要确认
    mem.delete(1, force=True)  # 强制删除
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import sqlite3

# 导入安全数据库管理器
import sys
from pathlib import Path

# 处理两种导入方式
try:
    # 作为包导入时
    from .storage.database import (
        SafeDatabaseManager, 
        MemoryHealthChecker,
        validate_limit, 
        validate_query,
        is_valid_source
    )
except ImportError:
    # 直接运行时
    sys.path.insert(0, str(Path(__file__).parent))
    from storage.database import (
        SafeDatabaseManager, 
        MemoryHealthChecker,
        validate_limit, 
        validate_query,
        is_valid_source
    )


class SafeMemory:
    """
    安全记忆引擎
    
    在 MemoryCoreClaw 基础上增加：
    1. 安全的数据库连接管理
    2. 完善的异常处理
    3. 边界条件检查
    4. 记忆来源标记
    5. 防误删除保护
    """
    
    # 受保护的记忆类别（删除需要确认）
    PROTECTED_CATEGORIES = {'identity', 'preference', 'milestone', 'core'}
    
    # 核心记忆阈值
    CORE_IMPORTANCE_THRESHOLD = 0.9
    
    def __init__(self, db_path: str):
        """
        初始化安全记忆引擎
        
        Args:
            db_path: 数据库路径
        """
        self.db = SafeDatabaseManager(db_path)
        self.health_checker = MemoryHealthChecker(self.db)
        self._init_tables()  # 确保表存在
        self._ensure_source_column()
    
    def _init_tables(self):
        """初始化数据库表结构"""
        self.db.execute_script('''
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                tags TEXT,
                importance REAL DEFAULT 0.5,
                emotion TEXT DEFAULT 'neutral',
                category TEXT DEFAULT 'general',
                source TEXT DEFAULT 'user',
                source_confidence REAL DEFAULT 1.0,
                last_accessed TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                context TEXT,
                outcome TEXT CHECK(outcome IN ('positive', 'negative', 'neutral')),
                insight TEXT,
                importance REAL DEFAULT 0.5,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP,
                access_count INTEGER DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT,
                metadata TEXT,
                importance REAL DEFAULT 0.5,
                last_accessed TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_entity TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                to_entity TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                evidence TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_entity, relation_type, to_entity)
            );
            
            CREATE TABLE IF NOT EXISTS memory_strength (
                memory_type TEXT NOT NULL,
                memory_id INTEGER NOT NULL,
                base_strength REAL DEFAULT 0.5,
                current_strength REAL DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_decay TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                retention_rate REAL DEFAULT 1.0,
                PRIMARY KEY (memory_type, memory_id)
            );
            
            CREATE TABLE IF NOT EXISTS contexts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context_hash TEXT,
                time TEXT,
                time_period TEXT,
                date TEXT,
                weekday TEXT,
                location TEXT,
                location_type TEXT,
                people TEXT,
                emotion TEXT,
                emotion_intensity REAL,
                activity TEXT,
                topic TEXT,
                weather TEXT,
                environment TEXT,
                channel TEXT,
                session_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS memory_context_bindings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT NOT NULL,
                memory_id INTEGER NOT NULL,
                context_id INTEGER NOT NULL,
                binding_strength REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (context_id) REFERENCES contexts(id)
            );
            
            CREATE TABLE IF NOT EXISTS working_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT DEFAULT 'default',
                key TEXT NOT NULL,
                value TEXT,
                priority REAL DEFAULT 0.5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP,
                UNIQUE(session_id, key)
            );
        ''')
    
    def _ensure_source_column(self):
        """确保 facts 表有 source 列"""
        with self.db.transaction() as cursor:
            # 检查列是否存在
            cursor.execute("PRAGMA table_info(facts)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'source' not in columns:
                cursor.execute("ALTER TABLE facts ADD COLUMN source TEXT DEFAULT 'user'")
            
            if 'source_confidence' not in columns:
                cursor.execute("ALTER TABLE facts ADD COLUMN source_confidence REAL DEFAULT 1.0")
    
    # ==================== 记忆存储 ====================
    
    def remember(
        self,
        content: str,
        importance: float = 0.5,
        category: str = "general",
        emotion: str = "neutral",
        source: str = "user",
        source_confidence: float = 1.0,
        tags: List[str] = None
    ) -> int:
        """
        存储记忆（带来源标记）
        
        解决 R5: 记忆来源标记
        
        Args:
            content: 记忆内容
            importance: 重要性 (0-1)
            category: 类别
            emotion: 情绪标记
            source: 来源类型
                - 'user': 用户主动提供（可信度高）
                - 'llm': LLM推理得出（需验证）
                - 'document': 从文档提取
                - 'system': 系统生成
            source_confidence: 来源置信度 (0-1)
            tags: 标签列表
        
        Returns:
            记忆ID
        """
        # 参数验证
        if not content or not content.strip():
            raise ValueError("记忆内容不能为空")
        
        importance = max(0.0, min(1.0, importance))
        source_confidence = max(0.0, min(1.0, source_confidence))
        
        if not is_valid_source(source):
            source = 'user'  # 默认值
        
        tags_str = ','.join(tags) if tags else None
        
        with self.db.transaction() as cursor:
            cursor.execute('''
                INSERT INTO facts (content, importance, category, emotion, source, source_confidence, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (content.strip(), importance, category, emotion, source, source_confidence, tags_str))
            
            fact_id = cursor.lastrowid
            
            # 记录记忆强度
            cursor.execute('''
                INSERT INTO memory_strength (memory_type, memory_id, base_strength, current_strength)
                VALUES ('fact', ?, ?, ?)
            ''', (fact_id, importance, importance))
            
            return fact_id
    
    # ==================== 记忆检索 ====================
    
    def recall(
        self,
        query: str,
        limit: int = 10,
        category: str = None,
        min_importance: float = None
    ) -> List[Dict]:
        """
        检索记忆（带边界检查）
        
        解决 R4: 边界条件检查
        
        Args:
            query: 查询字符串
            limit: 返回数量限制
            category: 类别过滤
            min_importance: 最小重要性过滤
        
        Returns:
            记忆列表
        """
        # 边界条件检查
        query = validate_query(query)
        limit = validate_limit(limit, max_limit=100, default=10)
        
        with self.db.readonly() as cursor:
            sql = '''
                SELECT id, content, importance, category, emotion, source, 
                       source_confidence, tags, created_at, access_count
                FROM facts
                WHERE 1=1
            '''
            params = []
            
            # 空查询不添加内容过滤
            if query:
                sql += ' AND content LIKE ?'
                params.append(f'%{query}%')
            
            if category:
                sql += ' AND category = ?'
                params.append(category)
            
            if min_importance is not None:
                sql += ' AND importance >= ?'
                params.append(min_importance)
            
            sql += ' ORDER BY importance DESC, created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(sql, params)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'content': row['content'],
                    'importance': row['importance'],
                    'category': row['category'],
                    'emotion': row['emotion'],
                    'source': row['source'],
                    'source_confidence': row['source_confidence'],
                    'tags': row['tags'].split(',') if row['tags'] else [],
                    'created_at': row['created_at'],
                    'access_count': row['access_count']
                })
            
            return results
    
    def recall_by_category(self, category: str, limit: int = 20) -> List[Dict]:
        """按类别检索"""
        return self.recall(query="", limit=limit, category=category)
    
    def recall_by_importance(self, min_importance: float = 0.7, limit: int = 20) -> List[Dict]:
        """按重要性检索"""
        return self.recall(query="", limit=limit, min_importance=min_importance)
    
    # ==================== 安全删除 ====================
    
    def delete(self, memory_id: int, force: bool = False) -> Dict:
        """
        安全删除记忆
        
        解决 R6: 防误删除机制
        
        Args:
            memory_id: 记忆ID
            force: 是否强制删除（跳过保护检查）
        
        Returns:
            {'success': bool, 'message': str, 'backup': dict}
        """
        with self.db.readonly() as cursor:
            cursor.execute(
                'SELECT id, content, importance, category, source FROM facts WHERE id = ?',
                (memory_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return {'success': False, 'message': f'记忆 {memory_id} 不存在', 'backup': None}
        
        # 备份记忆
        backup = {
            'id': row['id'],
            'content': row['content'],
            'importance': row['importance'],
            'category': row['category'],
            'source': row['source'],
            'deleted_at': datetime.now().isoformat()
        }
        
        # 检查是否需要确认
        if not force:
            if row['importance'] >= self.CORE_IMPORTANCE_THRESHOLD:
                return {
                    'success': False,
                    'message': f"核心记忆（importance={row['importance']}）需要确认删除，请使用 delete(id, force=True)",
                    'backup': backup
                }
            
            if row['category'] in self.PROTECTED_CATEGORIES:
                return {
                    'success': False,
                    'message': f"受保护的类别 '{row['category']}' 需要确认删除，请使用 delete(id, force=True)",
                    'backup': backup
                }
        
        # 执行删除
        with self.db.transaction() as cursor:
            cursor.execute('DELETE FROM facts WHERE id = ?', (memory_id,))
            cursor.execute('DELETE FROM memory_strength WHERE memory_type = ? AND memory_id = ?', 
                          ('fact', memory_id))
        
        return {
            'success': True,
            'message': f'记忆 {memory_id} 已删除',
            'backup': backup
        }
    
    def backup_memory(self, memory_id: int) -> Optional[Dict]:
        """备份单个记忆"""
        with self.db.readonly() as cursor:
            cursor.execute('SELECT * FROM facts WHERE id = ?', (memory_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None
    
    # ==================== 经验学习 ====================
    
    def learn(
        self,
        action: str,
        context: str,
        outcome: str,
        insight: str,
        importance: float = 0.7
    ) -> int:
        """
        学习教训
        
        Args:
            action: 行为
            context: 上下文
            outcome: 结果 ('positive', 'negative', 'neutral')
            insight: 洞察
            importance: 重要性
        
        Returns:
            经验ID
        """
        if outcome not in ('positive', 'negative', 'neutral'):
            outcome = 'neutral'
        
        importance = max(0.0, min(1.0, importance))
        
        with self.db.transaction() as cursor:
            cursor.execute('''
                INSERT INTO experiences (action, context, outcome, insight, importance)
                VALUES (?, ?, ?, ?, ?)
            ''', (action, context, outcome, insight, importance))
            
            return cursor.lastrowid
    
    def get_lessons(self, outcome: str = None, limit: int = 20) -> List[Dict]:
        """获取教训列表"""
        limit = validate_limit(limit)
        
        with self.db.readonly() as cursor:
            if outcome:
                cursor.execute('''
                    SELECT * FROM experiences 
                    WHERE outcome = ?
                    ORDER BY created_at DESC LIMIT ?
                ''', (outcome, limit))
            else:
                cursor.execute('''
                    SELECT * FROM experiences 
                    ORDER BY created_at DESC LIMIT ?
                ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 关系管理 ====================
    
    def relate(
        self,
        from_entity: str,
        relation_type: str,
        to_entity: str,
        weight: float = 1.0
    ) -> int:
        """
        建立实体关系
        
        Args:
            from_entity: 源实体
            relation_type: 关系类型
            to_entity: 目标实体
            weight: 关系权重
        
        Returns:
            关系ID
        """
        if not from_entity or not to_entity:
            raise ValueError("实体名称不能为空")
        
        weight = max(0.0, min(2.0, weight))
        
        with self.db.transaction() as cursor:
            # 创建实体（如果不存在）
            cursor.execute('''
                INSERT OR IGNORE INTO entities (name, importance)
                VALUES (?, 0.5)
            ''', (from_entity,))
            cursor.execute('''
                INSERT OR IGNORE INTO entities (name, importance)
                VALUES (?, 0.5)
            ''', (to_entity,))
            
            # 创建关系
            cursor.execute('''
                INSERT OR REPLACE INTO relations 
                (from_entity, relation_type, to_entity, weight)
                VALUES (?, ?, ?, ?)
            ''', (from_entity, relation_type, to_entity, weight))
            
            return cursor.lastrowid
    
    def get_relations(self, entity: str) -> List[Dict]:
        """获取实体的所有关系"""
        with self.db.readonly() as cursor:
            cursor.execute('''
                SELECT from_entity, relation_type, to_entity, weight
                FROM relations
                WHERE from_entity = ? OR to_entity = ?
                ORDER BY weight DESC
            ''', (entity, entity))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 健康检查 ====================
    
    def health_check(self) -> Dict:
        """执行健康检查"""
        return self.health_checker.check()
    
    def repair(self) -> Dict:
        """执行自动修复"""
        return self.health_checker.repair()
    
    # ==================== 统计信息 ====================
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self.db.readonly() as cursor:
            stats = {}
            
            cursor.execute('SELECT COUNT(*) as cnt FROM facts')
            stats['facts'] = cursor.fetchone()['cnt']
            
            cursor.execute('SELECT COUNT(*) as cnt FROM experiences')
            stats['experiences'] = cursor.fetchone()['cnt']
            
            cursor.execute('SELECT COUNT(*) as cnt FROM relations')
            stats['relations'] = cursor.fetchone()['cnt']
            
            cursor.execute('SELECT COUNT(*) as cnt FROM entities')
            stats['entities'] = cursor.fetchone()['cnt']
            
            # 来源统计
            cursor.execute('''
                SELECT source, COUNT(*) as cnt 
                FROM facts 
                GROUP BY source
            ''')
            stats['by_source'] = {row['source']: row['cnt'] for row in cursor.fetchall()}
            
            # 类别统计
            cursor.execute('''
                SELECT category, COUNT(*) as cnt 
                FROM facts 
                GROUP BY category
            ''')
            stats['by_category'] = {row['category']: row['cnt'] for row in cursor.fetchall()}
            
            return stats


# ==================== 测试代码 ====================

if __name__ == "__main__":
    import os
    
    print("=" * 60)
    print("SafeMemory 测试")
    print("=" * 60)
    
    # 使用环境变量或默认路径
    db_path = os.environ.get('MEMORY_DB_PATH', 'memory.db')
    mem = SafeMemory(db_path)
    
    # 1. 测试健康检查
    print("\n1. 健康检查:")
    health = mem.health_check()
    print(f"   状态: {health['status']}")
    print(f"   统计: {health['stats']}")
    
    # 2. 测试边界检查
    print("\n2. 边界检查测试:")
    results = mem.recall("", limit=-1)  # 空查询 + 负数limit
    print(f"   空查询 + limit=-1: 返回 {len(results)} 条记录")
    
    # 3. 测试记忆来源
    print("\n3. 记忆来源标记:")
    test_id = mem.remember(
        "测试记忆 - SafeMemory验证",
        importance=0.8,
        category="test",
        source="system",
        source_confidence=1.0
    )
    print(f"   插入记忆 ID: {test_id}")
    
    # 验证来源
    results = mem.recall("SafeMemory验证")
    if results:
        print(f"   来源: {results[0]['source']}")
        print(f"   来源置信度: {results[0]['source_confidence']}")
    
    # 4. 测试防误删除
    print("\n4. 防误删除测试:")
    result = mem.delete(test_id)  # 测试记忆，不是核心记忆，应该可以直接删除
    print(f"   删除结果: {result['success']}")
    print(f"   消息: {result['message']}")
    
    # 5. 测试统计
    print("\n5. 统计信息:")
    stats = mem.get_stats()
    print(f"   事实记忆: {stats['facts']}")
    print(f"   经验教训: {stats['experiences']}")
    print(f"   关系数量: {stats['relations']}")
    print(f"   来源分布: {stats['by_source']}")
    
    print("\n✅ 测试完成")