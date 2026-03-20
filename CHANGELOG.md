# Changelog

All notable changes to MemoryCoreClaw will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-03-20

### Added
- **Enhanced Visualization Module**
  - Interactive D3.js knowledge graph with drag/zoom/click
  - Statistics report with memory breakdown
  - Memory browser with search and filter
  - Standalone CLI for generating visualizations
- **Environment Variable Support**
  - `MEMORY_DB_PATH` - Custom database path
  - `MEMORY_OUTPUT_DIR` - Custom output directory
- **Improved Database Compatibility**
  - Fixed entity table column name (`type` vs `entity_type`)
  - Direct database query for visualization

### Changed
- Visualization module now works independently without Memory engine instance
- CLI uses environment variables instead of hardcoded paths
- Fixed project URLs in `pyproject.toml`

### Fixed
- Corrected GitHub repository URLs from `memorycoreclaw/memorycoreclaw` to `lcq225/MemoryCoreClaw`
- Removed hardcoded paths from visualization CLI

## [0.1.0] - 2026-03-19

### Added
- Core memory engine with fact/experience/entity storage
- Layered memory system (core/important/normal/minor)
- Ebbinghaus forgetting curve implementation
- Contextual memory triggers
- Working memory with limited capacity (9 items)
- Relation learning and inference
- 28 standard relation types
- Semantic search (optional with embedding model)
- Knowledge graph visualization (HTML)
- JSON/Markdown export
- SQLite database with optional encryption
- Comprehensive test suite
- Full API documentation

### Features

#### Memory Operations
- `remember()` - Store facts
- `recall()` - Search memories
- `learn()` - Store lessons
- `delete()` - Remove memories

#### Relations
- `relate()` - Create entity relations
- `get_relations()` - Query relations
- `associate()` - Get association network
- `infer_relation()` - Infer relation type

#### Cognitive
- Forgetting curve with access strengthening
- Context binding and triggering
- Working memory with TTL support
- Importance auto-scoring

#### Utilities
- JSON export/import
- Knowledge graph HTML visualization
- System health check
- Statistics dashboard