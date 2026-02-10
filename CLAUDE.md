# Claude Context

Repository context and implementation details for Claude Code/Desktop.

## Project Overview

**Purpose:** MCP server enabling Claude to search and read official ClickHouse documentation.

**Key Challenge:** ClickHouse uses Docusaurus with MDX files (Markdown + JSX), requiring enhanced parsing to strip JSX components while preserving markdown.

**Solution:** Regex-based MDX cleaning + SQLite FTS5 full-text search with BM25 ranking.

## Architecture

### Technology Stack

- **Language:** Python 3.12
- **Package Manager:** uv
- **MCP Framework:** FastMCP 2.x
- **Database:** SQLite with FTS5 extension
- **Parsing:** python-frontmatter + custom regex MDX cleaner

### Key Components

1. **Parser (`parser.py`)** - Handles MDX/MD files, strips JSX, extracts metadata
2. **Database (`database.py`)** - SQLite FTS5 operations with BM25 ranking
3. **Indexer (`indexer.py`)** - Clones repo (sparse checkout), indexes docs
4. **Server (`server.py`)** - FastMCP server with 2 tools (search, read)
5. **CLI (`cli.py`)** - Command-line for indexing and stats

### Data Flow

```
1. Indexing:
   Git Clone (sparse) → Parse MDX → Clean Content → Index in SQLite FTS5

2. Search:
   User Query → BM25 Search → Return Snippets + URLs

3. Read:
   Document Path → Retrieve from DB → Return Full Content
```

## Critical Implementation Details

### MDX Parsing Strategy

**Problem:** ClickHouse docs use MDX with JSX components like:
- `<Tabs>`, `<TabItem>` - Tab navigation
- `<CloudNotSupportedBadge />` - Feature badges
- `import` statements for React components
- `{expressions}` in content

**Solution:** Regex-based cleaning in `_clean_content()`:
1. Remove import/export statements
2. Remove JSX self-closing tags: `<Component />`
3. Remove JSX paired tags: `<Component>...</Component>`
4. Remove JSX expressions: `{expression}`
5. Remove HTML comments and tags
6. Clean excessive whitespace

**Why not MDX parser library:** Avoids Node.js dependency, simpler deployment, sufficient for indexing purposes.

### Multi-Directory Structure

ClickHouse docs have two main directories:
- `docs/` - Main documentation (SQL reference, operations, etc.)
- `knowledgebase/` - Integration guides, tutorials

**Section Extraction Logic:**
- `docs/en/sql-reference/select.md` → section: `sql-reference`
- `knowledgebase/integrations/kafka.md` → section: `knowledgebase-integrations`

Language prefixes (en, zh, ru, jp) are detected and skipped.

### URL Pattern

Docusaurus uses clean URLs without extensions:
- File: `docs/en/sql-reference/select.mdx`
- URL: `https://clickhouse.com/docs/docs/en/sql-reference/select`

No `.html`, `.mdx`, or `.md` in URLs.

### BM25 Ranking

Search uses weighted BM25 ranking:
- **Title:** 5.0x weight (most important)
- **Description:** 2.0x weight
- **Content:** 1.0x weight (baseline)

This prioritises matches in titles over body content.

### Sparse Checkout

Clone only needed directories:
```bash
git clone --filter=blob:none --no-checkout --depth 1 REPO
git sparse-checkout set docs knowledgebase
git checkout
```

Benefits: ~10MB vs full repository, faster clone.

## File Locations

### Development

- **Source:** `/Users/martoc/Developer/github.com/martoc/mcp-clickhouse-documentation/src/`
- **Tests:** `/Users/martoc/Developer/github.com/martoc/mcp-clickhouse-documentation/tests/`

### Runtime

- **Database:** `~/.cache/mcp-clickhouse-documentation/docs.db`
- **Repository:** `~/.cache/mcp-clickhouse-documentation/clickhouse-docs/`

### Configuration

- **MCP Config:** `~/.config/claude/config.json` or Claude Desktop config
- **Project:** `.mcp.json` in repository root

## Common Tasks

### First Time Setup

```bash
cd /Users/martoc/Developer/github.com/martoc/mcp-clickhouse-documentation
make init    # Install dependencies
make index   # Clone and index docs (~2-5 minutes)
make stats   # Verify indexing
```

### Development Workflow

```bash
make format  # Format code
make build   # Lint + type check + test
make test    # Run tests only
```

### Testing Parser Changes

```bash
uv run pytest tests/test_parser.py -v -k test_clean_content
```

### Re-indexing After Parser Changes

```bash
uv run clickhouse-docs-index index --force
```

### Debugging Search Results

```bash
# Start server and use MCP inspector
make run

# Or test directly in Python
uv run python -c "
from pathlib import Path
from mcp_clickhouse_documentation.database import DocumentDatabase

db = DocumentDatabase(Path.home() / '.cache/mcp-clickhouse-documentation/docs.db')
results = db.search('SELECT statement', limit=3)
for r in results:
    print(f'{r.title} - {r.relevance_score}')
"
```

## Known Limitations

1. **MDX Parsing:** Regex-based, may miss complex nested JSX
2. **Language Support:** Indexes all languages, no filtering yet
3. **Content Updates:** Manual re-indexing required (no auto-update)
4. **Large Results:** Returns snippets only, not full content in search

## Testing Strategy

### Test Coverage

Target: 80%+ coverage

Key test files:
- `test_parser.py` - MDX cleaning, URL generation, section extraction
- `test_database.py` - FTS5 search, BM25 ranking, CRUD operations
- `test_models.py` - Data model creation

### Critical Tests

1. **MDX Cleaning:**
   - JSX component removal
   - Import/export stripping
   - Markdown preservation

2. **Search Quality:**
   - BM25 ranking correctness
   - Snippet generation
   - Section filtering

3. **Path Handling:**
   - Multi-directory support
   - URL generation
   - Section extraction

## Performance Characteristics

- **Indexing:** ~500-1000 docs in 2-5 minutes
- **Search:** <100ms typical, <500ms complex queries
- **Database Size:** ~5-10MB
- **Memory Usage:** ~50-100MB at runtime

## Dependencies Rationale

- **fastmcp:** MCP protocol implementation, well-maintained
- **python-frontmatter:** YAML metadata extraction, standard library
- **pytest:** Testing framework, industry standard
- **ruff:** Fast linter/formatter, replaces flake8+black+isort
- **mypy:** Type checking, catches errors early

No heavy dependencies (no ML, no Node.js, no complex parsing libraries).

## Future Enhancements

Potential improvements (not currently implemented):

1. **Language Filtering:** Add language parameter to search
2. **Auto-Update:** Periodic background re-indexing
3. **Caching:** Cache frequently accessed documents
4. **Sections API:** List available sections dynamically
5. **Related Docs:** Suggest related documentation
6. **Code Examples:** Extract and index code snippets separately

## Troubleshooting

### Database Not Found

**Symptom:** Server warns "Database not found"

**Fix:**
```bash
make index
```

### Parser Errors

**Symptom:** "Failed to parse X files" during indexing

**Diagnosis:**
```bash
uv run clickhouse-docs-index index 2>&1 | grep "Failed"
```

Most parsing errors are non-critical (missing metadata, malformed frontmatter).

### Search Returns Nothing

**Possible causes:**
1. Database not indexed: `make stats` should show document count
2. Query syntax: Try simpler queries first
3. Section filter wrong: Check available sections with `make stats`

### MCP Server Not Appearing

1. Check config syntax (valid JSON)
2. Verify absolute path in config
3. Restart Claude Desktop
4. Check logs: `~/Library/Logs/Claude/` (macOS)

## Code Quality Standards

- **British English** throughout (initialise, colour, etc.)
- **Type hints** on all functions/methods
- **Docstrings** in Google style
- **Line length:** 120 characters
- **Import order:** stdlib → third-party → local

Run before commit:
```bash
make build  # Must pass
```

## Reference Implementation

This project follows the architecture from:
`/Users/martoc/Developer/github.com/martoc/mcp-spark-documentation`

Key differences:
- MDX parsing (vs plain Markdown)
- Multi-directory structure
- Clean URLs (vs .html extensions)
- ClickHouse-specific metadata handling

## Contact & Resources

- **Repository:** https://github.com/martoc/mcp-clickhouse-documentation
- **ClickHouse Docs:** https://clickhouse.com/docs
- **FastMCP:** https://github.com/jlowin/fastmcp
- **MCP Spec:** https://modelcontextprotocol.io/

## Development Principles

1. **Keep it simple:** Prefer simple solutions over complex ones
2. **Test first:** Write tests for new features
3. **Document why:** Explain decisions, not just what
4. **British English:** Consistent language throughout
5. **Type safety:** Use type hints everywhere
6. **Explicit errors:** Handle errors explicitly, no silent failures
