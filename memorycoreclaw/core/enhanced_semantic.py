#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced Semantic Memory (语义记忆增强)

功能：
- 事实存储和管理
- 实体-关系提取
- 置信度管理
- 事实更新和溯源
"""

import json
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class Fact:
    """事实数据类"""
    id: Optional[int] = None
    content: str = ""
    entity: str = ""
    value: str = ""
    confidence: float = 1.0
    source: str = ""
    category: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class SemanticMemoryEnhancer:
    """语义记忆增强器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def store_fact(
        self,
        content: str,
        entity: str = "",
        value: str = "",
        confidence: float = 1.0,
        source: str = "user",
        category: str = "general",
        tags: Optional[List[str]] = None
    ) -> int:
        """
        存储事实
        
        Args:
            content: 事实内容
            entity: 实体名 (存储到topic字段)
            value: 实体值 (合并到content)
            confidence: 置信度 (存储到source_confidence字段)
            source: 来源
            category: 分类
            tags: 标签
            
        Returns:
            int: 事实ID
        """
        # 合并entity和value到content
        full_content = content
        if entity:
            full_content = f"{entity}: {value}" if value else content
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 检查是否已存在相同事实
        cursor.execute("""
            SELECT id, source_confidence FROM facts 
            WHERE content = ? AND topic = ?
        """, (full_content, entity))
        
        existing = cursor.fetchone()
        
        if existing:
            # 如果新事实置信度更高，则更新
            if confidence > existing[1]:
                cursor.execute("""
                    UPDATE facts 
                    SET content = ?, topic = ?, source_confidence = ?, source = ?,
                        category = ?, tags = ?, updated_at = ?, status = 'active'
                    WHERE id = ?
                """, (
                    full_content, entity, confidence, source,
                    category, ','.join(tags) if tags else None,
                    datetime.now().isoformat(),
                    existing[0]
                ))
                fact_id = existing[0]
            else:
                fact_id = existing[0]
        else:
            # 新增事实
            cursor.execute("""
                INSERT INTO facts (
                    content, tags, importance, emotion, category,
                    last_accessed, access_count, created_at, updated_at,
                    source, source_confidence, status, topic
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                full_content,
                ','.join(tags) if tags else None,
                confidence,
                'neutral',
                category,
                datetime.now().isoformat(),
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                source,
                confidence,
                'active',
                entity if entity else None
            ))
            
            fact_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return fact_id
    
    def recall_facts(
        self,
        query: str,
        entity: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 10
    ) -> List[Dict]:
        """
        检索事实
        
        Args:
            query: 查询关键词
            entity: 实体名
            min_confidence: 最小置信度
            limit: 返回数量
            
        Returns:
            List[Dict]: 匹配的事实
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sql = """
            SELECT id, content, topic, category, importance, 
                   source, source_confidence, created_at, updated_at, tags
            FROM facts
            WHERE status = 'active' 
              AND source_confidence >= ?
        """
        params = [min_confidence]
        
        if query:
            sql += " AND (content LIKE ? OR topic LIKE ?)"
            params.extend([f'%{query}%', f'%{query}%'])
        
        if entity:
            sql += " AND topic = ?"
            params.append(entity)
        
        sql += " ORDER BY source_confidence DESC, importance DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'content': row[1],
                'entity': row[2],
                'category': row[3],
                'importance': row[4],
                'source': row[5],
                'confidence': row[6],
                'created_at': row[7],
                'updated_at': row[8],
                'tags': row[9].split(',') if row[9] else []
            })
        
        conn.close()
        return results
    
    def get_entity_facts(self, entity: str) -> List[Dict]:
        """获取实体的所有事实"""
        return self.recall_facts("", entity=entity, limit=50)
    
    def extract_and_store(self, text: str, source: str = "user") -> List[int]:
        """
        从文本中提取事实并存储
        
        Args:
            text: 文本内容
            source: 来源
            
        Returns:
            List[int]: 存储的事实ID列表
        """
        facts = self._extract_facts(text)
        fact_ids = []
        
        for fact_data in facts:
            fact_id = self.store_fact(
                content=fact_data['content'],
                entity=fact_data.get('entity', ''),
                value=fact_data.get('value', ''),
                confidence=fact_data.get('confidence', 0.8),
                source=source,
                category=fact_data.get('category', 'general'),
                tags=fact_data.get('tags', [])
            )
            fact_ids.append(fact_id)
        
        return fact_ids
    
    def _extract_facts(self, text: str) -> List[Dict]:
        """提取事实（简化版）"""
        facts = []
        
        # 简单规则：提取"X是Y"类型的事实
        import re
        
        # 模式1: "X是Y"
        pattern1 = r'([^\s]{2,})是([^\s]{2,})'
        matches1 = re.findall(pattern1, text)
        for entity, value in matches1:
            facts.append({
                'content': f'{entity}是{value}',
                'entity': entity,
                'value': value,
                'confidence': 0.9,
                'category': 'relationship',
                'tags': ['relation']
            })
        
        # 模式2: "X叫做Y"
        pattern2 = r'([^\s]{2,})叫做([^\s]{2,})'
        matches2 = re.findall(pattern2, text)
        for entity, value in matches2:
            facts.append({
                'content': f'{entity}叫做{value}',
                'entity': entity,
                'value': value,
                'confidence': 0.9,
                'category': 'alias',
                'tags': ['alias']
            })
        
        # 模式3: "X位于Y"
        pattern3 = r'([^\s]{2,})位于([^\s]{2,})'
        matches3 = re.findall(pattern3, text)
        for entity, value in matches3:
            facts.append({
                'content': f'{entity}位于{value}',
                'entity': entity,
                'value': value,
                'confidence': 0.8,
                'category': 'location',
                'tags': ['location']
            })
        
        # 如果没有提取到事实，将整个文本作为事实
        if not facts:
            facts.append({
                'content': text[:200],  # 截取前200字符
                'entity': '',
                'value': '',
                'confidence': 0.5,
                'category': 'general',
                'tags': ['text']
            })
        
        return facts
    
    def get_fact_statistics(self) -> Dict:
        """获取事实统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 总数
        cursor.execute("SELECT COUNT(*) FROM facts WHERE status = 'active'")
        total = cursor.fetchone()[0]
        
        # 按分类统计
        cursor.execute("""
            SELECT category, COUNT(*) 
            FROM facts 
            WHERE status = 'active'
            GROUP BY category
        """)
        by_category = dict(cursor.fetchall())
        
        # 按来源统计
        cursor.execute("""
            SELECT source, COUNT(*) 
            FROM facts 
            WHERE status = 'active'
            GROUP BY source
        """)
        by_source = dict(cursor.fetchall())
        
        # 平均置信度
        cursor.execute("SELECT AVG(source_confidence) FROM facts WHERE status = 'active'")
        avg_confidence = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total': total,
            'by_category': by_category,
            'by_source': by_source,
            'avg_confidence': round(avg_confidence, 3)
        }


def main():
    """测试"""
    db_path = os.environ.get('MEMORY_DB_PATH', '/path/to/memory.db')
    enhancer = SemanticMemoryEnhancer(db_path)
    
    # 存储事实
    fact_id = enhancer.store_fact(
        content="John Smith works at TechCorp Group",
        entity="John Smith",
        value="TechCorp Group",
        confidence=0.9,
        source="profile",
        category="work",
        tags=["person", "company"]
    )
    print(f'[Test] Stored fact ID: {fact_id}')
    
    # 提取并存储
    text = "Alice is an AI assistant with management and technical skills"
    fact_ids = enhancer.extract_and_store(text, source="extraction")
    print(f'[Test] Extracted {len(fact_ids)} facts from text')
    
    # 检索
    facts = enhancer.recall_facts('AI', limit=5)
    print(f'[Test] Found {len(facts)} facts')
    for f in facts:
        print(f'  - {f["content"][:50]}... (conf: {f["confidence"]})')
    
    # 统计
    stats = enhancer.get_fact_statistics()
    print(f'[Test] Statistics: {stats}')
    
    print('\n[OK] SemanticMemoryEnhancer test passed')


if __name__ == '__main__':
    main()