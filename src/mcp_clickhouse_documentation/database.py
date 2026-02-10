"""Database operations for ClickHouse documentation search."""

import sqlite3
from pathlib import Path

from mcp_clickhouse_documentation.models import Document, SearchResult


class DocumentDatabase:
    """SQLite database with FTS5 full-text search for documentation."""

    def __init__(self, db_path: Path) -> None:
        """Initialise database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialise database schema with FTS5 tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Create main documents table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    path TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    section TEXT NOT NULL,
                    url TEXT NOT NULL,
                    content TEXT NOT NULL
                )
            """)

            # Create FTS5 virtual table for full-text search with BM25 ranking
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                    path UNINDEXED,
                    title,
                    description,
                    section UNINDEXED,
                    url UNINDEXED,
                    content,
                    content=documents,
                    content_rowid=rowid
                )
            """)

            # Create triggers to keep FTS table synchronised
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
                    INSERT INTO documents_fts(rowid, path, title, description, section, url, content)
                    VALUES (new.rowid, new.path, new.title, new.description, new.section, new.url, new.content);
                END
            """)

            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
                    DELETE FROM documents_fts WHERE rowid = old.rowid;
                END
            """)

            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
                    DELETE FROM documents_fts WHERE rowid = old.rowid;
                    INSERT INTO documents_fts(rowid, path, title, description, section, url, content)
                    VALUES (new.rowid, new.path, new.title, new.description, new.section, new.url, new.content);
                END
            """)

            conn.commit()

    def insert_document(self, doc: Document) -> None:
        """Insert or replace a document in the database.

        Args:
            doc: Document to insert
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO documents (path, title, description, section, url, content)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (doc.path, doc.title, doc.description, doc.section, doc.url, doc.content),
            )
            conn.commit()

    def search(self, query: str, section: str | None = None, limit: int = 10) -> list[SearchResult]:
        """Search documents using full-text search with BM25 ranking.

        Args:
            query: Search query
            section: Optional section filter
            limit: Maximum number of results

        Returns:
            List of search results ordered by relevance
        """
        with sqlite3.connect(self.db_path) as conn:
            # BM25 ranking with weights: title (5.0), description (2.0), content (1.0)
            base_query = """
                SELECT
                    d.path,
                    d.title,
                    d.url,
                    d.section,
                    snippet(documents_fts, 5, '[', ']', '...', 32) as snippet,
                    bm25(documents_fts, 5.0, 2.0, 1.0, 1.0, 1.0, 1.0) as score
                FROM documents_fts
                JOIN documents d ON documents_fts.rowid = d.rowid
                WHERE documents_fts MATCH ?
            """

            params: list[str | int] = [query]

            if section:
                base_query += " AND d.section = ?"
                params.append(section)

            base_query += " ORDER BY score DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(base_query, params)

            results = []
            for row in cursor.fetchall():
                results.append(
                    SearchResult(
                        path=row[0],
                        title=row[1],
                        url=row[2],
                        section=row[3],
                        snippet=row[4],
                        relevance_score=abs(row[5]),  # BM25 scores are negative
                    )
                )

            return results

    def get_document(self, path: str) -> Document | None:
        """Retrieve a document by its path.

        Args:
            path: Document path

        Returns:
            Document if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT path, title, description, section, url, content
                FROM documents
                WHERE path = ?
            """,
                (path,),
            )

            row = cursor.fetchone()
            if row:
                return Document(
                    path=row[0],
                    title=row[1],
                    description=row[2],
                    section=row[3],
                    url=row[4],
                    content=row[5],
                )

            return None

    def clear(self) -> None:
        """Clear all documents from the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM documents")
            conn.commit()

    def count(self) -> int:
        """Count total documents in the database.

        Returns:
            Number of documents
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM documents")
            result = cursor.fetchone()
            return int(result[0]) if result else 0

    def get_sections(self) -> list[tuple[str, int]]:
        """Get all sections with document counts.

        Returns:
            List of (section, count) tuples ordered by count descending
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT section, COUNT(*) as count
                FROM documents
                GROUP BY section
                ORDER BY count DESC
            """
            )
            return cursor.fetchall()
