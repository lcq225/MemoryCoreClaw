# MemoryCoreClaw
# Human-brain-inspired Long-term Memory Engine for AI Agents

__version__ = "2.1.1"  # v2.1.1 - PyPI release with bug fixes and documentation update
__author__ = "MemoryCoreClaw Team"

from .core.memory import Memory, get_memory
from .core.engine import MemoryEngine, MemoryLayer, Emotion, Fact, Lesson, STANDARD_RELATIONS
from .cognitive.contextual import Context

# 新增安全模块
from .safe_memory import SafeMemory
from .storage.database import SafeDatabaseManager, MemoryHealthChecker

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
    # 新增安全导出
    'SafeMemory',
    'SafeDatabaseManager',
    'MemoryHealthChecker',
]