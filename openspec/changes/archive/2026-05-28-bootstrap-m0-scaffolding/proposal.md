## Why

Cerebro's design is locked but no code exists. Before any product behavior can
be built (M1's walking skeleton onward), the repository needs its skeleton: a
monorepo layout, a strictly-typed Python package, a UI project, quality gates
(lint/typecheck/test), CI, and the two cross-cutting foundations every later
module depends on — structured logging with correlation IDs, and the
`CerebroError` exception hierarchy. M0 establishes that foundation and nothing
more.

## What Changes

- Create the monorepo layout: `cerebro/` (backend package), `ui/` (frontend),
  `docker/`, `schemas/`, `contracts/`, plus a tracked `docs/` reserved for the
  future doc-site; the locked design narrative lives in the untracked `.docs/`.
- Stand up the Python project: `pyproject.toml` (PEP 621, hatchling), `src/`
  layout, `ruff` (lint + format), `mypy --strict`, `pytest` + `pytest-cov`,
  managed with **uv** and a committed `uv.lock` for reproducible installs.
- Initialize the UI project: pnpm (committed lockfile), Vite + React 18 +
  TypeScript (strict), Tailwind, shadcn/ui init.
- Formalize existing architectural seams by enforcement (not new abstraction):
  an `ARCHITECTURE.md` plus `import-linter` contracts (invariant #2 — no
  consumption module imports LightGBM) and an ESLint boundaries rule (Part III
  §4 — no view calls `fetch` directly).
- Add pre-commit hooks: `ruff format`, `ruff check`, `mypy`, `import-linter`,
  `eslint`.
- Add GitHub Actions CI: lint, typecheck, test, contract-drift gates, and build
  the slim-base Docker images.
- Implement the structured-logging foundation: `cerebro/logging.py` structlog
  JSON config plus a correlation-ID middleware that binds `X-Request-ID` to the
  log context, **shaped to be OpenTelemetry-ready (no OTel dependency in M0).**
- Implement the exception hierarchy: `cerebro/exceptions.py` with `CerebroError`
  and its descendants (`ExtractionError` and children, `SchemaValidationError`,
  `StorageError` and children, `AgentError` and children) per Part II §7.
- Seed contract artifacts and CI drift gates: author `schemas/registry/v1/
  init.sql` now (Part IV §4), stub the canonical JSON Schema and OpenAPI, and
  wire the consumer-driven API↔UI types gate (`pnpm api:types`).

No product features (extraction, schema models, API routes beyond a placeholder,
dashboard views) are built in M0. Those begin in M1.

## Capabilities

### New Capabilities

<!-- None. M0 is foundation/tooling; it implements no new product capability. -->

### Modified Capabilities

- `distribution`: ADD three foundation-level requirements that the existing
  *Structured errors and correlation IDs* and *REST API contract* requirements
  build on — a structured JSON logging foundation (structlog, correlation-ID
  propagation, no PII), the unified `CerebroError` exception hierarchy that the
  boundary handler maps to RFC 7807, and contract-integrity drift detection
  (canonical JSON Schema, registry DDL, and consumer-driven API↔UI types) gated
  in CI.

## Impact

- **New files (skeleton, no product logic):** `pyproject.toml`, `uv.lock`,
  `.python-version`, `src/cerebro/__init__.py`, `src/cerebro/logging.py`,
  `src/cerebro/exceptions.py`, `ARCHITECTURE.md`, `import-linter` config,
  `ui/` project files (+ `pnpm-lock.yaml`, `.node-version`, ESLint boundaries
  config), `docker/` slim-base placeholders, `schemas/registry/v1/init.sql`,
  `schemas/v1/` + `contracts/openapi/` stubs, `scripts/check_contracts`,
  `docs/README.md`, `.gitignore`, `.pre-commit-config.yaml`,
  `.github/workflows/ci.yml`, ruff/mypy config.
- **Runtimes (pinned, recent + security-supported):** Python 3.12, Node 22 LTS,
  uv (via `setup-uv`), pnpm (via `packageManager`); Docker bases pinned by
  digest.
- **Dependencies introduced:** Python — `pydantic`, `structlog`, dev tooling
  (`uv`, `ruff`, `mypy`, `pytest`, `pytest-cov`, `pytest-xdist`,
  `import-linter`); UI — `vite`, `react`, `typescript`, `tailwindcss`,
  shadcn/ui + Radix, `openapi-typescript`, ESLint boundaries plugin, Vitest.
  (Heavy ML deps like `lightgbm`/`shap` are declared but exercised only from
  M1+. **No OpenTelemetry dependency** — OTel-ready only.)
- **Testing approach:** parallel execution (`pytest -n auto`, Vitest); M0 tests
  cover core functional modules only (`logging`, `exceptions`) with no global
  coverage gate; a concurrency test guards correlation-ID isolation.
- **Deviations from locked design (user-authorized):** uv supersedes the
  `pip install --user` flow in Part V; runtime bases bump to `python:3.12-slim`
  and `node:22-alpine` (from 3.11/20) for recency + security. Both touch only
  the Part V placeholders (real Dockerfiles land in M4).
- **Repo doc layout:** the locked design narrative moved to the git-ignored
  `.docs/`; `docs/` is reserved (tracked) for the future doc-site; `openspec/`
  is committed. Spec cross-references now point at `.docs/…` (local-only —
  see `openspec/project.md`).
- **Constitution invariants engaged:** #2 (no consumption module imports
  LightGBM) becomes machine-enforced via `import-linter`; #5 (no bare
  `except`/`except Exception` in library code) and #6 (structured JSON logs, no
  PII/secrets, correlation ID end to end) become enforceable from M0.
- **Downstream:** every later milestone imports `cerebro.logging` and
  `cerebro.exceptions`; the CI, pre-commit, boundary, and contract-drift gates
  apply to all subsequent changes.
