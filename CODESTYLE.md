# Code Style Guide

Code style guidelines for the MCP ClickHouse Documentation project.

## Language

- Use British English in code, comments, and documentation
- Examples: "initialise" (not "initialize"), "colour" (not "color"), "serialise" (not "serialize")

## Python Standards

### General

- Follow PEP 8 guidelines
- Use type hints for all functions and methods
- Python 3.12+ features are allowed and encouraged
- Maximum line length: 120 characters

### Imports

```python
# Standard library imports first
import logging
import re
from pathlib import Path
from typing import Optional

# Third-party imports second
import frontmatter
from fastmcp import FastMCP

# Local imports last
from mcp_clickhouse_documentation.database import DocumentDatabase
from mcp_clickhouse_documentation.models import Document
```

### Type Hints

Always use type hints:

```python
def search(self, query: str, section: Optional[str] = None, limit: int = 10) -> list[SearchResult]:
    """Search documentation."""
    ...
```

Use modern Python 3.12 type syntax:
- `list[str]` instead of `List[str]`
- `dict[str, int]` instead of `Dict[str, int]`
- `tuple[str, int]` instead of `Tuple[str, int]`

### Docstrings

Use Google-style docstrings:

```python
def parse_file(self, file_path: Path) -> Document:
    """Parse an MDX or Markdown file into a Document.

    Args:
        file_path: Path to the documentation file

    Returns:
        Parsed Document

    Raises:
        ValueError: If file cannot be parsed or is missing required metadata
    """
```

### Error Handling

Prefer explicit error handling:

```python
# Good
try:
    doc = self.parser.parse_file(file_path)
    self.db.insert_document(doc)
except ValueError as e:
    logger.error(f"Failed to parse {file_path}: {e}")
    return None

# Bad (silent failure)
try:
    doc = self.parser.parse_file(file_path)
except:
    pass
```

### Logging

Use structured logging:

```python
import logging

logger = logging.getLogger(__name__)

# Appropriate log levels
logger.debug("Detailed information for debugging")
logger.info("General informational messages")
logger.warning("Warning messages for recoverable issues")
logger.error("Error messages for failures")
```

### Design Patterns

Use appropriate design patterns:

- **Dependency Injection:** Pass dependencies via constructor
  ```python
  class DocumentationIndexer:
      def __init__(self, db: DocumentDatabase, repo_path: Path) -> None:
          self.db = db
          self.repo_path = repo_path
  ```

- **Single Responsibility:** Each class has one clear purpose
- **Composition over Inheritance:** Prefer composition

### Testing

#### Framework

Use pytest for all tests:

```python
import pytest
from pathlib import Path

@pytest.fixture
def temp_docs_root(tmp_path: Path) -> Path:
    """Create temporary documentation root."""
    return tmp_path

def test_parse_file(temp_docs_root: Path) -> None:
    """Test file parsing."""
    # Arrange
    file_path = temp_docs_root / "test.md"
    file_path.write_text("# Test")

    # Act
    parser = DocumentParser(temp_docs_root)
    result = parser.parse_file(file_path)

    # Assert
    assert result.title == "Test"
```

#### Test Organisation

- One test file per source file: `test_parser.py` tests `parser.py`
- Use descriptive test names: `test_clean_content_removes_mdx_imports`
- Follow Arrange-Act-Assert pattern
- Use fixtures for shared setup

#### Coverage

- Maintain >80% test coverage
- Run with: `make test`
- View report: `open htmlcov/index.html`

## Code Quality Tools

### Ruff

Linter and formatter:

```bash
# Format code
make format

# Check linting
uv run ruff check src/ tests/

# Auto-fix issues
uv run ruff check --fix src/ tests/
```

Configuration in `pyproject.toml`:
```toml
[tool.ruff]
target-version = "py312"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "B", "UP"]
```

### Mypy

Type checking:

```bash
# Check types
uv run mypy src/
```

Configuration in `pyproject.toml`:
```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

## Project Structure

```
mcp-clickhouse-documentation/
├── src/mcp_clickhouse_documentation/    # Source code
│   ├── __init__.py                      # Package initialisation
│   ├── models.py                        # Data models (dataclasses)
│   ├── parser.py                        # MDX/Markdown parsing logic
│   ├── database.py                      # Database operations
│   ├── indexer.py                       # Documentation indexing
│   ├── server.py                        # FastMCP server
│   └── cli.py                           # Command-line interface
├── tests/                               # Test suite
│   ├── __init__.py                      # Test package initialisation
│   ├── test_models.py                   # Model tests
│   ├── test_parser.py                   # Parser tests
│   └── test_database.py                 # Database tests
├── pyproject.toml                       # Project configuration
├── Makefile                             # Build automation
├── README.md                            # Project overview
├── USAGE.md                             # Usage guide
├── CODESTYLE.md                         # This file
└── CLAUDE.md                            # Claude-specific context
```

## File Naming

- Python files: lowercase with underscores (`parser.py`, `database.py`)
- Test files: prefix with `test_` (`test_parser.py`)
- Constants: UPPERCASE_WITH_UNDERSCORES
- Classes: PascalCase (`DocumentParser`, `DocumentDatabase`)
- Functions/methods: lowercase_with_underscores
- Private methods: prefix with underscore (`_clean_content`)

## Comments

### When to Comment

Comment on "why", not "what":

```python
# Good
# Use BM25 ranking with higher weight for title matches
cursor = conn.execute("SELECT ... bm25(documents_fts, 5.0, 2.0, 1.0) ...")

# Bad (obvious from code)
# Execute SQL query
cursor = conn.execute("SELECT * FROM documents")
```

### TODO Comments

```python
# TODO(username): Description of future work
# FIXME(username): Description of known issue
```

## Git Workflow

### Branch Naming

- Feature: `feature/add-section-filtering`
- Bug fix: `bugfix/fix-mdx-parsing`
- Hotfix: `hotfix/critical-security-fix`

### Commit Messages

Follow Conventional Commits:

```
feat: Add section filtering to search
fix: Handle missing frontmatter gracefully
docs: Update installation instructions
test: Add parser tests for MDX components
refactor: Extract URL computation logic
```

### Pull Requests

- Never push directly to main
- Create PR for all changes
- Run `make build` before creating PR
- Include tests for new features
- Update documentation as needed

## Makefile Targets

Standard targets for all projects:

```bash
make init      # Initialise development environment
make test      # Run tests with coverage
make build     # Run linting, type checking, and tests
make format    # Format code
make generate  # Update generated files (uv.lock)
make clean     # Clean build artifacts
```

Project-specific targets:

```bash
make index     # Index ClickHouse documentation
make stats     # Show indexing statistics
make run       # Run MCP server
```

## Dependencies

### Adding Dependencies

```bash
# Add runtime dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Update lock file
make generate
```

### Dependency Guidelines

- Minimise dependencies
- Pin major versions: `"fastmcp>=2.0.0,<3.0.0"`
- Prefer pure Python packages
- Document why each dependency is needed

## Performance

### General Guidelines

- Use generators for large datasets
- Close resources properly (use context managers)
- Avoid premature optimisation
- Profile before optimising

### Database

- Use parameterised queries (prevent SQL injection)
- Batch inserts when possible
- Use transactions for multiple operations
- Index frequently queried columns

### Example

```python
# Good - uses context manager and parameterised query
with sqlite3.connect(self.db_path) as conn:
    conn.execute(
        "INSERT INTO documents (path, title) VALUES (?, ?)",
        (doc.path, doc.title),
    )
    conn.commit()

# Bad - doesn't close connection, SQL injection risk
conn = sqlite3.connect(self.db_path)
conn.execute(f"INSERT INTO documents VALUES ('{doc.path}')")
```

## Security

- Never commit secrets or credentials
- Use `.gitignore` for sensitive files
- Validate all external input
- Use parameterised SQL queries
- Keep dependencies updated

## Documentation

### README.md

- Project overview
- Quick start guide
- Features list
- Installation instructions
- Basic usage examples

### USAGE.md

- Comprehensive usage guide
- All tool parameters
- Example workflows
- Troubleshooting
- Advanced configuration

### CODESTYLE.md

- Coding standards
- Project structure
- Development workflow
- Testing guidelines

### CLAUDE.md

- Repository context
- Architecture decisions
- Key implementation details
- Development guidelines

## Pre-commit Checklist

Before committing:

- [ ] Run `make format` to format code
- [ ] Run `make build` to check quality
- [ ] All tests pass
- [ ] Type checking passes
- [ ] Documentation updated if needed
- [ ] Commit message follows conventions

## Resources

- [PEP 8](https://peps.python.org/pep-0008/) - Python style guide
- [PEP 484](https://peps.python.org/pep-0484/) - Type hints
- [pytest](https://docs.pytest.org/) - Testing framework
- [Ruff](https://docs.astral.sh/ruff/) - Linter and formatter
- [mypy](https://mypy.readthedocs.io/) - Type checker
- [Conventional Commits](https://www.conventionalcommits.org/) - Commit message format
