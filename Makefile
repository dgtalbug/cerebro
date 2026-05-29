# Cerebro Makefile — local dev orchestration. `make help` lists every target.
#
# The Makefile is a task runner, not a build system. Most targets are thin
# wrappers around `docker compose` or `uv` / `pnpm` so the surface stays
# consistent whether you run things in containers or on the host.

SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE ?= docker compose

# Resolve the ports that will actually be used (honour .env overrides).
UI_PORT  ?= 3000
API_PORT ?= 8000

.PHONY: help \
        up down build rebuild restart ps logs shell-backend shell-ui clean seed examples \
        lint fmt test contracts open

# ----------------------------------------------------------------------------
# Containers (docker-compose)
# ----------------------------------------------------------------------------

up: ## Bring up backend + ui, wait until healthy, then print service URLs
	$(COMPOSE) up -d --wait
	@$(MAKE) --no-print-directory _urls

down: ## Stop and remove containers (./data/ preserved on host)
	$(COMPOSE) down

build: ## Build images
	$(COMPOSE) build

rebuild: ## Rebuild images without cache, then start and print URLs
	$(COMPOSE) build --no-cache
	$(COMPOSE) up -d --wait
	@$(MAKE) --no-print-directory _urls

restart: down up ## Restart containers

ps: ## Show running containers
	$(COMPOSE) ps

logs: ## Tail logs from all services (Ctrl-C to stop)
	$(COMPOSE) logs -f

shell-backend: ## Open a shell in the backend container
	$(COMPOSE) exec backend sh

shell-ui: ## Open a shell in the ui container
	$(COMPOSE) exec ui sh

seed: ## Seed example artifacts into ./data/artifacts/ (run once before first `make up`)
	uv run python scripts/seed_dev_data.py

examples: ## (Re)generate example .cerebro.json artifacts into examples/
	uv run python scripts/generate_examples.py

clean: ## Stop containers AND remove ./data/ volume directory (DATA LOSS)
	$(COMPOSE) down
	rm -rf ./data

# Internal target — print the running service URLs.
# Not in .PHONY so it doesn't appear in `make help`.
_urls:
	@printf "\n\033[1mCerebro is up:\033[0m\n\n"
	@printf "  \033[36m%-28s\033[0m %s\n" "Artifact picker"              "http://localhost:$(UI_PORT)"
	@printf "  \033[36m%-28s\033[0m %s\n" "binary (overview)"            "http://localhost:$(UI_PORT)/artifacts/binary_artifact/overview"
	@printf "  \033[36m%-28s\033[0m %s\n" "binary (importance)"          "http://localhost:$(UI_PORT)/artifacts/binary_artifact/importance"
	@printf "  \033[36m%-28s\033[0m %s\n" "binary (trees)"               "http://localhost:$(UI_PORT)/artifacts/binary_artifact/trees"
	@printf "  \033[36m%-28s\033[0m %s\n" "multiclass (overview)"        "http://localhost:$(UI_PORT)/artifacts/multiclass_artifact/overview"
	@printf "  \033[36m%-28s\033[0m %s\n" "regression (overview)"        "http://localhost:$(UI_PORT)/artifacts/regression_artifact/overview"
	@printf "  \033[36m%-28s\033[0m %s\n" "ranker (overview)"            "http://localhost:$(UI_PORT)/artifacts/ranker_artifact/overview"
	@printf "  \033[36m%-28s\033[0m %s\n" "multi-output (overview)"      "http://localhost:$(UI_PORT)/artifacts/multi_output_artifact/overview"
	@printf "\n"
	@printf "  \033[36m%-28s\033[0m %s\n" "Swagger UI"   "http://localhost:$(API_PORT)/docs"
	@printf "  \033[36m%-28s\033[0m %s\n" "Health check" "http://localhost:$(API_PORT)/health"
	@printf "\n  \033[2mmake seed   — (re)seed example artifacts into ./data/\033[0m\n"
	@printf "  \033[2mmake logs   — tail service logs\033[0m\n"
	@printf "  \033[2mmake down   — stop all containers\033[0m\n\n"

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
