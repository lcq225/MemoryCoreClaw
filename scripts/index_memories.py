# -*- coding: utf-8 -*-
"""
使用 SemanticSearch.index() 方法生成向量
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, r'D:\CoPaw\.copaw\active_skills')

print('=' * 60)
print('为记忆生成向量索引（正确方法）')
print('=' * 60)

import sqlite3
from memorycoreclaw.retrieval.semantic import SemanticSearch, EmbeddingService

db_path = r'D:\CoPaw\.copaw\.agent-memory\memory.db'

# 创建 embedding 服务
emb = EmbeddingService(
    base_url='http://127.0.0.1:11434/v1',
    api_key='ollama',
    model_name='bge-m3:latest',
    dimensions=1024
)

# 创建语义搜索引擎
search = SemanticSearch(db_path, emb)

print('')
print('检查服务状态...')
status = search.get_status()
print('  embedding_available:', status['embedding_available'])
print('  model:', status['model'])

# 获取所有 facts
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute('SELECT id, content FROM facts')
facts = cursor.fetchall()
conn.close()

print('')
print('总记忆数:', len(facts))

# 索引所有记忆
print('')
print('开始索引...')
indexed = 0
failed = 0

for i, fact in enumerate(facts):
    success = search.index('fact', fact['id'], fact['content'])
    if success:
        indexed += 1
    else:
        failed += 1
    
    if (i + 1) % 20 == 0:
        print('  已处理:', i + 1, '成功:', indexed, '失败:', failed)

print('')
print('=' * 60)
print('索引完成')
print('  成功:', indexed)
print('  失败:', failed)
print('=' * 60)

# 测试语义搜索
print('')
print('测试语义搜索:')
results = search.search('海科化工', limit=3)
for r in results:
    print('  [' + r.search_type + '] ' + r.content[:40] + '...')