"""Parser for ClickHouse MDX/Markdown documentation files."""

import re
from pathlib import Path

import frontmatter  # type: ignore[import-untyped]

from mcp_clickhouse_documentation.models import Document, DocumentMetadata

# Pre-compile regex patterns for performance (used for every document)
IMPORT_PATTERN = re.compile(r"^import\s+.*?from\s+[\"'].*?[\"'];?\s*$", re.MULTILINE)
EXPORT_PATTERN = re.compile(r"^export\s+.*?;?\s*$", re.MULTILINE)
JSX_SELF_CLOSING_PATTERN = re.compile(r"<[A-Z][a-zA-Z0-9]*\s*(?:\{[^}]*\}|\w+=\"[^\"]*\"|\w+)*\s*/>")
JSX_PAIRED_TAGS_PATTERN = re.compile(r"</?[A-Z][a-zA-Z0-9]*(?:\s+[^>]*)?>")
JSX_EXPRESSIONS_PATTERN = re.compile(r"\{[^}]*\}")
HTML_COMMENTS_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
HTML_TAGS_PATTERN = re.compile(r"<[^>]+>")
EXCESSIVE_WHITESPACE_PATTERN = re.compile(r"\n\s*\n\s*\n+")


class DocumentParser:
    """Parser for MDX and Markdown documentation files."""

    CLICKHOUSE_DOCS_BASE_URL = "https://clickhouse.com/docs"

    def __init__(self, docs_root: Path) -> None:
        """Initialise parser with documentation root path.

        Args:
            docs_root: Root directory of documentation repository
        """
        self.docs_root = docs_root

    def parse_file(self, file_path: Path) -> Document:
        """Parse an MDX or Markdown file into a Document.

        Args:
            file_path: Path to the documentation file

        Returns:
            Parsed Document

        Raises:
            ValueError: If file cannot be parsed or is missing required metadata
        """
        with open(file_path, encoding="utf-8") as f:
            post = frontmatter.load(f)

        # Extract metadata
        metadata = self._extract_metadata(post, file_path)

        # Compute relative path from docs root
        relative_path = file_path.relative_to(self.docs_root)

        # Extract section from path
        section = self._extract_section(relative_path)

        # Clean content (remove MDX/JSX artifacts)
        content = self._clean_content(post.content)

        # Compute URL
        url = self._compute_url(relative_path)

        return Document(
            path=str(relative_path),
            title=metadata.title,
            description=metadata.description,
            section=section,
            url=url,
            content=content,
        )

    def _extract_metadata(self, post: frontmatter.Post, file_path: Path) -> DocumentMetadata:
        """Extract metadata from frontmatter.

        Args:
            post: Parsed frontmatter post
            file_path: Path to the file (for error messages)

        Returns:
            DocumentMetadata

        Raises:
            ValueError: If required metadata is missing
        """
        title = post.get("title") or post.get("sidebar_label")
        if not title:
            raise ValueError(f"Missing title in {file_path}")

        description = post.get("description") or post.get("sidebar_label") or title

        return DocumentMetadata(title=str(title), description=str(description))

    def _extract_section(self, relative_path: Path) -> str:
        """Extract section identifier from file path.

        Args:
            relative_path: Path relative to docs root

        Returns:
            Section identifier (e.g., "sql-reference", "knowledgebase-integrations")
        """
        parts = relative_path.parts

        if not parts:
            return "root"

        # Single file at root: index.md -> "index"
        if len(parts) == 1:
            name = parts[0]
            # Remove file extension for section name
            if name.endswith(".mdx"):
                return name[:-4]
            elif name.endswith(".md"):
                return name[:-3]
            return name

        # Handle knowledgebase structure: knowledgebase/integrations/kafka.md
        if parts[0] == "knowledgebase":
            # If there's a subdirectory (not just the filename), use it
            if len(parts) > 2 or (len(parts) == 2 and not parts[1].endswith((".md", ".mdx"))):
                return f"knowledgebase-{parts[1]}"
            return "knowledgebase"

        # For docs/ path: docs/en/sql-reference/select.md
        if parts[0] == "docs":
            # Skip "docs" and check for language code
            if len(parts) > 1:
                second_part = parts[1]
                if len(second_part) == 2 and second_part.lower() in {"en", "zh", "ru", "jp", "de", "fr", "es"}:
                    # Language code found, use next part if available
                    return parts[2] if len(parts) > 2 else second_part
                # No language code, use second part
                return second_part
            return "docs"

        # For other structures, check if first part is language code
        first_part = parts[0]
        if len(first_part) == 2 and first_part.lower() in {"en", "zh", "ru", "jp", "de", "fr", "es"}:
            # Language prefix, use next part if available
            return parts[1] if len(parts) > 1 else first_part
        return first_part

    def _compute_url(self, relative_path: Path) -> str:
        """Compute documentation URL from relative path.

        Args:
            relative_path: Path relative to docs root

        Returns:
            Full documentation URL
        """
        # Remove file extensions (.md, .mdx) - Docusaurus uses clean URLs
        path_str = str(relative_path)
        if path_str.endswith(".mdx"):
            path_str = path_str[:-4]
        elif path_str.endswith(".md"):
            path_str = path_str[:-3]

        return f"{self.CLICKHOUSE_DOCS_BASE_URL}/{path_str}"

    def _clean_content(self, content: str) -> str:
        """Clean MDX/Markdown content by removing JSX artifacts.

        Args:
            content: Raw content from file

        Returns:
            Cleaned content suitable for indexing
        """
        # Use pre-compiled patterns for better performance
        # 1. Remove import statements: import ... from ...
        content = IMPORT_PATTERN.sub("", content)

        # 2. Remove export statements: export ...
        content = EXPORT_PATTERN.sub("", content)

        # 3. Remove JSX self-closing tags: <Component />
        content = JSX_SELF_CLOSING_PATTERN.sub("", content)

        # 4. Remove JSX paired tags: <Component>...</Component>
        # This handles nested tags by matching component names (starting with uppercase)
        content = JSX_PAIRED_TAGS_PATTERN.sub("", content)

        # 5. Remove JSX expressions: {expression}
        # Be careful not to remove code block content
        content = JSX_EXPRESSIONS_PATTERN.sub("", content)

        # 6. Remove HTML comments
        content = HTML_COMMENTS_PATTERN.sub("", content)

        # 7. Remove remaining HTML tags (lowercase tags like <div>, <span>)
        content = HTML_TAGS_PATTERN.sub("", content)

        # 8. Clean up excessive whitespace
        content = EXCESSIVE_WHITESPACE_PATTERN.sub("\n\n", content)

        return content.strip()
