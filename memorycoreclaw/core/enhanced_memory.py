# -*- coding: utf-8 -*-
"""
MemoryCoreClaw v2.0 增强版记忆管理

核心功能：
- 决策生命周期管理（自动 superseded）
- 智能去重（向量相似度）
- 待办状态管理
- 来源可信度分层
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

# 导入基础引擎
from .engine import MemoryEngine


# 来源可信度配置
SOURCE_CONFIDENCE = {
    'user': 1.0,             # 用户明确输入
    'user_explicit': 1.0,    # 用户明确说"记住这个"
    'user_statement': 0.95,  # 用户说出的内容
    'compaction': 0.85,      # LLM 压缩提取（智能推断）
    'document': 0.8,         # 从文档读取
    'system': 0.95,          # 系统配置
    'test': 0.5,             # 测试数据
}

# 决策主题分类关键词
DECISION_TOPICS = {
    'compression_model': ['压缩模型', 'compaction model', '压缩', '模型选择', 'glm', 'deepseek', 'qwen'],
    'embedding_model': ['embedding', '向量模型', '嵌入模型', 'bge'],
    'active_model': ['主模型', 'active model', '对话模型'],
    'feature_implementation': ['实现', '功能', 'feature', '开发'],
    'architecture': ['架构', '设计', 'architecture', '结构'],
    'tool_selection': ['工具', 'tool', '选择'],
    'workflow': ['流程', '工作流', 'workflow', '步骤'],
    'configuration': ['配置', 'config', '设置'],
    'priority': ['优先级', 'priority', '重要'],
    'other': [],  # 默认
}


class EnhancedMemoryEngine(MemoryEngine):
    """增强版记忆引擎 - 支持决策生命周期和智能去重"""
    
    def __init__(self, db_path: str):
        super().__init__(db_path)
        self._ensure_v2_schema()
        self._embedding_model = None
        self._embedding_available = False
        self._check_embedding_availability()
    
    def _ensure_v2_schema(self):
        """确保 v2.0 schema 已应用"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 检查 todos 表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='todos'")
        if not cursor.fetchone():
            conn.close()
            print("检测到旧版 schema，正在迁移...")
            from .migration_v2 import migrate_v2
            migrate_v2(self.db_path)
        else:
            conn.close()
    
    def _check_embedding_availability(self):
        """检查向量搜索是否可用"""
        try:
            import urllib.request
            import json
            
            # 检查 Ollama 服务
            req = urllib.request.Request('http://127.0.0.1:11434/api/tags')
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode())
                models = [m['name'] for m in data.get('models', [])]
                
                # 检查是否有 embedding 模型
                for model in models:
                    if 'bge' in model.lower() or 'embedding' in model.lower():
                        self._embedding_available = True
                        self._embedding_model = model
                        print(f"向量搜索已启用: {model}")
                        return
            
            print("向量搜索未启用: 未找到 embedding 模型")
            
        except Exception as e:
            print(f"向量搜索未启用: {e}")
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """获取文本的向量表示"""
        if not self._embedding_available:
            return None
        
        try:
            import urllib.request
            import json
            
            data = json.dumps({
                "model": self._embedding_model,
                "input": text
            }).encode('utf-8')
            
            req = urllib.request.Request(
                'http://127.0.0.1:11434/api/embeddings',
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                return result.get('embedding')
                
        except Exception as e:
            print(f"获取向量失败: {e}")
            return None
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        import math
        
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    # ==================== 增强版写入方法 ====================
    
    def remember_decision(
        self,
        decision: str,
        reason: str = "",
        topic: str = None,
        source: str = "compaction",
        extraction_id: str = None,
        extraction_model: str = None,
    ) -> int:
        """
        记录决策（带生命周期管理）
        
        流程：
        1. 智能推断 topic（如果未指定）
        2. 查找同 topic 的 active 决策
        3. 将旧决策标记为 superseded
        4. 记录变更日志
        5. 写入新决策
        
        Args:
            decision: 决策内容
            reason: 决策原因
            topic: 决策主题（自动推断）
            source: 来源
            extraction_id: 提取ID
            extraction_model: 提取模型
            
        Returns:
            新决策ID
        """
        # 1. 推断 topic
        if not topic:
            topic = self._infer_topic(decision)
        
        # 2. 查找同 topic 的 active 决策
        old_decisions = self._find_active_decisions_by_topic(topic)
        
        # 3. 构建完整内容
        content = f"决策：{decision}"
        if reason:
            content += f"，原因：{reason}"
        
        # 4. 检查是否重复（向量相似度）
        if self._is_duplicate_enhanced(content, category="decision", threshold=0.92):
            print(f"  ⏭️ 决策已存在，跳过: {decision[:50]}...")
            return None
        
        # 5. 写入新决策
        source_detail = json.dumps({
            "extraction_id": extraction_id,
            "extraction_model": extraction_model,
        }, ensure_ascii=False) if extraction_id else None
        
        fact_id = self._insert_fact(
            content=content,
            category="decision",
            topic=topic,
            source=source,
            source_confidence=SOURCE_CONFIDENCE.get(source, 0.85),
            source_detail=source_detail,
            importance=0.8,  # 决策通常重要
        )
        
        # 6. 将旧决策标记为 superseded
        if old_decisions and fact_id:
            for old in old_decisions:
                self._supersede_decision(
                    old_id=old['id'],
                    new_id=fact_id,
                    topic=topic,
                    old_content=old['content'],
                    new_content=content,
                    extraction_id=extraction_id,
                )
        
        return fact_id
    
    def remember_lesson(
        self,
        lesson: str,
        context: str = "",
        source: str = "compaction",
        extraction_id: str = None,
    ) -> int:
        """
        记录教训（带去重）
        
        Args:
            lesson: 教训内容
            context: 上下文
            source: 来源
            extraction_id: 提取ID
            
        Returns:
            教训ID
        """
        # 检查是否重复
        if self._is_duplicate_enhanced(lesson, table="experiences", threshold=0.90):
            print(f"  ⏭️ 教训已存在，跳过: {lesson[:50]}...")
            return None
        
        source_detail = json.dumps({
            "extraction_id": extraction_id,
        }, ensure_ascii=False) if extraction_id else None
        
        return self._insert_experience(
            action=lesson,
            context=context,
            insight=lesson,
            outcome="neutral",
            source=source,
            source_confidence=SOURCE_CONFIDENCE.get(source, 0.85),
            source_detail=source_detail,
            importance=0.85,
        )
    
    def remember_fact(
        self,
        fact: str,
        category: str = "other",
        source: str = "compaction",
        extraction_id: str = None,
    ) -> int:
        """
        记录事实（带去重）
        """
        # 检查是否重复
        if self._is_duplicate_enhanced(fact, category=category, threshold=0.90):
            print(f"  ⏭️ 事实已存在，跳过: {fact[:50]}...")
            return None
        
        source_detail = json.dumps({
            "extraction_id": extraction_id,
        }, ensure_ascii=False) if extraction_id else None
        
        return self._insert_fact(
            content=fact,
            category=category,
            source=source,
            source_confidence=SOURCE_CONFIDENCE.get(source, 0.85),
            source_detail=source_detail,
            importance=0.7,
        )
    
    def add_todo(
        self,
        task: str,
        priority: str = "medium",
        source: str = "compaction",
        extraction_id: str = None,
    ) -> int:
        """
        添加待办
        
        Args:
            task: 待办内容
            priority: 优先级 (high/medium/low)
            source: 来源
            extraction_id: 提取ID
            
        Returns:
            待办ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 检查是否已存在相同待办
        cursor.execute('''
            SELECT id, status FROM todos 
            WHERE task = ? AND status IN ('pending', 'in_progress')
        ''', (task,))
        
        existing = cursor.fetchone()
        if existing:
            print(f"  ⏭️ 待办已存在，跳过: {task[:50]}...")
            conn.close()
            return existing[0]
        
        cursor.execute('''
            INSERT INTO todos (task, priority, source, extraction_id)
            VALUES (?, ?, ?, ?)
        ''', (task, priority, source, extraction_id))
        
        todo_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return todo_id
    
    # ==================== 压缩提取批量写入 ====================
    
    def write_extraction(
        self,
        extraction: Dict,
        extraction_id: str,
        extraction_model: str = "unknown",
    ) -> Dict[str, List[int]]:
        """
        批量写入压缩提取内容
        
        Args:
            extraction: 提取的 JSON 数据
            extraction_id: 提取ID
            extraction_model: 提取模型
            
        Returns:
            写入结果 {"decisions": [...], "lessons": [...], "todos": [...], "facts": [...]}
        """
        result = {
            "decisions": [],
            "lessons": [],
            "todos": [],
            "facts": [],
        }
        
        print(f"\n📝 写入压缩提取 (ID: {extraction_id[:8] if extraction_id else 'unknown'}...)")
        
        # 1. 决策
        for item in extraction.get("decisions", []):
            decision = item.get("decision", "")
            reason = item.get("reason", "")
            if decision:
                fact_id = self.remember_decision(
                    decision=decision,
                    reason=reason,
                    source="compaction",
                    extraction_id=extraction_id,
                    extraction_model=extraction_model,
                )
                if fact_id:
                    result["decisions"].append(fact_id)
        
        # 2. 教训
        for item in extraction.get("lessons", []):
            lesson = item.get("lesson", "")
            context = item.get("context", "")
            if lesson:
                exp_id = self.remember_lesson(
                    lesson=lesson,
                    context=context,
                    source="compaction",
                    extraction_id=extraction_id,
                )
                if exp_id:
                    result["lessons"].append(exp_id)
        
        # 3. 待办
        for item in extraction.get("todos", []):
            task = item.get("task", "")
            priority = item.get("priority", "medium")
            if task:
                todo_id = self.add_todo(
                    task=task,
                    priority=priority,
                    source="compaction",
                    extraction_id=extraction_id,
                )
                if todo_id:
                    result["todos"].append(todo_id)
        
        # 4. 事实
        for item in extraction.get("facts", []):
            fact = item.get("fact", "")
            category = item.get("category", "other")
            if fact:
                fact_id = self.remember_fact(
                    fact=fact,
                    category=category,
                    source="compaction",
                    extraction_id=extraction_id,
                )
                if fact_id:
                    result["facts"].append(fact_id)
        
        print(f"  ✅ 写入完成: {len(result['decisions'])} 决策, {len(result['lessons'])} 教训, {len(result['todos'])} 待办, {len(result['facts'])} 事实")
        
        return result
    
    # ==================== 增强版检索方法 ====================
    
    def get_active_decisions(self, topic: str = None) -> List[Dict]:
        """
        获取当前有效的决策
        
        Args:
            topic: 可选，按主题筛选
            
        Returns:
            有效决策列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if topic:
            cursor.execute('''
                SELECT id, content, topic, source, created_at
                FROM facts
                WHERE category = 'decision' AND status = 'active' AND topic = ?
                ORDER BY created_at DESC
            ''', (topic,))
        else:
            cursor.execute('''
                SELECT id, content, topic, source, created_at
                FROM facts
                WHERE category = 'decision' AND status = 'active'
                ORDER BY created_at DESC
            ''')
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "content": row[1],
                "topic": row[2],
                "source": row[3],
                "created_at": row[4],
            })
        
        conn.close()
        return results
    
    def get_pending_todos(self, priority: str = None) -> List[Dict]:
        """
        获取待办事项
        
        Args:
            priority: 可选，按优先级筛选
            
        Returns:
            待办列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if priority:
            cursor.execute('''
                SELECT id, task, priority, status, created_at
                FROM todos
                WHERE status IN ('pending', 'in_progress') AND priority = ?
                ORDER BY 
                    CASE priority 
                        WHEN 'high' THEN 1 
                        WHEN 'medium' THEN 2 
                        WHEN 'low' THEN 3 
                    END,
                    created_at ASC
            ''', (priority,))
        else:
            cursor.execute('''
                SELECT id, task, priority, status, created_at
                FROM todos
                WHERE status IN ('pending', 'in_progress')
                ORDER BY 
                    CASE priority 
                        WHEN 'high' THEN 1 
                        WHEN 'medium' THEN 2 
                        WHEN 'low' THEN 3 
                    END,
                    created_at ASC
            ''')
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "task": row[1],
                "priority": row[2],
                "status": row[3],
                "created_at": row[4],
            })
        
        conn.close()
        return results
    
    def complete_todo(self, todo_id: int) -> bool:
        """标记待办为完成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE todos 
            SET status = 'done', done_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (todo_id,))
        
        conn.commit()
        conn.close()
        
        return True
    
    # ==================== 辅助方法 ====================
    
    def _infer_topic(self, content: str) -> str:
        """根据内容推断决策主题"""
        content_lower = content.lower()
        
        for topic, keywords in DECISION_TOPICS.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    return topic
        
        return "other"
    
    def _find_active_decisions_by_topic(self, topic: str) -> List[Dict]:
        """查找同主题的有效决策"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, content, created_at
            FROM facts
            WHERE category = 'decision' AND status = 'active' AND topic = ?
        ''', (topic,))
        
        results = [{"id": row[0], "content": row[1], "created_at": row[2]} 
                   for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def _is_duplicate_enhanced(
        self, 
        content: str, 
        category: str = None, 
        table: str = "facts", 
        threshold: float = 0.90
    ) -> bool:
        """
        检查是否重复（使用向量相似度或精确匹配）
        
        Args:
            content: 要检查的内容
            category: 分类（仅 facts 表）
            table: 表名
            threshold: 相似度阈值
            
        Returns:
            True 如果重复
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取现有记录
        if table == "facts":
            if category:
                cursor.execute('''
                    SELECT id, content FROM facts 
                    WHERE category = ? AND status IN ('active', NULL)
                ''', (category,))
            else:
                cursor.execute('SELECT id, content FROM facts WHERE status IN (?, NULL)', ('active',))
        elif table == "experiences":
            cursor.execute('SELECT id, action FROM experiences')
        else:
            conn.close()
            return False
        
        existing_records = cursor.fetchall()
        conn.close()
        
        if not existing_records:
            return False
        
        # 如果向量搜索可用，使用向量相似度
        if self._embedding_available:
            query_embedding = self._get_embedding(content)
            if query_embedding:
                for record_id, existing_content in existing_records:
                    existing_embedding = self._get_embedding(existing_content)
                    if existing_embedding:
                        similarity = self._cosine_similarity(query_embedding, existing_embedding)
                        if similarity >= threshold:
                            return True
                return False
        
        # 否则使用精确匹配
        for record_id, existing_content in existing_records:
            if existing_content == content:
                return True
        
        return False
    
    def _insert_fact(
        self,
        content: str,
        category: str,
        topic: str = None,
        source: str = "user",
        source_confidence: float = 1.0,
        source_detail: str = None,
        importance: float = 0.5,
    ) -> int:
        """插入事实"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO facts (content, category, topic, source, source_confidence, source_detail, importance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (content, category, topic, source, source_confidence, source_detail, importance))
        
        fact_id = cursor.lastrowid
        
        # 初始化记忆强度
        cursor.execute('''
            INSERT INTO memory_strength (memory_type, memory_id, base_strength, current_strength, last_decay)
            VALUES ('fact', ?, ?, ?, datetime('now'))
        ''', (fact_id, importance, importance))
        
        conn.commit()
        conn.close()
        
        return fact_id
    
    def _insert_experience(
        self,
        action: str,
        context: str,
        insight: str,
        outcome: str,
        source: str = "user",
        source_confidence: float = 1.0,
        source_detail: str = None,
        importance: float = 0.5,
    ) -> int:
        """插入教训"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO experiences (action, context, insight, outcome, source, source_confidence, source_detail, importance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (action, context, insight, outcome, source, source_confidence, source_detail, importance))
        
        exp_id = cursor.lastrowid
        
        # 初始化记忆强度
        cursor.execute('''
            INSERT INTO memory_strength (memory_type, memory_id, base_strength, current_strength, last_decay)
            VALUES ('experience', ?, ?, ?, datetime('now'))
        ''', (exp_id, importance, importance))
        
        conn.commit()
        conn.close()
        
        return exp_id
    
    def _supersede_decision(
        self,
        old_id: int,
        new_id: int,
        topic: str,
        old_content: str,
        new_content: str,
        extraction_id: str = None,
    ):
        """将旧决策标记为已取代，并记录变更日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. 更新旧决策状态
        cursor.execute('''
            UPDATE facts SET status = 'superseded', superseded_by = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_id, old_id))
        
        # 2. 记录变更日志
        cursor.execute('''
            INSERT INTO decision_changelog 
            (old_decision_id, new_decision_id, old_content, new_content, topic, change_type, extraction_id)
            VALUES (?, ?, ?, ?, ?, 'update', ?)
        ''', (old_id, new_id, old_content, new_content, topic, extraction_id))
        
        conn.commit()
        conn.close()
        
        print(f"  🔄 决策变更: {topic} -> 更新")
    
    # ==================== 清理方法 ====================
    
    def cleanup_old_records(self) -> Dict[str, int]:
        """
        清理旧记录：
        - 40天前的 superseded 决策
        - 半年前完成的待办
        
        Returns:
            清理统计
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取清理配置
        cursor.execute('SELECT decision_retention_days, todo_done_retention_days FROM cleanup_config WHERE id = 1')
        config = cursor.fetchone()
        decision_days = config[0] if config else 40
        todo_days = config[1] if config else 180
        
        print(f"\n🧹 清理旧记录（决策: {decision_days}天, 待办: {todo_days}天）...")
        
        # 1. 清理旧的 superseded 决策
        cursor.execute('''
            DELETE FROM facts 
            WHERE category = 'decision' 
            AND status = 'superseded' 
            AND updated_at IS NOT NULL
            AND datetime(updated_at) < datetime('now', '-' || ? || ' days')
        ''', (decision_days,))
        deleted_decisions = cursor.rowcount
        
        # 2. 清理旧的已完成待办
        cursor.execute('''
            DELETE FROM todos 
            WHERE status = 'done' 
            AND done_at IS NOT NULL
            AND datetime(done_at) < datetime('now', '-' || ? || ' days')
        ''', (todo_days,))
        deleted_todos = cursor.rowcount
        
        # 更新清理时间
        cursor.execute('UPDATE cleanup_config SET last_cleanup = CURRENT_TIMESTAMP WHERE id = 1')
        
        conn.commit()
        conn.close()
        
        print(f"  ✅ 清理完成: {deleted_decisions} 条旧决策, {deleted_todos} 条已完成待办")
        
        return {
            "deleted_decisions": deleted_decisions,
            "deleted_todos": deleted_todos,
        }
    
    # ==================== 统计方法 ====================
    
    def get_stats(self) -> Dict:
        """获取记忆统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 事实统计
        cursor.execute('SELECT COUNT(*) FROM facts')
        total_facts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM facts WHERE category = 'decision' AND status = 'active'")
        active_decisions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM facts WHERE category = 'decision' AND status = 'superseded'")
        superseded_decisions = cursor.fetchone()[0]
        
        # 教训统计
        cursor.execute('SELECT COUNT(*) FROM experiences')
        total_experiences = cursor.fetchone()[0]
        
        # 待办统计
        cursor.execute("SELECT COUNT(*) FROM todos WHERE status IN ('pending', 'in_progress')")
        pending_todos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM todos WHERE status = 'done'")
        done_todos = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_facts": total_facts,
            "active_decisions": active_decisions,
            "superseded_decisions": superseded_decisions,
            "total_experiences": total_experiences,
            "pending_todos": pending_todos,
            "done_todos": done_todos,
            "embedding_available": self._embedding_available,
        }


# 便捷导出
def get_enhanced_memory(db_path: str = None) -> EnhancedMemoryEngine:
    """获取增强版记忆引擎实例"""
    if db_path is None:
        db_path = r"D:\CoPaw\.copaw\.agent-memory\memory.db"
    return EnhancedMemoryEngine(db_path)