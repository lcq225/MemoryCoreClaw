# MemoryCoreClaw Architecture

> **版本：v2.1.0**
> 
> 新增：SafeMemory 安全接口、SafeDatabaseManager 线程安全数据库管理器

## Overview

MemoryCoreClaw is a human-brain-inspired memory system for AI agents. It implements key cognitive memory concepts:

- **Layered Memory** - Different retention for different importance levels
- **Forgetting Curve** - Ebbinghaus model for memory decay
- **Contextual Memory** - Situation-based recall
- **Working Memory** - Limited capacity temporary storage
- **Relation Learning** - Entity relationship inference
- **Safety Operations** (v2.1.0) - Connection management, boundary checking, core memory protection

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MemoryCoreClaw v2.1.0                     │
├─────────────────────────────────────────────────────────────┤
│  API Layer                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Memory (基础接口)                                    │   │
│  │  remember | recall | learn | relate | hold | ...     │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  SafeMemory (安全接口 - v2.1.0)                       │   │
│  │  + 连接管理 + 事务保护 + 边界检查 + 核心保护          │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Core Engine (core/engine.py)                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  • Fact CRUD         • Lesson CRUD                   │   │
│  │  • Relation Management • Context Binding             │   │
│  │  • Working Memory     • Forgetting Curve             │   │
│  │  • Source Tracking (v2.1.0)                          │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Cognitive Modules (cognitive/)                             │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐             │
│  │ Forgetting │ │ Contextual │ │  Working   │             │
│  │  Curve     │ │  Memory    │ │  Memory    │             │
│  └────────────┘ └────────────┘ └────────────┘             │
│  ┌────────────┐ ┌────────────┐                             │
│  │ Importance │ │  Relation  │                             │
│  │  Scoring   │ │  Learning  │                             │
│  └────────────┘ └────────────┘                             │
├─────────────────────────────────────────────────────────────┤
│  Retrieval (retrieval/)                                     │
│  ┌────────────┐ ┌────────────┐                             │
│  │  Semantic  │ │  Ontology  │                             │
│  │   Search   │ │   Engine   │                             │
│  │ (v2.1.0:   │ │            │                             │
│  │  健康检查) │ │            │                             │
│  └────────────┘ └────────────┘                             │
├─────────────────────────────────────────────────────────────┤
│  Storage (storage/) - v2.1.0 增强                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐             │
│  │  Database  │ │ Multimodal │ │   Safe     │             │
│  │  Manager   │ │  Storage   │ │  Database  │             │
│  │            │ │            │ │  Manager   │             │
│  └────────────┘ └────────────┘ └────────────┘             │
│  ┌────────────┐                                             │
│  │  Health    │                                             │
│  │  Checker   │                                             │
│  └────────────┘                                             │
├─────────────────────────────────────────────────────────────┤
│  Utils (utils/)                                             │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐             │
│  │   Export   │ │Visualization│ │  GitHub   │             │
│  │   Import   │ │   (HTML)    │ │   API     │             │
│  └────────────┘ └────────────┘ └────────────┘             │
├─────────────────────────────────────────────────────────────┤
│  Scripts (scripts/) - v2.1.0 新增                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐             │
│  │  check_    │ │  optimize_ │ │    sync_   │             │
│  │  memory    │ │  database  │ │  to_md     │             │
│  └────────────┘ └────────────┘ └────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

## v2.1.0 新增模块

### SafeDatabaseManager

线程安全的数据库管理器：

```python
from memorycoreclaw.storage.database import SafeDatabaseManager

db = SafeDatabaseManager("memory.db")

# 事务操作（自动提交/回滚）
with db.transaction() as cursor:
    cursor.execute("INSERT INTO facts ...")
    # 异常时自动回滚

# 只读操作
with db.readonly() as cursor:
    cursor.execute("SELECT ...")
```

**特性：**
- 单例模式：同一数据库路径共享连接
- 线程安全：每个线程独立连接
- WAL 模式：提升并发性能

### MemoryHealthChecker

数据库健康检查：

```python
from memorycoreclaw.storage.database import MemoryHealthChecker

checker = MemoryHealthChecker(db_path)
report = checker.check()
# {'status': 'healthy', 'stats': {...}, 'issues': []}
```

### Source Tracking

记忆来源追踪：

```python
mem.remember(
    "重要信息",
    source="user",           # user/llm/document/system
    source_confidence=1.0    # 来源置信度
)
```

## Database Schema

### Core Tables

```sql
-- Facts (what you know)
facts (
    id, content, importance, category, 
    emotion, tags, created_at, last_accessed, access_count,
    source, source_confidence  -- v2.1.0 新增
)

-- Experiences (lessons learned)
experiences (
    id, action, context, outcome, insight,
    importance, created_at
)

-- Entities (people, places, things)
entities (
    id, name, entity_type, metadata, created_at
)

-- Relations (entity connections)
relations (
    id, from_entity, relation_type, to_entity,
    weight, evidence, created_at
)
```

### Cognitive Tables

```sql
-- Memory strength (for forgetting curve)
memory_strength (
    id, memory_type, memory_id,
    initial_strength, current_strength,
    last_accessed, access_count
)

-- Contexts (situations)
contexts (
    id, location, people, emotion,
    activity, channel, created_at
)

-- Memory-Context bindings
memory_context_bindings (
    id, memory_type, memory_id,
    context_id, match_score
)

-- Working memory (temporary)
working_memory (
    key, value, priority,
    created_at, expires_at
)
```

## Memory Lifecycle

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Input   │────▶│  Store   │────▶│  Age     │────▶│  Recall  │
│ (create) │     │(strength)│     │ (decay)  │     │(strengthen)
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                      │                                  │
                      │                                  │
                      ▼                                  ▼
                 ┌──────────┐                     ┌──────────┐
                 │  Core    │                     │ Stronger │
                 │ Memory   │                     │ Memory   │
                 │ (≥0.9)   │                     │(+10%)    │
                 └──────────┘                     └──────────┘
```

## Cognitive Models

### 1. Forgetting Curve (Ebbinghaus)

```
R = e^(-t/S)

R = Retention ratio (0-1)
t = Time in days
S = Memory strength
```

Example (strength = 0.7):
- Day 1: 87% retention
- Day 7: 41% retention
- Day 30: 3% retention

### 2. Working Memory (Baddeley)

- Capacity: 7±2 items (we use 9)
- Eviction: Lowest priority first
- TTL: Optional expiration

### 3. Contextual Memory (Tulving)

Context dimensions:
- Location (where)
- People (who)
- Emotion (how)
- Activity (what)
- Channel (medium)

## Relation Types

### Standard Relations (28 types)

| Category | Relations |
|----------|-----------|
| Work | works_at, works_in, manages, collaborates_with, reports_to |
| Location | located_in, part_of, connected_to |
| Knowledge | knows, learned, teaches, studies |
| Usage | uses, depends_on, implements, produces |
| Preference | prefers, likes, dislikes, avoids |
| Social | friend_of, family_of, partner_of, colleague_of |
| Temporal | before, after, during, since |
| Causal | causes, prevents, enables, hinders |
| General | related_to, belongs_to, associated_with, similar_to |

## Extension Points

### Custom Relation Types

```python
mem.relate("A", "custom_relation", "B")
```

### Custom Context

```python
ctx = Context(
    location="custom_location",
    people=["custom_person"],
    custom_field="value"  # Extensible
)
```

### Custom Scoring

Override `calculate_importance()` for custom scoring logic.

## Integration Patterns

### As AI Agent Memory

```python
class MyAgent:
    def __init__(self):
        self.memory = Memory()
    
    def process(self, user_input):
        # Recall relevant context
        context = self.memory.recall(user_input)
        
        # Process with context...
        response = self.generate_response(user_input, context)
        
        # Remember interaction
        self.memory.remember(f"User asked: {user_input}")
        
        return response
```

### As RAG Enhancement

```python
# Before RAG query, inject relevant memories
memories = mem.recall(query)
enriched_query = f"{query}\nContext: {memories}"
```

## Performance Considerations

- SQLite database scales to millions of records
- Indexes on content, from_entity, to_entity
- Semantic search optional (requires embedding model)
- In-memory caching for frequently accessed items