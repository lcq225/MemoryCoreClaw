# -*- coding: utf-8 -*-
"""
关系推理引擎 - Relation Inferencer

功能：
- 基于规则推理实体之间的隐含关系
- 支持多种推理规则（manages→works_at、同组织→colleague_of等）
- 提供置信度评分
- 可扩展的推理规则

版本：v1.0
日期：2026-04-16
"""

import sqlite3
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Relation:
    """关系数据结构"""
    from_entity: str
    relation_type: str
    to_entity: str
    confidence: float
    reason: str
    inferred: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class RelationInferencer:
    """关系推理引擎"""
    
    # 推理规则
    INFERENCE_RULES = {
        # 规则1：manages → works_at
        'manages_to_works_at': {
            'trigger_relation': 'manages',
            'infer_relation': 'works_at',
            'reason': '领导关系推理为工作关系',
            'confidence': 0.9
        },
        # 规则2：serves → knows
        'serves_to_knows': {
            'trigger_relation': 'serves',
            'infer_relation': 'knows',
            'reason': '服务关系推理为认识关系',
            'confidence': 0.85
        },
        # 规则3：uses（高频率）→ masters
        'uses_to_masters': {
            'trigger_relation': 'uses',
            'trigger_count': 3,  # 使用次数>=3
            'infer_relation': 'masters',
            'reason': '频繁使用推理为掌握',
            'confidence': 0.8
        },
        # 规则4：works_at + works_at → colleague_of（同组织同事）
        'works_at_to_colleague': {
            'trigger_relation': 'works_at',
            'same_to_entity': True,
            'infer_relation': 'colleague_of',
            'reason': '同组织推理为同事关系',
            'confidence': 0.75
        },
        # 规则5：leads → works_at
        'leads_to_works_at': {
            'trigger_relation': 'leads',
            'infer_relation': 'works_at',
            'reason': '领导关系推理为工作关系',
            'confidence': 0.9
        },
        # 规则6：participates_in → knows
        'participates_to_knows': {
            'trigger_relation': 'participates_in',
            'infer_relation': 'knows',
            'reason': '参与关系推理为认识关系',
            'confidence': 0.8
        }
    }
    
    def __init__(self, db_path: str = None):
        """初始化关系推理引擎"""
        self.db_path = db_path or os.environ.get("MEMORY_DB_PATH", "memory.db")
        self.rules = self.INFERENCE_RULES
    
    def _get_conn(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_existing_relations(self) -> List[Dict]:
        """获取现有关系"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT from_entity, relation_type, to_entity, weight, evidence
            FROM relations
        ''')
        
        relations = []
        for row in cursor.fetchall():
            relations.append({
                'from': row['from_entity'],
                'type': row['relation_type'],
                'to': row['to_entity'],
                'weight': row['weight'],
                'evidence': row['evidence']
            })
        
        conn.close()
        return relations
    
    def infer_relations(self) -> List[Relation]:
        """
        推理关系
        
        Returns:
            推理出的关系列表
        """
        existing_relations = self.get_existing_relations()
        inferred_relations = []
        
        # 规则1：manages → works_at
        for relation in existing_relations:
            if relation['type'] == 'manages':
                inferred_relations.append(Relation(
                    from_entity=relation['from'],
                    relation_type='works_at',
                    to_entity=relation['to'],
                    confidence=self.rules['manages_to_works_at']['confidence'],
                    reason=self.rules['manages_to_works_at']['reason']
                ))
        
        # 规则2：serves → knows
        for relation in existing_relations:
            if relation['type'] == 'serves':
                inferred_relations.append(Relation(
                    from_entity=relation['from'],
                    relation_type='knows',
                    to_entity=relation['to'],
                    confidence=self.rules['serves_to_knows']['confidence'],
                    reason=self.rules['serves_to_knows']['reason']
                ))
        
        # 规则3：leads → works_at
        for relation in existing_relations:
            if relation['type'] == 'leads':
                inferred_relations.append(Relation(
                    from_entity=relation['from'],
                    relation_type='works_at',
                    to_entity=relation['to'],
                    confidence=self.rules['leads_to_works_at']['confidence'],
                    reason=self.rules['leads_to_works_at']['reason']
                ))
        
        # 规则4：works_at + works_at → colleague_of
        works_at_relations = [r for r in existing_relations if r['type'] == 'works_at']
        
        # 按组织分组
        org_to_persons = {}
        for relation in works_at_relations:
            org = relation['to']
            if org not in org_to_persons:
                org_to_persons[org] = []
            org_to_persons[org].append(relation['from'])
        
        # 同组织的推理为同事
        for org, persons in org_to_persons.items():
            if len(persons) >= 2:
                for i in range(len(persons)):
                    for j in range(i + 1, len(persons)):
                        inferred_relations.append(Relation(
                            from_entity=persons[i],
                            relation_type='colleague_of',
                            to_entity=persons[j],
                            confidence=self.rules['works_at_to_colleague']['confidence'],
                            reason=f'{self.rules["works_at_to_colleague"]["reason"]}（同组织：{org}）'
                        ))
        
        return inferred_relations
    
    def save_inferred_relations(self, inferred_relations: List[Relation]) -> int:
        """
        保存推理出的关系到数据库
        
        Args:
            inferred_relations: 推理出的关系列表
        
        Returns:
            保存的关系数量
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        saved_count = 0
        
        for relation in inferred_relations:
            # 检查是否已存在（避免重复）
            cursor.execute('''
                SELECT COUNT(*) FROM relations
                WHERE from_entity = ? AND relation_type = ? AND to_entity = ?
            ''', (relation.from_entity, relation.relation_type, relation.to_entity))
            
            count = cursor.fetchone()[0]
            
            if count == 0:
                cursor.execute('''
                    INSERT INTO relations (from_entity, relation_type, to_entity, weight, evidence, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    relation.from_entity,
                    relation.relation_type,
                    relation.to_entity,
                    relation.confidence,
                    f'推理：{relation.reason}',
                    relation.created_at.isoformat()
                ))
                saved_count += 1
        
        conn.commit()
        conn.close()
        
        return saved_count
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        existing_relations = self.get_existing_relations()
        inferred_relations = self.infer_relations()
        
        stats = {
            'existing_relations': len(existing_relations),
            'inferred_relations': len(inferred_relations),
            'by_type': {},
            'by_confidence': {
                'high': 0,  # >=0.8
                'medium': 0,  # 0.7-0.8
                'low': 0  # <0.7
            }
        }
        
        # 按类型统计推理关系
        for relation in inferred_relations:
            if relation.relation_type not in stats['by_type']:
                stats['by_type'][relation.relation_type] = 0
            stats['by_type'][relation.relation_type] += 1
            
            # 按置信度统计
            if relation.confidence >= 0.8:
                stats['by_confidence']['high'] += 1
            elif relation.confidence >= 0.7:
                stats['by_confidence']['medium'] += 1
            else:
                stats['by_confidence']['low'] += 1
        
        return stats
    
    def print_report(self) -> Dict:
        """打印推理报告"""
        inferred_relations = self.infer_relations()
        stats = self.get_statistics()
        
        print("=" * 60)
        print("🔗 关系推理报告")
        print("=" * 60)
        
        print(f"\n📊 统计:")
        print(f"  现有关系: {stats['existing_relations']}条")
        print(f"  推理关系: {stats['inferred_relations']}条")
        
        print(f"\n按类型分布:")
        for rel_type, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {rel_type}: {count}条")
        
        print(f"\n按置信度分布:")
        print(f"  - 高置信度(>=0.8): {stats['by_confidence']['high']}条")
        print(f"  - 中置信度(0.7-0.8): {stats['by_confidence']['medium']}条")
        print(f"  - 低置信度(<0.7): {stats['by_confidence']['low']}条")
        
        print(f"\n推理示例（前10条）:")
        for i, relation in enumerate(inferred_relations[:10], 1):
            print(f"  {i}. {relation.from_entity} --[{relation.relation_type}]--> {relation.to_entity}")
            print(f"     置信度: {relation.confidence:.2f} | 原因: {relation.reason}")
        
        print("\n" + "=" * 60)
        
        return stats


# 测试代码
if __name__ == '__main__':
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    inferencer = RelationInferencer()
    stats = inferencer.print_report()
    
    # 测试保存（可选）
    print("\n是否保存推理出的关系到数据库？(y/n): ")
    # 这里不实际保存，仅展示功能
    print("  提示：实际使用时可调用 inferencer.save_inferred_relations() 保存")