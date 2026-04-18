#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Triple Memory Interface (三层记忆统一接口)

整合情节记忆、语义记忆、程序记忆的统一接口
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from typing import Optional, List, Dict, Any, Union
from enhanced_episodic import EpisodicMemoryEnhancer
from enhanced_semantic import SemanticMemoryEnhancer
from enhanced_procedural import ProceduralMemoryEnhancer
from enhanced_search import EnhancedSearch


class TripleMemory:
    """
    三层记忆统一接口
    
    功能：
    - 情节记忆：交互事件记录
    - 语义记忆：事实和知识管理
    - 程序记忆：流程和技能存储
    """
    
    def __init__(self, db_path: str):
        """
        初始化三层记忆
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        
        # 初始化三个增强器
        self.episodic = EpisodicMemoryEnhancer(db_path)
        self.semantic = SemanticMemoryEnhancer(db_path)
        self.procedural = ProceduralMemoryEnhancer(db_path)
        
        # 初始化增强搜索（向量搜索 + 自动切换）
        self.search_engine = EnhancedSearch(db_path)
    
    # ========== 情节记忆 ==========
    
    def remember_event(
        self,
        content: str,
        action: str,
        outcome: str,
        importance: float = 0.5,
        context: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """
        记住事件
        
        Args:
            content: 事件内容
            action: 执行的动作
            outcome: 结果
            importance: 重要性 (0-1)
            context: 上下文
            tags: 标签
            
        Returns:
            int: 记忆ID
        """
        return self.episodic.store_episode(
            content=content,
            action=action,
            outcome=outcome,
            importance=importance,
            context=context,
            tags=tags
        )
    
    def recall_events(
        self,
        query: str,
        limit: int = 5,
        min_importance: float = 0.0
    ) -> List[Dict]:
        """
        检索事件
        
        Args:
            query: 查询关键词
            limit: 返回数量
            min_importance: 最小重要性
            
        Returns:
            List[Dict]: 匹配的事件
        """
        return self.episodic.recall_episodes(query, limit, min_importance)
    
    def get_important_events(self, limit: int = 10) -> List[Dict]:
        """获取重要事件"""
        return self.episodic.get_important_episodes(limit)
    
    # ========== 语义记忆 ==========
    
    def learn_fact(
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
        学习事实
        
        Args:
            content: 事实内容
            entity: 实体
            value: 值
            confidence: 置信度
            source: 来源
            category: 分类
            tags: 标签
            
        Returns:
            int: 事实ID
        """
        return self.semantic.store_fact(
            content=content,
            entity=entity,
            value=value,
            confidence=confidence,
            source=source,
            category=category,
            tags=tags
        )
    
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
            entity: 实体
            min_confidence: 最小置信度
            limit: 返回数量
            
        Returns:
            List[Dict]: 匹配的事实
        """
        return self.semantic.recall_facts(query, entity, min_confidence, limit)
    
    def extract_knowledge(self, text: str, source: str = "user") -> List[int]:
        """
        从文本中提取知识
        
        Args:
            text: 文本
            source: 来源
            
        Returns:
            List[int]: 提取的事实ID列表
        """
        return self.semantic.extract_and_store(text, source)
    
    # ========== 程序记忆 ==========
    
    def remember_procedure(
        self,
        name: str,
        description: str,
        steps: List[str],
        skill_name: str = "",
        version: str = "",
        category: str = "general",
        tags: Optional[List[str]] = None
    ) -> int:
        """
        记住流程
        
        Args:
            name: 流程名称
            description: 描述
            steps: 步骤列表
            skill_name: 技能名称
            version: 版本
            category: 分类
            tags: 标签
            
        Returns:
            int: 程序ID
        """
        return self.procedural.store_procedure(
            name=name,
            description=description,
            steps=steps,
            skill_name=skill_name,
            version=version,
            category=category,
            tags=tags
        )
    
    def recall_procedures(
        self,
        query: str,
        category: Optional[str] = None,
        min_success_rate: float = 0.0,
        limit: int = 10
    ) -> List[Dict]:
        """
        检索流程
        
        Args:
            query: 查询关键词
            category: 分类
            min_success_rate: 最小成功率
            limit: 返回数量
            
        Returns:
            List[Dict]: 匹配的程序
        """
        return self.procedural.recall_procedures(
            query, category, min_success_rate, limit
        )
    
    def record_skill_execution(
        self,
        procedure_name: str,
        success: bool,
        error: Optional[str] = None,
        duration_ms: int = 0
    ):
        """
        记录技能执行
        
        Args:
            procedure_name: 程序名称
            success: 是否成功
            error: 错误信息
            duration_ms: 执行时间
        """
        self.procedural.record_execution(
            procedure_name, success, error, duration_ms
        )
    
    # ========== 统一检索 ==========
    
    def search(
        self,
        query: str,
        memory_types: List[str] = None,
        limit: int = 5,
        use_vector: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        统一搜索 - 向量优先，自动切换
        
        Args:
            query: 查询关键词
            memory_types: 搜索类型 ['episodic', 'semantic', 'procedural']
            limit: 每类返回数量
            use_vector: 是否优先使用向量搜索
            
        Returns:
            Dict: 按类型分类的结果
        """
        if memory_types is None:
            memory_types = ['episodic', 'semantic', 'procedural']
        
        # 使用增强搜索（向量优先，失败自动切换关键词）
        if use_vector:
            return self.search_engine.search(query, memory_types, limit)
        
        # 回退到传统关键词搜索
        return self._keyword_search_fallback(query, memory_types, limit)
    
    def _keyword_search_fallback(
        self,
        query: str,
        memory_types: List[str],
        limit: int
    ) -> Dict[str, List[Dict]]:
        """传统关键词搜索（回退方案）"""
        results = {}
        
        if 'episodic' in memory_types:
            results['episodic'] = self.recall_events(query, limit)
        
        if 'semantic' in memory_types:
            results['semantic'] = self.recall_facts(query, limit=limit)
        
        if 'procedural' in memory_types:
            results['procedural'] = self.recall_procedures(query, limit=limit)
        
        return results
    
    def get_vector_status(self) -> Dict:
        """获取向量服务状态"""
        return self.search_engine.get_vector_status()
    
    # ========== 统计信息 ==========
    
    def get_statistics(self) -> Dict:
        """获取记忆统计"""
        return {
            'episodic': {
                'recent': len(self.episodic.get_recent_episodes(limit=100)),
                'important': len(self.episodic.get_important_episodes(limit=100))
            },
            'semantic': self.semantic.get_fact_statistics(),
            'procedural': self.procedural.get_statistics()
        }


def main():
    """测试"""
    db_path = os.environ.get('MEMORY_DB_PATH', '/path/to/memory.db')
    memory = TripleMemory(db_path)
    
    # 记住事件
    event_id = memory.remember_event(
        content="User asked to create a PowerPoint",
        action="create_presentation",
        outcome="Successfully created",
        importance=0.8,
        tags=["pptx", "presentation"]
    )
    print(f'[Test] Remembered event: {event_id}')
    
    # 学习事实
    fact_id = memory.learn_fact(
        content="An AI agent framework example",
        entity="ExampleAgent",
        value="AI agent framework",
        confidence=0.9,
        source="documentation"
    )
    print(f'[Test] Learned fact: {fact_id}')
    
    # 记住流程
    proc_id = memory.remember_procedure(
        name="create_pptx_workflow",
        description="创建PPT的流程",
        steps=["需求收集", "设计结构", "创建内容", "导出文件"],
        skill_name="pptx"
    )
    print(f'[Test] Remembered procedure: {proc_id}')
    
    # 统一搜索
    results = memory.search("create")
    print(f'\n[Test] Search results:')
    print(f'  - Episodic: {len(results.get("episodic", []))}')
    print(f'  - Semantic: {len(results.get("semantic", []))}')
    print(f'  - Procedural: {len(results.get("procedural", []))}')
    
    # 统计
    stats = memory.get_statistics()
    print(f'\n[Test] Statistics:')
    print(f'  - Episodic recent: {stats["episodic"]["recent"]}')
    print(f'  - Semantic total: {stats["semantic"]["total"]}')
    print(f'  - Procedural total: {stats["procedural"]["total"]}')
    
    print('\n[OK] TripleMemory test passed')


if __name__ == '__main__':
    main()