# Getting Started with MemoryCoreClaw

## Installation

```bash
pip install memorycoreclaw
```

## Basic Usage

### 1. Initialize

```python
from memorycoreclaw import Memory

mem = Memory()
```

### 2. Remember Facts

```python
# Simple
mem.remember("Alice works at TechCorp")

# With metadata
mem.remember(
    "Project X uses Python 3.11",
    importance=0.8,
    category="technical",
    tags=["project", "python"]
)
```

### 3. Recall Facts

```python
# Keyword search
results = mem.recall("Alice")
for r in results:
    print(r['content'])
```

### 4. Learn Lessons

```python
mem.learn(
    action="Deployed without testing",
    context="Production release",
    outcome="negative",
    insight="Always test before deployment",
    importance=0.9
)
```

### 5. Entity Relations

```python
# Create relations
mem.relate("Alice", "works_at", "TechCorp")
mem.relate("Alice", "knows", "Bob")
mem.relate("Bob", "works_at", "TechCorp")

# Get relations
relations = mem.get_relations("Alice")

# Association network
network = mem.associate("Alice", depth=2)
```

### 6. Contextual Memory

```python
from memorycoreclaw import Context

# Create context
ctx = Context(
    location="office",
    people=["Alice", "Bob"],
    activity="meeting"
)

# Bind to memory
mem.bind_context('fact', fact_id, ctx)

# Recall by context
results = mem.recall_by_context(people=["Alice"])
```

### 7. Working Memory

```python
# Store temporary data
mem.hold("current_task", "Processing data", priority=0.9)
mem.hold("temp_list", [1, 2, 3], priority=0.7, ttl_seconds=3600)

# Retrieve
task = mem.retrieve("current_task")

# Clear
mem.clear_working_memory()
```

## Memory Layers

| Importance | Layer | Behavior |
|------------|-------|----------|
| ≥ 0.9 | Core | Permanent, high priority |
| 0.7 - 0.9 | Important | Long-term retention |
| 0.5 - 0.7 | Normal | Standard retention |
| < 0.5 | Minor | May decay |

## Forgetting Curve

MemoryCoreClaw implements the Ebbinghaus forgetting curve:

```
Retention = e^(-days / strength)
```

- 1 day: ~90% retention
- 7 days: ~60% retention  
- 30 days: ~30% retention

**Strengthening**: Each access increases strength by 10%.

## Database Location

Default: `~/.memorycoreclaw/memory.db`

Custom:
```python
mem = Memory(db_path="/path/to/custom.db")
```

## Statistics

```python
stats = mem.get_stats()
print(f"Facts: {stats['facts']}")
print(f"Lessons: {stats['experiences']}")
print(f"Relations: {stats['relations']}")
```

## Export

```python
# JSON export
data = mem.export_json()

# Save to file
import json
with open('memory_backup.json', 'w') as f:
    json.dump(data, f, indent=2)
```