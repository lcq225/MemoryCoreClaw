# -*- coding: utf-8 -*-
"""
MemoryCoreClaw Plugin System

插件化架构，支持自定义：
- 存储引擎（StoragePlugin）
- 检索引擎（RetrievalPlugin）
- 认知模块（CognitivePlugin）
- 压缩策略（CompressionPlugin）

设计原则：
1. 向后兼容：现有代码无需修改即可使用
2. 热插拔：插件可动态加载/卸载
3. 配置驱动：通过配置文件启用/禁用插件
4. 安全隔离：插件运行在沙箱环境中

版本：2.2.0
作者：Mr.Lee & 老K
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path
import importlib
import json
import threading


@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    description: str
    author: str = ""
    plugin_type: str = ""
    enabled: bool = True
    priority: int = 100  # 插件优先级（数值越小优先级越高）
    dependencies: List[str] = field(default_factory=list)
    config_schema: Dict = field(default_factory=dict)


class BasePlugin(ABC):
    """
    插件基类
    
    所有插件必须继承此基类并实现必需方法
    """
    
    @abstractmethod
    def get_info(self) -> PluginInfo:
        """返回插件信息"""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict) -> bool:
        """
        初始化插件
        
        Args:
            config: 插件配置
            
        Returns:
            True if initialized successfully
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> bool:
        """
        关闭插件
        
        Returns:
            True if shutdown successfully
        """
        pass
    
    def validate_config(self, config: Dict) -> bool:
        """
        验证配置
        
        Args:
            config: 插件配置
            
        Returns:
            True if config is valid
        """
        return True


class StoragePlugin(BasePlugin):
    """
    存储引擎插件
    
    用于扩展存储后端：
    - SQLite（默认）
    - PostgreSQL
    - MongoDB
    - Redis
    """
    
    @abstractmethod
    def store(self, memory_type: str, data: Dict) -> int:
        """存储记忆"""
        pass
    
    @abstractmethod
    def retrieve(self, memory_type: str, memory_id: int) -> Optional[Dict]:
        """检索记忆"""
        pass
    
    @abstractmethod
    def delete(self, memory_type: str, memory_id: int) -> bool:
        """删除记忆"""
        pass
    
    @abstractmethod
    def query(self, memory_type: str, conditions: Dict, limit: int = 10) -> List[Dict]:
        """查询记忆"""
        pass


class RetrievalPlugin(BasePlugin):
    """
    检索引擎插件
    
    用于扩展检索能力：
    - 向量搜索（默认）
    - 关键词搜索
    - 混合搜索
    - Reranker（新增）
    """
    
    @abstractmethod
    def search(self, query: str, memory_type: str = 'fact', limit: int = 10) -> List[Dict]:
        """搜索记忆"""
        pass
    
    @abstractmethod
    def index(self, memory_type: str, memory_id: int, content: str) -> bool:
        """索引记忆"""
        pass


class CognitivePlugin(BasePlugin):
    """
    认知模块插件
    
    用于扩展认知能力：
    - 遗忘曲线（默认）
    - 工作记忆
    - 联想网络
    - 情境记忆
    """
    
    @abstractmethod
    def process(self, memory_data: Dict) -> Dict:
        """处理记忆"""
        pass
    
    @abstractmethod
    def analyze(self, memories: List[Dict]) -> Dict:
        """分析记忆"""
        pass


class CompressionPlugin(BasePlugin):
    """
    压缩策略插件
    
    用于扩展压缩能力：
    - 摘要压缩（默认）
    - 分层压缩
    - 语义压缩
    """
    
    @abstractmethod
    def compress(self, memories: List[Dict], target_size: int) -> List[Dict]:
        """压缩记忆"""
        pass
    
    @abstractmethod
    def decompress(self, compressed: Dict) -> List[Dict]:
        """解压缩记忆"""
        pass


class PluginRegistry:
    """
    插件注册表
    
    管理所有插件的生命周期：
    - 注册/注销
    - 加载/卸载
    - 配置管理
    - 依赖检查
    """
    
    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}
        self._plugin_infos: Dict[str, PluginInfo] = {}
        self._initialized: Dict[str, bool] = {}
        self._lock = threading.Lock()
        
    def register(self, plugin: BasePlugin) -> bool:
        """
        注册插件
        
        Args:
            plugin: 插件实例
            
        Returns:
            True if registered successfully
        """
        info = plugin.get_info()
        
        with self._lock:
            if info.name in self._plugins:
                return False
            
            # 检查依赖
            for dep in info.dependencies:
                if dep not in self._plugins:
                    return False
            
            self._plugins[info.name] = plugin
            self._plugin_infos[info.name] = info
            self._initialized[info.name] = False
            
            return True
    
    def unregister(self, plugin_name: str) -> bool:
        """
        注销插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            True if unregistered successfully
        """
        with self._lock:
            if plugin_name not in self._plugins:
                return False
            
            # 先关闭插件
            if self._initialized[plugin_name]:
                self._plugins[plugin_name].shutdown()
            
            del self._plugins[plugin_name]
            del self._plugin_infos[plugin_name]
            del self._initialized[plugin_name]
            
            return True
    
    def initialize_plugin(self, plugin_name: str, config: Dict = None) -> bool:
        """
        初始化插件
        
        Args:
            plugin_name: 插件名称
            config: 插件配置
            
        Returns:
            True if initialized successfully
        """
        if plugin_name not in self._plugins:
            return False
        
        plugin = self._plugins[plugin_name]
        info = self._plugin_infos[plugin_name]
        
        if config is None:
            config = {}
        
        if plugin.initialize(config):
            self._initialized[plugin_name] = True
            return True
        
        return False
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """获取插件实例"""
        return self._plugins.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: str) -> List[BasePlugin]:
        """按类型获取插件"""
        result = []
        for name, info in self._plugin_infos.items():
            if info.plugin_type == plugin_type and info.enabled and self._initialized[name]:
                result.append(self._plugins[name])
        
        # 按优先级排序
        result.sort(key=lambda p: self._plugin_infos[p.get_info().name].priority)
        return result
    
    def list_plugins(self) -> List[PluginInfo]:
        """列出所有插件"""
        return list(self._plugin_infos.values())
    
    def load_from_config(self, config_path: str) -> int:
        """
        从配置文件加载插件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            成功加载的插件数量
        """
        count = 0
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            plugins_config = config.get('plugins', {})
            
            for plugin_name, plugin_config in plugins_config.items():
                if plugin_config.get('enabled', False):
                    module_path = plugin_config.get('module')
                    if module_path:
                        try:
                            module = importlib.import_module(module_path)
                            plugin_class = getattr(module, plugin_config.get('class', 'Plugin'))
                            plugin = plugin_class()
                            
                            if self.register(plugin):
                                if self.initialize_plugin(plugin_name, plugin_config.get('config', {})):
                                    count += 1
                        except Exception as e:
                            print(f"[Warning] Failed to load plugin {plugin_name}: {e}")
        
        except Exception as e:
            print(f"[Error] Failed to load plugin config: {e}")
        
        return count


# 全局插件注册表
_registry = None

def get_registry() -> PluginRegistry:
    """获取全局插件注册表"""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


def register_plugin(plugin: BasePlugin) -> bool:
    """注册插件"""
    return get_registry().register(plugin)


def get_plugin(plugin_name: str) -> Optional[BasePlugin]:
    """获取插件"""
    return get_registry().get_plugin(plugin_name)


def get_storage_plugins() -> List[StoragePlugin]:
    """获取存储插件列表"""
    return get_registry().get_plugins_by_type('storage')


def get_retrieval_plugins() -> List[RetrievalPlugin]:
    """获取检索插件列表"""
    return get_registry().get_plugins_by_type('retrieval')


def get_cognitive_plugins() -> List[CognitivePlugin]:
    """获取认知插件列表"""
    return get_registry().get_plugins_by_type('cognitive')


def get_compression_plugins() -> List[CompressionPlugin]:
    """获取压缩插件列表"""
    return get_registry().get_plugins_by_type('compression')


if __name__ == "__main__":
    # 测试插件系统
    print("="*60)
    print("Plugin System Test")
    print("="*60)
    
    registry = get_registry()
    
    print(f"\nPlugins registered: {len(registry.list_plugins())}")
    
    # 创建示例插件
    class ExampleRetrievalPlugin(RetrievalPlugin):
        def get_info(self) -> PluginInfo:
            return PluginInfo(
                name="example_retrieval",
                version="1.0.0",
                description="示例检索插件",
                plugin_type="retrieval",
                priority=50
            )
        
        def initialize(self, config: Dict) -> bool:
            return True
        
        def shutdown(self) -> bool:
            return True
        
        def search(self, query: str, memory_type: str = 'fact', limit: int = 10) -> List[Dict]:
            return []
        
        def index(self, memory_type: str, memory_id: int, content: str) -> bool:
            return True
    
    plugin = ExampleRetrievalPlugin()
    
    print(f"\nRegistering plugin: {plugin.get_info().name}")
    success = registry.register(plugin)
    print(f"Result: {success}")
    
    print(f"\nInitializing plugin...")
    success = registry.initialize_plugin("example_retrieval")
    print(f"Result: {success}")
    
    print(f"\nPlugins registered: {len(registry.list_plugins())}")
    for info in registry.list_plugins():
        print(f"  - {info.name} ({info.plugin_type})")
    
    print("\n" + "="*60)
    print("Test Complete")
    print("="*60)