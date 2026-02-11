.PHONY: init test build format generate index stats run clean docker-build docker-run help

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

init: ## Initialise development environment
	uv sync --all-groups

test: ## Run tests with coverage
	uv run pytest

build: ## Run linting, type checking, and tests
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/
	uv run mypy src/
	uv run pytest

format: ## Format code with ruff
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

generate: ## Update generated files (uv.lock)
	uv lock

index: ## Index ClickHouse documentation
	uv run clickhouse-docs-index index

stats: ## Show indexing statistics
	uv run clickhouse-docs-index stats

run: ## Run MCP server
	uv run mcp-clickhouse-documentation

clean: ## Clean build artifacts and data
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache htmlcov/
	rm -rf data/ clickhouse-docs/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

docker-build: ## Build Docker image for local platform only (faster than multi-platform)
	docker build --platform linux/arm64 -t mcp-clickhouse-documentation .

docker-build-amd64: ## Build Docker image for amd64 platform
	docker build --platform linux/amd64 -t mcp-clickhouse-documentation .

docker-run: ## Run Docker container
	docker run --rm -i mcp-clickhouse-documentation
