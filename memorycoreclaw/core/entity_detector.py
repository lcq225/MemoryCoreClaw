#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实体识别器 - Entity Detector

功能：
- 基于关键词识别实体类型
- 支持Person、Organization、Technology、Project等实体类型
- 提供置信度评分
- 可扩展的识别规则

版本：v1.0
日期：2026-04-16
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Entity:
    """实体数据结构"""
    name: str
    type: str
    confidence: float
    context: str
    source: str
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class EntityDetector:
    """实体识别器"""
    
    # 实体识别规则（基于关键词）
    ENTITY_RULES = {
        'Person': {
            'keywords': [
                'Mr Smith', 'Alice', 'Bob', 'Manager Wang', 'Director Zhang',
                'Engineer Li', 'Dr Liu', 'Manager Zhao', 'Director Zhou'
            ],
            'patterns': [
                r'[A-Z][a-z]+\s+[A-Z][a-z]+',  # English names (e.g., John Doe)
                r'\w+Manager',  # Manager titles
                r'\w+Director',  # Director titles
                r'\w+Engineer',  # Engineer titles
                r'\w+Doctor',  # Academic titles
            ],
            'confidence_base': 0.8
        },
        'Organization': {
            'keywords': [
                'Company', 'Organization', 'Department',
                'Engineering Dept', 'Production Dept', 'Operations Dept',
                'IT Department', 'Group', 'Subsidiary', 'Factory', 'Laboratory'
            ],
            'patterns': [
                r'\w+Company',  # Company names
                r'\w+Group',  # Groups
                r'\w+Department',  # Departments
                r'\w+Laboratory',  # Laboratories
                r'\w+Factory',  # Factories
            ],
            'confidence_base': 0.85
        },
        'Technology': {
            'keywords': [
                'Project', 'Agent', 'Skill', 'Technology',
                'Python', 'FastAPI', 'JavaScript', 'React',
                'Docker', 'Kubernetes', 'Git', 'Linux',
                'AI', 'LLM', 'GPT', 'Claude', 'Qwen',
                'Embedding', 'Vector', 'Knowledge Graph', 'Ontology'
            ],
            'patterns': [
                r'[A-Z][a-z]+[A-Z][a-z]+',  # Technical names (e.g., TensorFlow)
                r'[A-Z]{2,}',  # Technical abbreviations (e.g., AI, LLM)
                r'\w+Technology',  # Technology names
            ],
            'confidence_base': 0.75
        },
        'Project': {
            'keywords': [
                'Project', 'AI Project', 'Digital Project',
                'Digital Transformation Project', 'System Upgrade Project', 'Platform Construction Project'
            ],
            'patterns': [
                r'\w+Project',  # Project names
                r'[A-Z][a-z]+Project',  # Technical projects
            ],
            'confidence_base': 0.8
        },
        'System': {
            'keywords': [
                'System', 'ERP', 'MES', 'DCS', 'LIMS', 'OA',
                'CRM', 'HR System', 'Finance System', 'Production System',
                'Monitoring System', 'Logging System', 'Permission System'
            ],
            'patterns': [
                r'[A-Z]{2,}',  # System abbreviations (e.g., ERP, MES)
                r'\w+System',  # System names
            ],
            'confidence_base': 0.85
        },
        'Service': {
            'keywords': [
                'Service', 'API', 'Server', 'Client', 'Microservice',
                'Gateway', 'Nginx', 'Redis', 'MySQL', 'PostgreSQL'
            ],
            'patterns': [
                r'[A-Z][a-z]+',  # Service names
                r'\w+Service',  # Service names
            ],
            'confidence_base': 0.75
        },
        'Location': {
            'keywords': [
                'Beijing', 'Shanghai', 'Shenzhen',
                'Headquarters', 'Production Base', 'R&D Center'
            ],
            'patterns': [
                r'\w+Province',  # Provinces
                r'\w+City',  # Cities
                r'\w+Headquarters',  # Headquarters
                r'\w+Base',  # Bases
                r'\w+Center',  # Centers
            ],
            'confidence_base': 0.8
        },
        'Knowledge': {
            'keywords': [
                'Memory', 'Knowledge', 'Experience', 'Lesson', 'Decision',
                'Preference', 'Rule', 'Configuration', 'Best Practice'
            ],
            'patterns': [
                r'\w+Preference',  # Preferences
                r'\w+Rule',  # Rules
                r'\w+Configuration',  # Configurations
                r'\w+Practice',  # Best practices
            ],
            'confidence_base': 0.7
        }
    }
    
    def __init__(self):
        """初始化实体识别器"""
        self.rules = self.ENTITY_RULES
        # 静默初始化，不打印信息（避免导入时输出）
    
    def detect_entities(self, content: str, source: str = 'memory') -> List[Entity]:
        """
        从内容中识别实体
        
        Args:
            content: 待识别的内容
            source: 来源（memory/manual/api）
        
        Returns:
            识别出的实体列表
        """
        entities = []
        
        for entity_type, rule in self.rules.items():
            # 1. 关键词匹配
            for keyword in rule['keywords']:
                if keyword in content:
                    entities.append(Entity(
                        name=keyword,
                        type=entity_type,
                        confidence=rule['confidence_base'],
                        context=content[:100],
                        source=source
                    ))
            
            # 2. 正则表达式匹配
            for pattern in rule['patterns']:
                matches = re.findall(pattern, content)
                for match in matches:
                    # 避免重复
                    if match not in [e.name for e in entities]:
                        entities.append(Entity(
                            name=match,
                            type=entity_type,
                            confidence=rule['confidence_base'] - 0.1,  # 正则匹配置信度稍低
                            context=content[:100],
                            source=source
                        ))
        
        return entities
    
    def detect_entities_batch(self, contents: List[str], source: str = 'memory') -> List[Entity]:
        """
        批量识别实体
        
        Args:
            contents: 待识别的内容列表
            source: 来源
        
        Returns:
            所有识别出的实体
        """
        all_entities = []
        
        for i, content in enumerate(contents):
            entities = self.detect_entities(content, source)
            all_entities.extend(entities)
        
        # 去重（基于name和type）
        unique_entities = []
        seen = set()
        
        for entity in all_entities:
            key = (entity.name, entity.type)
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def get_entity_statistics(self, entities: List[Entity]) -> Dict:
        """
        获取实体统计信息
        
        Args:
            entities: 实体列表
        
        Returns:
            统计信息
        """
        stats = {
            'total': len(entities),
            'by_type': {},
            'by_confidence': {
                'high': 0,  # confidence >= 0.8
                'medium': 0,  # 0.7 <= confidence < 0.8
                'low': 0  # confidence < 0.7
            }
        }
        
        for entity in entities:
            # 按类型统计
            if entity.type not in stats['by_type']:
                stats['by_type'][entity.type] = 0
            stats['by_type'][entity.type] += 1
            
            # 按置信度统计
            if entity.confidence >= 0.8:
                stats['by_confidence']['high'] += 1
            elif entity.confidence >= 0.7:
                stats['by_confidence']['medium'] += 1
            else:
                stats['by_confidence']['low'] += 1
        
        return stats
    
    def export_entities(self, entities: List[Entity], format: str = 'json') -> str:
        """
        导出实体
        
        Args:
            entities: 实体列表
            format: 导出格式（json/csv/text）
        
        Returns:
            导出的内容
        """
        if format == 'json':
            import json
            return json.dumps([{
                'name': e.name,
                'type': e.type,
                'confidence': e.confidence,
                'context': e.context,
                'source': e.source,
                'created_at': e.created_at.isoformat()
            } for e in entities], ensure_ascii=False, indent=2)
        
        elif format == 'csv':
            lines = ['name,type,confidence,source']
            for e in entities:
                lines.append(f"{e.name},{e.type},{e.confidence:.2f},{e.source}")
            return '\n'.join(lines)
        
        elif format == 'text':
            lines = ['Detected Entities:']
            for e in entities:
                lines.append(f"  {e.type}: {e.name} (confidence: {e.confidence:.2f})")
            return '\n'.join(lines)
        
        else:
            raise ValueError(f"Unsupported format: {format}")


# 测试代码
if __name__ == '__main__':
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    print("=" * 60)
    print("Entity Detector Test")
    print("=" * 60)
    print()
    
    # 创建识别器
    detector = EntityDetector()
    print(f"✓ EntityDetector initialized, supports {len(detector.rules)} entity types")
    print()
    
    # 测试内容
    test_contents = [
        "Mr Smith, 43 years old, TechCorp Group, Engineering Dept",
        "Mr Smith prefers BLUF communication style",
        "Alice is a versatile assistant with management and technical skills",
        "AI project using Python and FastAPI",
        "TechCorp is advancing digital transformation project",
        "ERP system and MES system need integration",
        "Beijing is the headquarters of TechCorp"
    ]
    
    print("Test contents:")
    for i, content in enumerate(test_contents, 1):
        print(f"  {i}. {content}")
    print()
    
    # 批量识别
    entities = detector.detect_entities_batch(test_contents)
    
    print("Detection results:")
    stats = detector.get_entity_statistics(entities)
    
    print(f"  Total entities: {stats['total']}")
    print()
    
    print("  By type:")
    for entity_type, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
        print(f"    - {entity_type}: {count}")
    print()
    
    print("  By confidence:")
    print(f"    - High (>=0.8): {stats['by_confidence']['high']}")
    print(f"    - Medium (0.7-0.8): {stats['by_confidence']['medium']}")
    print(f"    - Low (<0.7): {stats['by_confidence']['low']}")
    print()
    
    print("  Detailed results:")
    for entity in entities:
        print(f"    {entity.type}: {entity.name} (confidence: {entity.confidence:.2f})")
    
    print()
    print("=" * 60)
    print("Test complete")
    print("=" * 60)
