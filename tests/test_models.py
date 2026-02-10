"""Tests for data models."""

from mcp_clickhouse_documentation.models import Document, DocumentMetadata, SearchResult


def test_document_metadata_creation() -> None:
    """Test DocumentMetadata creation."""
    metadata = DocumentMetadata(title="Test Title", description="Test Description")

    assert metadata.title == "Test Title"
    assert metadata.description == "Test Description"


def test_document_creation() -> None:
    """Test Document creation."""
    doc = Document(
        path="docs/test.md",
        title="Test Document",
        description="A test document",
        section="testing",
        url="https://example.com/test",
        content="# Test\n\nContent here.",
    )

    assert doc.path == "docs/test.md"
    assert doc.title == "Test Document"
    assert doc.description == "A test document"
    assert doc.section == "testing"
    assert doc.url == "https://example.com/test"
    assert doc.content == "# Test\n\nContent here."


def test_search_result_creation() -> None:
    """Test SearchResult creation."""
    result = SearchResult(
        path="docs/test.md",
        title="Test Document",
        url="https://example.com/test",
        section="testing",
        snippet="This is a [test] snippet...",
        relevance_score=0.95,
    )

    assert result.path == "docs/test.md"
    assert result.title == "Test Document"
    assert result.url == "https://example.com/test"
    assert result.section == "testing"
    assert result.snippet == "This is a [test] snippet..."
    assert result.relevance_score == 0.95
