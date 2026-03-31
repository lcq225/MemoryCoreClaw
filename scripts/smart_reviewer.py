# -*- coding: utf-8 -*-
"""
智能复习提醒 - 根据遗忘曲线主动提醒需要复习的记忆

功能：
- 计算哪些记忆需要复习
- 根据重要性和访问频率智能排序
- 生成复习建议
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

# 数据库路径
DB_PATH = r"D:\CoPaw\.copaw\.agent-memory\memory.db"


@dataclass
class MemoryReviewItem:
    """需要复习的记忆项"""
    memory_type: str
    memory_id: int
    content: str
    importance: float
    current_strength: float
    retention_rate: float
    days_since_access: int
    review_priority: float  # 0-100，越高越需要复习


class SmartReviewer:
    """
    智能复习提醒器
    
    基于遗忘曲线计算哪些记忆需要复习。
    
    优先级计算：
    - retention_rate 越低越需要复习
    - importance 越高越需要复习
    - days_since_access 越长越需要复习
    
    公式: priority = (1 - retention_rate) * 50 + importance * 30 + days_weight * 20
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
    
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def calculate_retention(self, last_accessed: str, importance: float) -> float:
        """
        计算记忆保持率
        
        使用 Ebbinghaus 遗忘曲线公式
        """
        if not last_accessed:
            return 1.0
        
        try:
            last_time = datetime.fromisoformat(last_accessed.replace('Z', '+00:00'))
        except:
            return 1.0
        
        # 计算天数
        days = (datetime.now() - last_time.replace(tzinfo=None)).total_seconds() / 86400
        if days < 0:
            days = 0
        
        # Ebbinghaus 公式: R = e^(-t/S)
        # S 是记忆强度（基于 importance）
        S = 0.2 + importance * 0.8  # 0.2 ~ 1.0
        
        import math
        retention = math.exp(-days / (S * 10))  # 调整系数让衰减更合理
        
        return max(0, min(1, retention))
    
    def calculate_priority(self, retention: float, importance: float, days: int) -> float:
        """计算复习优先级 (0-100)"""
        # 保持率权重
        retention_weight = (1 - retention) * 50
        
        # 重要性权重
        importance_weight = importance * 30
        
        # 时间权重
        days_weight = min(days / 30, 1) * 20  # 30天以上饱和
        
        return min(100, retention_weight + importance_weight + days_weight)
    
    def get_memories_to_review(self, min_priority: float = 20, limit: int = 20) -> List[MemoryReviewItem]:
        """
        获取需要复习的记忆
        
        Args:
            min_priority: 最小优先级阈值
            limit: 返回数量限制
            
        Returns:
            List[MemoryReviewItem]: 需要复习的记忆列表
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        results = []
        
        # 1. 从 facts 表获取
        cursor.execute('''
            SELECT id, content, importance, last_accessed
            FROM facts
            WHERE last_accessed IS NOT NULL
        ''')
        
        for row in cursor.fetchall():
            retention = self.calculate_retention(row['last_accessed'], row['importance'])
            days = (datetime.now() - datetime.fromisoformat(row['last_accessed'].replace('Z', '+00:00')).replace(tzinfo=None)).days if row['last_accessed'] else 0
            priority = self.calculate_priority(retention, row['importance'], days)
            
            if priority >= min_priority:
                results.append(MemoryReviewItem(
                    memory_type='fact',
                    memory_id=row['id'],
                    content=row['content'][:100],
                    importance=row['importance'],
                    current_strength=0,  # 从 memory_strength 表获取更准确
                    retention_rate=retention,
                    days_since_access=days,
                    review_priority=priority
                ))
        
        # 2. 从 experiences 表获取
        cursor.execute('''
            SELECT id, action, importance, last_accessed
            FROM experiences
            WHERE last_accessed IS NOT NULL
        ''')
        
        for row in cursor.fetchall():
            retention = self.calculate_retention(row['last_accessed'], row['importance'])
            days = (datetime.now() - datetime.fromisoformat(row['last_accessed'].replace('Z', '+00:00')).replace(tzinfo=None)).days if row['last_accessed'] else 0
            priority = self.calculate_priority(retention, row['importance'], days)
            
            if priority >= min_priority:
                results.append(MemoryReviewItem(
                    memory_type='experience',
                    memory_id=row['id'],
                    content=row['action'][:100],
                    importance=row['importance'],
                    current_strength=0,
                    retention_rate=retention,
                    days_since_access=days,
                    review_priority=priority
                ))
        
        conn.close()
        
        # 按优先级排序
        results.sort(key=lambda x: -x.review_priority)
        
        return results[:limit]
    
    def get_review_summary(self, limit: int = 10) -> Dict:
        """
        获取复习摘要
        
        Args:
            limit: 返回数量限制
            
        Returns:
            dict: 复习摘要
        """
        items = self.get_memories_to_review(min_priority=10, limit=limit)
        
        # 按类型分组
        by_type = {}
        for item in items:
            if item.memory_type not in by_type:
                by_type[item.memory_type] = []
            by_type[item.memory_type].append({
                'content': item.content,
                'importance': item.importance,
                'retention': f"{item.retention_rate:.1%}",
                'days': item.days_since_access,
                'priority': f"{item.review_priority:.0f}"
            })
        
        # 按优先级分组
        high_priority = [i for i in items if i.review_priority >= 50]
        medium_priority = [i for i in items if 20 <= i.review_priority < 50]
        low_priority = [i for i in items if i.review_priority < 20]
        
        return {
            "generated_at": datetime.now().isoformat(),
            "total_to_review": len(items),
            "high_priority_count": len(high_priority),
            "medium_priority_count": len(medium_priority),
            "low_priority_count": len(low_priority),
            "by_type": by_type,
            "high_priority_items": [
                {
                    "type": i.memory_type,
                    "content": i.content,
                    "retention": f"{i.retention_rate:.1%}",
                    "days": i.days_since_access
                }
                for i in high_priority[:5]
            ]
        }
    
    def print_review_report(self, limit: int = 10):
        """打印复习报告"""
        summary = self.get_review_summary(limit)
        
        print("\n" + "=" * 60)
        print("🧠 智能复习提醒报告")
        print("=" * 60)
        
        print(f"\n📊 统计:")
        print(f"  需要复习总数: {summary['total_to_review']}")
        print(f"  🔴 高优先级: {summary['high_priority_count']}")
        print(f"  🟡 中优先级: {summary['medium_priority_count']}")
        print(f"  🟢 低优先级: {summary['low_priority_count']}")
        
        if summary['high_priority_items']:
            print(f"\n🔴 高优先级复习项:")
            for i, item in enumerate(summary['high_priority_items'], 1):
                print(f"  {i}. [{item['type']}] {item['content']}")
                print(f"     保持率: {item['retention']}, 距上次: {item['days']}天")
        
        print("\n" + "=" * 60)
    
    def get_recommended_actions(self) -> List[Dict]:
        """获取推荐的复习动作"""
        items = self.get_memories_to_review(min_priority=30, limit=10)
        
        actions = []
        for item in items:
            if item.retention_rate < 0.5:
                action = "立即复习 - 记忆即将遗忘"
            elif item.retention_rate < 0.7:
                action = "尽快复习 - 记忆正在衰减"
            else:
                action = "建议复习 - 保持记忆鲜活"
            
            actions.append({
                "memory_type": item.memory_type,
                "content": item.content,
                "action": action,
                "priority": item.review_priority
            })
        
        return actions


# ========== 主入口 ==========

if __name__ == "__main__":
    reviewer = SmartReviewer()
    
    # 生成报告
    reviewer.print_review_report()
    
    # 推荐动作
    print("\n📋 推荐动作:")
    for action in reviewer.get_recommended_actions():
        print(f"  [{action['priority']:.0f}] {action['action']}")
        print(f"     {action['content'][:60]}...")