"""Command-line interface for ClickHouse documentation indexer."""

import argparse
import logging
import sys
from pathlib import Path

from mcp_clickhouse_documentation.database import DocumentDatabase
from mcp_clickhouse_documentation.indexer import DocumentationIndexer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Paths
DB_PATH = Path.home() / ".cache" / "mcp-clickhouse-documentation" / "docs.db"
REPO_PATH = Path.home() / ".cache" / "mcp-clickhouse-documentation" / "clickhouse-docs"


def cmd_index(args: argparse.Namespace) -> int:
    """Index ClickHouse documentation.

    Args:
        args: Command arguments

    Returns:
        Exit code
    """
    db = DocumentDatabase(DB_PATH)
    indexer = DocumentationIndexer(db, REPO_PATH)

    try:
        # Clone repository if needed
        if not REPO_PATH.exists() or args.force:
            if args.force and REPO_PATH.exists():
                logger.info("Removing existing repository...")
                import shutil

                shutil.rmtree(REPO_PATH)
                db.clear()

            indexer.clone_repository()
        else:
            logger.info("Repository already exists, updating...")
            indexer.update_repository()

        # Index documentation
        successful, failed = indexer.index_documentation()

        logger.info(f"Indexing complete: {successful} documents indexed, {failed} failed")

        if failed > 0:
            logger.warning(f"{failed} documents failed to index")

        return 0

    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        return 1


def cmd_stats(args: argparse.Namespace) -> int:
    """Show indexing statistics.

    Args:
        args: Command arguments

    Returns:
        Exit code
    """
    if not DB_PATH.exists():
        logger.error(f"Database not found at {DB_PATH}")
        logger.info("Run 'clickhouse-docs-index index' to create the index")
        return 1

    db = DocumentDatabase(DB_PATH)

    try:
        total = db.count()
        sections = db.get_sections()

        print("\nClickHouse Documentation Index Statistics")
        print(f"{'=' * 50}")
        print(f"Total documents: {total}")
        print("\nDocuments by section:")
        print(f"{'-' * 50}")

        for section, count in sections:
            percentage = (count / total * 100) if total > 0 else 0
            print(f"  {section:30s} {count:5d} ({percentage:5.1f}%)")

        print(f"{'=' * 50}\n")

        return 0

    except Exception as e:
        logger.error(f"Failed to retrieve statistics: {e}")
        return 1


def cmd_clear(args: argparse.Namespace) -> int:
    """Clear the documentation index.

    Args:
        args: Command arguments

    Returns:
        Exit code
    """
    if not DB_PATH.exists():
        logger.info("No database to clear")
        return 0

    db = DocumentDatabase(DB_PATH)

    try:
        count = db.count()
        db.clear()
        logger.info(f"Cleared {count} documents from index")
        return 0

    except Exception as e:
        logger.error(f"Failed to clear database: {e}")
        return 1


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="ClickHouse documentation indexer")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Index command
    index_parser = subparsers.add_parser("index", help="Index ClickHouse documentation")
    index_parser.add_argument("--force", action="store_true", help="Force re-clone and re-index")

    # Stats command
    subparsers.add_parser("stats", help="Show indexing statistics")

    # Clear command
    subparsers.add_parser("clear", help="Clear the documentation index")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == "index":
        sys.exit(cmd_index(args))
    elif args.command == "stats":
        sys.exit(cmd_stats(args))
    elif args.command == "clear":
        sys.exit(cmd_clear(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
