"""Tests for MDX/Markdown parser."""

from pathlib import Path

import pytest

from mcp_clickhouse_documentation.parser import DocumentParser


@pytest.fixture
def temp_docs_root(tmp_path: Path) -> Path:
    """Create temporary documentation root."""
    return tmp_path


@pytest.fixture
def parser(temp_docs_root: Path) -> DocumentParser:
    """Create parser instance."""
    return DocumentParser(temp_docs_root)


def test_clean_content_removes_mdx_imports(parser: DocumentParser) -> None:
    """Test that import statements are removed."""
    content = """
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Heading

Some content here.
"""
    cleaned = parser._clean_content(content)
    assert "import" not in cleaned
    assert "from" not in cleaned.split("\n")[0]  # First line should not have import
    assert "# Heading" in cleaned
    assert "Some content here" in cleaned


def test_clean_content_removes_mdx_exports(parser: DocumentParser) -> None:
    """Test that export statements are removed."""
    content = """
export const foo = 'bar';
export default SomeComponent;

# Content
"""
    cleaned = parser._clean_content(content)
    assert "export" not in cleaned
    assert "# Content" in cleaned


def test_clean_content_removes_jsx_self_closing(parser: DocumentParser) -> None:
    """Test that JSX self-closing tags are removed."""
    content = """
# Example

<CloudNotSupportedBadge />

Some text here.

<VersionBadge minVersion="23.8" />
"""
    cleaned = parser._clean_content(content)
    assert "<CloudNotSupportedBadge" not in cleaned
    assert "<VersionBadge" not in cleaned
    assert "# Example" in cleaned
    assert "Some text here" in cleaned


def test_clean_content_removes_jsx_paired_tags(parser: DocumentParser) -> None:
    """Test that JSX paired tags are removed."""
    content = """
# Title

<Tabs>
<TabItem value="js" label="JavaScript">
Code here
</TabItem>
<TabItem value="py" label="Python">
More code
</TabItem>
</Tabs>

After tabs.
"""
    cleaned = parser._clean_content(content)
    assert "<Tabs" not in cleaned
    assert "<TabItem" not in cleaned
    assert "</Tabs>" not in cleaned
    assert "# Title" in cleaned
    assert "Code here" in cleaned
    assert "More code" in cleaned
    assert "After tabs" in cleaned


def test_clean_content_removes_jsx_expressions(parser: DocumentParser) -> None:
    """Test that JSX expressions in braces are removed."""
    content = """
# Example

This is {someVariable} in text.

{/* This is a comment */}

More text.
"""
    cleaned = parser._clean_content(content)
    assert "{someVariable}" not in cleaned
    assert "{/*" not in cleaned
    assert "# Example" in cleaned
    assert "More text" in cleaned


def test_clean_content_removes_html_comments(parser: DocumentParser) -> None:
    """Test that HTML comments are removed."""
    content = """
# Title

<!-- This is a comment -->

Content here.

<!-- Multi-line
comment
here -->

More content.
"""
    cleaned = parser._clean_content(content)
    assert "<!--" not in cleaned
    assert "-->" not in cleaned
    assert "# Title" in cleaned
    assert "Content here" in cleaned
    assert "More content" in cleaned


def test_clean_content_removes_html_tags(parser: DocumentParser) -> None:
    """Test that HTML tags are removed."""
    content = """
# Title

<div class="container">
Content in div
</div>

<span style="color: red">Red text</span>
"""
    cleaned = parser._clean_content(content)
    assert "<div" not in cleaned
    assert "</div>" not in cleaned
    assert "<span" not in cleaned
    assert "# Title" in cleaned
    assert "Content in div" in cleaned
    assert "Red text" in cleaned


def test_clean_content_preserves_markdown(parser: DocumentParser) -> None:
    """Test that standard markdown is preserved."""
    content = """
# Heading 1

## Heading 2

This is **bold** and *italic* text.

- List item 1
- List item 2

```sql
SELECT * FROM table;
```

[Link text](https://example.com)

| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
"""
    cleaned = parser._clean_content(content)
    assert "# Heading 1" in cleaned
    assert "## Heading 2" in cleaned
    assert "**bold**" in cleaned
    assert "*italic*" in cleaned
    assert "- List item 1" in cleaned
    assert "```sql" in cleaned
    assert "SELECT * FROM table" in cleaned
    assert "[Link text]" in cleaned
    assert "| Column 1 |" in cleaned


def test_clean_content_cleans_excessive_whitespace(parser: DocumentParser) -> None:
    """Test that excessive whitespace is cleaned."""
    content = """
# Title


Content here.



More content.
"""
    cleaned = parser._clean_content(content)
    # Should have at most double newlines
    assert "\n\n\n" not in cleaned
    assert "# Title" in cleaned
    assert "Content here" in cleaned


def test_parse_mdx_file_with_frontmatter(temp_docs_root: Path) -> None:
    """Test parsing a complete MDX file with frontmatter."""
    # Create test file
    file_path = temp_docs_root / "docs" / "en" / "sql-reference" / "select.mdx"
    file_path.parent.mkdir(parents=True, exist_ok=True)

    content = """---
title: SELECT Statement
description: Query data from tables
sidebar_label: SELECT
---

import Tabs from '@theme/Tabs';

# SELECT Statement

<CloudNotSupportedBadge />

The SELECT statement retrieves data.

## Syntax

```sql
SELECT * FROM table;
```
"""

    file_path.write_text(content)

    # Parse file
    parser = DocumentParser(temp_docs_root)
    doc = parser.parse_file(file_path)

    # Verify metadata
    assert doc.title == "SELECT Statement"
    assert doc.description == "Query data from tables"
    assert doc.path == "docs/en/sql-reference/select.mdx"
    assert doc.section == "sql-reference"  # Language code skipped
    assert doc.url == "https://clickhouse.com/docs/docs/en/sql-reference/select"

    # Verify content cleaning
    assert "import" not in doc.content
    assert "<CloudNotSupportedBadge" not in doc.content
    assert "# SELECT Statement" in doc.content
    assert "```sql" in doc.content
    assert "SELECT * FROM table" in doc.content


def test_parse_md_file(temp_docs_root: Path) -> None:
    """Test parsing a standard Markdown file."""
    file_path = temp_docs_root / "knowledgebase" / "integrations" / "kafka.md"
    file_path.parent.mkdir(parents=True, exist_ok=True)

    content = """---
title: Kafka Integration
description: Connect ClickHouse to Kafka
---

# Kafka Integration

This guide shows how to integrate with Kafka.
"""

    file_path.write_text(content)

    parser = DocumentParser(temp_docs_root)
    doc = parser.parse_file(file_path)

    assert doc.title == "Kafka Integration"
    assert doc.description == "Connect ClickHouse to Kafka"
    assert doc.path == "knowledgebase/integrations/kafka.md"
    assert doc.section == "knowledgebase-integrations"
    assert doc.url == "https://clickhouse.com/docs/knowledgebase/integrations/kafka"


def test_compute_url_clickhouse_pattern(parser: DocumentParser) -> None:
    """Test URL computation follows ClickHouse clean URL pattern."""
    # MDX file
    url = parser._compute_url(Path("docs/en/sql-reference/statements/select.mdx"))
    assert url == "https://clickhouse.com/docs/docs/en/sql-reference/statements/select"
    assert ".mdx" not in url
    assert ".html" not in url

    # MD file
    url = parser._compute_url(Path("knowledgebase/integrations/kafka.md"))
    assert url == "https://clickhouse.com/docs/knowledgebase/integrations/kafka"
    assert ".md" not in url


def test_extract_section_multi_directory(parser: DocumentParser) -> None:
    """Test section extraction from different directory structures."""
    # Knowledgebase structure
    assert parser._extract_section(Path("knowledgebase/integrations/kafka.md")) == "knowledgebase-integrations"
    assert parser._extract_section(Path("knowledgebase/index.md")) == "knowledgebase"

    # Docs with language prefix
    assert parser._extract_section(Path("en/sql-reference/select.md")) == "sql-reference"
    assert parser._extract_section(Path("zh/operations/monitoring.md")) == "operations"

    # Docs without language prefix
    assert parser._extract_section(Path("sql-reference/functions/date.md")) == "sql-reference"

    # Root level
    assert parser._extract_section(Path("index.md")) == "index"


def test_extract_metadata_with_sidebar_label_fallback(temp_docs_root: Path) -> None:
    """Test metadata extraction with sidebar_label as fallback."""
    file_path = temp_docs_root / "test.mdx"

    # Title present
    content = """---
title: Main Title
sidebar_label: Sidebar
---
Content
"""
    file_path.write_text(content)
    parser = DocumentParser(temp_docs_root)
    doc = parser.parse_file(file_path)
    assert doc.title == "Main Title"

    # Only sidebar_label
    content = """---
sidebar_label: Sidebar Only
---
Content
"""
    file_path.write_text(content)
    doc = parser.parse_file(file_path)
    assert doc.title == "Sidebar Only"


def test_extract_metadata_missing_title_raises_error(temp_docs_root: Path) -> None:
    """Test that missing title raises ValueError."""
    file_path = temp_docs_root / "test.mdx"
    content = """---
description: Some description
---
Content
"""
    file_path.write_text(content)

    parser = DocumentParser(temp_docs_root)
    with pytest.raises(ValueError, match="Missing title"):
        parser.parse_file(file_path)


def test_extract_metadata_description_fallback(temp_docs_root: Path) -> None:
    """Test description fallback chain: description -> sidebar_label -> title."""
    file_path = temp_docs_root / "test.mdx"
    parser = DocumentParser(temp_docs_root)

    # Description present
    content = """---
title: Title
description: Description text
sidebar_label: Sidebar
---
Content
"""
    file_path.write_text(content)
    doc = parser.parse_file(file_path)
    assert doc.description == "Description text"

    # Fallback to sidebar_label
    content = """---
title: Title
sidebar_label: Sidebar label
---
Content
"""
    file_path.write_text(content)
    doc = parser.parse_file(file_path)
    assert doc.description == "Sidebar label"

    # Fallback to title
    content = """---
title: Title only
---
Content
"""
    file_path.write_text(content)
    doc = parser.parse_file(file_path)
    assert doc.description == "Title only"
