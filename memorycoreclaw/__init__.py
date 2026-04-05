# MemoryCoreClaw
# Human-brain-inspired Long-term Memory Engine for AI Agents

__version__ = "2.4.0"  # v2.4.0 - Plugin architecture + Reranker + More scripts
__author__ = "Mr.Lee & 老K"

from .core.memory import Memory, get_memory
from .core.engine import MemoryEngine, MemoryLayer, Emotion, Fact, Lesson, STANDARD_RELATIONS
from .cognitive.contextual import Context
from .cognitive.associative import AssociativeMemory, ActivatedNode, ConvergenceResult

# 安全模块
from .safe_memory import SafeMemory
from .storage.database import SafeDatabaseManager, MemoryHealthChecker

# 插件系统（v2.4.0新增）
from .core.plugin_system import (
    PluginRegistry, PluginInfo, BasePlugin,
    StoragePlugin, RetrievalPlugin, CognitivePlugin, CompressionPlugin,
    get_registry, register_plugin, get_plugin,
    get_storage_plugins, get_retrieval_plugins,
    get_cognitive_plugins, get_compression_plugins
)

# Reranker服务（v2.4.0新增）
from .retrieval.reranker import RerankerService, create_reranker_service

__all__ = [
    # 原有导出
    'Memory',
    'MemoryEngine',
    'get_memory',
    'Context',
    'MemoryLayer',
    'Emotion',
    'Fact',
    'Lesson',
    'STANDARD_RELATIONS',
    # 联想记忆（v2.2.0）
    'AssociativeMemory',
    'ActivatedNode',
    'ConvergenceResult',
    # 安全导出
    'SafeMemory',
    'SafeDatabaseManager',
    'MemoryHealthChecker',
    # 插件系统导出（v2.4.0）
    'PluginRegistry',
    'PluginInfo',
    'BasePlugin',
    'StoragePlugin',
    'RetrievalPlugin',
    'CognitivePlugin',
    'CompressionPlugin',
    'get_registry',
    'register_plugin',
    'get_plugin',
    'get_storage_plugins',
    'get_retrieval_plugins',
    'get_cognitive_plugins',
    'get_compression_plugins',
    # Reranker导出（v2.4.0）
    'RerankerService',
    'create_reranker_service',
]
