# -*- coding: utf-8 -*-
"""
记录本次会话的关键记忆
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, r'active_skills')

from memorycoreclaw import Memory

mem = Memory(db_path=r'memory.db')

# 记录 Embedding 向量索引功能
mem.remember(
    'MemoryCoreClaw 向量索引功能：使用 VectorIndexManager 自动管理。新数据入库时 remember() 和 learn() 自动生成向量（auto_index=True）。定期维护脚本：maintain_vector_index.py',
    importance=0.7,
    category='feature',
    tags=['embedding', 'vector', 'semantic-search']
)

# 记录 SivaAgent 删除
mem.remember(
    'SivaAgent 已于 2026-03-22 删除。原因：用户认为没有实际用途。移交内容：腾讯会议MCP配置经验、MCP环境变量配置经验。当前仅保留 default（老K）作为唯一 Agent',
    importance=0.6,
    category='milestone',
    tags=['agent', 'cleanup']
)

# 记录教训
mem.learn(
    action='修复 Embedding 向量索引系统',
    context='发现模型名称不匹配（bge-m3 vs bge-m3:latest）、编码冲突、索引不完整等问题',
    outcome='positive',
    insight='Ollama 模型名需要包含 tag，用 ollama list 确认。库文件不应设置编码，只在入口脚本设置。向量索引需要自动维护机制',
    importance=0.7
)

print('已记录本次会话关键记忆')
