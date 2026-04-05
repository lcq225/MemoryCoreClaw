# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import sqlite3
conn = sqlite3.connect(r'D:\CoPaw\.copaw\.agent-memory\memory.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM embedding_cache')
total = cursor.fetchone()[0]
print('embedding_cache total:', total)

cursor.execute('SELECT COUNT(*) FROM embedding_cache WHERE embedding IS NOT NULL')
with_vec = cursor.fetchone()[0]
print('with embedding:', with_vec)

cursor.execute('SELECT memory_id FROM embedding_cache LIMIT 5')
ids = cursor.fetchall()
print('memory_ids:', [i[0] for i in ids])

conn.close()