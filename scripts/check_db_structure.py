# -*- coding: utf-8 -*-
import sys
import io
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

DB_PATH = r"D:\CoPaw\.copaw\.agent-memory\memory.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 获取所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("=" * 60)
print("MemoryCoreClaw 数据库结构")
print("=" * 60)
print(f"\n表总数: {len(tables)}")

for (table_name,) in tables:
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print(f"\n表: {table_name}")
    print(f"  字段数: {len(columns)}")
    for col in columns:
        nullable = "NULL" if col[3] == 0 else "NOT NULL"
        default = f"DEFAULT {col[4]}" if col[4] else ""
        print(f"    - {col[1]}: {col[2]} {nullable} {default}")

conn.close()