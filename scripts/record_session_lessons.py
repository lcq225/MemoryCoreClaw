"""
记录会话中的经验教训

使用方法：
    python scripts/record_session_lessons.py

环境变量：
    MEMORY_DB_PATH - 数据库路径
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from memorycoreclaw import Memory

DB_PATH = os.environ.get('MEMORY_DB_PATH', 'memory.db')


def record_lesson(action: str, context: str, outcome: str, insight: str, importance: float = 0.8):
    """记录一条教训"""
    
    mem = Memory(db_path=DB_PATH)
    
    mem.learn(
        action=action,
        context=context,
        outcome=outcome,  # positive / negative / neutral
        insight=insight,
        importance=importance
    )
    
    print(f"✅ 已记录教训: {action[:50]}...")


def interactive_record():
    """交互式记录"""
    
    print("=" * 60)
    print("📝 记录会话教训")
    print("=" * 60)
    
    print("\n请输入教训信息（直接回车跳过）：\n")
    
    action = input("操作描述: ").strip()
    if not action:
        print("已取消")
        return
    
    context = input("发生情境: ").strip()
    outcome = input("结果 (positive/negative/neutral): ").strip() or "neutral"
    insight = input("学到的教训: ").strip()
    importance = float(input("重要性 (0-1, 默认0.8): ").strip() or "0.8")
    
    record_lesson(action, context, outcome, insight, importance)
    
    print("=" * 60)


if __name__ == "__main__":
    interactive_record()
