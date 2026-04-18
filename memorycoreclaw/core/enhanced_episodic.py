#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced Episodic Memory (情节记忆增强)

功能：
- 自动将交互事件存储为情节记忆
- 支持重要性评分和自动分类
- 向量嵌入支持语义检索
"""

import json
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path


class EpisodicMemoryEnhancer:
    """情节记忆增强器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def store_episode(
        self,
        content: str,
        action: str,
        outcome: str,
        importance: float = 0.5,
        context: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """
        存储情节记忆
        
        Args:
            content: 交互内容
            action: 执行的动作
            outcome: 结果
            importance: 重要性 (0-1)
            context: 上下文信息
            tags: 标签
            
        Returns:
            int: 存储的记忆ID
        """
        # 转换outcome为有效值
        outcome_normalized = self._normalize_outcome(outcome)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 提取洞察
        insight = self._extract_insight(content, action, outcome)
        
        # 提取模式
        pattern = self._extract_pattern(action, outcome)
        
        # 准备数据
        context_json = json.dumps(context) if context else None
        tags_str = ','.join(tags) if tags else None
        
        # 标准化source
        source_normalized = self._normalize_source('EpisodicMemoryEnhancer')
        
        cursor.execute("""
            INSERT INTO experiences (
                action, context, outcome, insight, importance,
                category, last_accessed, access_count, created_at,
                root_cause, contributing_factors, pattern,
                action_plan, implementation_status, verification_status,
                consolidation_status, lifecycle_state, tags, source, source_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            action,
            context_json,
            outcome_normalized,
            insight,
            importance,
            self._categorize_action(action),
            datetime.now().isoformat(),
            1,
            datetime.now().isoformat(),
            None,  # root_cause
            None,  # contributing_factors
            pattern,
            None,  # action_plan
            'pending',  # implementation_status
            'unverified',  # verification_status
            'pending',  # consolidation_status
            'active',  # lifecycle_state
            tags_str,
            source_normalized,
            importance
        ))
        
        episode_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return episode_id
    
    def recall_episodes(
        self,
        query: str,
        limit: int = 5,
        min_importance: float = 0.0
    ) -> List[Dict]:
        """
        检索情节记忆
        
        Args:
            query: 查询关键词
            limit: 返回数量
            min_importance: 最小重要性
            
        Returns:
            List[Dict]: 匹配的情节记忆
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, action, context, outcome, insight, importance, 
                   pattern, created_at, tags
            FROM experiences
            WHERE importance >= ?
              AND (action LIKE ? OR context LIKE ? OR outcome LIKE ? OR insight LIKE ?)
            ORDER BY importance DESC, created_at DESC
            LIMIT ?
        """, (
            min_importance,
            f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%',
            limit
        ))
        
        results = []
        for row in cursor.fetchall():
            # 安全解析JSON
            context_data = None
            if row[2]:
                try:
                    context_data = json.loads(row[2])
                except (json.JSONDecodeError, TypeError):
                    pass
            
            results.append({
                'id': row[0],
                'action': row[1],
                'context': context_data,
                'outcome': row[3],
                'insight': row[4],
                'importance': row[5],
                'pattern': row[6],
                'created_at': row[7],
                'tags': row[8].split(',') if row[8] else []
            })
        
        conn.close()
        return results
    
    def get_recent_episodes(self, limit: int = 10) -> List[Dict]:
        """获取最近的情节记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, action, context, outcome, insight, importance, created_at
            FROM experiences
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        results = []
        for row in cursor.fetchall():
            # 安全解析JSON
            context_data = None
            if row[2]:
                try:
                    context_data = json.loads(row[2])
                except (json.JSONDecodeError, TypeError):
                    pass
            
            results.append({
                'id': row[0],
                'action': row[1],
                'context': context_data,
                'outcome': row[3],
                'insight': row[4],
                'importance': row[5],
                'created_at': row[6]
            })
        
        conn.close()
        return results
    
    def get_important_episodes(self, limit: int = 10) -> List[Dict]:
        """获取重要的情节记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, action, context, outcome, insight, importance, created_at
            FROM experiences
            WHERE importance >= 0.7
            ORDER BY importance DESC, created_at DESC
            LIMIT ?
        """, (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'action': row[1],
                'outcome': row[3],
                'insight': row[4],
                'importance': row[5],
                'created_at': row[6]
            })
        
        conn.close()
        return results
    
    def _extract_insight(self, content: str, action: str, outcome: str) -> str:
        """提取洞察"""
        # 简单规则：从结果中提取关键信息
        if 'success' in outcome.lower() or '完成' in outcome:
            return f"Action '{action}' was successful"
        elif 'fail' in outcome.lower() or '失败' in outcome:
            return f"Action '{action}' failed - needs review"
        return f"Action '{action}' resulted in: {outcome[:100]}"
    
    def _extract_pattern(self, action: str, outcome: str) -> str:
        """提取模式"""
        # 简单模式识别
        if 'create' in action.lower() or '创建' in action:
            return 'create_operation'
        elif 'read' in action.lower() or '读取' in action:
            return 'read_operation'
        elif 'update' in action.lower() or '更新' in action:
            return 'update_operation'
        elif 'delete' in action.lower() or '删除' in action:
            return 'delete_operation'
        return 'general_operation'
    
    def _categorize_action(self, action: str) -> str:
        """动作分类"""
        action_lower = action.lower()
        
        if 'file' in action_lower or '文件' in action:
            return 'file_operation'
        elif 'skill' in action_lower or '技能' in action:
            return 'skill_operation'
        elif 'memory' in action_lower or '记忆' in action:
            return 'memory_operation'
        elif 'git' in action_lower or 'github' in action_lower:
            return 'version_control'
        else:
            return 'general'
    
    def _normalize_outcome(self, outcome: str) -> str:
        """标准化outcome值"""
        outcome_lower = outcome.lower()
        
        if 'success' in outcome_lower or '完成' in outcome_lower or '成功' in outcome_lower:
            return 'positive'
        elif 'fail' in outcome_lower or '失败' in outcome_lower or '错误' in outcome_lower:
            return 'negative'
        else:
            return 'neutral'
    
    def _normalize_source(self, source: str) -> str:
        """标准化source值"""
        valid_sources = ['user', 'compaction', 'system']
        source_lower = source.lower()
        
        if source_lower in valid_sources:
            return source_lower
        elif 'enhancer' in source_lower or 'memory' in source_lower:
            return 'system'
        else:
            return 'user'


def main():
    """测试"""
    db_path = os.environ.get('MEMORY_DB_PATH', '/path/to/memory.db')
    enhancer = EpisodicMemoryEnhancer(db_path)
    
    # 存储情节
    episode_id = enhancer.store_episode(
        content="User asked to create a PowerPoint presentation",
        action="create_presentation",
        outcome="Successfully created presentation with 10 slides",
        importance=0.8,
        context={"user": "Mr Lee", "tool": "pptx"},
        tags=["presentation", "pptx", "success"]
    )
    print(f'[Test] Stored episode ID: {episode_id}')
    
    # 检索
    episodes = enhancer.recall_episodes('presentation', limit=3)
    print(f'[Test] Found {len(episodes)} episodes')
    for ep in episodes:
        print(f'  - {ep["action"]}: {ep["outcome"][:50]}...')
    
    # 重要记忆
    important = enhancer.get_important_episodes(limit=5)
    print(f'[Test] Important episodes: {len(important)}')
    
    print('\n[OK] EpisodicMemoryEnhancer test passed')


if __name__ == '__main__':
    main()