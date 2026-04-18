# -*- coding: utf-8 -*-
"""
主动协作增强器 - 主动汇报、确认执行、智能提醒
提升与用户协作的效率和体验
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass

# 配置
MEMORY_DB = r"memory.db"
WORKSPACE = r"."


class CollaborationMode(Enum):
    """协作模式"""
    AUTO = "auto"           # 自动执行
    CONFIRM = "confirm"    # 确认后执行
    ASK = "ask"            # 询问后执行


@dataclass
class UserProfile:
    """用户画像"""
    user_id: str
    name: str
    communication_style: str  # 沟通风格
    preferences: Dict
    last_active: str


class CollaborationEnhancer:
    """
    协作增强器
    
    功能：
    - 用户画像管理
    - 智能提醒
    - 进度汇报
    - 意图预判
    """
    
    def __init__(self):
        self.user_profile = self._load_user_profile()
        self.pending_confirmations = []
        
    def _load_user_profile(self) -> UserProfile:
        """加载用户画像"""
        # 从记忆系统加载User A的信息
        try:
            conn = sqlite3.connect(MEMORY_DB)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 查找User A相关信息
            cursor.execute('''
                SELECT content, category FROM facts 
                WHERE content LIKE '%User A%' OR content LIKE '%User%'
                ORDER BY importance DESC LIMIT 20
            ''')
            
            profile = UserProfile(
                user_id="HI2044",
                name="User A",
                communication_style="BLUF",
                preferences={},
                last_active=datetime.now().isoformat()
            )
            
            # 解析偏好
            for row in cursor.fetchall():
                content = row['content']
                if "偏好" in content or "喜欢" in content:
                    # 提取偏好信息
                    if "BLUF" in content:
                        profile.communication_style = "BLUF"
                    if "简洁" in content:
                        profile.preferences["brief"] = True
                    if "详细" in content:
                        profile.preferences["detailed"] = True
            
            conn.close()
            return profile
            
        except Exception as e:
            return UserProfile(
                user_id="HI2044",
                name="User A",
                communication_style="BLUF",
                preferences={},
                last_active=datetime.now().isoformat()
            )
    
    def format_bluf(self, conclusion: str, details: str = "", 
                   suggestion: str = "", background: str = "") -> str:
        """
        格式化 BLUD 消息（结论先行）
        
        User A 偏好：BLUF 沟通风格
        """
        parts = []
        
        # 结论（必须有）
        parts.append(f"📌 {conclusion}")
        
        # 背景（可选）
        if background:
            parts.append(f"\n📋 背景: {background}")
        
        # 详情（可选）
        if details:
            parts.append(f"\n📝 详情:")
            for line in details.split('\n'):
                parts.append(f"   {line}")
        
        # 建议（可选）
        if suggestion:
            parts.append(f"\n💡 建议: {suggestion}")
        
        return '\n'.join(parts)
    
    def should_confirm(self, action_type: str) -> bool:
        """判断是否需要确认"""
        # 高危操作需要确认
        dangerous_actions = [
            "delete", "remove", "drop",   # 删除
            "deploy", "publish", "push",  # 发布
            "execute", "run", "sudo",      # 执行命令
            "config", "settings",          # 配置修改
        ]
        
        action_lower = action_type.lower()
        for dangerous in dangerous_actions:
            if dangerous in action_lower:
                return True
        
        return False
    
    def get_execution_advice(self, task_type: str) -> str:
        """获取执行建议"""
        advice = {
            "code_change": "先备份，再修改，最后验证",
            "file_delete": "先放回收站，确认后再清空",
            "config_change": "先备份原配置，标记修改点",
            "api_call": "先测试环境，再生产环境",
            "data_query": "注意数据隐私，脱敏处理",
            "report": "先确认格式，再生成内容",
        }
        
        return advice.get(task_type, "小心执行，注意验证")
    
    def log_interaction(self, user_id: str, action: str, result: str):
        """记录交互"""
        try:
            conn = sqlite3.connect(MEMORY_DB)
            cursor = conn.cursor()
            
            content = f"[交互] {action}: {result[:100]}"
            
            cursor.execute('''
                INSERT INTO facts (content, category, importance, created_at)
                VALUES (?, ?, ?, datetime('now'))
            ''', (content, "interaction", 0.6))
            
            conn.commit()
            conn.close()
        except:
            pass
    
    def suggest_next_actions(self, context: str) -> List[str]:
        """建议下一步操作"""
        suggestions = []
        
        # 根据上下文建议
        if "开发" in context or "code" in context.lower():
            suggestions.extend([
                "运行测试验证",
                "检查代码格式",
                "提交代码"
            ])
        
        if "文件" in context or "file" in context.lower():
            suggestions.extend([
                "确认文件路径",
                "备份原文件",
                "验证结果"
            ])
        
        if "报告" in context or "report" in context.lower():
            suggestions.extend([
                "确认报告格式",
                "检查数据准确性",
                "导出为PDF"
            ])
        
        return suggestions[:3]
    
    def check_incomplete_tasks(self) -> List[Dict]:
        """检查未完成的任务"""
        TASK_DB = r"tasks.db"
        
        if not os.path.exists(TASK_DB):
            return []
        
        try:
            conn = sqlite3.connect(TASK_DB)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 查找进行中的任务
            cursor.execute('''
                SELECT * FROM tasks 
                WHERE status = 'running' 
                ORDER BY updated_at DESC
            ''')
            
            tasks = []
            for row in cursor.fetchall():
                tasks.append({
                    "id": row['id'],
                    "name": row['name'],
                    "progress": row['progress'],
                    "updated": row['updated_at']
                })
            
            conn.close()
            return tasks
            
        except:
            return []


# 全局实例
collaboration = CollaborationEnhancer()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="协作增强器")
    parser.add_argument("--bluf", "-b", help="测试BLUF格式")
    parser.add_argument("--profile", "-p", action="store_true", help="显示用户画像")
    parser.add_argument("--tasks", "-t", action="store_true", help="检查未完成任务")
    parser.add_argument("--suggest", "-s", help="获取建议")
    args = parser.parse_args()
    
    collab = CollaborationEnhancer()
    
    if args.bluf:
        print("\n" + collab.format_bluf(
            conclusion=args.bluf,
            background="这是背景信息",
            details="这是详细说明\n包含多个要点",
            suggestion="建议执行下一步"
        ))
    
    elif args.profile:
        print("\n👤 用户画像")
        print("=" * 40)
        print(f"  名字: {collab.user_profile.name}")
        print(f"  ID: {collab.user_profile.user_id}")
        print(f"  沟通风格: {collab.user_profile.communication_style}")
        print(f"  偏好: {collab.user_profile.preferences}")
    
    elif args.tasks:
        tasks = collab.check_incomplete_tasks()
        print("\n🔄 进行中的任务")
        print("=" * 40)
        if tasks:
            for t in tasks:
                print(f"  • {t['name']} ({t['progress']}%)")
        else:
            print("  无进行中的任务")
    
    elif args.suggest:
        suggestions = collab.suggest_next_actions(args.suggest)
        print("\n💡 建议操作")
        print("=" * 40)
        for s in suggestions:
            print(f"  • {s}")
    
    else:
        print("用法:")
        print("  python collab_enhancer.py --bluf '结论'        # 测试BLUF格式")
        print("  python collab_enhancer.py --profile            # 显示用户画像")
        print("  python collab_enhancer.py --tasks               # 检查未完成任务")
        print("  python collab_enhancer.py -s '开发'             # 获取建议")
