"""
从 MEMORY.md 更新记忆数据库

使用方法：
    python scripts/update_memory.py

环境变量：
    MEMORY_DB_PATH - 数据库路径
    MEMORY_MD_PATH - MEMORY.md 路径
"""
import os
import re
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = os.environ.get('MEMORY_DB_PATH', 'memory.db')
MD_PATH = os.environ.get('MEMORY_MD_PATH', 'MEMORY.md')


def update_from_md():
    """从 MEMORY.md 更新数据库"""
    
    print("=" * 60)
    print("📥 从 MEMORY.md 更新数据库")
    print("=" * 60)
    print(f"\nMarkdown 路径: {MD_PATH}")
    print(f"数据库路径: {DB_PATH}\n")
    
    if not Path(MD_PATH).exists():
        print("❌ MEMORY.md 文件不存在")
        return
    
    # 读取 MEMORY.md
    content = Path(MD_PATH).read_text(encoding='utf-8')
    
    # 解析事实记忆
    facts = []
    fact_pattern = r'\|\s*(\d+)\s*\|\s*([^\|]+)\s*\|\s*([^\|]+)\s*\|\s*([\d.]+)\s*\|'
    
    in_facts_section = False
    for line in content.split('\n'):
        if '## 📝 事实记忆' in line:
            in_facts_section = True
            continue
        if in_facts_section and line.startswith('## '):
            in_facts_section = False
        
        if in_facts_section:
            match = re.match(fact_pattern, line)
            if match:
                _, category, content_text, importance = match.groups()
                facts.append({
                    'content': content_text.strip(),
                    'category': category.strip(),
                    'importance': float(importance)
                })
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 插入事实
    added = 0
    for fact in facts:
        try:
            cursor.execute("""
                INSERT INTO facts (content, importance, category, created_at)
                VALUES (?, ?, ?, ?)
            """, (fact['content'], fact['importance'], fact['category'], datetime.now()))
            added += 1
        except sqlite3.IntegrityError:
            pass  # 已存在
    
    conn.commit()
    conn.close()
    
    print(f"✅ 导入了 {added} 条新记忆")
    print("=" * 60)


if __name__ == "__main__":
    update_from_md()
