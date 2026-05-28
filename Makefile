# Cerebro Makefile — local dev orchestration. `make help` lists every target.
#
# The Makefile is a task runner, not a build system. Most targets are thin
# wrappers around `docker compose` or `uv` / `pnpm` so the surface stays
# consistent whether you run things in containers or on the host.

SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE ?= docker compose

.PHONY: help \
        up down build rebuild restart ps logs shell-backend shell-ui clean \
        lint fmt test contracts

# ----------------------------------------------------------------------------
# Containers (docker-compose)
# ----------------------------------------------------------------------------

up: ## Bring up backend + ui in the background
	$(COMPOSE) up -d

down: ## Stop and remove containers (named volume preserved)
	$(COMPOSE) down

build: ## Build images
	$(COMPOSE) build

rebuild: ## Rebuild images without cache, then start
	$(COMPOSE) build --no-cache
	$(COMPOSE) up -d

restart: down up ## Restart containers

ps: ## Show running containers
	$(COMPOSE) ps

logs: ## Tail logs from all services (Ctrl-C to stop)
	$(COMPOSE) logs -f

shell-backend: ## Open a shell in the backend container
	$(COMPOSE) exec backend sh

shell-ui: ## Open a shell in the ui container
	$(COMPOSE) exec ui sh

clean: ## Stop containers AND remove the data volume (DATA LOSS)
	$(COMPOSE) down -v

# ----------------------------------------------------------------------------
# Quality gates — same checks CI runs
# ----------------------------------------------------------------------------

lint: ## Run all linters (backend + ui)
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy
	uv run lint-imports
	cd ui && pnpm lint && pnpm typecheck

fmt: ## Apply formatters in-place
	uv run ruff format .

test: ## Run backend + ui tests
	uv run pytest -n auto
	cd ui && pnpm test

contracts: ## Check OpenAPI / schema / registry-DDL drift
	uv run python scripts/check_contracts.py

# ----------------------------------------------------------------------------
# Help
# ----------------------------------------------------------------------------

help: ## Show this help message
	@printf "\nCerebro — Makefile targets:\n\n"
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo
