"""
MemoryCoreClaw - Vector Index Manager

自动管理向量索引：
- 新数据入库时自动生成向量
- 定期检查并更新索引
- 支持删除、修改、合并操作
"""

import sqlite3
import json
import urllib.request
import struct
import hashlib
import time
from typing import Optional, List, Dict, Set
from pathlib import Path
from datetime import datetime


class VectorIndexManager:
    """
    向量索引管理器
    
    功能：
    1. 自动为新记忆生成向量
    2. 定期检查并修复缺失的向量
    3. 支持删除、更新操作
    """
    
    def __init__(self, db_path: str, embedding_config: Dict = None):
        self.db_path = db_path
        
        # Embedding 配置
        if embedding_config is None:
            embedding_config = {
                'base_url': 'http://127.0.0.1:11434/v1',
                'api_key': 'ollama',
                'model_name': 'bge-m3:latest',
                'dimensions': 1024
            }
        
        self.embedding_url = f"{embedding_config['base_url'].rstrip('/')}/embeddings"
        self.embedding_headers = {
            'Authorization': f"Bearer {embedding_config['api_key']}",
            'Content-Type': 'application/json'
        }
        self.embedding_model = embedding_config['model_name']
        self.dimensions = embedding_config['dimensions']
        
        # 缓存状态
        self._service_available = None
        self._last_check = 0
        self._check_interval = 60  # 60秒检查一次
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """获取向量"""
        data = json.dumps({
            'model': self.embedding_model,
            'input': text
        }).encode('utf-8')
        
        try:
            req = urllib.request.Request(
                self.embedding_url,
                data=data,
                headers=self.embedding_headers
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result['data'][0]['embedding']
        except Exception:
            return None
    
    def _store_embedding(self, cursor, memory_type: str, memory_id: int, 
                         content: str, embedding: List[float]) -> bool:
        """存储向量"""
        try:
            content_hash = hashlib.md5(content.encode()).hexdigest()
            embedding_bytes = struct.pack(f'{len(embedding)}f', *embedding)
            
            cursor.execute('''
                INSERT OR REPLACE INTO embedding_cache 
                (memory_type, memory_id, content_hash, embedding)
                VALUES (?, ?, ?, ?)
            ''', (memory_type, memory_id, content_hash, embedding_bytes))
            return True
        except Exception:
            return False
    
    # ==================== 自动索引接口 ====================
    
    def index_fact(self, fact_id: int, content: str) -> bool:
        """为单个 fact 生成向量索引"""
        if not content or len(content) < 5:
            return False
        
        embedding = self._get_embedding(content)
        if not embedding:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        success = self._store_embedding(cursor, 'fact', fact_id, content, embedding)
        conn.commit()
        conn.close()
        
        return success
    
    def index_experience(self, exp_id: int, action: str, context: str, insight: str) -> bool:
        """为单个 experience 生成向量索引"""
        content = f"{action or ''} {context or ''} {insight or ''}".strip()
        if len(content) < 5:
            return False
        
        embedding = self._get_embedding(content)
        if not embedding:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        success = self._store_embedding(cursor, 'experience', exp_id, content, embedding)
        conn.commit()
        conn.close()
        
        return success
    
    def delete_index(self, memory_type: str, memory_id: int) -> bool:
        """删除向量索引"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM embedding_cache 
            WHERE memory_type = ? AND memory_id = ?
        ''', (memory_type, memory_id))
        conn.commit()
        conn.close()
        return True
    
    # ==================== 批量维护接口 ====================
    
    def check_missing_indices(self) -> Dict[str, List[int]]:
        """
        检查缺失的向量索引
        
        Returns:
            {'facts': [缺失的ID列表], 'experiences': [缺失的ID列表]}
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 检查 facts
        cursor.execute('''
            SELECT f.id FROM facts f
            LEFT JOIN embedding_cache ec ON f.id = ec.memory_id AND ec.memory_type = 'fact'
            WHERE ec.id IS NULL AND f.content IS NOT NULL AND f.content != ''
        ''')
        missing_facts = [row[0] for row in cursor.fetchall()]
        
        # 检查 experiences
        cursor.execute('''
            SELECT e.id FROM experiences e
            LEFT JOIN embedding_cache ec ON e.id = ec.memory_id AND ec.memory_type = 'experience'
            WHERE ec.id IS NULL
        ''')
        missing_exps = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'facts': missing_facts,
            'experiences': missing_exps
        }
    
    def repair_missing_indices(self, batch_size: int = 10) -> Dict:
        """
        修复缺失的向量索引
        
        Returns:
            {'facts': 修复数量, 'experiences': 修复数量, 'failed': 失败数量}
        """
        missing = self.check_missing_indices()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        result = {'facts': 0, 'experiences': 0, 'failed': 0}
        
        # 修复 facts
        for fact_id in missing['facts']:
            cursor.execute('SELECT content FROM facts WHERE id = ?', (fact_id,))
            row = cursor.fetchone()
            if row and row[0]:
                embedding = self._get_embedding(row[0])
                if embedding:
                    self._store_embedding(cursor, 'fact', fact_id, row[0], embedding)
                    result['facts'] += 1
                else:
                    result['failed'] += 1
            time.sleep(0.1)
            
            if result['facts'] % batch_size == 0:
                conn.commit()
        
        # 修复 experiences
        for exp_id in missing['experiences']:
            cursor.execute('SELECT action, context, insight FROM experiences WHERE id = ?', (exp_id,))
            row = cursor.fetchone()
            if row:
                content = f"{row[0] or ''} {row[1] or ''} {row[2] or ''}".strip()
                if len(content) >= 5:
                    embedding = self._get_embedding(content)
                    if embedding:
                        self._store_embedding(cursor, 'experience', exp_id, content, embedding)
                        result['experiences'] += 1
                    else:
                        result['failed'] += 1
            time.sleep(0.1)
            
            if result['experiences'] % batch_size == 0:
                conn.commit()
        
        conn.commit()
        conn.close()
        
        return result
    
    def clean_orphan_indices(self) -> int:
        """
        清理孤立的向量索引（对应的记忆已被删除）
        
        Returns:
            清理数量
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 清理 facts 的孤立索引
        cursor.execute('''
            DELETE FROM embedding_cache
            WHERE memory_type = 'fact'
            AND memory_id NOT IN (SELECT id FROM facts)
        ''')
        facts_removed = cursor.rowcount
        
        # 清理 experiences 的孤立索引
        cursor.execute('''
            DELETE FROM embedding_cache
            WHERE memory_type = 'experience'
            AND memory_id NOT IN (SELECT id FROM experiences)
        ''')
        exps_removed = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return facts_removed + exps_removed
    
    def update_changed_content(self) -> int:
        """
        更新内容变化的向量索引
        
        通过 content_hash 检测内容变化
        
        Returns:
            更新数量
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updated = 0
        
        # 检查 facts
        cursor.execute('''
            SELECT f.id, f.content, ec.content_hash
            FROM facts f
            JOIN embedding_cache ec ON f.id = ec.memory_id AND ec.memory_type = 'fact'
        ''')
        
        for row in cursor.fetchall():
            fact_id, content, stored_hash = row
            current_hash = hashlib.md5(content.encode()).hexdigest()
            
            if current_hash != stored_hash:
                # 内容已变化，重新生成向量
                embedding = self._get_embedding(content)
                if embedding:
                    self._store_embedding(cursor, 'fact', fact_id, content, embedding)
                    updated += 1
                time.sleep(0.1)
        
        conn.commit()
        conn.close()
        
        return updated
    
    # ==================== 统计接口 ====================
    
    def get_stats(self) -> Dict:
        """获取向量索引统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 总记忆数
        cursor.execute('SELECT COUNT(*) FROM facts')
        total_facts = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM experiences')
        total_exps = cursor.fetchone()[0]
        
        # 已索引数
        cursor.execute("SELECT COUNT(*) FROM embedding_cache WHERE memory_type = 'fact'")
        indexed_facts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM embedding_cache WHERE memory_type = 'experience'")
        indexed_exps = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'facts': {
                'total': total_facts,
                'indexed': indexed_facts,
                'missing': total_facts - indexed_facts
            },
            'experiences': {
                'total': total_exps,
                'indexed': indexed_exps,
                'missing': total_exps - indexed_exps
            },
            'total_indexed': indexed_facts + indexed_exps
        }
    
    def health_check(self) -> Dict:
        """
        健康检查
        
        Returns:
            健康状态报告
        """
        stats = self.get_stats()
        missing = self.check_missing_indices()
        
        return {
            'status': 'healthy' if not missing['facts'] and not missing['experiences'] else 'needs_repair',
            'stats': stats,
            'missing': {
                'facts': len(missing['facts']),
                'experiences': len(missing['experiences'])
            },
            'embedding_service': self._get_embedding('test') is not None
        }


# 便捷函数
def get_vector_manager(db_path: str = None, embedding_config: Dict = None) -> VectorIndexManager:
    """获取向量索引管理器实例"""
    if db_path is None:
        db_path = os.environ.get("MEMORY_DB_PATH", "memory.db")
    
    return VectorIndexManager(db_path, embedding_config)