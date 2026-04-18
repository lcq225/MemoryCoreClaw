#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vector Model Service
向量模型服务 - 支持云端优先，本地备用，自动切换
"""

import json
import requests
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import subprocess
import time


class VectorModelService:
    """向量模型服务 - 云端优先，本地备用"""
    
    def __init__(self, config_path: str = None):
        """初始化"""
        # 加载配置
        self.secret_dir = Path(os.environ.get('SECRET_DIR', '/path/to/.secret'))
        self.config_path = config_path or os.environ.get('MEMORY_CONFIG', '/path/to/config.json')
        
        self._load_config()
        self._load_provider_config()
        
        # 当前使用的后端
        self.current_backend = None  # 'cloud' or 'local'
        self.embedding_model = None
        self.reranker_model = None
    
    def _load_config(self):
        """加载主配置"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 本地配置
        self.local_config = {
            'base_url': self.config.get('base_url', 'http://localhost:13333/'),
            'use_lmstudio': self.config.get('use_lmstudio', True),
            'fallback_enabled': self.config.get('fallback_enabled', True),
        }
    
    def _load_provider_config(self):
        """加载服务商配置"""
        # 云端配置 - GiteeAI
        giteeai_path = self.secret_dir / 'giteeai.json'
        if giteeai_path.exists():
            with open(giteeai_path, 'r', encoding='utf-8') as f:
                giteeai = json.load(f).get('giteeai', {})
                self.cloud_config = {
                    'provider': 'giteeai',
                    'api_key': giteeai.get('api_key'),
                    'base_url': giteeai.get('base_url'),
                    'embedding_model': giteeai.get('models', {}).get('embedding'),
                    'reranker_model': giteeai.get('models', {}).get('reranker'),
                    'enabled': giteeai.get('enabled', True),
                }
        else:
            self.cloud_config = None
        
        # SiliconFlow 配置（备用云端）
        sf_path = self.secret_dir / 'providers' / 'custom' / 'siliconflow.json'
        if sf_path.exists():
            with open(sf_path, 'r', encoding='utf-8') as f:
                sf = json.load(f)
                self.sf_config = {
                    'provider': 'siliconflow',
                    'api_key': sf.get('api_key'),
                    'base_url': sf.get('base_url'),
                }
        else:
            self.sf_config = None
    
    def initialize(self) -> bool:
        """初始化向量模型，优先云端，本地备用"""
        print('[VectorModel] 初始化向量模型服务...')
        
        # 1. 优先尝试云端
        if self.cloud_config and self.cloud_config.get('enabled'):
            print(f'  [1] 尝试云端: {self.cloud_config["provider"]}')
            if self._try_cloud_embedding():
                self.current_backend = 'cloud'
                self.embedding_model = self.cloud_config['embedding_model']
                self.reranker_model = self.cloud_config['reranker_model']
                print(f'  ✓ 云端 Embedding 就绪: {self.embedding_model}')
                print(f'  ✓ 云端 Reranker 就绪: {self.reranker_model}')
                return True
        
        # 2. 云端失败，尝试本地
        if self.local_config.get('fallback_enabled'):
            print('  [2] 云端失败，尝试本地模型...')
            if self._try_local_embedding():
                self.current_backend = 'local'
                # 获取本地模型列表
                local_models = self._get_local_models()
                self.embedding_model = local_models.get('embedding')
                print(f'  ✓ 本地 Embedding 就绪: {self.embedding_model}')
                return True
        
        print('  ✗ 无法初始化向量模型')
        return False
    
    def _try_cloud_embedding(self) -> bool:
        """尝试云端Embedding"""
        try:
            # 测试GiteeAI Embedding API
            url = f"{self.cloud_config['base_url']}/embeddings"
            headers = {
                'Authorization': f'Bearer {self.cloud_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            data = {
                'model': self.cloud_config.get('embedding_model', 'Qwen3-Embedding-8B'),
                'input': '测试'
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if 'data' in result:
                    print(f'    ✓ 云端Embedding测试成功')
                    return True
            
            print(f'    ✗ 云端Embedding测试失败: {response.status_code}')
            return False
            
        except Exception as e:
            print(f'    ✗ 云端连接失败: {e}')
            return False
    
    def _try_local_embedding(self) -> bool:
        """尝试本地Embedding（LM Studio）"""
        try:
            # 1. 检查LM Studio是否运行
            url = f"{self.local_config['base_url']}v1/models"
            response = requests.get(url, timeout=5)
            
            if response.status_code != 200:
                # 尝试启动LM Studio
                print('    - 尝试启动LM Studio...')
                self._start_lmstudio()
                time.sleep(5)
                response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                models = response.json().get('data', [])
                # 查找embedding模型
                for m in models:
                    model_id = m.get('id', '').lower()
                    if 'embedding' in model_id or 'bge' in model_id or 'e5' in model_id:
                        self.embedding_model = m.get('id')
                        return True
                
                # 如果没有专门的embedding模型，返回第一个
                if models:
                    self.embedding_model = models[0].get('id')
                    return True
            
            return False
            
        except Exception as e:
            print(f'    ✗ 本地连接失败: {e}')
            return False
    
    def _start_lmstudio(self) -> bool:
        """启动LM Studio"""
        try:
            # 尝试启动LM Studio（需要用户手动启动或配置自启动）
            # 这里只是尝试，实际应该由用户或系统启动
            print('    ! 请手动启动LM Studio或配置开机自启动')
            return False
        except Exception as e:
            return False
    
    def _get_local_models(self) -> Dict:
        """获取本地模型列表"""
        models = {'embedding': None, 'chat': None}
        
        try:
            url = f"{self.local_config['base_url']}v1/models"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json().get('data', [])
                for m in data:
                    model_id = m.get('id', '').lower()
                    if 'embedding' in model_id or 'bge' in model_id:
                        models['embedding'] = m.get('id')
                    elif 'embedding' not in model_id:
                        models['chat'] = m.get('id')
                        
        except:
            pass
        
        return models
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """获取文本向量"""
        if self.current_backend == 'cloud':
            return self._get_cloud_embedding(text)
        elif self.current_backend == 'local':
            return self._get_local_embedding(text)
        else:
            # 回退到简单hash
            return self._get_fallback_embedding(text)
    
    def _get_cloud_embedding(self, text: str) -> Optional[List[float]]:
        """云端Embedding"""
        try:
            url = f"{self.cloud_config['base_url']}/embeddings"
            headers = {
                'Authorization': f'Bearer {self.cloud_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            data = {
                'model': self.cloud_config.get('embedding_model', 'Qwen3-Embedding-8B'),
                'input': text
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if 'data' in result and len(result['data']) > 0:
                    return result['data'][0].get('embedding')
            
            # 失败尝试本地
            print('    ! 云端失败，尝试本地...')
            if self._try_local_embedding():
                self.current_backend = 'local'
                return self._get_local_embedding(text)
                
        except Exception as e:
            print(f'    ✗ 云端Embedding失败: {e}')
        
        return None
    
    def _get_local_embedding(self, text: str) -> Optional[List[float]]:
        """本地Embedding (LM Studio)"""
        try:
            # 使用Ollama格式或LM Studio格式
            url = f"{self.local_config['base_url']}v1/embeddings"
            headers = {'Content-Type': 'application/json'}
            
            # 尝试常见的本地embedding端点
            model = self.embedding_model or 'mxbai-embed-large'
            data = {'model': model, 'prompt': text}
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'embedding' in result:
                    return result.get('embedding')
                elif 'data' in result and len(result['data']) > 0:
                    return result['data'][0].get('embedding')
            
        except Exception as e:
            print(f'    ✗ 本地Embedding失败: {e}')
        
        return None
    
    def _get_fallback_embedding(self, text: str) -> List[float]:
        """回退到简单的hash向量"""
        # 简单的回退方案：将文本转为固定长度向量
        import hashlib
        vector = []
        for i in range(384):  # 标准维度
            hash_val = hashlib.md5(f"{text}_{i}".encode()).hexdigest()
            vector.append(float(int(hash_val[:8], 16) % 1000) / 1000.0)
        return vector
    
    def rerank(self, query: str, documents: List[str], top_k: int = 3) -> List[Tuple[int, float]]:
        """Rerank文档"""
        if self.current_backend == 'cloud':
            return self._cloud_rerank(query, documents, top_k)
        else:
            # 本地没有reranker，返回相似度排序
            return self._simple_rerank(query, documents, top_k)
    
    def _cloud_rerank(self, query: str, documents: List[str], top_k: int) -> List[Tuple[int, float]]:
        """云端Rerank"""
        try:
            # GiteeAI Reranker API
            url = f"{self.cloud_config['base_url']}/rerank"
            headers = {
                'Authorization': f'Bearer {self.cloud_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            data = {
                'model': self.cloud_config.get('reranker_model', 'Qwen3-Reranker-8B'),
                'query': query,
                'documents': documents
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if 'results' in result:
                    return [(r['index'], r['relevance_score']) for r in result['results'][:top_k]]
                    
        except Exception as e:
            print(f'    ✗ 云端Rerank失败: {e}')
        
        # 失败使用简单排序
        return self._simple_rerank(query, documents, top_k)
    
    def _simple_rerank(self, query: str, documents: List[str], top_k: int) -> List[Tuple[int, float]]:
        """简单的相似度计算"""
        query_vec = self.get_embedding(query)
        if not query_vec:
            return [(i, 0.0) for i in range(min(top_k, len(documents)))]
        
        results = []
        for i, doc in enumerate(documents):
            doc_vec = self.get_embedding(doc)
            if doc_vec:
                # 余弦相似度
                sim = sum(a * b for a, b in zip(query_vec, doc_vec)) / (
                    (sum(a * a for a in query_vec) ** 0.5) * (sum(b * b for b in doc_vec) ** 0.5)
                )
                results.append((i, sim))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'backend': self.current_backend,
            'embedding_model': self.embedding_model,
            'reranker_model': self.reranker_model,
            'cloud_enabled': self.cloud_config is not None,
            'local_enabled': self.local_config.get('fallback_enabled', True),
        }


# 全局实例
_vector_service: Optional[VectorModelService] = None


def get_vector_service() -> VectorModelService:
    """获取向量服务实例"""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorModelService()
        _vector_service.initialize()
    return _vector_service


if __name__ == '__main__':
    # 测试
    service = VectorModelService()
    if service.initialize():
        print('\n状态:', service.get_status())
        
        # 测试embedding
        print('\n测试Embedding:')
        vec = service.get_embedding('你好世界')
        if vec:
            print(f'  ✓ 向量维度: {len(vec)}')
        else:
            print('  ✗ Embedding失败')
        
        # 测试rerank
        print('\n测试Rerank:')
        docs = ['这是一个关于Python的教程', '今天天气很好', 'Python编程入门指南']
        results = service.rerank('Python学习', docs, top_k=2)
        print(f'  结果: {results}')
    else:
        print('初始化失败')