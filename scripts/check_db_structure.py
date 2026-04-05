# -*- coding: utf-8 -*-
import sys
import io
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

DB_PATH = r"memory.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 鑾峰彇鎵€鏈夎〃
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("=" * 60)
print("MemoryCoreClaw 鏁版嵁搴撶粨鏋?)
print("=" * 60)
print(f"\n琛ㄦ€绘暟: {len(tables)}")

for (table_name,) in tables:
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print(f"\n琛? {table_name}")
    print(f"  瀛楁鏁? {len(columns)}")
    for col in columns:
        nullable = "NULL" if col[3] == 0 else "NOT NULL"
        default = f"DEFAULT {col[4]}" if col[4] else ""
        print(f"    - {col[1]}: {col[2]} {nullable} {default}")

conn.close()

