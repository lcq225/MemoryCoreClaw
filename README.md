# MemoryCoreClaw

> A human-brain-inspired long-term memory engine for AI Agents

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Layered Memory** - Core/Important/Normal layers with different retention policies
- **Forgetting Curve** - Ebbinghaus model for memory strength decay
- **Contextual Memory** - Trigger memories by location, people, activity
- **Working Memory** - Limited capacity temporary storage (7±2 items)
- **Relation Learning** - Automatic inference of entity relationships
- **Semantic Search** - Optional embedding-based retrieval
- **Multi-modal** - Support for images, files, and web content
- **Export & Visualization** - JSON/Markdown export, knowledge graph HTML

## Quick Start

```bash
pip install memorycoreclaw
```

```python
from memorycoreclaw import Memory

# Initialize
mem = Memory()

# Remember
mem.remember("Alice works at TechCorp", importance=0.8)

# Recall
results = mem.recall("Alice")

# Relations
mem.relate("Alice", "works_at", "TechCorp")
network = mem.associate("Alice")

# Context trigger
mem.recall_by_context(people=["Alice"], location="office")

# Working memory
mem.hold("current_task", "processing", priority=0.9)
task = mem.retrieve("current_task")
```

## Architecture

```
MemoryCoreClaw
├── core/           # Core memory engine
├── cognitive/      # Forgetting, context, working memory
├── retrieval/      # Semantic search, ontology
├── storage/        # Database, multimodal
└── utils/          # Export, visualization
```

## Documentation

- [Getting Started](docs/GETTING_STARTED.md)
- [API Reference](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)

## License

MIT License"# MemoryCoreClaw" 
