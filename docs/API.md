# MemoryCoreClaw API Reference

> **版本：v2.1.0**
> 
> 新增：SafeMemory 安全接口、来源追踪、边界检查

---

## Quick Start

```python
from memorycoreclaw import Memory

# 基础接口
mem = Memory(db_path="memory.db")

# 安全接口（推荐）
from memorycoreclaw import SafeMemory
safe_mem = SafeMemory(db_path="memory.db")
```

---

## Core Classes

### Memory (基础接口)

```python
from memorycoreclaw import Memory

mem = Memory(db_path=None, session_id=None)
```

### SafeMemory (安全接口 - v2.1.0)

```python
from memorycoreclaw import SafeMemory

mem = SafeMemory(db_path="memory.db")
```

**安全特性：**
- 连接管理（自动关闭）
- 事务保护（自动提交/回滚）
- 边界检查（自动修正无效参数）
- 核心记忆保护（防误删）
- 来源标记（追踪记忆来源）

---

## Memory Operations

### remember()

Store a fact in memory.

```python
mem.remember(
    content: str,
    importance: float = 0.5,
    category: str = None,
    emotion: str = None,
    tags: List[str] = None,
    # v2.1.0 新增
    source: str = "user",        # user/llm/document/system
    source_confidence: float = 1.0
) -> int
```

**Returns**: Fact ID

**Example**:
```python
# 基础用法
fid = mem.remember("Python 3.11 released", importance=0.7)

# v2.1.0: 带来源标记
fid = mem.remember(
    "用户偏好简洁回复",
    importance=0.85,
    category="preference",
    source="user",
    source_confidence=1.0
)
```

---

### recall()

Search and retrieve memories.

```python
mem.recall(
    query: str,
    limit: int = 10,
    min_importance: float = 0.0
) -> List[Dict]
```

**v2.1.0 边界检查：**
- `limit < 0` → 自动修正为 `10`
- `limit is None` → 自动修正为 `10`
- `query is None` → 自动修正为 `""`

**Returns**: List of matching memories

**Example**:
```python
results = mem.recall("Python", limit=5)
for r in results:
    print(r['content'], r['importance'], r.get('source'))
```

---

### learn()

Store a lesson learned.

```python
mem.learn(
    action: str,
    context: str = None,
    outcome: str = "neutral",  # positive, negative, neutral
    insight: str = None,
    importance: float = 0.7
) -> int
```

**Returns**: Experience ID

**Example**:
```python
eid = mem.learn(
    action="Skipped backup before update",
    context="Production server",
    outcome="negative",
    insight="Always backup before updates",
    importance=0.9
)
```

---

### delete() - v2.1.0 增强

Delete a memory with protection.

```python
mem.delete(
    memory_id: int,
    force: bool = False
) -> Dict
```

**核心记忆保护：**
- 重要性 ≥ 0.9 的记忆需要 `force=True` 才能删除
- 返回警告信息而不是直接删除

**Returns**: Dict with `success`, `message`, and optionally `warning`

**Example**:
```python
# 普通记忆可直接删除
result = mem.delete(123)

# 核心记忆需要确认
result = mem.delete(456)  # 返回 warning
# {'success': False, 'warning': 'Core memory requires force=True'}

result = mem.delete(456, force=True)  # 强制删除
```

---

### health_check() - v2.1.0 新增

Check database health.

```python
mem.health_check() -> Dict
```

**Returns**:
```python
{
    'status': 'healthy' | 'warning' | 'error',
    'stats': {
        'facts': int,
        'experiences': int,
        'relations': int,
        'orphaned_relations': int
    },
    'issues': List[str]
}
```

---

### get_lessons()

Retrieve all lessons.

```python
mem.get_lessons(limit: int = 100) -> List[Dict]
```

---

### delete()

Delete a memory by ID.

```python
mem.delete(memory_id: int, memory_type: str = 'fact') -> bool
```

---

## Entity Relations

### relate()

Create a relation between entities.

```python
mem.relate(
    from_entity: str,
    relation_type: str,
    to_entity: str,
    evidence: str = None
) -> int
```

**Example**:
```python
mem.relate("Alice", "works_at", "TechCorp")
mem.relate("Alice", "knows", "Bob")
```

---

### get_relations()

Get all relations for an entity.

```python
mem.get_relations(entity: str) -> List[Dict]
```

**Returns**:
```python
[
    {'from': 'Alice', 'relation': 'works_at', 'to': 'TechCorp'},
    {'from': 'Alice', 'relation': 'knows', 'to': 'Bob'}
]
```

---

### associate()

Get association network starting from an entity.

```python
mem.associate(
    entity: str,
    depth: int = 2
) -> Dict
```

**Returns**:
```python
{
    'center': 'Alice',
    'associations': [
        {'from': 'Alice', 'relation': 'works_at', 'to': 'TechCorp', 'level': 1},
        {'from': 'Alice', 'relation': 'knows', 'to': 'Bob', 'level': 1},
        {'from': 'Bob', 'relation': 'works_at', 'to': 'StartupInc', 'level': 2}
    ]
}
```

---

### infer_relation()

Infer relation type between entities.

```python
mem.infer_relation(
    from_entity: str,
    to_entity: str
) -> Tuple[str, float]
```

**Returns**: (relation_type, confidence)

---

## Contextual Memory

### Context Class

```python
from memorycoreclaw import Context

ctx = Context(
    location: str = None,
    people: List[str] = None,
    emotion: str = None,
    activity: str = None,
    channel: str = None
)
```

---

### bind_context()

Bind a memory to a context.

```python
mem.bind_context(
    memory_type: str,  # 'fact' or 'experience'
    memory_id: int,
    context: Context
) -> int
```

---

### recall_by_context()

Recall memories matching a context.

```python
mem.recall_by_context(
    location: str = None,
    people: List[str] = None,
    emotion: str = None,
    activity: str = None
) -> List[Dict]
```

**Example**:
```python
results = mem.recall_by_context(people=["Alice"])
```

---

## Working Memory

### hold()

Store temporary data.

```python
mem.hold(
    key: str,
    value: Any,
    priority: float = 0.5,
    ttl_seconds: int = None
)
```

**Example**:
```python
mem.hold("task", "Processing", priority=0.9, ttl_seconds=3600)
```

---

### retrieve()

Get temporary data.

```python
mem.retrieve(key: str) -> Any
```

---

### clear_working_memory()

Clear all temporary data.

```python
mem.clear_working_memory()
```

---

## Forgetting Curve

### get_memory_strength()

Get current strength of a memory.

```python
mem.get_memory_strength(
    memory_type: str,
    memory_id: int
) -> Dict
```

**Returns**:
```python
{
    'initial_strength': 0.7,
    'current_strength': 0.65,
    'last_accessed': '2024-01-15T10:30:00',
    'access_count': 3
}
```

---

### calculate_retention()

Calculate retention rate.

```python
mem.calculate_retention(
    days: float,
    strength: float = 0.7
) -> float
```

**Returns**: Retention ratio (0-1)

---

## Statistics

### get_stats()

Get system statistics.

```python
mem.get_stats() -> Dict
```

**Returns**:
```python
{
    'facts': 48,
    'experiences': 21,
    'relations': 26,
    'entities': 15,
    'working_memory': {'used': 3, 'capacity': 9}
}
```

---

## Export

### export_json()

Export all data to JSON.

```python
mem.export_json() -> Dict
```

---

### visualize()

Generate knowledge graph HTML.

```python
mem.visualize(output_path: str = None) -> str
```

**Returns**: HTML file path

---

## Constants

### MemoryLayer

```python
from memorycoreclaw import MemoryLayer

MemoryLayer.CORE       # importance >= 0.9
MemoryLayer.IMPORTANT  # 0.7 <= importance < 0.9
MemoryLayer.NORMAL     # 0.5 <= importance < 0.7
MemoryLayer.MINOR      # importance < 0.5
```

### Standard Relations

```python
from memorycoreclaw import STANDARD_RELATIONS

# 28 standard relation types
['works_at', 'works_in', 'manages', 'collaborates_with', 
 'knows', 'friend_of', 'uses', 'depends_on', ...]
```

---

## Error Handling

```python
from memorycoreclaw import MemoryError

try:
    mem.remember("")
except MemoryError as e:
    print(f"Error: {e}")
```