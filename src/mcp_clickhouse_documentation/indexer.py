"""Indexer for ClickHouse documentation repository."""

import logging
import subprocess
from pathlib import Path

from mcp_clickhouse_documentation.database import DocumentDatabase
from mcp_clickhouse_documentation.parser import DocumentParser

logger = logging.getLogger(__name__)

CLICKHOUSE_REPO = "https://github.com/ClickHouse/clickhouse-docs.git"
DOCS_PATHS = ["docs", "knowledgebase"]


class DocumentationIndexer:
    """Indexes ClickHouse documentation from Git repository."""

    def __init__(self, db: DocumentDatabase, repo_path: Path) -> None:
        """Initialise indexer.

        Args:
            db: Database instance for storing documents
            repo_path: Path where repository will be cloned
        """
        self.db = db
        self.repo_path = repo_path
        self.parser: DocumentParser | None = None

    def clone_repository(self) -> None:
        """Clone ClickHouse documentation repository with sparse checkout."""
        if self.repo_path.exists():
            logger.info(f"Repository already exists at {self.repo_path}")
            return

        logger.info(f"Cloning ClickHouse docs to {self.repo_path}")

        # Create parent directory
        self.repo_path.parent.mkdir(parents=True, exist_ok=True)

        # Clone with sparse checkout
        subprocess.run(
            [
                "git",
                "clone",
                "--filter=blob:none",
                "--no-checkout",
                "--depth",
                "1",
                CLICKHOUSE_REPO,
                str(self.repo_path),
            ],
            check=True,
            capture_output=True,
        )

        # Configure sparse checkout
        subprocess.run(
            ["git", "-C", str(self.repo_path), "sparse-checkout", "set"] + DOCS_PATHS,
            check=True,
            capture_output=True,
        )

        # Checkout files
        subprocess.run(
            ["git", "-C", str(self.repo_path), "checkout"],
            check=True,
            capture_output=True,
        )

        logger.info("Repository cloned successfully")

    def index_documentation(self) -> tuple[int, int]:
        """Index all documentation files from the repository.

        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Repository not found at {self.repo_path}")

        self.parser = DocumentParser(self.repo_path)

        successful = 0
        failed = 0
        batch_size = 100
        document_batch: list = []

        # Index all documentation paths
        for docs_path_name in DOCS_PATHS:
            docs_path = self.repo_path / docs_path_name

            if not docs_path.exists():
                logger.warning(f"Documentation path not found: {docs_path}")
                continue

            logger.info(f"Indexing documentation from {docs_path_name}/")

            # Find all .md and .mdx files
            md_files = list(docs_path.rglob("*.md"))
            mdx_files = list(docs_path.rglob("*.mdx"))
            all_files = md_files + mdx_files

            logger.info(f"Found {len(all_files)} files in {docs_path_name}/ ({len(mdx_files)} MDX, {len(md_files)} MD)")

            for file_path in all_files:
                # Skip fragment/partial directories - they're reusable content, not standalone docs
                skip_patterns = ["_snippets", "_clients", "_partials", "_includes", "_components"]
                if any(pattern in str(file_path) for pattern in skip_patterns):
                    continue

                try:
                    doc = self.parser.parse_file(file_path)
                    document_batch.append(doc)
                    successful += 1

                    # Insert in batches for better performance
                    if len(document_batch) >= batch_size:
                        self.db.insert_documents_batch(document_batch)
                        document_batch = []
                        logger.info(f"Indexed {successful} documents...")

                except Exception as e:
                    logger.error(f"Failed to parse {file_path}: {e}")
                    failed += 1

            # Insert any remaining documents in the batch
            if document_batch:
                self.db.insert_documents_batch(document_batch)
                document_batch = []

        logger.info(f"Indexing complete: {successful} successful, {failed} failed")
        return successful, failed

    def update_repository(self) -> None:
        """Update existing repository to latest version."""
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Repository not found at {self.repo_path}")

        logger.info("Updating repository...")

        subprocess.run(
            ["git", "-C", str(self.repo_path), "pull", "--depth", "1"],
            check=True,
            capture_output=True,
        )

        logger.info("Repository updated successfully")
