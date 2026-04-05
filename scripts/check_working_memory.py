# -*- coding: utf-8 -*-
import sys
import io
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = sqlite3.connect(r"memory.db")
cursor = conn.cursor()

# 检查 working_memory 表结构
print("working_memory 表结构:")
cursor.execute("PRAGMA table_info(working_memory)")
for col in cursor.fetchall():
    print(f"  {col}")

print("\nmemory_strength 表结构:")
cursor.execute("PRAGMA table_info(memory_strength)")
for col in cursor.fetchall():
    print(f"  {col}")

conn.close()
