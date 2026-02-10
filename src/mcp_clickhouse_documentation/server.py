"""FastMCP server for ClickHouse documentation search."""

import logging
from pathlib import Path

from fastmcp import FastMCP

from mcp_clickhouse_documentation.database import DocumentDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialise MCP server
mcp = FastMCP("ClickHouse Documentation")

# Database path
DB_PATH = Path.home() / ".cache" / "mcp-clickhouse-documentation" / "docs.db"

# Initialise database
db = DocumentDatabase(DB_PATH)


@mcp.tool()
def search_documentation(query: str, section: str | None = None, limit: int = 10) -> list[dict[str, str | float]]:
    """Search ClickHouse documentation using full-text search.

    This tool searches the official ClickHouse documentation and knowledge base
    using BM25 ranking for relevance. Results include snippets with matched terms
    highlighted in [brackets].

    Args:
        query: Search query (supports full-text search syntax)
        section: Optional section filter (e.g., "sql-reference", "knowledgebase-integrations")
        limit: Maximum number of results to return (default: 10)

    Returns:
        List of search results with title, URL, path, section, snippet, and relevance score
    """
    try:
        results = db.search(query, section, limit)

        return [
            {
                "title": r.title,
                "url": r.url,
                "path": r.path,
                "section": r.section,
                "snippet": r.snippet,
                "relevance_score": r.relevance_score,
            }
            for r in results
        ]
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []


@mcp.tool()
def read_documentation(path: str) -> dict[str, str]:
    """Read full content of a ClickHouse documentation page.

    Retrieves the complete content of a documentation page by its path.
    Use paths returned from search_documentation results.

    Args:
        path: Document path (e.g., "docs/en/sql-reference/statements/select.md")

    Returns:
        Dictionary with path, title, description, section, URL, and full content
    """
    try:
        doc = db.get_document(path)

        if not doc:
            return {"error": f"Document not found: {path}"}

        return {
            "path": doc.path,
            "title": doc.title,
            "description": doc.description,
            "section": doc.section,
            "url": doc.url,
            "content": doc.content,
        }
    except Exception as e:
        logger.error(f"Read failed: {e}")
        return {"error": str(e)}


def main() -> None:
    """Run the MCP server."""
    # Check if database exists
    if not DB_PATH.exists():
        logger.warning(
            f"Database not found at {DB_PATH}. "
            "Please run 'clickhouse-docs-index index' to index the documentation first."
        )

    # Run server
    mcp.run()


if __name__ == "__main__":
    main()
