## Context

The repository today contains only the locked design narrative (now in the
untracked `.docs/`) and `openspec/`. M0 turns it into a working monorepo with quality gates and the two
cross-cutting runtime foundations — structured logging and the exception
hierarchy — that Part II §6–§8 require and that every later module imports. The
tech stack is locked by `openspec/project.md`: Python 3.11+, Pydantic v2, ruff,
mypy --strict, hatchling, pytest; React 18 + TS strict, Vite, pnpm, Tailwind +
shadcn. M0 commits to that stack's *scaffolding* without building product
behavior.

Source of truth: `.docs/cerebro-open-spec.md` Part II §3 (project layout),
§7 (exception hierarchy), §8 (logging), §10 (dependencies); Part III §3 (UI
layout), §10 (UI workflow); Part V §2 (repo layout); Part VI §3.2 (M0 tasks
E1.001–E1.007).

## Goals / Non-Goals

**Goals:**
- A monorepo (`cerebro/`, `ui/`, `docker/`, `docs/`) that mirrors Part V §2,
  with a tracked `docs/` reserved for the future doc-site and the working design
  narrative kept in an untracked `.docs/` (meta).
- A Python package importable as `cerebro` with `src/` layout, passing
  `ruff check`, `ruff format --check`, and `mypy --strict` on an empty-but-real
  module set.
- A UI project that installs and type-checks (`pnpm typecheck`) with Tailwind +
  shadcn initialized.
- Pre-commit + CI that enforce the gates so M1 starts on a green baseline.
- `cerebro/logging.py` and `cerebro/exceptions.py` implemented and unit-tested —
  the only runtime code M0 ships.

**Non-Goals:**
- No extractors, schema models, analyzers, storage, API routes, agent, or
  dashboard views. (M1+.)
- No Docker image *content* beyond slim-base placeholders sufficient for CI to
  attempt a build; the real multi-stage Dockerfiles land in M4 per the roadmap.
- No release/publish pipeline.
- **No OpenTelemetry dependency.** M0 is OTel-*ready* (Decision 7), not
  OTel-instrumented.
- **No speculative enterprise abstractions** — no DI container, no
  repository+unit-of-work, no service layer, no config framework. M0 only
  *formalizes and enforces* seams the locked design already has (Decision 6),
  per the KISS invariant in `openspec/project.md`.
- **No global test-coverage gate in M0** (Decision 11). Tests cover the core
  functional modules that exist; coverage thresholds attach as `schema/` and
  `analyzers/` land.

## Decisions

### Decision 1: `src/` layout with hatchling

Use a PEP 621 `pyproject.toml` with hatchling and `src/cerebro/`. Rationale: the
locked stack specifies hatchling; `src/` layout prevents accidental imports of
the un-installed package during tests and matches Part II §3 exactly.
*Alternative considered:* flat layout — rejected; it lets tests import the
working tree instead of the installed package, hiding packaging bugs.

### Decision 2: One ruff for lint + format; mypy --strict from day one

Adopt ruff as both linter and formatter (one tool, per stack) and run
`mypy --strict` immediately. Rationale: turning strict typing on after code
exists is a painful retrofit; starting strict on a near-empty package is free.
*Alternative considered:* black + flake8 + isort — rejected; three tools where
ruff does all three.

### Decision 3: structlog JSON config centralized in `cerebro/logging.py`

Configure structlog once (processors: merge_contextvars, add_log_level, ISO
timestamper, stack/except info, JSONRenderer) exactly as Part II §8 specifies,
exposing a `configure_logging(level)` entrypoint and a `get_logger()` helper.
Correlation IDs are carried via `structlog.contextvars` so any call site logs
the bound `correlation_id` without threading it through signatures. The ASGI
correlation-ID middleware (binds/propagates `X-Request-ID`) is defined in M0 but
only *wired into* a FastAPI app in M1 when `api/app.py` exists.
*Alternative considered:* stdlib `logging` + JSON formatter — rejected; loses
contextvars binding and the no-f-string discipline structlog encourages
(invariant #6).

### Decision 4: Exception hierarchy as a standalone, dependency-free module

`cerebro/exceptions.py` defines `CerebroError(Exception)` as the base with a
structured `context: dict` attribute and the full descendant tree from Part II
§7. It imports nothing from the rest of `cerebro`, so every other module can
depend on it without cycles. Each error preserves cause chains
(`raise NewError(...) from original`).
*Alternative considered:* per-module exception definitions — rejected; a single
taxonomy is what lets the future FastAPI handler map any `CerebroError` to RFC
7807 in one place (invariant #5, distribution spec).

### Decision 5: Placeholder Docker (slim base) + CI that builds images

CI runs lint → typecheck → test, then attempts `docker build` on placeholder
Dockerfiles so the build job exists and fails loudly if context/paths drift. The
placeholders already use slim/alpine bases — bumped to the recent, security-
supported versions of Decision 10 (`python:3.12-slim` + uv for the backend,
`node:22-alpine` build → `nginx:1.27-alpine` runtime for the UI), pinned by
digest — so M4's production multi-stage build is a fill-in, not a rebase. M0
only proves the build step is wired.
*Alternative considered:* skip Docker in CI until M4 — rejected; wiring it now
catches path/context regressions cheaply, and the roadmap lists "build docker
images" under E1.005.

### Decision 6: uv + lockfiles for reproducible installs

Adopt **uv** as the Python package/dependency manager with a committed
`uv.lock`, and commit `pnpm-lock.yaml` for the UI; CI installs with
`uv sync --frozen` and `pnpm install --frozen-lockfile`. Rationale: faster,
reproducible, hash-locked installs; pins the toolchain so every machine and CI
run is identical. This *supersedes* the `pip install --user` flow in the locked
Part V Dockerfile — an explicitly user-authorized deviation, low-risk because
Part V is only a placeholder until M4.
*Alternative considered:* pip + `requirements.txt` as written in Part V —
rejected per the user's direction; uv gives lockfile reproducibility pip lacks
without a manual `pip-compile` step.

### Decision 7: OTel-ready, but no OTel dependency in M0

Keep structlog as the M0 observability stack (Part II §8). Shape
`logging.py` and the correlation-ID middleware so the `correlation_id` is held
in context in a way that maps cleanly onto a future OpenTelemetry trace/span
context — i.e. adding OTel later is a wiring change, not a refactor. No
`opentelemetry-*` dependency is added now.
*Alternatives considered:* (a) wire OTel now — rejected; it extends the locked
stack beyond Part II §8 and the roadmap defers real-time monitoring, so it would
be speculative weight in a scaffolding milestone. (b) ignore OTel entirely —
rejected; a few cheap shaping choices now avoid a later refactor.

### Decision 8: Formalize existing seams by *enforcement*, not new abstraction

"Enterprise design patterns" is scoped to codifying and mechanically enforcing
the seams the locked design already has — not adding new ones. Concretely: an
`ARCHITECTURE.md` documenting the layer boundary and the existing protocol/ports
seams (Extractor & LLMProvider protocols, storage repository, FastAPI DI), plus
**`import-linter`** contracts that enforce invariant #2 (no consumption module
imports `lightgbm`) and the layer dependency direction, and an **ESLint
boundaries** rule enforcing Part III §4 (no view calls `fetch` directly).
Rationale: this is the enterprise-grade rigor that *defends* the architecture
while honoring the KISS invariant that forbids "academic abstraction layers" and
premature patterns.
*Alternative considered:* introduce a DI container, repository+unit-of-work, and
service layer now — rejected; it directly violates `openspec/project.md`'s KISS
invariant and adds abstraction where no variation is yet proven.

### Decision 9: Contracts authored/seeded in M0, drift-gated in CI

Establish contract artifacts and the drift-detection harness in M0, applying
them as their sources land:

- `schemas/registry/v1/init.sql` — authored *now* in full from Part IV §4 (the
  DDL is completely specified there).
- `schemas/v1/` canonical JSON Schema and `contracts/openapi/openapi.json` —
  seeded as stubs in M0; the drift check (`model_json_schema()` vs committed,
  generated OpenAPI vs committed) becomes meaningful as the Pydantic models and
  FastAPI app land in M1+.
- Consumer-driven API↔UI gate — `pnpm api:types` regenerates UI types and CI
  fails on drift (Part III §7).

Rationale: contract-first for the parts that are already specified, contract-
*ready* for the parts that aren't, with CI gates wired from day one so drift can
never land silently.
*Alternative considered:* defer all contracts until their implementations exist
— rejected per the user's direction; wiring the gates now is cheap and the
registry DDL is already authoritative.

### Decision 10: Recent, security-supported runtimes (pinned)

Pin to current, security-supported runtime versions rather than the exact
numbers in the locked doc: **Python 3.12** (satisfies the constitution's
"3.11+", and has the broadest binary-wheel coverage for the lightgbm/shap/numpy
stack — safer than 3.13 for those wheels today) and **Node 22 LTS**. Pin uv (via
`setup-uv`) and pnpm (via the `packageManager` field) too, and pin Docker bases
by digest. Rationale: "recent + secure" without chasing the bleeding edge that
the scientific wheels may not yet support.
*Alternatives considered:* (a) keep the doc's `python:3.11-slim` / `node:20` —
rejected per the user's direction for recent+secure; (b) Python 3.13 / Node 24 —
rejected for M0 as the riskier edge for lightgbm/shap wheels and not yet LTS
(Node 24), revisitable later.

### Decision 11: Tests run in parallel; M0 covers core functionality only

Two distinct things the user asked for. **Parallelism** (suite speed): adopt
`pytest-xdist` with `-n auto` as the default; Vitest is already parallel. Tests
must be isolation-safe (no shared tmp/DB/global state) to run under xdist.
**Concurrency** (behavior under load): add a targeted test that the logging
`correlation_id` stays isolated across concurrent asyncio tasks and threads
(the M0-relevant concurrency surface); the registry's single-writer/WAL
concurrent-reader semantics (Part IV §8) get their concurrency tests in M4 when
that module lands. **Core-only coverage:** M0 gates tests on the core functional
modules that exist (`logging`, `exceptions`) — not all scaffolding needs tests
now; the project's ≥80%/≥60% coverage targets attach to `schema/`+`analyzers/`
as they arrive (MVP-1 acceptance), not to this milestone.
*Alternative considered:* enforce a global coverage threshold from M0 — rejected
per the user's direction; it would force busywork tests on inert scaffolding.

## Risks / Trade-offs

- **Heavy ML deps slow CI from M0** → declare `lightgbm`/`shap` in
  `pyproject.toml` but keep them out of the default install/test path in M0
  (install only lint/type/test extras in the relevant CI job); exercise them
  starting M1.
- **mypy --strict friction on near-empty modules** → minimal; the two real
  modules (`logging`, `exceptions`) are small and fully typed, so strict mode is
  a benefit, not a tax.
- **shadcn init churn** → pin shadcn/Radix and Tailwind versions in the UI
  lockfile so `pnpm install --frozen-lockfile` in CI is reproducible.
- **Placeholder Dockerfiles diverge from M4 reality** → mark them clearly as
  placeholders; M4's distribution work replaces them and updates the
  `distribution` spec accordingly.

## Open Questions

- None blocking. Runtime majors are pinned (Decision 10: Python 3.12, Node 22
  LTS); exact patch/minor pins for shadcn/Radix and the dev toolchain are settled
  during implementation against the lockfiles.
