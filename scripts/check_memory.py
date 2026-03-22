"""
检查记忆数据库状态

使用方法：
    python scripts/check_memory.py

环境变量：
    MEMORY_DB_PATH - 数据库路径（默认：memory.db）
"""
import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# 支持环境变量配置
DB_PATH = os.environ.get('MEMORY_DB_PATH', 'memory.db')


def check_database():
    """检查数据库状态并输出统计信息"""
    
    print("=" * 60)
    print("📊 MemoryCoreClaw 数据库状态")
    print("=" * 60)
    print(f"\n数据库路径: {DB_PATH}\n")
    
    if not Path(DB_PATH).exists():
        print("❌ 数据库文件不存在，请先初始化")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取各表统计
    tables = {
        'facts': '事实记忆',
        'experiences': '经验教训',
        'relations': '实体关系',
        'entities': '实体定义',
        'working_memory': '工作记忆'
    }
    
    stats = {}
    for table, name in tables.items():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
            print(f"📝 {name}：{stats[table]} 条")
        except sqlite3.OperationalError:
            stats[table] = 0
            print(f"📝 {name}：表不存在")
    
    # 检查记忆强度
    try:
        cursor.execute("SELECT COUNT(*) FROM memory_strength")
        strength_count = cursor.fetchone()[0]
        print(f"💪 记忆强度记录：{strength_count} 条")
    except:
        pass
    
    # 检查情境绑定
    try:
        cursor.execute("SELECT COUNT(*) FROM contexts")
        context_count = cursor.fetchone()[0]
        print(f"🎯 情境记录：{context_count} 条")
    except:
        pass
    
    conn.close()
    
    print("\n" + "=" * 60)
    
    # 健康检查
    issues = []
    if stats.get('facts', 0) == 0:
        issues.append("⚠️ 没有事实记忆")
    if stats.get('experiences', 0) == 0:
        issues.append("⚠️ 没有经验教训")
    
    if issues:
        print("健康检查：")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ 数据库健康")
    
    print("=" * 60)


if __name__ == "__main__":
    check_database()