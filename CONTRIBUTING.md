# Contributing to MemoryCoreClaw

Thank you for your interest in contributing to MemoryCoreClaw!

## Development Setup

1. Fork and clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/MemoryCoreClaw.git
cd MemoryCoreClaw
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. Install development dependencies
```bash
pip install -e ".[dev]"
```

4. Run tests
```bash
pytest tests/ -v
```

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for public functions
- Keep functions under 50 lines

## Pull Request Process

1. Create a feature branch
```bash
git checkout -b feature/your-feature-name
```

2. Make changes and write tests

3. Run tests and linting
```bash
pytest tests/ -v
flake8 memorycoreclaw/
```

4. Submit PR with clear description

## Adding New Features

### New Relation Types

Add to `memorycoreclaw/core/types.py`:

```python
STANDARD_RELATIONS = {
    # ... existing relations ...
    'your_new_relation',
}
```

### New Memory Types

1. Add table schema in `storage/database.py`
2. Add CRUD methods in `core/engine.py`
3. Add API in `core/memory.py`

### New Cognitive Modules

1. Create file in `cognitive/`
2. Implement with `MemoryEngine` integration
3. Add tests in `tests/`

## Bug Reports

Open an issue with:
- Python version
- MemoryCoreClaw version
- Minimal reproducible example
- Expected vs actual behavior

## Feature Requests

Open an issue with:
- Use case description
- Proposed API
- Implementation ideas (optional)

## Code of Conduct

Be respectful, inclusive, and constructive.