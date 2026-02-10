# Usage Guide

Comprehensive guide for using the MCP ClickHouse Documentation Server.

## Installation

### Prerequisites

- Python 3.12 or higher
- uv package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Git

### Setup

```bash
# Clone repository
git clone https://github.com/martoc/mcp-clickhouse-documentation.git
cd mcp-clickhouse-documentation

# Initialise development environment
make init

# Index ClickHouse documentation (first time only)
make index
```

This will:
1. Install dependencies via uv
2. Clone ClickHouse docs repository (sparse checkout)
3. Parse and index ~500-1000 documentation files
4. Create SQLite database with FTS5 index

### Docker Installation (Recommended)

Use the pre-built container with documentation already indexed:

```bash
# Pull the latest image
docker pull martoc/mcp-clickhouse-documentation:latest

# Test the server
docker run --rm -i martoc/mcp-clickhouse-documentation:latest
```

**Advantages:**
- ✅ No local dependencies needed (only Docker)
- ✅ Documentation pre-indexed and ready to use
- ✅ Consistent environment across platforms
- ✅ Automatic updates with new releases

## MCP Integration

### Claude Desktop

Edit your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

Add the server configuration:

```json
{
  "mcpServers": {
    "clickhouse-documentation": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-clickhouse-documentation",
        "run",
        "mcp-clickhouse-documentation"
      ]
    }
  }
}
```

**Important:** Use absolute path, not relative path.

**Docker Configuration (Alternative):**

```json
{
  "mcpServers": {
    "clickhouse-documentation": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "martoc/mcp-clickhouse-documentation:latest"
      ]
    }
  }
}
```

**Benefits of Docker:**
- No local Python/uv installation required
- Pre-indexed documentation (instant startup)
- Isolated environment
- Easy updates (`docker pull`)

Restart Claude Desktop after configuration.

### Claude Code

The server is automatically available in Claude Code when configured in Claude Desktop.

## Using the Tools

### Search Documentation

**Natural language:**
- "Search ClickHouse docs for SELECT statement"
- "Find information about Kafka integration"
- "How do I create a MergeTree table?"

**Direct tool call:**
```json
{
  "tool": "search_documentation",
  "arguments": {
    "query": "SELECT DISTINCT",
    "limit": 5
  }
}
```

**With section filter:**
```json
{
  "tool": "search_documentation",
  "arguments": {
    "query": "Kafka",
    "section": "knowledgebase-integrations",
    "limit": 10
  }
}
```

### Read Full Document

After searching, read the complete document:

**Natural language:**
- "Read the full SELECT reference"
- "Show me the complete Kafka integration guide"

**Direct tool call:**
```json
{
  "tool": "read_documentation",
  "arguments": {
    "path": "docs/en/sql-reference/statements/select.md"
  }
}
```

## Common Sections

Use these section identifiers for filtering:

- `sql-reference` - SQL statements and functions
- `operations` - Server operations and configuration
- `engines` - Table engines (MergeTree, etc.)
- `interfaces` - Client interfaces (HTTP, JDBC, etc.)
- `knowledgebase-integrations` - Integration guides (Kafka, Spark, etc.)
- `development` - Development and contribution guides

### Finding Available Sections

```bash
# View all sections with document counts
make stats
```

## Command-Line Interface

The package includes a CLI tool for managing the documentation index.

### Index Documentation

```bash
# Initial indexing
uv run clickhouse-docs-index index

# Force re-index (clears and rebuilds)
uv run clickhouse-docs-index index --force
```

### View Statistics

```bash
# Show document counts by section
uv run clickhouse-docs-index stats
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

### Clear Index

```bash
# Remove all indexed documents
uv run clickhouse-docs-index clear
```

## Search Tips

### Basic Search

```
"SELECT statement"
```

Searches for documents containing both "SELECT" and "statement".

### Phrase Search

```
"exact phrase match"
```

Searches for the exact phrase.

### Boolean Operators

```
"SELECT AND DISTINCT"
"Kafka OR Confluent"
"table NOT temporary"
```

### Wildcard Search

```
"ARRAY*"
```

Matches ARRAY, ARRAYS, ARRAY_JOIN, etc.

### Section-Specific Search

Limit search to specific documentation areas:

```json
{
  "query": "monitoring",
  "section": "operations"
}
```

## Example Workflows

### Learning SQL Functions

1. Search for function category:
   ```
   "Search for string functions"
   ```

2. Read specific function:
   ```
   "Read the substring function documentation"
   ```

### Setting Up Integration

1. Search for integration:
   ```
   "Search for Kafka integration"
   ```

2. Read integration guide:
   ```
   "Read the full Kafka integration guide"
   ```

### Troubleshooting

1. Search for error message:
   ```
   "Search for 'memory limit exceeded'"
   ```

2. Read troubleshooting guide:
   ```
   "Read the memory configuration docs"
   ```

## Updating Documentation

Keep the index up to date with the latest ClickHouse documentation:

```bash
# Update repository and re-index
cd ~/.cache/mcp-clickhouse-documentation/clickhouse-docs
git pull
cd -
make index
```

Or force a complete refresh:

```bash
make index --force
```

## Advanced Configuration

### Custom Database Location

Set environment variable before indexing:

```bash
export MCP_CLICKHOUSE_DB_PATH="$HOME/custom/path/docs.db"
make index
```

### Custom Repository Location

Edit `src/mcp_clickhouse_documentation/cli.py`:

```python
REPO_PATH = Path("/custom/path/clickhouse-docs")
```

## Performance

### Index Size

- **Repository:** ~10MB (sparse checkout)
- **Database:** ~5-10MB (depends on document count)
- **Total:** ~15-20MB

### Search Speed

- **Typical search:** <100ms
- **Complex queries:** <500ms
- **Document retrieval:** <10ms

### Memory Usage

- **Indexing:** ~200-300MB
- **Server runtime:** ~50-100MB

## Troubleshooting

### Server Not Appearing in Claude

1. Check configuration file syntax (valid JSON)
2. Verify absolute path is correct
3. Restart Claude Desktop
4. Check Claude Desktop logs

### Search Returns No Results

```bash
# Verify database exists
ls -lh ~/.cache/mcp-clickhouse-documentation/docs.db

# Check document count
make stats

# Re-index if needed
make index --force
```

### Parser Errors During Indexing

Check logs for specific files:
```bash
uv run clickhouse-docs-index index 2>&1 | grep "Failed to parse"
```

Most parsing errors are non-critical and can be ignored.

### Permission Errors

```bash
# Ensure cache directory is writable
chmod -R u+w ~/.cache/mcp-clickhouse-documentation/
```

## Development Usage

### Running Tests

```bash
# All tests
make test

# Specific test file
uv run pytest tests/test_parser.py -v

# With coverage
uv run pytest --cov=src/mcp_clickhouse_documentation
```

### Running Server Directly

```bash
# Start MCP server in stdio mode
make run

# Or with uv
uv run mcp-clickhouse-documentation
```

### Debugging

Enable debug logging:

```python
# In server.py or cli.py
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

1. **Index once** - Run `make index` once after installation
2. **Update periodically** - Update index monthly for latest docs
3. **Use sections** - Filter by section for faster, more relevant results
4. **Iterate searches** - Start broad, then narrow with section filters
5. **Read full docs** - Use search to find, then read complete documentation

## Support

For issues, questions, or contributions:

- GitHub Issues: https://github.com/martoc/mcp-clickhouse-documentation/issues
- ClickHouse Docs: https://clickhouse.com/docs
- MCP Documentation: https://modelcontextprotocol.io/

## See Also

- [README.md](README.md) - Project overview
- [CODESTYLE.md](CODESTYLE.md) - Coding standards
- [CLAUDE.md](CLAUDE.md) - Claude-specific context
