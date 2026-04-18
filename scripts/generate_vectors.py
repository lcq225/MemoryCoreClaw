# -*- coding: utf-8 -*-
"""
为所有记忆生成向量索引（调试版）
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, r'active_skills')

print('=' * 60)
print('为记忆生成向量索引')
print('=' * 60)

import sqlite3
import pickle
from memorycoreclaw.retrieval.semantic import EmbeddingService

db_path = os.environ.get('MEMORY_DB_PATH', 'memory.db')

# 连接数据库
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 获取所有 facts
cursor.execute('SELECT id, content FROM facts')
facts = cursor.fetchall()

print('')
print('总记忆数:', len(facts))

# 创建 embedding 服务
emb = EmbeddingService(
    base_url='http://127.0.0.1:11434/v1',
    api_key='ollama',
    model_name='bge-m3:latest',
    dimensions=1024
)

# 强制检查服务
print('')
print('检查 embedding 服务...')
available = emb.is_available(force_check=True)
print('服务可用:', available)

print('')
print('逐个生成向量...')

generated = 0
failed = 0
failed_ids = []

for i, fact in enumerate(facts):
    # 检查是否已有向量
    cursor.execute('SELECT id FROM vector_index WHERE memory_type = ? AND memory_id = ?', ('fact', fact['id']))
    if cursor.fetchone():
        continue
    
    try:
        vec = emb.get_embedding(fact['content'])
        if vec:
            vec_blob = pickle.dumps(vec)
            cursor.execute('''
                INSERT OR REPLACE INTO vector_index 
                (memory_type, memory_id, content_hash, vector, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            ''', ('fact', fact['id'], str(hash(fact['content'])), vec_blob))
            conn.commit()
            generated += 1
            if generated % 10 == 0:
                print('  已生成:', generated)
        else:
            failed += 1
            failed_ids.append(fact['id'])
    except Exception as e:
        failed += 1
        failed_ids.append(fact['id'])
        print('  错误 ID', fact['id'], ':', str(e)[:50])

conn.close()

print('')
print('=' * 60)
print('生成完成')
print('  成功:', generated)
print('  失败:', failed)
print('=' * 60)
