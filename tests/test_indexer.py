"""Tests for documentation indexer."""

from pathlib import Path

import pytest

from mcp_clickhouse_documentation.database import DocumentDatabase
from mcp_clickhouse_documentation.indexer import DocumentationIndexer


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """Create temporary repository structure."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    return repo_path


@pytest.fixture
def temp_db(tmp_path: Path) -> DocumentDatabase:
    """Create temporary database."""
    db_path = tmp_path / "test.db"
    return DocumentDatabase(db_path)


def test_snippet_files_are_skipped(temp_repo: Path, temp_db: DocumentDatabase) -> None:
    """Test that snippet files are skipped during indexing."""
    # Create test structure
    docs_path = temp_repo / "docs"
    docs_path.mkdir()

    # Create a regular doc file
    regular_file = docs_path / "regular.md"
    regular_file.write_text(
        """---
title: Regular Document
description: A normal doc
---

# Regular Document

Content here.
"""
    )

    # Create a snippet file (should be skipped)
    snippets_dir = docs_path / "_snippets"
    snippets_dir.mkdir()
    snippet_file = snippets_dir / "_example.md"
    snippet_file.write_text(
        """---
title: Snippet
---

Snippet content.
"""
    )

    # Create knowledgebase with snippet (should also be skipped)
    kb_path = temp_repo / "knowledgebase"
    kb_path.mkdir()
    kb_snippets = kb_path / "_snippets"
    kb_snippets.mkdir()
    kb_snippet = kb_snippets / "_another.md"
    kb_snippet.write_text("Content without frontmatter")

    # Create normal knowledgebase file
    kb_file = kb_path / "guide.md"
    kb_file.write_text(
        """---
title: Guide
description: A guide
---

# Guide

Guide content.
"""
    )

    # Index documentation
    indexer = DocumentationIndexer(temp_db, temp_repo)
    successful, failed = indexer.index_documentation()

    # Should index only the 2 regular files, skip 2 snippet files
    assert successful == 2
    assert failed == 0
    assert temp_db.count() == 2

    # Verify the indexed documents
    docs = [temp_db.get_document("docs/regular.md"), temp_db.get_document("knowledgebase/guide.md")]

    assert docs[0] is not None
    assert docs[0].title == "Regular Document"

    assert docs[1] is not None
    assert docs[1].title == "Guide"

    # Verify snippet files were not indexed
    assert temp_db.get_document("docs/_snippets/_example.md") is None
    assert temp_db.get_document("knowledgebase/_snippets/_another.md") is None


def test_files_named_with_underscore_but_not_in_snippets_are_indexed(
    temp_repo: Path, temp_db: DocumentDatabase
) -> None:
    """Test that files starting with underscore but not in _snippets/ are still indexed."""
    docs_path = temp_repo / "docs"
    docs_path.mkdir()

    # Create file starting with underscore but not in _snippets directory
    underscore_file = docs_path / "_important.md"
    underscore_file.write_text(
        """---
title: Important Document
description: Important
---

Important content.
"""
    )

    # Index documentation
    indexer = DocumentationIndexer(temp_db, temp_repo)
    successful, failed = indexer.index_documentation()

    # Should index the file (it's not in _snippets/)
    assert successful == 1
    assert failed == 0
    assert temp_db.count() == 1

    doc = temp_db.get_document("docs/_important.md")
    assert doc is not None
    assert doc.title == "Important Document"
