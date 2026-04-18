#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced Search Module
增强搜索模块 - 向量搜索 + 关键词搜索 + 自动切换
"""

import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime


class EnhancedSearch:
    """增强搜索 - 支持向量、关键词、自动切换"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.vector_service = None
        self.use_vector = False
        
        # 尝试初始化向量服务
        self._init_vector_service()
    
    def _init_vector_service(self):
        """初始化向量服务"""
        try:
            from vector_model_service import get_vector_service
            self.vector_service = get_vector_service()
            self.use_vector = True
            print('[EnhancedSearch] 向量服务已启用')
        except Exception as e:
            print(f'[EnhancedSearch] 向量服务初始化失败: {e}')
            self.use_vector = False
    
    def search(
        self,
        query: str,
        memory_types: List[str] = None,
        limit: int = 5
    ) -> Dict[str, List[Dict]]:
        """
        统一搜索 - 向量优先，失败则回退关键词
        
        Args:
            query: 查询内容
            memory_types: 搜索类型 ['episodic', 'semantic', 'procedural']
            limit: 返回数量
            
        Returns:
            Dict: 按类型分类的结果
        """
        if memory_types is None:
            memory_types = ['episodic', 'semantic', 'procedural']
        
        results = {}
        
        # 优先尝试向量搜索
        if self.use_vector:
            try:
                print(f'[EnhancedSearch] 使用向量搜索: "{query}"')
                results = self._vector_search(query, memory_types, limit)
                
                # 检查结果是否有效
                total_results = sum(len(v) for v in results.values())
                if total_results > 0:
                    print(f'[EnhancedSearch] 向量搜索成功: {total_results} 条结果')
                    return results
                else:
                    print('[EnhancedSearch] 向量搜索无结果，回退关键词搜索')
                    
            except Exception as e:
                print(f'[EnhancedSearch] 向量搜索失败: {e}，回退关键词搜索')
        
        # 回退到关键词搜索
        print(f'[EnhancedSearch] 使用关键词搜索: "{query}"')
        results = self._keyword_search(query, memory_types, limit)
        
        return results
    
    def _vector_search(
        self,
        query: str,
        memory_types: List[str],
        limit: int
    ) -> Dict[str, List[Dict]]:
        """向量搜索"""
        results = {}
        
        # 获取查询向量
        query_vec = self.vector_service.get_embedding(query)
        if not query_vec:
            raise Exception('无法获取查询向量')
        
        if 'episodic' in memory_types:
            results['episodic'] = self._vector_search_episodic(query, query_vec, limit)
        
        if 'semantic' in memory_types:
            results['semantic'] = self._vector_search_semantic(query, query_vec, limit)
        
        if 'procedural' in memory_types:
            results['procedural'] = self._vector_search_procedural(query, query_vec, limit)
        
        return results
    
    def _vector_search_episodic(
        self,
        query: str,
        query_vec: List[float],
        limit: int
    ) -> List[Dict]:
        """向量搜索情节记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取所有记录
        cursor.execute("""
            SELECT id, action, context, outcome, insight, importance, category, tags, created_at
            FROM experiences
            ORDER BY created_at DESC
            LIMIT 100
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        # 简单方案：先获取文本，用关键词粗筛后用向量精排
        candidates = []
        query_lower = query.lower()
        
        for row in rows:
            # 粗筛：关键词匹配
            text = ' '.join([
                str(row[1] or ''),  # action
                str(row[3] or ''),  # outcome
                str(row[4] or ''),  # insight
                str(row[6] or ''),  # category
            ]).lower()
            
            if query_lower in text:
                candidates.append({
                    'id': row[0],
                    'action': row[1],
                    'context': row[2],
                    'outcome': row[3],
                    'insight': row[4],
                    'importance': row[5],
                    'category': row[6],
                    'tags': row[7],
                    'created_at': row[8],
                    'text': text,
                })
        
        # 如果有候选，用向量重排
        if candidates and self.vector_service:
            texts = [c['text'] for c in candidates]
            reranked = self.vector_service.rerank(query, texts, top_k=min(limit, len(texts)))
            
            # 构建结果
            result_list = []
            for idx, score in reranked:
                c = candidates[idx]
                c['rerank_score'] = score
                result_list.append(c)
            
            return result_list[:limit]
        
        return candidates[:limit]
    
    def _vector_search_semantic(
        self,
        query: str,
        query_vec: List[float],
        limit: int
    ) -> List[Dict]:
        """向量搜索语义记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, content, category, importance, tags, created_at, source, source_confidence
            FROM facts
            ORDER BY importance DESC
            LIMIT 100
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        candidates = []
        query_lower = query.lower()
        
        for row in rows:
            text = ' '.join([
                str(row[1] or ''),  # content
                str(row[2] or ''),  # category
            ]).lower()
            
            if query_lower in text:
                candidates.append({
                    'id': row[0],
                    'content': row[1],
                    'category': row[2],
                    'importance': row[3],
                    'tags': row[4],
                    'created_at': row[5],
                    'source': row[6],
                    'source_confidence': row[7],
                    'text': text,
                })
        
        # 向量重排
        if candidates and self.vector_service:
            texts = [c['text'] for c in candidates]
            reranked = self.vector_service.rerank(query, texts, top_k=min(limit, len(texts)))
            
            result_list = []
            for idx, score in reranked:
                c = candidates[idx]
                c['rerank_score'] = score
                result_list.append(c)
            
            return result_list[:limit]
        
        return candidates[:limit]
    
    def _vector_search_procedural(
        self,
        query: str,
        query_vec: List[float],
        limit: int
    ) -> List[Dict]:
        """向量搜索程序记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, steps, skill_name, category, success_rate
            FROM procedures
            ORDER BY success_rate DESC, usage_count DESC
            LIMIT 50
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        candidates = []
        query_lower = query.lower()
        
        for row in rows:
            text = ' '.join([
                str(row[1] or ''),  # name
                str(row[2] or ''),  # description
                str(row[5] or ''),  # category
            ]).lower()
            
            if query_lower in text:
                candidates.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'steps': row[3],
                    'skill_name': row[4],
                    'category': row[5],
                    'success_rate': row[6],
                    'text': text,
                })
        
        return candidates[:limit]
    
    def _keyword_search(
        self,
        query: str,
        memory_types: List[str],
        limit: int
    ) -> Dict[str, List[Dict]]:
        """关键词搜索（回退方案）"""
        results = {}
        
        if 'episodic' in memory_types:
            results['episodic'] = self._keyword_search_episodic(query, limit)
        
        if 'semantic' in memory_types:
            results['semantic'] = self._keyword_search_semantic(query, limit)
        
        if 'procedural' in memory_types:
            results['procedural'] = self._keyword_search_procedural(query, limit)
        
        return results
    
    def _keyword_search_episodic(self, query: str, limit: int) -> List[Dict]:
        """关键词搜索情节记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, action, context, outcome, insight, importance, category, tags, created_at
            FROM experiences
            WHERE action LIKE ? OR outcome LIKE ? OR insight LIKE ? OR category LIKE ?
            ORDER BY importance DESC, created_at DESC
            LIMIT ?
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'action': row[1],
                'context': row[2],
                'outcome': row[3],
                'insight': row[4],
                'importance': row[5],
                'category': row[6],
                'tags': row[7],
                'created_at': row[8],
            }
            for row in rows
        ]
    
    def _keyword_search_semantic(self, query: str, limit: int) -> List[Dict]:
        """关键词搜索语义记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, content, category, importance, tags, created_at, source, source_confidence
            FROM facts
            WHERE content LIKE ? OR category LIKE ? OR tags LIKE ?
            ORDER BY importance DESC, created_at DESC
            LIMIT ?
        """, (f'%{query}%', f'%{query}%', f'%{query}%', limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'content': row[1],
                'category': row[2],
                'importance': row[3],
                'tags': row[4],
                'created_at': row[5],
                'source': row[6],
                'source_confidence': row[7],
            }
            for row in rows
        ]
    
    def _keyword_search_procedural(self, query: str, limit: int) -> List[Dict]:
        """关键词搜索程序记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, steps, skill_name, category, success_rate, usage_count
            FROM procedures
            WHERE name LIKE ? OR description LIKE ? OR category LIKE ? OR skill_name LIKE ?
            ORDER BY success_rate DESC, usage_count DESC
            LIMIT ?
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'steps': row[3],
                'skill_name': row[4],
                'category': row[5],
                'success_rate': row[6],
                'usage_count': row[7],
            }
            for row in rows
        ]
    
    def get_vector_status(self) -> Dict:
        """获取向量服务状态"""
        if self.vector_service:
            return self.vector_service.get_status()
        return {'enabled': False}