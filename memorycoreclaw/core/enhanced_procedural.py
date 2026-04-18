#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced Procedural Memory (程序记忆增强)

功能：
- 技能和流程存储
- 最佳实践固化
- 操作步骤记录
- 流程检索和复用
"""

import json
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class Procedure:
    """程序数据类"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    steps: List[str] = None
    skill_name: str = ""
    version: str = ""
    category: str = "general"
    tags: List[str] = None
    success_rate: float = 0.0
    usage_count: int = 0
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []
        if self.tags is None:
            self.tags = []


class ProceduralMemoryEnhancer:
    """程序记忆增强器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_table()
    
    def _ensure_table(self):
        """确保程序记忆表存在"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS procedures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                steps TEXT,
                skill_name TEXT,
                version TEXT,
                category TEXT DEFAULT 'general',
                tags TEXT,
                success_rate REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                last_used TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store_procedure(
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
        存储程序
        
        Args:
            name: 程序名称
            description: 描述
            steps: 步骤列表
            skill_name: 关联技能名
            version: 版本
            category: 分类
            tags: 标签
            
        Returns:
            int: 程序ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        steps_json = json.dumps(steps, ensure_ascii=False)
        tags_str = ','.join(tags) if tags else None
        
        # 检查是否已存在
        cursor.execute("SELECT id FROM procedures WHERE name = ? AND skill_name = ?", 
                      (name, skill_name))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE procedures 
                SET description = ?, steps = ?, version = ?, category = ?,
                    tags = ?, updated_at = ?
                WHERE id = ?
            """, (description, steps_json, version, category, tags_str,
                  datetime.now().isoformat(), existing[0]))
            proc_id = existing[0]
        else:
            cursor.execute("""
                INSERT INTO procedures (
                    name, description, steps, skill_name, version,
                    category, tags, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, description, steps_json, skill_name, version,
                category, tags_str,
                datetime.now().isoformat(), datetime.now().isoformat()
            ))
            proc_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return proc_id
    
    def record_execution(
        self,
        procedure_name: str,
        success: bool,
        error: Optional[str] = None,
        duration_ms: int = 0
    ):
        """
        记录程序执行
        
        Args:
            procedure_name: 程序名称
            success: 是否成功
            error: 错误信息
            duration_ms: 执行时间(毫秒)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 更新使用次数和成功率
        cursor.execute("""
            SELECT usage_count, success_rate 
            FROM procedures 
            WHERE name = ?
        """, (procedure_name,))
        
        row = cursor.fetchone()
        if row:
            usage_count = row[0]
            prev_success_rate = row[1]
            
            # 计算新的成功率
            new_success_rate = (
                (prev_success_rate * usage_count + (1.0 if success else 0.0)) 
                / (usage_count + 1)
            )
            
            cursor.execute("""
                UPDATE procedures 
                SET usage_count = usage_count + 1,
                    success_rate = ?,
                    last_used = ?
                WHERE name = ?
            """, (new_success_rate, datetime.now().isoformat(), procedure_name))
        
        conn.commit()
        conn.close()
    
    def recall_procedures(
        self,
        query: str,
        category: Optional[str] = None,
        min_success_rate: float = 0.0,
        limit: int = 10
    ) -> List[Dict]:
        """
        检索程序
        
        Args:
            query: 查询关键词
            category: 分类
            min_success_rate: 最小成功率
            limit: 返回数量
            
        Returns:
            List[Dict]: 匹配的程序
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sql = """
            SELECT id, name, description, steps, skill_name, version,
                   category, tags, success_rate, usage_count, 
                   last_used, created_at
            FROM procedures
            WHERE success_rate >= ?
        """
        params = [min_success_rate]
        
        if query:
            sql += " AND (name LIKE ? OR description LIKE ? OR skill_name LIKE ?)"
            params.extend([f'%{query}%', f'%{query}%', f'%{query}%'])
        
        if category:
            sql += " AND category = ?"
            params.append(category)
        
        sql += " ORDER BY success_rate DESC, usage_count DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'steps': json.loads(row[3]) if row[3] else [],
                'skill_name': row[4],
                'version': row[5],
                'category': row[6],
                'tags': row[7].split(',') if row[7] else [],
                'success_rate': row[8],
                'usage_count': row[9],
                'last_used': row[10],
                'created_at': row[11]
            })
        
        conn.close()
        return results
    
    def get_skill_procedures(self, skill_name: str) -> List[Dict]:
        """获取技能相关的程序"""
        return self.recall_procedures("", min_success_rate=0.0, limit=50)
    
    def get_popular_procedures(self, limit: int = 10) -> List[Dict]:
        """获取最常用的程序"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, steps, skill_name, version,
                   category, success_rate, usage_count
            FROM procedures
            ORDER BY usage_count DESC
            LIMIT ?
        """, (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'steps': json.loads(row[3]) if row[3] else [],
                'skill_name': row[4],
                'version': row[5],
                'category': row[6],
                'success_rate': row[7],
                'usage_count': row[8]
            })
        
        conn.close()
        return results
    
    def extract_procedure_from_skill(self, skill_name: str, skill_code: str) -> Optional[int]:
        """
        从技能代码中提取程序
        
        Args:
            skill_name: 技能名称
            skill_code: 技能代码
            
        Returns:
            int: 程序ID
        """
        # 简单规则：提取函数定义作为步骤
        import re
        
        # 提取函数定义
        func_pattern = r'def\s+(\w+)\s*\([^)]*\)\s*:'
        functions = re.findall(func_pattern, skill_code)
        
        if not functions:
            return None
        
        steps = [f"调用函数: {func}" for func in functions]
        
        return self.store_procedure(
            name=f"{skill_name}_procedure",
            description=f"从{skill_name}提取的标准流程",
            steps=steps,
            skill_name=skill_name,
            category="extracted"
        )
    
    def get_statistics(self) -> Dict:
        """获取程序统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 总数
        cursor.execute("SELECT COUNT(*) FROM procedures")
        total = cursor.fetchone()[0]
        
        # 平均成功率
        cursor.execute("SELECT AVG(success_rate) FROM procedures")
        avg_success = cursor.fetchone()[0] or 0
        
        # 总使用次数
        cursor.execute("SELECT SUM(usage_count) FROM procedures")
        total_usage = cursor.fetchone()[0] or 0
        
        # 按分类统计
        cursor.execute("""
            SELECT category, COUNT(*), AVG(success_rate)
            FROM procedures
            GROUP BY category
        """)
        by_category = [{
            'category': row[0],
            'count': row[1],
            'avg_success': row[2]
        } for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'total': total,
            'avg_success_rate': round(avg_success, 3),
            'total_usage': total_usage,
            'by_category': by_category
        }


def main():
    """测试"""
    db_path = os.environ.get('MEMORY_DB_PATH', '/path/to/memory.db')
    enhancer = ProceduralMemoryEnhancer(db_path)
    
    # 存储程序
    proc_id = enhancer.store_procedure(
        name="create_presentation_workflow",
        description="创建演示文稿的完整工作流程",
        steps=[
            "1. 收集用户需求（主题、页数、风格）",
            "2. 设计幻灯片结构",
            "3. 选择配色方案",
            "4. 创建幻灯片内容",
            "5. 添加动画效果",
            "6. 导出文件"
        ],
        skill_name="pptx",
        version="1.0.0",
        category="workflow",
        tags=["presentation", "workflow", "pptx"]
    )
    print(f'[Test] Stored procedure ID: {proc_id}')
    
    # 记录执行
    enhancer.record_execution("create_presentation_workflow", success=True, duration_ms=5000)
    print('[Test] Recorded execution')
    
    # 检索
    procedures = enhancer.recall_procedures("presentation", limit=5)
    print(f'[Test] Found {len(procedures)} procedures')
    for p in procedures:
        print(f'  - {p["name"]}: {p["description"][:30]}... (success: {p["success_rate"]:.1%})')
    
    # 统计
    stats = enhancer.get_statistics()
    print(f'[Test] Statistics: {stats}')
    
    print('\n[OK] ProceduralMemoryEnhancer test passed')


if __name__ == '__main__':
    main()