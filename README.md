# Cerebro

> *"Like Professor X's machine — but for peering into ML models instead of mutant minds."*

![status: pre-alpha](https://img.shields.io/badge/status-pre--alpha-orange)
![python: 3.12](https://img.shields.io/badge/python-3.12-blue)
[![CI](https://github.com/dgtalbug/cerebro/actions/workflows/ci.yml/badge.svg)](https://github.com/dgtalbug/cerebro/actions/workflows/ci.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A model introspection and visualization platform for gradient-boosted tree
models. A trained ML artifact goes in; a canonical, library-agnostic JSON
representation comes out. Dashboards, the AI agent, and downstream tools all
read that JSON — never the live model.

> **Status: pre-alpha.** Scaffolding and quality gates are in place; product
> behavior is being built. The sections below describe exactly what is
> shipping today, what is coming next, and what is on the longer roadmap.

## What ships today

- **Project skeleton** — uv-managed Python package, Vite + React + TypeScript
  UI, multi-stage Dockerfile.
- **Structured logging** — `structlog` JSON logs with correlation IDs
  propagated through `contextvars`. Shaped to be OpenTelemetry-ready.
- **Exception taxonomy** — a single `CerebroError` base lets process
  boundaries (CLI, FastAPI) map the whole hierarchy to RFC 7807.
- **Quality gates** — `ruff`, `mypy --strict`, `pytest`, `import-linter`
  (architectural-boundary enforcement), ESLint UI boundaries, pre-commit.
- **Contract-drift CI** — OpenAPI and JSON-schema drift gated before merge.

## Coming next

- LightGBM artifact extraction (all five variants) into the canonical schema.
- Dashboards for tree topology, feature importance, and gain / cover surfaces.
- AI agent over the canonical artifact (BYOK; Anthropic provider first).
- Production Docker build with dev and prod compose profiles.

## On the roadmap

- XGBoost extractor.
- Diagnostics and recommendations derived from the canonical artifact.
- `cerebro train` — apply recommendations and retrain.

## Layout

```text
src/cerebro/     Python package (backend) — see ARCHITECTURE.md
ui/              Frontend (Vite + React + TS)
docker/          Container build (slim multi-stage)
schemas/         Versioned contract artifacts (canonical JSON Schema, registry DDL)
contracts/       OpenAPI contract (drift-gated)
scripts/         Dev/CI helpers (contract drift checks)
openspec/        Spec-driven source of truth + change history (tracked)
docs/            Reserved for the published documentation site (tracked)
.docs/           Locked design narrative + discussion (git-ignored "meta")
```

## Backend — quickstart

The backend is managed with [uv](https://docs.astral.sh/uv/). Python 3.12 is
pinned via `.python-version` (uv will provision it).

```bash
uv sync                      # create .venv and install deps from uv.lock
uv run ruff check .          # lint
uv run ruff format --check . # format check
uv run mypy --strict src     # type check
uv run lint-imports          # architectural boundary checks (import-linter)
uv run pytest -n auto        # tests, in parallel
```

Install the pre-commit hooks once:

```bash
uv run pre-commit install
```

## Frontend — quickstart

The UI uses pnpm + Vite. Node 22 LTS is pinned via `.node-version`.

```bash
cd ui
pnpm install --frozen-lockfile
pnpm dev          # dev server (expects the backend at http://localhost:8000)
pnpm typecheck
pnpm lint
pnpm build
pnpm test
```

## Design references

- [`openspec/project.md`](openspec/project.md) — project constitution: tech
  stack, hard invariants, scope guardrails.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — architectural seams and the
  CI-enforced boundaries between them.
- `.docs/cerebro-open-spec.md` — full locked design narrative (git-ignored;
  available in a local checkout that has the narrative).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Every change starts as an OpenSpec
proposal under `openspec/changes/<name>/`. Commits follow Conventional
Commits and never include AI-attribution trailers.

Questions and discussion belong in
[GitHub Discussions](https://github.com/dgtalbug/cerebro/discussions);
bugs and feature requests in
[Issues](https://github.com/dgtalbug/cerebro/issues).

## License

[MIT](LICENSE).
