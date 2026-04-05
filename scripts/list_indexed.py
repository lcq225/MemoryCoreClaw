# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import sqlite3
conn = sqlite3.connect(r'D:\CoPaw\.copaw\.agent-memory\memory.db')
cursor = conn.cursor()
cursor.execute('''
    SELECT f.id, f.content 
    FROM embedding_cache ec
    JOIN facts f ON ec.memory_id = f.id
    WHERE ec.memory_type = 'fact'
''')
rows = cursor.fetchall()
print('有向量的记忆:')
for row in rows:
    print('ID:', row[0], '-', row[1][:40] + '...')
conn.close()