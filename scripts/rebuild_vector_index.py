# -*- coding: utf-8 -*-
"""
重建向量索引（直接调用 API，不依赖缓存）
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, r'D:\CoPaw\.copaw\active_skills')

print('=' * 70)
print('                    重建向量索引')
print('=' * 70)

import sqlite3
import json
import urllib.request
import struct
import time
import hashlib

db_path = r'D:\CoPaw\.copaw\.agent-memory\memory.db'

# Embedding API 配置
EMBEDDING_URL = 'http://127.0.0.1:11434/v1/embeddings'
EMBEDDING_HEADERS = {
    'Authorization': 'Bearer ollama',
    'Content-Type': 'application/json'
}
EMBEDDING_MODEL = 'bge-m3:latest'

def get_embedding(text):
    """直接调用 API 获取向量"""
    data = json.dumps({
        'model': EMBEDDING_MODEL,
        'input': text
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(EMBEDDING_URL, data=data, headers=EMBEDDING_HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result['data'][0]['embedding']
    except Exception as e:
        return None

def store_embedding(cursor, memory_type, memory_id, content, embedding):
    """存储向量到数据库"""
    # 计算内容哈希
    content_hash = hashlib.md5(content.encode()).hexdigest()
    
    # 将向量转换为字节
    embedding_bytes = struct.pack(f'{len(embedding)}f', *embedding)
    
    cursor.execute('''
        INSERT OR REPLACE INTO embedding_cache 
        (memory_type, memory_id, content_hash, embedding)
        VALUES (?, ?, ?, ?)
    ''', (memory_type, memory_id, content_hash, embedding_bytes))

# 连接数据库
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 清空现有索引
print('')
print('[1] 清空现有索引')
cursor.execute('DELETE FROM embedding_cache')
conn.commit()
print('  已清空')

# 测试 API
print('')
print('[2] 测试 Embedding API')
test_vec = get_embedding('测试')
if test_vec:
    print('  API 正常, 维度:', len(test_vec))
else:
    print('  API 失败!')
    sys.exit(1)

# 索引 facts
print('')
print('[3] 索引 facts')
cursor.execute('SELECT id, content FROM facts WHERE content IS NOT NULL AND content != ""')
facts = cursor.fetchall()
print('  总数:', len(facts))

facts_ok = 0
facts_fail = 0

for i, fact in enumerate(facts):
    if not fact['content'] or len(fact['content']) < 5:
        continue
    
    vec = get_embedding(fact['content'])
    if vec:
        store_embedding(cursor, 'fact', fact['id'], fact['content'], vec)
        facts_ok += 1
    else:
        facts_fail += 1
    
    if (i + 1) % 10 == 0:
        conn.commit()
        print('  进度:', i + 1, '/', len(facts), '- 成功:', facts_ok, '失败:', facts_fail)
    
    time.sleep(0.1)  # 稍微暂停

conn.commit()
print('  完成: 成功', facts_ok, '失败', facts_fail)

# 索引 experiences
print('')
print('[4] 索引 experiences')
cursor.execute('SELECT id, action, context, insight FROM experiences')
experiences = cursor.fetchall()
print('  总数:', len(experiences))

exp_ok = 0
exp_fail = 0

for i, exp in enumerate(experiences):
    content = f"{exp['action'] or ''} {exp['context'] or ''} {exp['insight'] or ''}".strip()
    if len(content) < 5:
        continue
    
    vec = get_embedding(content)
    if vec:
        store_embedding(cursor, 'experience', exp['id'], content, vec)
        exp_ok += 1
    else:
        exp_fail += 1
    
    if (i + 1) % 10 == 0:
        conn.commit()
        print('  进度:', i + 1, '/', len(experiences), '- 成功:', exp_ok, '失败:', exp_fail)
    
    time.sleep(0.1)

conn.commit()
print('  完成: 成功', exp_ok, '失败', exp_fail)

# 验证
print('')
print('[5] 验证索引')
cursor.execute("SELECT COUNT(*) FROM embedding_cache WHERE memory_type = 'fact'")
fact_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM embedding_cache WHERE memory_type = 'experience'")
exp_count = cursor.fetchone()[0]
print('  facts:', fact_count)
print('  experiences:', exp_count)
print('  总计:', fact_count + exp_count)

conn.close()

# 测试搜索
print('')
print('[6] 测试语义搜索')
from memorycoreclaw.retrieval.semantic import SemanticSearch, EmbeddingService

emb = EmbeddingService(
    base_url='http://127.0.0.1:11434/v1',
    api_key='ollama',
    model_name='bge-m3:latest',
    dimensions=1024
)
search = SemanticSearch(db_path, emb)

test_queries = ['Example', '进化', 'User A', '数据库']
for q in test_queries:
    results = search.search(q, limit=2)
    if results:
        r = results[0]
        print('  [' + q + '] ' + r.search_type + ' - ' + r.content[:35] + '...')

print('')
print('=' * 70)
print('                    重建完成')
print('=' * 70)