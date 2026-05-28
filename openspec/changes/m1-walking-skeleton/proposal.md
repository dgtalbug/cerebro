# Walking Skeleton — proposal

> **Spec reference:** Implements `.docs/cerebro-open-spec.md` Part VI §3 (MVP 1
> task list E1.008–E1.016). Schema, extractor, storage, CLI, and API surfaces
> are constrained by Part I §6, Part II §5, §6, §7, §8, and Part III §3, §4, §6.

## What

A single vertical slice that proves the whole pipeline works end to end:

> train a tiny binary LightGBM model → extract a canonical JSON artifact →
> load it via the API → render it in the Overview view of the dashboard.

That is the entire product surface for this change. Everything else stays
unbuilt until later changes.

## Why

The pipeline has eight independently-designed layers (schema, extractor,
storage, CLI, API, UI shell, Overview view, integration test). Each layer is
small in isolation but their seams are the riskiest surface in the product.
A walking skeleton wires them together at minimum depth, surfaces every seam
defect immediately, and yields a binary signal — *the artifact a real model
produces is the same artifact the dashboard renders* — that every later
milestone is built on top of.

Without this slice, an extractor change can pass its own tests while
silently breaking what the API serves or what the dashboard expects.
With it, we have a single end-to-end test that catches that class of
regression before it leaves a PR.

## Scope

**In scope — binary classifier only**

1. Pydantic v2 models for the canonical schema, JSON-Schema export, and the
   freeze of `schemas/v1/`.
2. LightGBM extractor for the **binary** objective only, via
   `Booster.dump_model()`.
3. Filesystem read/write with gzip and validation-on-read.
4. `cerebro extract` and `cerebro validate` CLI commands.
5. FastAPI app exposing `GET /health` and `GET /artifacts/{id}`.
6. Design tokens lifted verbatim from the mockup + UI shell (TopBar,
   Sidebar, ViewHeader, theme toggle).
7. Overview view wired to the API via TanStack Query.
8. End-to-end test from a fixture model through to a rendered Overview.

**Out of scope (deferred to later changes)**

- Multiclass, regression, ranker, multi-output extraction.
- SHAP, decision-path tracing, partial dependence.
- Evaluation metrics (no AUC, no confusion matrix — the Overview metric tile
  renders `—` with subtitle "no samples at extraction time").
- All views other than Overview (Trees, Importance, Explanations, Evaluation,
  Agent, Schema, Data, Artifacts list).
- SQLite registry, listing/filtering, indexing.
- The `POST /artifacts`, `POST /artifacts/{id}/validate`, and sub-resource
  endpoints (`/model`, `/trees`, `/importance`, `/explanations`,
  `/evaluation`) — the full-artifact endpoint covers every Overview need at
  this size.
- Docker production packaging (the placeholder Dockerfiles stay placeholders;
  compose still works as the dev-loop surface).

## How — eight tasks in dependency order

The numbering matches the task list given by the change owner. Backend tasks
1→5 are sequential because the schema gates everything downstream. Frontend
tasks (6a, 6b, 7) can be developed in parallel with backend tasks 2–5 once
the API contract is frozen by task 1. Task 8 lands last as the done-signal.

| # | Task | Spec | Acceptance check |
|---|------|------|------------------|
| 1 | `schema/v1/` Pydantic models + JSON-Schema export | Part I §6, Part II §4.2 | `python -c "from cerebro.schema.v1 import CerebroArtifact; CerebroArtifact.model_validate_json(...)"` round-trips a known-good fixture; the exported JSON Schema diff against `schemas/v1/cerebro.schema.json` is empty in CI. |
| 2 | `extractors/base.py` Protocol + `extractors/lightgbm.py` (binary only) | Part II §5, Part I §6 | A tiny in-fixture binary booster extracts to a `CerebroArtifact` with `model.objective == "binary"`, non-empty `trees`, and `importance.gain` populated. |
| 3 | `storage/files.py` — gzipped read/write + validation-on-read | Part I §8 ("fail fast at boundaries"), Part II §4 | Writing then reading an artifact produces a byte-identical Pydantic instance; a corrupt file raises `CorruptArtifactError` with structured `context`. |
| 4 | `cerebro extract` and `cerebro validate` CLI via typer | Part II §6 (Distribution: CLI) | `cerebro extract <model> --output art.cerebro.json` produces a file that passes `cerebro validate art.cerebro.json` with exit code 0; a tampered file exits non-zero with an RFC-7807-ish error body. |
| 5 | `api/app.py` FastAPI bootstrap with `/health` and `/artifacts/{id}` + correlation-ID middleware + exception handler | Part II §6, §7, §8 | `GET /health` returns `{"status":"ok","version":<pkg ver>,"schema_version":"1.0.0"}`; `GET /artifacts/{id}` round-trips the canonical artifact; a missing id returns 404 with RFC-7807 body and a correlation ID in both response header and log. |
| 6a | Design tokens lifted verbatim from `.docs/cerebro-dashboard.html`: `ui/src/styles/tokens.css`, `ui/tailwind.config.ts` extension, `ui/src/lib/theme.ts` (Zustand + `applyTheme` + `prefers-color-scheme` on first load) | Part III §8 | `data-theme="dark"` and `data-theme="light"` cycle visibly; `localStorage["cerebro-theme"]` persists; every shadcn primitive picks up the mapped tokens; no hardcoded hex in any TS/TSX file. |
| 6b | UI shell: `TopBar`, `Sidebar`, `ViewHeader`, theme-toggle component | Part III §3, §4 | Side-by-side comparison against the mockup shows the shell layout, typography, grain, and glow match. Theme toggle round-trips. |
| 7 | Overview view consuming `GET /artifacts/{id}` via TanStack Query | Part III §6 (state mgmt: TanStack Query), Part VI §3 (F1.13) | Rendering the route against the fixture artifact shows objective, tree count, feature count, headline-metric tile (with `—` for M1), training params, and feature schema — laid out exactly as the mockup specifies. |
| 8 | End-to-end test | Part II §9 (testing strategy) | Single pytest test: train a 50-tree binary `LGBMClassifier` on `make_classification(n=500)` → `cerebro extract` → `TestClient(app).get("/artifacts/{id}")` → assert the JSON's `model.objective`, `trees` count, and `importance.gain` keys match the trained model. This test is the M1 done-signal. |

## Schema freeze

When task 1 lands, **schema v1.0.0 is frozen.** No in-place edits to
`schemas/v1/` or `cerebro/schema/v1/` after that point. A future breaking
change creates a new folder (`schemas/v1.1/` or `schemas/v2/`); a future
additive change becomes a separate proposal that explicitly bumps the
schema version. This matches Part I §6 and project invariant #3.

## Constraints carried forward

These bind every task in this change without restatement in each commit:

- **No spec identifiers** (`M1`, `E1.014`, change-folder names, milestone tags)
  in source code, comments, log fields, or runtime artifacts. Domain language
  only.
- **Exception hierarchy** per Part II §7: no bare `except:` / `except Exception:`
  in library code; only at process boundaries (CLI entry, FastAPI exception
  handler). Every catch handles, transforms-and-rethrows with `raise NewError(...)
  from original`, or log-and-rethrows. Errors carry a structured `context`
  dict.
- **Logging** per Part II §8: structlog JSON, fields not f-strings,
  correlation ID bound at request entry and propagated via `contextvars`, no
  PII / secrets / model contents.
- **Fail fast at boundaries**: validate the source model on load, validate the
  canonical JSON on read, never carry malformed state deeper into the
  pipeline.
- **Code intelligence first**: every task runs `gitnexus_search` for relevant
  symbols *before* creating new modules, and `npx gitnexus analyze` *after*
  the commit lands.
- **Commit hygiene**: one Conventional Commit per task (no megacommits, no
  AI-attribution trailers).

## Dependencies

This change depends on what is already in `main` post-`bootstrap-m0-scaffolding`:

- `cerebro.logging` and `cerebro.exceptions` modules (used by tasks 2–5).
- `import-linter` contracts that enforce extraction-vs-consumption boundary.
- Quality gates: `ruff`, `mypy --strict`, `pytest -n auto`, `lint-imports`,
  `pnpm lint`, `pnpm typecheck`, `pnpm build`, `pnpm test`,
  `scripts/check_contracts.py`.
- The dep modernization from `PR #2` (latest pytest, vitest, vite, etc.).

This change does **not** depend on a separate design-tokens proposal — the
token extraction and the shell that consumes it are folded into task 6 as
6a → 6b for the reason stated in the "Surprises" note in `design.md`.

## Acceptance — the full change ships when

- [ ] All 8 tasks above pass their individual acceptance checks (one commit
      per task, all green on CI).
- [ ] `openspec validate m1-walking-skeleton --strict` is clean.
- [ ] The end-to-end test in task 8 passes locally and on CI.
- [ ] Quality gates (`ruff check`, `ruff format --check`, `mypy`,
      `lint-imports`, `pytest -n auto`, UI lint/typecheck/build/test,
      contract drift) are all green on the final commit.
- [ ] `schemas/v1/cerebro.schema.json` exists, matches the Pydantic export,
      and is referenced from the proposal's "Schema freeze" section.
- [ ] No hardcoded colors, fonts, or radii in any UI file outside
      `ui/src/styles/tokens.css`.
- [ ] No `M1` / `E1.xxx` / change-folder identifiers anywhere in code,
      comments, or log fields.
- [ ] `openspec/specs/canonical-schema/spec.md`, `extraction/spec.md`,
      `registry/spec.md`, `distribution/spec.md`, and `dashboard/spec.md`
      reflect the new requirements after sync.

## Risks and how we mitigate them

| Risk | Mitigation |
|------|------------|
| Schema v1.0.0 lands then immediately needs revision. | Task 1's acceptance includes round-tripping a fixture; the JSON-Schema export is contract-drift-gated in CI so any unintended change shows up immediately. |
| LightGBM's `dump_model()` output evolves between minor versions. | Pin lightgbm version range in `pyproject.toml`, snapshot-test the extractor output against a committed JSON fixture. |
| Overview view drifts visually from the mockup. | Side-by-side comparison is part of task 6b/7 acceptance; design tokens are extracted verbatim, no re-derivation. |
| API↔UI contract drifts. | `pnpm api:types` already runs in CI; the drift check fails the build if the API's OpenAPI changes without regenerating `schema.d.ts`. |
| Gzipped artifacts break stdout streaming. | `cerebro extract` writes to a file path, never to stdout; `.cerebro.json` files always have the gzip envelope when on disk, transparent to callers. |

## What this change deliberately leaves for later

- Multi-variant extractors (multiclass, regression, ranker, multi-output) →
  next change, scoped per Part VI §3 M2.
- Importance (`split`, `permutation`), explanations, evaluation, decision
  paths → M2 / M3.
- Registry + `cerebro index` → M4.
- Production Docker packaging → M4.
- Every view other than Overview → M2 / M3 / M4.

The walking skeleton is intentionally narrow. Each later change adds one
capability at a time, anchored to the artifact the skeleton already
produces.
