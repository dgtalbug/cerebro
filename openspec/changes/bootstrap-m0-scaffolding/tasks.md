## 1. Monorepo layout (E1.001)

- [ ] 1.1 Create top-level directories: `cerebro/` as the Python package root via `src/cerebro/`; add `ui/`, `docker/`, `schemas/`, `contracts/`, and a tracked `docs/` (reserved for the future doc-site, with a placeholder README); keep `openspec/` and the untracked `.docs/` (design narrative / meta)
- [ ] 1.2 Add root `README.md` (project one-liner, first-run + `uv sync` pointer) and `.gitignore` (Python, Node, `.env`, `data/`, `.venv`)
- [ ] 1.3 Add `.env.example` documenting `CEREBRO_DATA_DIR`, `CEREBRO_LOG_LEVEL`, `ANTHROPIC_API_KEY`, `UI_PORT`
- [ ] 1.4 Write `ARCHITECTURE.md`: document the locked layer boundary (extraction → canonical JSON → consumption) and the existing protocol/ports-and-adapters seams (Extractor & LLMProvider protocols, storage repository, FastAPI DI). Conventions only — no new abstractions (honors KISS, project.md)

## 2. Python project + uv (E1.002)

- [ ] 2.1 Write `pyproject.toml` (PEP 621, hatchling backend, **`requires-python >=3.12`** — recent + security-supported, best wheel coverage for the lightgbm/shap/scientific stack); declare project deps and `dev` optional-deps per Part II §10, with **pinned lower+upper bounds** where practical
- [ ] 2.2 Adopt **uv** as the package + Python manager: pin the interpreter via `.python-version` (3.12.x), generate `uv.lock`, document `uv sync` / `uv run`; supersedes the pip flow in Part V (placeholder until M4)
- [ ] 2.3 Create `src/cerebro/__init__.py` exporting the public surface (version)
- [ ] 2.4 Configure ruff (lint + format) and `mypy --strict`; pin the dev toolchain versions in the lockfile
- [ ] 2.5 Configure pytest + pytest-cov + **pytest-xdist** (`tests/` discovery; default `addopts = -n auto` for **parallel** execution). **Core-only focus:** require tests for the core functional modules that exist in M0 (`logging`, `exceptions`); no global coverage gate yet — the ≥80% (`schema/`+`analyzers/`) / ≥60% overall targets apply as those modules land in M1+, not per-M0
- [ ] 2.6 Create empty-but-importable package subdirs from Part II §3 (`extractors/`, `schema/`, `analyzers/`, `storage/`, `api/`, `agent/`, `cli/`) each with `__init__.py`, so the layer boundaries exist for M1
- [ ] 2.7 Add **`import-linter`** contracts enforcing invariant #2 (no `extractors`-downstream module imports `lightgbm`) and the layer dependency direction (consumption never imports extraction internals)
- [ ] 2.8 Create `tests/conftest.py` placeholder and `tests/` mirror dirs

## 3. UI project (E1.003)

- [ ] 3.1 Initialize pnpm + Vite + React 18 + TypeScript (strict) in `ui/` on **Node 22 LTS** (pin via `.node-version`/`.nvmrc`); pin **pnpm** via the `packageManager` field (corepack), pin versions in `package.json`, commit `pnpm-lock.yaml`
- [ ] 3.2 Add and configure Tailwind (`tailwind.config.ts`, `globals.css` token stubs)
- [ ] 3.3 Run shadcn/ui init (`components.json`, Radix primitives wired to CSS-variable tokens)
- [ ] 3.4 Configure ESLint with a **boundaries rule** enforcing Part III §4 (no `views/` component calls `fetch` directly — must go through query hooks); add `ui/.env.example` (`VITE_API_URL=http://localhost:8000`)
- [ ] 3.5 Wire the `pnpm api:types` script (openapi-typescript) as the consumer-driven type pipeline stub; confirm `pnpm typecheck` passes on the bootstrap app

## 4. Structured logging foundation — OTel-ready (E1.006)

- [ ] 4.1 Implement `src/cerebro/logging.py`: `configure_logging(level)` with the structlog processor chain from Part II §8 (merge_contextvars, add_log_level, ISO TimeStamper, StackInfoRenderer, format_exc_info, JSONRenderer) and a `get_logger()` helper
- [ ] 4.2 Implement correlation-ID support via `structlog.contextvars` (bind/clear helpers) and the ASGI middleware that reads/generates `X-Request-ID` and binds `correlation_id`. **OTel-ready:** carry the id so it maps onto a future OTel trace/span context with no refactor; **no OpenTelemetry dependency added in M0**
- [ ] 4.3 Unit tests: JSON output shape, `correlation_id` propagates to sub-call log records, fields-not-strings, no PII/secrets emitted
- [ ] 4.4 **Concurrency test:** run many `configure_logging`-bound units of work concurrently (asyncio tasks + threads) and assert each retains its own `correlation_id` with no cross-bleed — verifies contextvars isolation under concurrency and that tests are xdist-parallel-safe. (Registry single-writer / WAL concurrent-reader concurrency tests are deferred to M4 with `storage/registry.py`, Part IV §8)

## 5. Exception hierarchy (E1.007)

- [ ] 5.1 Implement `src/cerebro/exceptions.py`: `CerebroError` base with structured `context: dict`, and the full Part II §7 taxonomy (`ExtractionError` → `UnsupportedFrameworkError`/`UnsupportedObjectiveError`/`CorruptArtifactError`; `SchemaValidationError`; `StorageError` → `ArtifactNotFoundError`/`RegistryError`; `AgentError` → `LLMProviderError`/`ContextTooLargeError`)
- [ ] 5.2 Ensure the module imports nothing from the rest of `cerebro` (no cycles) and supports `raise ... from original`
- [ ] 5.3 Unit tests: every descendant is a `CerebroError`, `context` is carried, cause chains preserved

## 6. Contracts & drift gates (schema + DB + API↔UI)

- [ ] 6.1 Create contracts layout: `schemas/v1/` (canonical artifact JSON Schema), `schemas/registry/v1/init.sql` (registry DDL), `contracts/openapi/openapi.json` (OpenAPI stub)
- [ ] 6.2 Author the **registry DDL contract** `schemas/registry/v1/init.sql` now from Part IV §4 (fully specified there); seed the canonical JSON Schema and OpenAPI as stubs to be regenerated from Pydantic/FastAPI as M1+ lands
- [ ] 6.3 Add a `scripts/check_contracts` harness: assert exported Pydantic `model_json_schema()` matches the committed canonical JSON Schema (active from M1); assert the live registry DDL matches `init.sql`; assert generated OpenAPI matches the committed stub
- [ ] 6.4 Add the **consumer-driven API↔UI contract gate**: regenerate UI types via `pnpm api:types` and fail on drift from committed types (Part III §7)

## 7. Pre-commit hooks (E1.004)

- [ ] 7.1 Add `.pre-commit-config.yaml` with `ruff format`, `ruff check`, `mypy`, `import-linter`, and `eslint` (UI) hooks
- [ ] 7.2 Document `pre-commit install` in `README.md`; verify hooks run clean on the M0 tree

## 8. CI (E1.005)

- [ ] 8.1 Add `.github/workflows/ci.yml` Python job (pinned `setup-uv`, Python 3.12): `uv sync --frozen`, `ruff check`, `ruff format --check`, `mypy --strict`, `import-linter`, `pytest -n auto` (parallel; dev extras only — keep heavy ML deps out of M0; no global coverage gate in M0)
- [ ] 8.2 UI job (Node 22 LTS, corepack pnpm): `pnpm install --frozen-lockfile`, `pnpm lint`, `pnpm typecheck`, `pnpm build`, `pnpm test` (Vitest, parallel by default)
- [ ] 8.3 Contract-drift job: run `scripts/check_contracts` (schema / registry DDL / OpenAPI) and the `pnpm api:types` drift gate; fail the build on any drift
- [ ] 8.4 Docker build job: placeholder **slim-base** Dockerfiles — `docker/backend.Dockerfile` (`python:3.12-slim` + uv) and `docker/ui.Dockerfile` (`node:22-alpine` build → `nginx:1.27-alpine` runtime); pin base images by digest; full multi-stage builds land in M4

## 9. Verify

- [ ] 9.1 `uv sync --frozen` reproduces the locked env; `ruff check`, `ruff format --check`, `mypy --strict`, and `import-linter` pass on `src/`
- [ ] 9.2 `pytest -n auto` passes in parallel (logging + exceptions unit tests + the correlation-ID concurrency test green; suite is parallel-safe)
- [ ] 9.3 `pnpm install --frozen-lockfile`, `pnpm typecheck`, and `pnpm build` succeed in `ui/`
- [ ] 9.4 Contract-drift gates pass (registry DDL contract is real; JSON Schema/OpenAPI stubs in place and wired)
- [ ] 9.5 CI is green on a clean checkout; pre-commit runs clean
- [ ] 9.6 Confirm no product behavior shipped beyond `logging.py` and `exceptions.py`, and no OTel/DI-container/service-layer abstractions were introduced (M0 scope + KISS guardrail)
