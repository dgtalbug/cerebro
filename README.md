# Cerebro

> *"Like Professor X's machine — but for peering into ML models instead of mutant minds."*

A model introspection and visualization platform. A trained ML artifact goes in;
a canonical, library-agnostic JSON representation comes out. Dashboards, the AI
agent, and downstream tools all read that JSON — never the live model.

This repository is at **milestone M0 (scaffolding)**: project skeleton, quality
gates, and the cross-cutting foundations (structured logging, exception
hierarchy). Product behavior (extraction, schema, dashboard, agent) lands from
M1 onward.

## Layout

```
src/cerebro/     Python package (backend) — see ARCHITECTURE.md
ui/              Frontend (Vite + React + TS)
docker/          Container build (slim multi-stage; real builds in M4)
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

## Design

The full, locked design lives in `.docs/cerebro-open-spec.md` (git-ignored
working material). The binding rules are in `openspec/project.md`; capability
specs are in `openspec/specs/`.
