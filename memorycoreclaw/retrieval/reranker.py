# -*- coding: utf-8 -*-
"""
Reranker Service for MemoryCoreClaw
支持GiteeAI云端优先，本地备用（如果可用）
"""
import json
import urllib.request
import urllib.error
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RerankResult:
    """重排序结果"""
    index: int
    relevance_score: float
    document: str


class RerankerService:
    """
    Reranker服务
    
    支持GiteeAI云端Reranker（优先）
    """
    
    def __init__(self, 
                 base_url: str = "https://ai.gitee.com/v1",
                 api_key: str = "",
                 model_name: str = "Qwen3-Reranker-8B"):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model_name = model_name
    
    def rerank(self, query: str, documents: List[str], top_n: int = None) -> List[RerankResult]:
        """
        对文档进行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_n: 返回数量（默认返回全部）
            
        Returns:
            按相关性排序的结果列表
        """
        if not self.api_key:
            return []
        
        if top_n is None:
            top_n = len(documents)
        
        try:
            url = f"{self.base_url}/rerank"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.model_name,
                "query": query,
                "documents": documents,
                "top_n": top_n
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if 'results' in result:
                    results = []
                    for item in result['results']:
                        results.append(RerankResult(
                            index=item.get('index', 0),
                            relevance_score=item.get('relevance_score', 0),
                            document=item.get('document', {}).get('text', '')
                        ))
                    return results
                    
            return []
            
        except Exception as e:
            print(f"[Reranker] Error: {e}")
            return []
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        try:
            # 简单测试
            results = self.rerank("test", ["test document"], top_n=1)
            return len(results) > 0
        except:
            return False


def load_reranker_config() -> Dict:
    """
    加载Reranker配置
    
    Returns:
        {
            'primary': {...},
            'fallback': {...} or None,
            'has_fallback': bool
        }
    """
    import os
    
    workspace_dir = os.environ.get('WORKSPACE_DIR', '/path/to/workspace')
    secret_dir = os.environ.get('SECRET_DIR', '/path/to/secret')
    config_path = os.path.join(workspace_dir, 'config.json')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查是否有reranker配置
        reranker_config = config.get('agents', {}).get('running', {}).get('reranker_config', {})
        
        if reranker_config:
            # Primary
            primary = {
                'base_url': reranker_config.get('base_url', 'https://ai.gitee.com/v1'),
                'api_key': reranker_config.get('api_key', ''),
                'model_name': reranker_config.get('model_name', 'Qwen3-Reranker-8B'),
            }
            
            # 如果没有api_key，尝试从giteeai.json加载
            if not primary['api_key']:
                giteeai_path = os.path.join(secret_dir, 'giteeai.json')
                try:
                    with open(giteeai_path, 'r', encoding='utf-8') as f:
                        giteeai_config = json.load(f)
                        primary['api_key'] = giteeai_config.get('giteeai', {}).get('api_key', '')
                except:
                    pass
            
            # Fallback
            fallback = None
            fallback_config = reranker_config.get('fallback', {})
            if fallback_config.get('enabled', False):
                fallback = {
                    'base_url': fallback_config.get('base_url', ''),
                    'api_key': fallback_config.get('api_key', ''),
                    'model_name': fallback_config.get('model_name', ''),
                }
            
            return {
                'primary': primary,
                'fallback': fallback,
                'has_fallback': fallback is not None
            }
        
    except Exception as e:
        print(f"[Warning] Failed to load reranker config: {e}")
    
    # 默认配置：使用GiteeAI
    giteeai_key = ''
    giteeai_path = os.path.join(secret_dir, 'giteeai.json')
    try:
        with open(giteeai_path, 'r', encoding='utf-8') as f:
            giteeai_config = json.load(f)
            giteeai_key = giteeai_config.get('giteeai', {}).get('api_key', '')
    except:
        pass
    
    return {
        'primary': {
            'base_url': 'https://ai.gitee.com/v1',
            'api_key': giteeai_key,
            'model_name': 'Qwen3-Reranker-8B',
        },
        'fallback': None,
        'has_fallback': False
    }


def create_reranker_service() -> RerankerService:
    """创建Reranker服务实例"""
    config = load_reranker_config()
    primary = config.get('primary', {})
    
    return RerankerService(
        base_url=primary.get('base_url', 'https://ai.gitee.com/v1'),
        api_key=primary.get('api_key', ''),
        model_name=primary.get('model_name', 'Qwen3-Reranker-8B')
    )


if __name__ == "__main__":
    # 测试
    print("=" * 60)
    print("Reranker Service Test")
    print("=" * 60)
    
    reranker = create_reranker_service()
    
    print(f"\nBase URL: {reranker.base_url}")
    print(f"Model: {reranker.model_name}")
    print(f"Available: {reranker.is_available()}")
    
    # 测试重排序
    query = "机器学习"
    documents = [
        "机器学习是人工智能的一个分支",
        "今天天气很好",
        "深度学习使用神经网络"
    ]
    
    print(f"\nQuery: {query}")
    print(f"Documents: {len(documents)}")
    
    results = reranker.rerank(query, documents)
    
    print(f"\nResults ({len(results)}):")
    for r in results:
        print(f"  {r.index}. Score: {r.relevance_score:.4f} | {documents[r.index][:40]}...")