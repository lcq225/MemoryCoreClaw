# MemoryCoreClaw
# Human-brain-inspired Long-term Memory Engine for AI Agents

__version__ = "2.3.0"  # v2.2.0 - Add associative memory module
__author__ = "MemoryCoreClaw Team"

from .core.memory import Memory, get_memory
from .core.engine import MemoryEngine, MemoryLayer, Emotion, Fact, Lesson, STANDARD_RELATIONS
from .cognitive.contextual import Context
from .cognitive.associative import AssociativeMemory, ActivatedNode, ConvergenceResult

# Safety module
from .safe_memory import SafeMemory
from .storage.database import SafeDatabaseManager, MemoryHealthChecker

__all__ = [
    # Core
    'Memory',
    'MemoryEngine',
    'get_memory',
    'Context',
    'MemoryLayer',
    'Emotion',
    'Fact',
    'Lesson',
    'STANDARD_RELATIONS',
    # Associative Memory (NEW in v2.2.0)
    'AssociativeMemory',
    'ActivatedNode',
    'ConvergenceResult',
    # Safety
    'SafeMemory',
    'SafeDatabaseManager',
    'MemoryHealthChecker',
]