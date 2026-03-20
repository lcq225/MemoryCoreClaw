# MemoryCoreClaw

> A human-brain-inspired long-term memory engine for AI Agents

[English](README.md) | [中文](README_zh.md)

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/v/release/lcq225/MemoryCoreClaw.svg)](https://github.com/lcq225/MemoryCoreClaw/releases)

---

## Overview

MemoryCoreClaw is a long-term memory engine that simulates human brain memory mechanisms, designed specifically for AI Agents. It implements cognitive science concepts including layered memory, forgetting curve, contextual triggers, and working memory, giving AI Agents the ability to "remember".

### Why MemoryCoreClaw?

Traditional AI Agents have limited conversation context and cannot remember user preferences or historical interactions over the long term. MemoryCoreClaw solves this problem:

| Traditional Approach | MemoryCoreClaw |
|---------------------|----------------|
| Limited context window | Permanent memory storage |
| Cannot remember user preferences | Remembers and associates user information |
| Every conversation starts from zero | Automatically recalls relevant memories |
| No knowledge accumulation | Knowledge graph continues to grow |

---

## Features

### 🧠 Layered Memory
- **Core Layer** (importance ≥ 0.9): Permanent retention, injected into context
- **Important Layer** (0.7 ≤ importance < 0.9): Long-term retention
- **Normal Layer** (0.5 ≤ importance < 0.7): Periodic consolidation
- **Minor Layer** (importance < 0.5): May decay

### 📉 Forgetting Curve
Based on the Ebbinghaus forgetting curve model:
- Memory strength decays over time
- Access strengthens memory
- Low-strength memories can be cleaned up

### 🎯 Contextual Memory
- Bind memories by people, location, emotion, activity
- Context-triggered memory recall
- Support for "What did we discuss at the coffee shop last time?"

### 💼 Working Memory
- Capacity limit (7±2 model)
- Priority-based eviction strategy
- TTL expiration mechanism

### 🔗 Relation Learning
- 28 standard relation types
- Automatic relation inference
- Knowledge graph visualization

### 📤 Export
- JSON format export
- Markdown format export
- Knowledge graph HTML visualization

### 📊 Visualization (New in v2.0.0)
- **Knowledge Graph** - Interactive D3.js force-directed graph with drag, zoom, and click-to-view details
- **Statistics Report** - Memory count, categories, relation types visualization
- **Memory Browser** - Searchable facts/lessons/relations list

```bash
# Generate visualizations
python -m memorycoreclaw.utils.visualization

# Or specify custom paths via environment variables
MEMORY_DB_PATH=/path/to/memory.db MEMORY_OUTPUT_DIR=./output python -m memorycoreclaw.utils.visualization
```

---

## Quick Start

### Installation

```bash
pip install memorycoreclaw
```

### Basic Usage

```python
from memorycoreclaw import Memory

# Initialize
mem = Memory()

# Remember facts
mem.remember("Alice works at TechCorp", importance=0.8)
mem.remember("Alice is skilled in Python", importance=0.7, category="technical")

# Recall memories
results = mem.recall("Alice")
for r in results:
    print(f"- {r['content']} (importance: {r['importance']})")

# Learn lessons
mem.learn(
    action="Deployed without testing",
    context="Production release",
    outcome="negative",
    insight="Always test before deployment",
    importance=0.9
)

# Create relations
mem.relate("Alice", "works_at", "TechCorp")
mem.relate("Alice", "knows", "Bob")

# Query relations
relations = mem.get_relations("Alice")
for rel in relations:
    print(f"{rel['from_entity']} --[{rel['relation_type']}]--> {rel['to_entity']}")

# Working memory
mem.hold("current_task", "Writing documentation", priority=0.9)
task = mem.retrieve("current_task")
print(f"Current task: {task}")
```

---

## Project Structure

```
MemoryCoreClaw/
├── memorycoreclaw/          # Core code
│   ├── core/                # Core engine
│   │   ├── engine.py        # Memory engine
│   │   └── memory.py        # Unified interface
│   ├── cognitive/           # Cognitive modules
│   │   ├── forgetting.py    # Forgetting curve
│   │   ├── contextual.py    # Contextual memory
│   │   └── working_memory.py # Working memory
│   ├── retrieval/           # Retrieval modules
│   │   ├── semantic.py      # Semantic search
│   │   └── ontology.py      # Ontology
│   ├── storage/             # Storage modules
│   │   ├── database.py      # Database
│   │   └── multimodal.py    # Multimodal
│   └── utils/               # Utility modules
│       ├── export.py        # Export
│       └── visualization.py # Visualization
├── docs/                    # Documentation
│   ├── GETTING_STARTED.md   # Getting started
│   ├── API.md               # API reference
│   ├── ARCHITECTURE.md      # Architecture
│   └── DEPLOYMENT.md        # Deployment guide
├── examples/                # Example code
├── tests/                   # Test cases
└── config/                  # Configuration files
```

---

## Documentation

- [Getting Started](docs/GETTING_STARTED.md) - Quick start guide
- [API Reference](docs/API.md) - Complete API documentation
- [Architecture](docs/ARCHITECTURE.md) - System architecture
- [Deployment](docs/DEPLOYMENT.md) - Installation and deployment guide

---

## Configuration

Default configuration file `config/default.yaml`:

```yaml
# Database configuration
database:
  path: "~/.memorycoreclaw/memory.db"
  encrypt: false

# Memory layers
layers:
  core:
    min_importance: 0.9
    retention: permanent
  important:
    min_importance: 0.7
    retention: long_term
  normal:
    min_importance: 0.5
    retention: standard
  minor:
    min_importance: 0.0
    retention: may_decay

# Forgetting curve
forgetting:
  enabled: true
  min_strength: 0.1
  access_bonus: 1.1

# Working memory
working_memory:
  capacity: 9
  eviction_policy: lowest_priority
```

---

## Integration Examples

### LangChain Integration

```python
from langchain.memory import BaseMemory
from memorycoreclaw import Memory

class MemoryCoreClawMemory(BaseMemory):
    """LangChain memory adapter"""
    
    def __init__(self, db_path=None):
        self.mem = Memory(db_path=db_path)
    
    @property
    def memory_variables(self):
        return ["memory_context"]
    
    def load_memory_variables(self, inputs):
        query = inputs.get("input", "")
        memories = self.mem.recall(query, limit=5)
        context = "\n".join([m["content"] for m in memories])
        return {"memory_context": context}
    
    def save_context(self, inputs, outputs):
        user_input = inputs.get("input", "")
        ai_output = outputs.get("output", "")
        self.mem.remember(f"User: {user_input}", importance=0.5)
        self.mem.remember(f"AI: {ai_output}", importance=0.5)
    
    def clear(self):
        pass

# Usage
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain

memory = MemoryCoreClawMemory()
llm = ChatOpenAI()
chain = ConversationChain(llm=llm, memory=memory)
```

### RAG Enhancement

```python
from memorycoreclaw import Memory

mem = Memory()

def enhanced_rag_query(query):
    # Recall relevant memories before RAG query
    memories = mem.recall(query, limit=3)
    context = "\n".join([m["content"] for m in memories])
    
    # Enhanced query
    enriched_query = f"""
Context memories:
{context}

User question: {query}
"""
    return enriched_query

# Remember new information after query
mem.remember(f"User asked about: {query}", importance=0.6)
```

---

## Performance

| Metric | Value |
|--------|-------|
| Memory storage | SQLite, supports millions of records |
| Query latency | < 10ms (keyword search) |
| Memory usage | < 50MB (100k memories) |
| Concurrency | Multi-process read safe |

---

## Development

### Setup Environment

```bash
# Clone repository
git clone https://github.com/lcq225/MemoryCoreClaw.git
cd MemoryCoreClaw

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install development dependencies
pip install -e ".[dev]"

# Run tests
python tests/standalone_test.py
```

### Run Examples

```bash
# Basic example
python examples/basic_usage.py

# Knowledge graph example
python examples/knowledge_graph.py
```

---

## Contributing

Contributions are welcome! Please check [Contributing Guide](CONTRIBUTING.md).

---

## License

[MIT License](LICENSE)

---

## Contact

- GitHub: [https://github.com/lcq225/MemoryCoreClaw](https://github.com/lcq225/MemoryCoreClaw)
- Issues: [https://github.com/lcq225/MemoryCoreClaw/issues](https://github.com/lcq225/MemoryCoreClaw/issues)

---

**MemoryCoreClaw** - Give AI Agents the power of memory 🧠