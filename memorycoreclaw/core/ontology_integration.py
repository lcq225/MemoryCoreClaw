# -*- coding: utf-8 -*-
"""
Ontology集成模块 - Integration Module

功能：
- 整合entity_detector和relation_inferencer
- 提供统一的集成接口
- 支持实体识别、关系推理、知识补全
- 可集成到MemoryCoreClaw

版本：v1.0
日期：2026-04-16
"""

import sqlite3
import sys
from typing import List, Dict, Optional
from pathlib import Path

# 导入Ontology组件（内置模块，使用相对导入）
from .entity_detector import EntityDetector, Entity
from .relation_inferencer import RelationInferencer, Relation

# Validator可选（可能不存在）
try:
    from .validator import OntologyValidator
except ImportError:
    OntologyValidator = None


class OntologyIntegration:
    """Ontology集成模块"""
    
    def __init__(self, db_path: str = None):
        """
        初始化Ontology集成模块
        
        Args:
            db_path: Memory.db路径
        """
        self.db_path = db_path or os.environ.get("MEMORY_DB_PATH", "memory.db")
        
        # 初始化组件
        self.entity_detector = EntityDetector()
        self.relation_inferencer = RelationInferencer(self.db_path)
        
        # 初始化Validator（可选）
        try:
            schema_path = Path(__file__).parent.parent / 'schema' / 'ontology_schema.yaml'
            self.validator = OntologyValidator(str(schema_path))
        except Exception as e:
            self.validator = None
            # OntologyValidator初始化失败时静默处理
        
        # 初始化成功（静默处理）
    
    def process_content(self, content: str, source: str = 'memory') -> Dict:
        """
        处理内容：实体识别 + 关系推理
        
        Args:
            content: 待处理的内容
            source: 来源
        
        Returns:
            处理结果（包含实体和关系）
        """
        # 1. 实体识别
        entities = self.entity_detector.detect_entities(content, source)
        
        # 2. 关系推理（基于识别出的实体）
        relations = self._infer_relations_from_entities(entities)
        
        # 3. 验证（可选）
        if self.validator:
            self._validate_entities(entities)
        
        return {
            'entities': entities,
            'relations': relations,
            'stats': self._get_stats(entities, relations)
        }
    
    def _infer_relations_from_entities(self, entities: List[Entity]) -> List[Relation]:
        """
        基于识别出的实体推理关系
        
        Args:
            entities: 实体列表
        
        Returns:
            推理出的关系列表
        """
        relations = []
        
        # 简单推理规则：
        # 如果内容中有Person和Organization实体，推理works_at关系
        persons = [e for e in entities if e.type == 'Person']
        organizations = [e for e in entities if e.type == 'Organization']
        
        for person in persons:
            for org in organizations:
                relations.append(Relation(
                    from_entity=person.name,
                    relation_type='works_at',
                    to_entity=org.name,
                    confidence=0.7,
                    reason='基于实体识别推理'
                ))
        
        # 如果内容中有Person和Technology实体，推理uses关系
        technologies = [e for e in entities if e.type == 'Technology']
        
        for person in persons:
            for tech in technologies:
                relations.append(Relation(
                    from_entity=person.name,
                    relation_type='uses',
                    to_entity=tech.name,
                    confidence=0.65,
                    reason='基于实体识别推理'
                ))
        
        # 如果内容中有Person和Project实体，推理participates_in关系
        projects = [e for e in entities if e.type == 'Project']
        
        for person in persons:
            for project in projects:
                relations.append(Relation(
                    from_entity=person.name,
                    relation_type='participates_in',
                    to_entity=project.name,
                    confidence=0.7,
                    reason='基于实体识别推理'
                ))
        
        return relations
    
    def _validate_entities(self, entities: List[Entity]) -> List[Dict]:
        """
        验证实体
        
        Args:
            entities: 实体列表
        
        Returns:
            验证结果列表
        """
        validation_results = []
        
        for entity in entities:
            # 将Entity转换为字典
            entity_data = {
                'name': entity.name,
                'content': entity.name
            }
            
            result = self.validator.validate_entity(entity.type, entity_data)
            validation_results.append({
                'entity': entity.name,
                'type': entity.type,
                'valid': result.valid,
                'errors': result.errors if not result.valid else []
            })
        
        return validation_results
    
    def _get_stats(self, entities: List[Entity], relations: List[Relation]) -> Dict:
        """
        获取统计信息
        
        Args:
            entities: 实体列表
            relations: 关系列表
        
        Returns:
            统计信息
        """
        entity_stats = self.entity_detector.get_entity_statistics(entities)
        
        relation_stats = {
            'total': len(relations),
            'by_type': {},
            'by_confidence': {
                'high': 0,
                'medium': 0,
                'low': 0
            }
        }
        
        for relation in relations:
            # 按类型统计
            if relation.relation_type not in relation_stats['by_type']:
                relation_stats['by_type'][relation.relation_type] = 0
            relation_stats['by_type'][relation.relation_type] += 1
            
            # 按置信度统计
            if relation.confidence >= 0.8:
                relation_stats['by_confidence']['high'] += 1
            elif relation.confidence >= 0.7:
                relation_stats['by_confidence']['medium'] += 1
            else:
                relation_stats['by_confidence']['low'] += 1
        
        return {
            'entities': entity_stats,
            'relations': relation_stats
        }
    
    def save_to_database(self, result: Dict) -> Dict:
        """
        保存到数据库
        
        Args:
            result: 处理结果
        
        Returns:
            保存结果
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        saved_entities = 0
        saved_relations = 0
        
        # 保存实体到entities表（如果存在）
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entities'")
        if cursor.fetchone():
            for entity in result['entities']:
                if entity.confidence >= 0.75:  # 只保存高置信度实体
                    cursor.execute('''
                        INSERT OR IGNORE INTO entities (name, type, confidence, context, source, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        entity.name,
                        entity.type,
                        entity.confidence,
                        entity.context[:100],
                        entity.source,
                        entity.created_at.isoformat()
                    ))
                    saved_entities += 1
        
        # 保存关系到relations表
        for relation in result['relations']:
            if relation.confidence >= 0.7:  # 只保存中高置信度关系
                cursor.execute('''
                    INSERT OR IGNORE INTO relations (from_entity, relation_type, to_entity, weight, evidence, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    relation.from_entity,
                    relation.relation_type,
                    relation.to_entity,
                    relation.confidence,
                    relation.reason,
                    relation.created_at.isoformat()
                ))
                saved_relations += 1
        
        conn.commit()
        conn.close()
        
        return {
            'saved_entities': saved_entities,
            'saved_relations': saved_relations,
            'total_entities': len(result['entities']),
            'total_relations': len(result['relations'])
        }
    
    def process_batch(self, contents: List[str], source: str = 'memory') -> Dict:
        """
        批量处理内容
        
        Args:
            contents: 内容列表
            source: 来源
        
        Returns:
            批量处理结果
        """
        all_entities = []
        all_relations = []
        
        for content in contents:
            result = self.process_content(content, source)
            all_entities.extend(result['entities'])
            all_relations.extend(result['relations'])
        
        # 去重
        unique_entities = []
        seen_entities = set()
        for entity in all_entities:
            key = (entity.name, entity.type)
            if key not in seen_entities:
                seen_entities.add(key)
                unique_entities.append(entity)
        
        unique_relations = []
        seen_relations = set()
        for relation in all_relations:
            key = (relation.from_entity, relation.relation_type, relation.to_entity)
            if key not in seen_relations:
                seen_relations.add(key)
                unique_relations.append(relation)
        
        return {
            'entities': unique_entities,
            'relations': unique_relations,
            'stats': self._get_stats(unique_entities, unique_relations)
        }
    
    def print_report(self, result: Dict):
        """
        打印处理报告
        
        Args:
            result: 处理结果
        """
        print("=" * 60)
        print("📊 Ontology集成处理报告")
        print("=" * 60)
        
        stats = result['stats']
        
        print(f"\n实体统计:")
        print(f"  总数: {stats['entities']['total']}")
        print(f"  按类型:")
        for entity_type, count in sorted(stats['entities']['by_type'].items(), key=lambda x: x[1], reverse=True):
            print(f"    - {entity_type}: {count}个")
        
        print(f"\n关系统计:")
        print(f"  总数: {stats['relations']['total']}")
        print(f"  按类型:")
        for rel_type, count in sorted(stats['relations']['by_type'].items(), key=lambda x: x[1], reverse=True):
            print(f"    - {rel_type}: {count}条")
        
        print(f"\n置信度分布:")
        print(f"  实体:")
        print(f"    - 高(>=0.8): {stats['entities']['by_confidence']['high']}个")
        print(f"    - 中(0.7-0.8): {stats['entities']['by_confidence']['medium']}个")
        print(f"    - 低(<0.7): {stats['entities']['by_confidence']['low']}个")
        
        print(f"  关系:")
        print(f"    - 高(>=0.8): {stats['relations']['by_confidence']['high']}条")
        print(f"    - 中(0.7-0.8): {stats['relations']['by_confidence']['medium']}条")
        print(f"    - 低(<0.7): {stats['relations']['by_confidence']['low']}条")
        
        print("\n" + "=" * 60)


# 测试代码
if __name__ == '__main__':
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    print("=" * 60)
    print("Ontology集成模块测试")
    print("=" * 60)
    print()
    
    # 创建集成模块
    integration = OntologyIntegration()
    print()
    
    # 测试内容
    test_contents = [
        "Mr Lee, 43岁, 山东海科化工集团, 卓越与智能部",
        "AI assistant using modern tech stack",
        "海科化工正在推进智能转型项目",
        "ERP系统和MES系统需要集成"
    ]
    
    print("测试内容:")
    for i, content in enumerate(test_contents, 1):
        print(f"  {i}. {content}")
    print()
    
    # 批量处理
    result = integration.process_batch(test_contents)
    integration.print_report(result)
    
    # 显示识别结果
    print("\n识别出的实体（高置信度）:")
    high_entities = [e for e in result['entities'] if e.confidence >= 0.75]
    for entity in high_entities[:10]:
        print(f"  {entity.type}: {entity.name} (置信度: {entity.confidence:.2f})")
    
    print("\n推理出的关系（中高置信度）:")
    high_relations = [r for r in result['relations'] if r.confidence >= 0.7]
    for relation in high_relations[:10]:
        print(f"  {relation.from_entity} --[{relation.relation_type}]--> {relation.to_entity}")
        print(f"    置信度: {relation.confidence:.2f} | 原因: {relation.reason}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)