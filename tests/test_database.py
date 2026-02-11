"""Tests for database operations."""

from pathlib import Path

import pytest

from mcp_clickhouse_documentation.database import DocumentDatabase
from mcp_clickhouse_documentation.models import Document


@pytest.fixture
def db(tmp_path: Path) -> DocumentDatabase:
    """Create test database."""
    db_path = tmp_path / "test.db"
    return DocumentDatabase(db_path)


@pytest.fixture
def sample_document() -> Document:
    """Create sample document."""
    return Document(
        path="docs/en/sql-reference/select.md",
        title="SELECT Statement",
        description="Query data from tables",
        section="sql-reference",
        url="https://clickhouse.com/docs/en/sql-reference/select",
        content="# SELECT Statement\n\nThe SELECT statement retrieves data from tables.",
    )


def test_insert_document(db: DocumentDatabase, sample_document: Document) -> None:
    """Test inserting a document."""
    db.insert_document(sample_document)
    assert db.count() == 1

    # Retrieve and verify
    doc = db.get_document(sample_document.path)
    assert doc is not None
    assert doc.title == sample_document.title
    assert doc.content == sample_document.content


def test_insert_document_replaces_existing(db: DocumentDatabase, sample_document: Document) -> None:
    """Test that inserting with same path replaces existing document."""
    db.insert_document(sample_document)
    assert db.count() == 1

    # Update document
    updated_doc = Document(
        path=sample_document.path,
        title="Updated Title",
        description="Updated description",
        section=sample_document.section,
        url=sample_document.url,
        content="Updated content",
    )
    db.insert_document(updated_doc)

    # Should still have only one document
    assert db.count() == 1

    # Verify updated content
    doc = db.get_document(sample_document.path)
    assert doc is not None
    assert doc.title == "Updated Title"
    assert doc.content == "Updated content"


def test_get_document_not_found(db: DocumentDatabase) -> None:
    """Test getting non-existent document returns None."""
    doc = db.get_document("non/existent/path.md")
    assert doc is None


def test_search_basic(db: DocumentDatabase) -> None:
    """Test basic search functionality."""
    # Insert test documents
    docs = [
        Document(
            path="docs/select.md",
            title="SELECT Statement",
            description="Query data",
            section="sql-reference",
            url="https://example.com/select",
            content="The SELECT statement retrieves data from tables using SQL queries.",
        ),
        Document(
            path="docs/insert.md",
            title="INSERT Statement",
            description="Insert data",
            section="sql-reference",
            url="https://example.com/insert",
            content="The INSERT statement adds new rows to tables.",
        ),
        Document(
            path="docs/kafka.md",
            title="Kafka Integration",
            description="Connect to Kafka",
            section="integrations",
            url="https://example.com/kafka",
            content="Learn how to integrate ClickHouse with Apache Kafka for streaming data.",
        ),
    ]

    for doc in docs:
        db.insert_document(doc)

    # Search for "SELECT"
    results = db.search("SELECT")
    assert len(results) > 0
    assert any("SELECT" in r.title for r in results)

    # Search for "Kafka"
    results = db.search("Kafka")
    assert len(results) > 0
    assert any("Kafka" in r.title for r in results)


def test_search_with_section_filter(db: DocumentDatabase) -> None:
    """Test search with section filtering."""
    docs = [
        Document(
            path="docs/select.md",
            title="SELECT Query",
            description="SQL SELECT",
            section="sql-reference",
            url="https://example.com/select",
            content="SELECT statement documentation",
        ),
        Document(
            path="kb/select.md",
            title="SELECT Examples",
            description="Query examples",
            section="knowledgebase",
            url="https://example.com/kb-select",
            content="SELECT query examples and best practices",
        ),
    ]

    for doc in docs:
        db.insert_document(doc)

    # Search in sql-reference section only
    results = db.search("SELECT", section="sql-reference")
    assert len(results) == 1
    assert results[0].section == "sql-reference"

    # Search in knowledgebase section only
    results = db.search("SELECT", section="knowledgebase")
    assert len(results) == 1
    assert results[0].section == "knowledgebase"


def test_search_with_limit(db: DocumentDatabase) -> None:
    """Test search result limiting."""
    # Insert multiple documents
    for i in range(20):
        doc = Document(
            path=f"docs/doc{i}.md",
            title=f"Document {i}",
            description="Test document",
            section="test",
            url=f"https://example.com/doc{i}",
            content="This is a test document with common search terms.",
        )
        db.insert_document(doc)

    # Search with limit
    results = db.search("test", limit=5)
    assert len(results) == 5


def test_search_relevance_ranking(db: DocumentDatabase) -> None:
    """Test that search results are ranked by relevance."""
    docs = [
        Document(
            path="docs/exact.md",
            title="SELECT Statement Reference",
            description="SELECT in ClickHouse",
            section="sql",
            url="https://example.com/exact",
            content="SELECT SELECT SELECT ClickHouse queries with multiple SELECT statements",
        ),
        Document(
            path="docs/partial.md",
            title="Query Guide",
            description="General queries",
            section="sql",
            url="https://example.com/partial",
            content="This document mentions querying once.",
        ),
    ]

    for doc in docs:
        db.insert_document(doc)

    results = db.search("SELECT")
    assert len(results) >= 1

    # Document with SELECT in title and multiple times in content should be first
    assert results[0].path == "docs/exact.md"
    assert results[0].relevance_score > 0


def test_search_snippet_highlights_matches(db: DocumentDatabase, sample_document: Document) -> None:
    """Test that search snippets highlight matched terms."""
    db.insert_document(sample_document)

    results = db.search("SELECT")
    assert len(results) > 0

    # Snippet should contain highlighted term in [brackets]
    snippet = results[0].snippet
    assert "[" in snippet and "]" in snippet


def test_clear_database(db: DocumentDatabase, sample_document: Document) -> None:
    """Test clearing all documents."""
    db.insert_document(sample_document)
    assert db.count() == 1

    db.clear()
    assert db.count() == 0


def test_count_documents(db: DocumentDatabase) -> None:
    """Test counting documents."""
    assert db.count() == 0

    for i in range(5):
        doc = Document(
            path=f"docs/doc{i}.md",
            title=f"Doc {i}",
            description="Test",
            section="test",
            url=f"https://example.com/{i}",
            content="Content",
        )
        db.insert_document(doc)

    assert db.count() == 5


def test_get_sections(db: DocumentDatabase) -> None:
    """Test getting sections with counts."""
    # Insert documents in different sections
    sections_data = [
        ("sql-reference", 5),
        ("integrations", 3),
        ("knowledgebase", 2),
    ]

    for section, count in sections_data:
        for i in range(count):
            doc = Document(
                path=f"{section}/doc{i}.md",
                title=f"Doc {i}",
                description="Test",
                section=section,
                url=f"https://example.com/{section}/{i}",
                content="Content",
            )
            db.insert_document(doc)

    sections = db.get_sections()

    # Should be ordered by count descending
    assert len(sections) == 3
    assert sections[0] == ("sql-reference", 5)
    assert sections[1] == ("integrations", 3)
    assert sections[2] == ("knowledgebase", 2)


def test_fts_synchronisation(db: DocumentDatabase) -> None:
    """Test that FTS table stays synchronised with main table."""
    doc = Document(
        path="docs/test.md",
        title="Test Document",
        description="Test",
        section="test",
        url="https://example.com/test",
        content="Searchable content here",
    )

    # Insert
    db.insert_document(doc)
    results = db.search("Searchable")
    assert len(results) == 1

    # Update
    doc.content = "Updated searchable content"
    db.insert_document(doc)
    results = db.search("Updated")
    assert len(results) == 1

    # Old content should not be found
    results = db.search("here")
    assert len(results) == 0


def test_insert_documents_batch(db: DocumentDatabase) -> None:
    """Test batch insert of multiple documents."""
    docs = [
        Document(
            path=f"docs/test{i}.md",
            title=f"Test Document {i}",
            description=f"Description {i}",
            section="test",
            url=f"https://example.com/test{i}",
            content=f"Content for document {i}",
        )
        for i in range(10)
    ]

    db.insert_documents_batch(docs)
    assert db.count() == 10

    # Verify all documents are searchable
    for i in range(10):
        doc = db.get_document(f"docs/test{i}.md")
        assert doc is not None
        assert doc.title == f"Test Document {i}"


def test_insert_documents_batch_empty(db: DocumentDatabase) -> None:
    """Test batch insert with empty list."""
    db.insert_documents_batch([])
    assert db.count() == 0
