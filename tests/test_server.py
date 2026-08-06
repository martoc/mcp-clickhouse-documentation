"""Tests for the MCP server entrypoint."""

from unittest.mock import patch

import pytest

from mcp_clickhouse_documentation.server import main


def test_main_uses_stdio_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that the server runs over stdio when MCP_TRANSPORT is unset."""
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)

    with patch("mcp_clickhouse_documentation.server.mcp.run") as mock_run:
        main()

    mock_run.assert_called_once_with(transport="stdio")


def test_main_uses_http_with_custom_host_and_port(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that MCP_TRANSPORT=http honours custom MCP_HOST/MCP_PORT."""
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_PORT", "9000")

    with patch("mcp_clickhouse_documentation.server.mcp.run") as mock_run:
        main()

    mock_run.assert_called_once_with(transport="http", host="127.0.0.1", port=9000)


def test_main_uses_http_with_default_host_and_port(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that MCP_TRANSPORT=http falls back to 0.0.0.0:8000 when unset."""
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    monkeypatch.delenv("MCP_HOST", raising=False)
    monkeypatch.delenv("MCP_PORT", raising=False)

    with patch("mcp_clickhouse_documentation.server.mcp.run") as mock_run:
        main()

    mock_run.assert_called_once_with(transport="http", host="0.0.0.0", port=8000)
