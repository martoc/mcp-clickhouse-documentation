"""Data models for ClickHouse documentation."""

from dataclasses import dataclass


@dataclass
class DocumentMetadata:
    """Metadata extracted from document frontmatter."""

    title: str
    description: str


@dataclass
class Document:
    """Represents a parsed documentation file."""

    path: str
    title: str
    description: str
    section: str
    url: str
    content: str


@dataclass
class SearchResult:
    """Result from a documentation search."""

    path: str
    title: str
    url: str
    section: str
    snippet: str
    relevance_score: float
