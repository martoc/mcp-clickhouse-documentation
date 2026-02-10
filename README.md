# MCP ClickHouse Documentation Server

Model Context Protocol (MCP) server that enables Claude to search and read official ClickHouse documentation. Built with FastMCP and SQLite FTS5 for efficient full-text search with BM25 ranking.

## Features

- **Full-text search** across ClickHouse docs and knowledge base
- **MDX parsing** - Handles Docusaurus MDX files with JSX components
- **BM25 ranking** - Relevance-ranked search results
- **Section filtering** - Search within specific documentation sections
- **Multi-directory indexing** - Covers both `docs/` and `knowledgebase/`
- **Fast MCP integration** - Ready for Claude Desktop and Claude Code

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/martoc/mcp-clickhouse-documentation.git
cd mcp-clickhouse-documentation

# Initialise development environment
make init

# Index ClickHouse documentation
make index
```

### MCP Configuration

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "clickhouse-documentation": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-clickhouse-documentation",
        "run",
        "mcp-clickhouse-documentation"
      ]
    }
  }
}
```

### Usage

Once configured, Claude can:

1. **Search documentation:**
   - "Search ClickHouse docs for SELECT statement"
   - "Find information about Kafka integration"
   - "How do I use ARRAY functions?"

2. **Read full documents:**
   - "Read the complete SELECT reference"
   - "Show me the full Kafka integration guide"

## Tools

The MCP server provides two tools:

### `search_documentation`

Search ClickHouse documentation with full-text search.

**Parameters:**
- `query` (required): Search query
- `section` (optional): Filter by section (e.g., "sql-reference", "knowledgebase-integrations")
- `limit` (optional): Maximum results (default: 10)

**Returns:**
- `title`: Document title
- `url`: Full documentation URL
- `path`: Relative file path
- `section`: Documentation section
- `snippet`: Content snippet with highlighted matches
- `relevance_score`: BM25 relevance score

### `read_documentation`

Read full content of a documentation page.

**Parameters:**
- `path` (required): Document path from search results

**Returns:**
- `path`: Document path
- `title`: Document title
- `description`: Document description
- `section`: Documentation section
- `url`: Full documentation URL
- `content`: Complete document content (cleaned MDX/Markdown)

## Architecture

```
mcp-clickhouse-documentation/
├── src/mcp_clickhouse_documentation/
│   ├── models.py          # Data models
│   ├── parser.py          # MDX/Markdown parser
│   ├── database.py        # SQLite FTS5 operations
│   ├── indexer.py         # Documentation indexer
│   ├── server.py          # FastMCP server
│   └── cli.py             # Command-line interface
├── tests/                 # Test suite
├── Makefile               # Build automation
└── pyproject.toml         # Project configuration
```

## Development

### Prerequisites

- Python 3.12+
- uv package manager
- Git

### Commands

```bash
# Initialise environment
make init

# Run tests
make test

# Run linting and type checking
make build

# Format code
make format

# Index documentation
make index

# View statistics
make stats

# Run MCP server
make run

# Clean artifacts
make clean
```

### Testing

```bash
# Run all tests with coverage
make test

# Run specific test file
uv run pytest tests/test_parser.py -v

# Run with coverage report
uv run pytest --cov=src/mcp_clickhouse_documentation --cov-report=html
```

## Technical Details

### MDX Parsing

The parser handles Docusaurus MDX files by:
1. Extracting YAML frontmatter (title, description)
2. Removing JSX imports and exports
3. Stripping JSX components and expressions
4. Cleaning HTML tags and comments
5. Preserving Markdown formatting

### Database Schema

SQLite with FTS5 virtual table:
- **Main table:** `documents` - Stores complete document data
- **FTS table:** `documents_fts` - Full-text search index
- **BM25 ranking:** Title (5.0), Description (2.0), Content (1.0)
- **Triggers:** Automatic synchronisation between tables

### Repository Indexing

- **Sparse checkout:** Only clones `docs/` and `knowledgebase/` directories
- **Shallow clone:** Uses `--depth 1` for faster cloning
- **File types:** Indexes both `.md` and `.mdx` files
- **URL pattern:** Matches ClickHouse docs clean URLs (no extensions)

## Statistics

After indexing, view statistics:

```bash
make stats
```

Example output:
```
ClickHouse Documentation Index Statistics
==================================================
Total documents: 856

Documents by section:
--------------------------------------------------
  sql-reference                   324 ( 37.9%)
  operations                      156 ( 18.2%)
  knowledgebase-integrations      128 ( 15.0%)
  engines                          98 ( 11.4%)
  interfaces                       87 ( 10.2%)
  development                      63 (  7.4%)
==================================================
```

## Troubleshooting

### Database not found

```bash
# Re-index documentation
make index --force
```

### Search returns no results

```bash
# Check database statistics
make stats

# Verify database exists
ls -lh ~/.cache/mcp-clickhouse-documentation/
```

### Parser errors

Check logs for specific file parsing errors:
```bash
# Run indexer with verbose logging
uv run clickhouse-docs-index index
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make build`
5. Submit a pull request

## Licence

MIT Licence - see LICENCE file for details.

## See Also

- [ClickHouse Documentation](https://clickhouse.com/docs)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [Model Context Protocol](https://modelcontextprotocol.io/)
