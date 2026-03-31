# -*- coding: utf-8 -*-
"""
固化今日重要记忆到长期记忆数据库
"""
import sqlite3
import sys
import io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

db_path = r'D:\CoPaw\.copaw\.agent-memory\memory.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

today = datetime.now().strftime('%Y-%m-%d')

# 今日重要事实记忆
facts = [
    ('project', f'Enterprise extension module created - src/copaw/extensions/enterprise/ 目录，包含技能效用追踪钩子和记忆增强工具函数', 0.8, today),
    ('github', f'GitHub Issue #2215 提交 - Feature Request: memory_compact_skip_summary 配置选项', 0.7, today),
    ('github', f'GitHub Issue #2216 提交 - Feature Request: Skill/Tool Execution Tracking 功能', 0.7, today),
    ('decision', f'核心代码修改策略决策 - 暂时保留侵入式修改，等待官方 Issue 回复，等 v0.3.0 时再论证', 0.9, today),
    ('warning', f'安装包版本问题 - 当前安装包使用官方 v0.2.0，without enterprise custom code modifications', 0.7, today),
]

# 今日经验教训
lessons = [
    ('版本升级', '核心代码修改评估框架：官方接受度 > 升级冲突风险 > 功能必要性 > 替代方案 > 维护成本', 0.9, today),
    ('定制代码', '定制代码处理策略：先提交 Issue → 创建非侵入式替代 → 验证功能 → 观望官方回复 → 定期评估', 0.9, today),
    ('GitHub API', '使用 Python urllib.request + GitHub Token 可直接提交 Issue，无需浏览器', 0.6, today),
]

print("=== 固化今日记忆 ===")

# 插入事实
for category, content, importance, date in facts:
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO facts (category, content, importance, created_date, source)
            VALUES (?, ?, ?, ?, 'llm')
        """, (category, content, importance, date))
        print(f"[事实] {category}: {content[:50]}...")
    except Exception as e:
        print(f"[错误] {e}")

# 插入教训
for category, content, importance, date in lessons:
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO lessons_learned (category, lesson, importance, created_date, source)
            VALUES (?, ?, ?, ?, 'llm')
        """, (category, content, importance, date))
        print(f"[教训] {category}: {content[:50]}...")
    except Exception as e:
        print(f"[错误] {e}")

conn.commit()
conn.close()

print("\n✅ 今日记忆已固化到长期记忆数据库")