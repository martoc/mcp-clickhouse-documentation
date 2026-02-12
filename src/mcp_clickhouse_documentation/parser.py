"""Parser for ClickHouse MDX/Markdown documentation files."""

import re
from pathlib import Path

import frontmatter  # type: ignore[import-untyped]

from mcp_clickhouse_documentation.models import Document, DocumentMetadata

# Simple, fast patterns that won't cause catastrophic backtracking
# These are used line-by-line, not on entire document
IMPORT_LINE = re.compile(r"^import\s+")
EXPORT_LINE = re.compile(r"^export\s+")
JSX_COMPONENT_TAG = re.compile(r"<[A-Z]")  # JSX components start with uppercase
HTML_COMMENT_START = re.compile(r"<!--")
HTML_TAG = re.compile(r"<[^>]+>")
EXCESSIVE_WHITESPACE = re.compile(r"\n{3,}")


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

        Uses a fast line-by-line approach to avoid regex catastrophic backtracking.

        Args:
            content: Raw content from file

        Returns:
            Cleaned content suitable for indexing
        """
        lines = []
        in_code_block = False
        skip_html_comment = False

        for line in content.splitlines():
            # Track code blocks (don't process content inside them)
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                lines.append(line)
                continue

            if in_code_block:
                lines.append(line)
                continue

            # Skip HTML comment blocks
            if HTML_COMMENT_START.search(line):
                skip_html_comment = True
            if skip_html_comment:
                if "-->" in line:
                    skip_html_comment = False
                continue

            # Skip import/export statements
            if IMPORT_LINE.match(line) or EXPORT_LINE.match(line):
                continue

            # Skip lines that are pure JSX component tags
            stripped = line.strip()
            if stripped and (stripped.startswith("<") or stripped.startswith("{")):
                if JSX_COMPONENT_TAG.search(stripped):
                    continue

            # Remove remaining HTML/JSX tags from the line
            line = HTML_TAG.sub("", line)

            # Remove JSX expressions {like this} but only simple ones
            # Avoid complex regex that can cause backtracking
            while "{" in line and "}" in line:
                start = line.find("{")
                end = line.find("}", start)
                if end > start and end - start < 100:  # Only remove short expressions
                    line = line[:start] + line[end + 1 :]
                else:
                    break

            lines.append(line)

        # Join and clean up whitespace
        content = "\n".join(lines)
        content = EXCESSIVE_WHITESPACE.sub("\n\n", content)

        return content.strip()
