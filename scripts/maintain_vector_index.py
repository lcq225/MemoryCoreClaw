# -*- coding: utf-8 -*-
"""
向量索引维护脚本

功能：
1. 检查缺失的向量索引
2. 修复缺失的索引
3. 清理孤立索引
4. 更新变化的索引
5. 生成健康报告

建议：集成到 Heartbeat 每日执行一次
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, r'D:\CoPaw\.copaw\active_skills')

print('=' * 70)
print('                    向量索引维护')
print('=' * 70)

from memorycoreclaw.core.vector_index_manager import VectorIndexManager

db_path = '/path/to\CoPaw\.copaw\.agent-memory\memory.db'
manager = VectorIndexManager(db_path)

# 1. 健康检查
print('')
print('[1] 健康检查')
health = manager.health_check()
print('  状态:', health['status'])
print('  Embedding 服务:', '正常' if health['embedding_service'] else '异常')

stats = health['stats']
print('  Facts:', stats['facts']['indexed'], '/', stats['facts']['total'])
print('  Experiences:', stats['experiences']['indexed'], '/', stats['experiences']['total'])
print('  缺失 - Facts:', health['missing']['facts'], 'Experiences:', health['missing']['experiences'])

# 2. 修复缺失索引
if health['missing']['facts'] > 0 or health['missing']['experiences'] > 0:
    print('')
    print('[2] 修复缺失索引')
    repair = manager.repair_missing_indices()
    print('  修复 Facts:', repair['facts'])
    print('  修复 Experiences:', repair['experiences'])
    print('  失败:', repair['failed'])
else:
    print('')
    print('[2] 无需修复缺失索引')

# 3. 清理孤立索引
print('')
print('[3] 清理孤立索引')
removed = manager.clean_orphan_indices()
print('  清理数量:', removed)

# 4. 更新变化的索引
print('')
print('[4] 更新变化的索引')
updated = manager.update_changed_content()
print('  更新数量:', updated)

# 5. 最终统计
print('')
print('[5] 最终统计')
final_stats = manager.get_stats()
print('  Facts:', final_stats['facts']['indexed'], '/', final_stats['facts']['total'])
print('  Experiences:', final_stats['experiences']['indexed'], '/', final_stats['experiences']['total'])
print('  总计:', final_stats['total_indexed'])

print('')
print('=' * 70)
print('                    维护完成')
print('=' * 70)