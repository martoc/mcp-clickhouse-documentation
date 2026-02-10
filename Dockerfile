# Multi-stage build for MCP ClickHouse Documentation Server

# Stage 1: Build and index documentation
FROM python:3.12-slim AS builder

# Install git and curl
RUN apt-get update && \
    apt-get install -y git curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv and add to PATH
ENV PATH="/root/.cargo/bin:$PATH"
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Install dependencies
RUN uv sync

# Clone and index documentation
RUN mkdir -p /root/.cache/mcp-clickhouse-documentation && \
    uv run clickhouse-docs-index index

# Stage 2: Runtime image
FROM python:3.12-slim

# Install curl
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv and add to PATH
ENV PATH="/root/.cargo/bin:$PATH"
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /app

# Copy application and dependencies
COPY pyproject.toml .
COPY src/ src/

# Copy pre-indexed database from builder
COPY --from=builder /root/.cache/mcp-clickhouse-documentation /root/.cache/mcp-clickhouse-documentation

# Install dependencies
RUN uv sync

# Run MCP server
CMD ["uv", "run", "mcp-clickhouse-documentation"]
