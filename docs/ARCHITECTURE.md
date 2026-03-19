# MemoryCoreClaw Architecture

## Overview

MemoryCoreClaw is a human-brain-inspired memory system for AI agents. It implements key cognitive memory concepts:

- **Layered Memory** - Different retention for different importance levels
- **Forgetting Curve** - Ebbinghaus model for memory decay
- **Contextual Memory** - Situation-based recall
- **Working Memory** - Limited capacity temporary storage
- **Relation Learning** - Entity relationship inference

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MemoryCoreClaw                            │
├─────────────────────────────────────────────────────────────┤
│  API Layer                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Memory (unified interface)                          │   │
│  │  remember | recall | learn | relate | hold | ...     │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Core Engine (core/engine.py)                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  • Fact CRUD         • Lesson CRUD                   │   │
│  │  • Relation Management • Context Binding             │   │
│  │  • Working Memory     • Forgetting Curve             │   │
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
│  └────────────┘ └────────────┘                             │
├─────────────────────────────────────────────────────────────┤
│  Storage (storage/)                                         │
│  ┌────────────┐ ┌────────────┐                             │
│  │  Database  │ │ Multimodal │                             │
│  │  (SQLite)  │ │  Storage   │                             │
│  └────────────┘ └────────────┘                             │
├─────────────────────────────────────────────────────────────┤
│  Utils (utils/)                                             │
│  ┌────────────┐ ┌────────────┐                             │
│  │   Export   │ │Visualization│                            │
│  │   Import   │ │   (HTML)    │                            │
│  └────────────┘ └────────────┘                             │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

### Core Tables

```sql
-- Facts (what you know)
facts (
    id, content, importance, category, 
    emotion, tags, created_at, last_accessed, access_count
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