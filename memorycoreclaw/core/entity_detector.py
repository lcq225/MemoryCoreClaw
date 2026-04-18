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
                'Mr Lee', '老K', 'Siva', '王经理', '张总', '李主任',
                '陈工程师', '刘博士', '赵经理', '周部长'
            ],
            'patterns': [
                r'[A-Z][a-z]+\s+[A-Z][a-z]+',  # 英文名（如 Mr Lee）
                r'老\w+',  # 中文称呼（如 老K）
                r'\w+经理',  # 职位称呼
                r'\w+总',  # 高管称呼
                r'\w+主任',  # 部门负责人
                r'\w+工程师',  # 技术人员
                r'\w+博士',  # 学术人员
                r'\w+部长',  # 部门领导
            ],
            'confidence_base': 0.8
        },
        'Organization': {
            'keywords': [
                '海科', '海科化工', '海科新源', '公司', '组织', '部门',
                '卓越与智能部', '生产部门', '运维部门', 'IT部门',
                '集团', '子公司', '工厂', '实验室'
            ],
            'patterns': [
                r'\w+化工',  # 化工公司
                r'\w+公司',  # 公司
                r'\w+集团',  # 集团
                r'\w+部门',  # 部门
                r'\w+实验室',  # 实验室
                r'\w+工厂',  # 工厂
            ],
            'confidence_base': 0.85
        },
        'Technology': {
            'keywords': [
                'Project', 'Agent', 'Skill', '技能', '技术',
                'Python', 'FastAPI', 'JavaScript', 'React',
                'Docker', 'Kubernetes', 'Git', 'Linux',
                'AI', 'LLM', 'GPT', 'Claude', 'Qwen',
                'Embedding', '向量', '知识图谱', 'Ontology'
            ],
            'patterns': [
                r'[A-Z][a-z]+[A-Z][a-z]+',  # 技术名（如 QwenPaw）
                r'[A-Z]{2,}',  # 技术缩写（如 AI, LLM）
                r'\w+技能',  # 技能名
                r'\w+技术',  # 技术名
            ],
            'confidence_base': 0.75
        },
        'Project': {
            'keywords': [
                'Project', 'AI Project', 'Digital Project',
                '数字化项目', '系统升级项目', '平台建设项目'
            ],
            'patterns': [
                r'\w+项目',  # 项目名
                r'[A-Z][a-z]+项目',  # 技术项目
            ],
            'confidence_base': 0.8
        },
        'System': {
            'keywords': [
                '系统', 'ERP', 'MES', 'DCS', 'LIMS', 'OA',
                'CRM', 'HR系统', '财务系统', '生产系统',
                '监控系统', '日志系统', '权限系统'
            ],
            'patterns': [
                r'[A-Z]{2,}',  # 系统缩写（如 ERP, MES）
                r'\w+系统',  # 系统名
            ],
            'confidence_base': 0.85
        },
        'Service': {
            'keywords': [
                '服务', 'API', '服务端', '客户端', '微服务',
                'Gateway', 'Nginx', 'Redis', 'MySQL', 'PostgreSQL',
                'Ollama', 'Higress'
            ],
            'patterns': [
                r'[A-Z][a-z]+',  # 服务名
                r'\w+服务',  # 服务名
            ],
            'confidence_base': 0.75
        },
        'Location': {
            'keywords': [
                '山东', '东营', '北京', '上海', '深圳',
                '海科总部', '生产基地', '研发中心'
            ],
            'patterns': [
                r'\w+省',  # 省份
                r'\w+市',  # 城市
                r'\w+总部',  # 总部
                r'\w+基地',  # 基地
                r'\w+中心',  # 中心
            ],
            'confidence_base': 0.8
        },
        'Knowledge': {
            'keywords': [
                '记忆', '知识', '经验', '教训', '决策',
                '偏好', '规则', '配置', '最佳实践'
            ],
            'patterns': [
                r'\w+偏好',  # 偏好
                r'\w+规则',  # 规则
                r'\w+配置',  # 配置
                r'\w+实践',  # 最佳实践
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
            lines = ['识别出的实体：']
            for e in entities:
                lines.append(f"  {e.type}: {e.name} (置信度: {e.confidence:.2f})")
            return '\n'.join(lines)
        
        else:
            raise ValueError(f"不支持的格式: {format}")


# 测试代码
if __name__ == '__main__':
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    print("=" * 60)
    print("实体识别器测试")
    print("=" * 60)
    print()
    
    # 创建识别器
    detector = EntityDetector()
    print(f"✓ EntityDetector初始化成功，支持{len(detector.rules)}种实体类型")
    print()
    
    # 测试内容
    test_contents = [
        "Mr Lee, 43岁, 山东海科化工集团, 卓越与智能部",
        "Mr Lee 偏好 BLUF 沟通风格",
        "老K 是全能助手，具有顶级管理者、领导者思维，兼具全方位的技术与业务能力",
        "AI project using Python and FastAPI",
        "海科化工正在推进智能转型项目",
        "ERP系统和MES系统需要集成",
        "山东东营是海科化工的总部所在地"
    ]
    
    print("测试内容:")
    for i, content in enumerate(test_contents, 1):
        print(f"  {i}. {content}")
    print()
    
    # 批量识别
    entities = detector.detect_entities_batch(test_contents)
    
    print("识别结果:")
    stats = detector.get_entity_statistics(entities)
    
    print(f"  总实体数: {stats['total']}")
    print()
    
    print("  按类型分布:")
    for entity_type, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
        print(f"    - {entity_type}: {count}个")
    print()
    
    print("  按置信度分布:")
    print(f"    - 高置信度(>=0.8): {stats['by_confidence']['high']}个")
    print(f"    - 中置信度(0.7-0.8): {stats['by_confidence']['medium']}个")
    print(f"    - 低置信度(<0.7): {stats['by_confidence']['low']}个")
    print()
    
    print("  详细识别结果:")
    for entity in entities:
        print(f"    {entity.type}: {entity.name} (置信度: {entity.confidence:.2f})")
    
    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)