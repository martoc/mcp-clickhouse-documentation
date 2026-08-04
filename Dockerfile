# Multi-stage build for MCP ClickHouse Documentation Server

# Stage 1: Build and index documentation
FROM python:3.12-slim AS builder

# Install git and curl
RUN apt-get update && \
    apt-get install -y git curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock .
COPY src/ src/

# Install dependencies from the committed lockfile, baking them into the
# image at build time
RUN uv sync --locked --no-dev

# Clone and index documentation
RUN mkdir -p /root/.cache/mcp-clickhouse-documentation && \
    uv run --no-sync clickhouse-docs-index index

# Stage 2: Runtime image
FROM python:3.12-slim

# Disable FastMCP's startup update check; the container has no need to
# reach PyPI at runtime
ENV FASTMCP_CHECK_FOR_UPDATES=off

WORKDIR /app

# Copy the venv and application baked in the builder stage
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Copy pre-indexed database from builder
COPY --from=builder /root/.cache/mcp-clickhouse-documentation /root/.cache/mcp-clickhouse-documentation

# Run the MCP server directly from the baked venv so no dependency
# resolution happens on container start
CMD ["/app/.venv/bin/mcp-clickhouse-documentation"]
