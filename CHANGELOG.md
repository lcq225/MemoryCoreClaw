# Changelog

All notable changes to MemoryCoreClaw will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.1] - 2026-03-22

### Changed
- Added PyPI badge to README.md and README_zh.md
- Updated documentation with detailed bug fix information
- Added functional verification test (`test_v210.py`) to repository

### Fixed
- **SafeMemory initialization** - Added `_init_tables()` to ensure database schema exists before operations
- **MemoryHealthChecker path support** - Now accepts both string path and SafeDatabaseManager object
- **Windows encoding issues** - Removed temporary UTF-8 encoding overrides from semantic.py and safe_memory.py

### PyPI
- Published to PyPI: https://pypi.org/project/memorycoreclaw/2.1.1/
- Install: `pip install memorycoreclaw`

## [2.1.0] - 2026-03-22

### Added
- **Safety-First Memory Operations**
  - `SafeMemory` class with connection management and transaction protection
  - Boundary checking for limit parameters
  - Core memory deletion protection with force flag
  - Automatic parameter validation and correction
- **Source Tracking**
  - Memory source attribution (user/llm/document/system)
  - Source confidence scoring
  - Provenance chain for memory origins
- **Health Check & Maintenance Scripts**
  - `check_memory.py` - Database status inspection
  - `optimize_database.py` - Clean, repair, and enhance database
  - `auto_check.py` - Scheduled health monitoring
  - `check_duplicates.py` - Detect duplicate memories
  - `remove_duplicates.py` - Safe duplicate removal
- **Utility Scripts**
  - `sync_to_memory_md.py` - Export to human-readable format
  - `record_session_lessons.py` - Capture lessons from sessions
  - `create_entities_for_relations.py` - Auto-create entities from relations
- **GitHub API Integration**
  - `github_api.py` - Safe GitHub operations with SSL handling
- **Functional Verification Test**
  - `test_v210.py` - Comprehensive test suite for v2.1.0 features

### Changed
- Enhanced `MemoryEngine` with source tracking support
- Improved database operations with automatic cleanup
- Better error handling and recovery

### Fixed
- Parameter boundary issues in recall operations
- Memory strength initialization consistency
- Entity-relation integrity
- **SafeMemory initialization** - Added `_init_tables()` to ensure database schema exists before operations
- **MemoryHealthChecker path support** - Now accepts both string path and SafeDatabaseManager object
- **Windows encoding issues** - Removed temporary UTF-8 encoding overrides from semantic.py and safe_memory.py

### PyPI
- Published to PyPI: https://pypi.org/project/memorycoreclaw/2.1.0/
- Install: `pip install memorycoreclaw`

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

## [1.0.0] - 2026-03-19

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