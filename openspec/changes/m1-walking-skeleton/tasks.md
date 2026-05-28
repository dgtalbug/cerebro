# Walking Skeleton — tasks

> Implementation runs in this order. Each task lands as exactly one
> Conventional Commit (Subject lines specified inline). Before creating
> any new module, run `gitnexus_search` for similar names; after each
> commit lands, run `npx gitnexus analyze` so the next task starts on a
> fresh index. No `Co-Authored-By` trailers anywhere.

## Task 1 — Pydantic v2 canonical schema + JSON-Schema export

**Spec:** `.docs/cerebro-open-spec.md` Part I §6, Part II §4.2.
**Commit:** `feat(schema): canonical artifact schema v1.0.0 (Pydantic + JSON Schema)`

- [x] `gitnexus_search` for `Artifact`, `Tree`, `Node`, `FeatureSchema`, `Source`, `Importance`, `Model` — confirm none exist as Python symbols today. (verified via grep over `src/`, `tests/` — zero collisions)
- [x] Create `src/cerebro/schema/__init__.py` (re-exports `v1` symbols).
- [x] Create `src/cerebro/schema/v1/__init__.py` re-exporting `CerebroArtifact`, `Source`, `Model`, `FeatureSchema`, `Tree`, `TreeNode`, `Importance`.
- [x] Create `src/cerebro/schema/v1/artifact.py` with the `CerebroArtifact` model (`schema_version: Literal["1.0.0"]`).
- [x] Create `src/cerebro/schema/v1/source.py`, `model.py`, `tree.py`, `importance.py` matching the shape defined in `design.md`.
- [x] Add a `model_config = ConfigDict(extra="forbid", frozen=True)` to every model so unknown keys fail validation.
- [x] Replace the seed-stub at `schemas/v1/cerebro-artifact.schema.json` with the real export from `CerebroArtifact.model_json_schema()` (committed bytes). Filename corrected to match the file that already exists from M0.
- [x] Extend `scripts/check_contracts.py` with a real `check_canonical_schema` that compares the committed file to `render_schema()` output; CI fails on any drift. `scripts/export_schema.py` is the regeneration entrypoint.
- [x] `tests/schema/test_round_trip.py`: round-trip a known-good fixture artifact through `model_validate_json` and `model_dump_json`; bytes are stable.
- [x] `tests/schema/test_extra_keys_rejected.py`: extra keys in any nested object raise `SchemaValidationError`. Plus a separate assertion that `explanations` and `evaluation` reject any non-None value (the v1.0.0 lock).
- [x] **Schema freeze.** No further edits to `schemas/v1/` or `cerebro/schema/v1/` in subsequent tasks.
- [x] `uv run pytest tests/schema -n auto` passes (11/11 in 0.93s; full suite 40/40).
- [x] `npx gitnexus analyze` after commit.

## Task 2 — Extractor protocol + LightGBM binary extractor

**Spec:** `.docs/cerebro-open-spec.md` Part II §5, Part I §6.
**Commit:** `feat(extractor): lightgbm binary extractor via Booster.dump_model`

- [x] `gitnexus_search` for `Extractor`, `LGBExtractor`, `lightgbm` — confirm no extractors exist yet. (verified via grep; the M0 stub at `src/cerebro/extractors/__init__.py` was empty)
- [x] Create `src/cerebro/extractors/__init__.py` — re-exports `Extractor`, `LGBExtractor`.
- [x] Create `src/cerebro/extractors/base.py` defining `Extractor` as a `@runtime_checkable Protocol` with `extract(model_path: str | Path) -> CerebroArtifact`.
- [x] Create `src/cerebro/extractors/lightgbm.py` with `LGBExtractor` implementing that protocol — accepts a model file path, loads via `lightgbm.Booster(model_file=...)`, calls `booster.dump_model()`, builds a `CerebroArtifact`.
- [x] Binary-only guard: if `objective` isn't `binary`, raise `UnsupportedObjectiveError` with `context = {"objective": <found>}`. LightGBM stores objective as `"<name> <args>"`; we parse the leading keyword.
- [x] Map `dump_model()` fields to canonical schema: `tree_info` → `trees[]` (with `class_index=None`), `feature_names` → `model.feature_schema.names`, importance via `booster.feature_importance(importance_type="gain"/"split")`. Categorical indices resolved from `Booster.params["categorical_feature"]` (canonical declaration); `feature_infos` heuristic dropped after early test exposed mis-classification.
- [x] Set `permutation = None`, `explanations = None`, `evaluation = None`.
- [x] No bare excepts; load-time `(lightgbm.basic.LightGBMError, FileNotFoundError, OSError)` are transformed via `raise CorruptArtifactError(...) from original` with structured context. Unexpected `decision_type` operators also fail with `CorruptArtifactError`.
- [x] Node ids re-numbered with a monotonic per-tree counter so they're unique within a tree (LightGBM's `split_index` and `leaf_index` are independent sequences and can collide).
- [x] Added `lightgbm>=4.6,<5`, `scikit-learn>=1.8,<2`, `numpy>=2.4,<3` to `[dependency-groups].dev` so `uv sync` installs them; mypy override for untyped `lightgbm.*` / `sklearn.*` imports.
- [x] `tests/extractors/test_lightgbm_binary.py`: train a 10-tree `LGBMClassifier` (`make_classification(n=200, n_features=8)`), extract, assert objective, tree count, importance keys, locked-None fields, schema round-trip, and unique node ids.
- [x] `tests/extractors/test_unsupported_objective.py`: a regression booster raises `UnsupportedObjectiveError` with `context["objective"] == "regression"`.
- [x] `tests/extractors/test_corrupt_model.py`: missing path raises `CorruptArtifactError`; a non-model text file raises `CorruptArtifactError`.
- [x] `uv run lint-imports` still green (extractors-only-imports-lightgbm contract holds — 2 contracts kept, 0 broken).
- [x] `pytest -n auto`: 49/49 passed in ~2 s (9 new extractor tests + 40 prior).
- [x] `npx gitnexus analyze` after commit.

## Task 3 — Filesystem read/write with gzip and validate-on-read

**Spec:** `.docs/cerebro-open-spec.md` Part I §8 (fail fast at boundaries), Part VI §3 F1.12 (gzip-on-disk).
**Commit:** `feat(storage): gzipped .cerebro.json read/write with validate-on-read`

- [x] `gitnexus_search` for `read_artifact`, `write_artifact`, `cerebro.storage` — verified no collisions (storage package was empty M0 stub).
- [x] Update `src/cerebro/storage/__init__.py` to re-export `read_artifact`, `write_artifact`.
- [x] Create `src/cerebro/storage/files.py` exposing `write_artifact(artifact: CerebroArtifact, path: Path) -> None` and `read_artifact(path: Path) -> CerebroArtifact`.
- [x] Write path: `model_dump_json` -> utf-8 -> `gzip.compress` -> sibling `.tmp` file -> `Path.replace` for atomic rename. Parent directories created on demand via `mkdir(parents=True, exist_ok=True)`.
- [x] Read path: `gzip.decompress(path.read_bytes())` -> `CerebroArtifact.model_validate_json`. `(gzip.BadGzipFile, OSError, EOFError)` and `pydantic.ValidationError` are transformed via `raise CorruptArtifactError(...) from original` with `context = {"artifact_path": str(path)}`.
- [x] Missing path raises `ArtifactNotFoundError` with structured context.
- [x] Hoist `binary_artifact_dict` and add `binary_artifact` (parsed instance) fixtures into top-level `tests/conftest.py` so schema, storage, and future tests share one source of truth.
- [x] `tests/storage/test_round_trip.py`: write then read produces an equal model; on-disk bytes start with gzip magic (`1f 8b`); parent directories are created on demand.
- [x] `tests/storage/test_atomic_write.py`: no `.tmp` left after success; second write replaces first; recovered model reflects the second write.
- [x] `tests/storage/test_corrupt_input.py`: three modes — random bytes (not gzip), gzip of malformed JSON, gzip of JSON missing required fields — each raises `CorruptArtifactError`.
- [x] `tests/storage/test_missing_path.py`: missing file raises `ArtifactNotFoundError` with context.
- [x] All gates green: ruff, mypy strict (37 files), lint-imports (2/2 kept), pytest -n auto (58/58 in ~2 s; 9 new storage tests).
- [x] `npx gitnexus analyze` after commit.

## Task 4 — CLI: `cerebro extract` and `cerebro validate`

**Spec:** `.docs/cerebro-open-spec.md` Part II §6 (Distribution: CLI), Part VI §3 F1.25.
**Commit:** `feat(cli): cerebro extract and cerebro validate commands (binary)`

- [x] `gitnexus_search` for `cli`, `typer`, `extract_command`, `validate_command` — confirmed no symbol collisions (M0 CLI package was empty stub).
- [x] Create `src/cerebro/cli/__init__.py` (exports `app`) and `src/cerebro/cli/main.py` exposing `app = typer.Typer(...)` with the project description and `no_args_is_help=True`.
- [x] `extract`: `cerebro extract <model> --output <file>` (also `-o`). Loads via `LGBExtractor`, writes via `storage.write_artifact`. Exit 0 on success with a one-line summary; non-zero on any `CerebroError`.
- [x] `validate`: `cerebro validate <artifact>`. Reads via `storage.read_artifact` — the same path the API uses, so a green validate is a strong signal the API will serve the file.
- [x] Process-boundary exception handler: `@_handle_cerebro_errors` decorator catches `CerebroError`, logs at `error` level with structured context, prints `error: <Class>: <message>` to stderr, exits with the mapped code. Uses PEP 695 `[**P]` generic syntax so typer can introspect parameters through the wrapper. No bare excepts; non-`CerebroError` exceptions propagate so genuine bugs surface with tracebacks.
- [x] Stable exit codes: `ArtifactNotFoundError` → 2, `CorruptArtifactError` → 3, `UnsupportedObjective` / `UnsupportedFramework` → 4, other `CerebroError` → 1.
- [x] Wire `cerebro` console-script entry in `pyproject.toml` under `[project.scripts]` (M0 had it deferred).
- [x] Add `typer>=0.26,<1`, `fastapi>=0.136,<1`, `uvicorn[standard]>=0.48,<1` to `[dependency-groups].dev` (mirrors the `[api]` optional-extra so CLI/API tests run under `uv sync` without an explicit extra).
- [x] `tests/cli/test_extract_validate.py`: happy path via `typer.testing.CliRunner` — extract → validate → exit 0; `-o` short flag works.
- [x] `tests/cli/test_error_paths.py`: missing file → exit 2; corrupt gzip → exit 3; schema-invalid JSON → exit 3; regression model → exit 4 with no partial output file.
- [x] All gates green: ruff, mypy --strict (41 files), lint-imports (2/2 kept), pytest -n auto (64/64 in ~2.5 s, +6 CLI tests).
- [x] `npx gitnexus analyze` after commit.

## Task 5 — FastAPI bootstrap: `/health`, `/artifacts/{id}`, middleware, exception handler

**Spec:** `.docs/cerebro-open-spec.md` Part II §6, §7, §8.
**Commit:** `feat(api): fastapi bootstrap with /health and /artifacts/{id}`

- [x] `gitnexus_search` for `FastAPI`, `app`, `correlation_id`, `exception_handler` — confirmed no collisions; M0 stubs (`api/__init__.py`, `api/routes/__init__.py`) were empty.
- [x] Create `src/cerebro/api/__init__.py` (exports `app`, `create_app`), `src/cerebro/api/app.py` (factory + module-level `app`), `src/cerebro/api/deps.py`, `src/cerebro/api/handlers.py`.
- [x] `app.py`: `app = FastAPI(title="Cerebro", version=__version__, openapi_url="/openapi.json", docs_url="/docs", redoc_url="/redoc")`. Mounts `CorrelationIdMiddleware` from `cerebro.logging` (pure ASGI, framework-agnostic) and the `CerebroError` exception handler.
- [x] `GET /health` returns `{"status": "ok", "version": <pkg version>, "schema_version": "1.0.0"}` via a typed `HealthBody` Pydantic response model.
- [x] `GET /artifacts/{id}` resolves the path via `deps.get_artifact_loader` (DI uses `Annotated[Path, Depends(get_artifact_dir)]` so test overrides propagate cleanly), reads via `storage.read_artifact`, returns the validated artifact. `response_model=CerebroArtifact` so the OpenAPI doc embeds the canonical schema.
- [x] Correlation-ID middleware reuses the existing `cerebro.logging.CorrelationIdMiddleware` (pure ASGI). Reads `X-Request-ID` or generates `uuid4().hex` (32-hex OTel trace-id shape), binds via `structlog.contextvars`, echoes header on every response, clears in `finally`.
- [x] Single `cerebro_error_handler` registered with `app.add_exception_handler(CerebroError, ...)`. Walks `__mro__` so subclasses resolve to the nearest mapped status; RFC-7807 body with `type`, `title`, `status`, `detail`, `instance`, `correlation_id`, and JSON-safe `context`. Header injection left to middleware (avoid duplicate-header drift).
- [x] Wired `scripts/export_openapi.py` (mirrors `export_schema.py` — `app.openapi()` → sorted JSON → committed bytes). `contracts/openapi/openapi.json` now matches the live FastAPI app.
- [x] Extended `scripts/check_contracts.py` with an active OpenAPI drift gate; the gate now reports `OK` instead of `PENDING`.
- [x] `tests/api/test_health.py`: `GET /health` returns the expected body; correlation-ID middleware echoes a client-supplied id.
- [x] `tests/api/test_artifacts.py`: existing artifact returns 200 with the canonical shape; missing id → 404 RFC-7807 body; corrupt gzip → 422; schema-invalid → 422; error body's `correlation_id` matches the response header.
- [x] `tests/api/test_correlation_id.py`: client-supplied id preserved; generated id matches the 32-hex trace-id shape; ids do not bleed across requests.
- [x] All gates green: ruff, mypy --strict (51 source files), lint-imports (2/2 kept), pytest -n auto (74/74 in ~3 s, +10 API tests), all three contract checks (registry / canonical schema / OpenAPI) OK.
- [x] `npx gitnexus analyze` after commit.
- [ ] `import-linter` still green (api imports schema + storage + exceptions; no `lightgbm`).
- [ ] `npx gitnexus analyze` after commit.

## Task 6a — Design tokens lifted verbatim from the mockup

**Spec:** `.docs/cerebro-open-spec.md` Part III §8.
**Commit:** `feat(ui): design tokens from mockup (tokens.css, tailwind, theme.ts)`

- [ ] `gitnexus_search` for `tokens.css`, `theme.ts`, `applyTheme`, `useTheme` — confirm none exist.
- [ ] Create `ui/src/styles/tokens.css` containing the 28 dark + 23 light tokens **verbatim** from `.docs/cerebro-dashboard.html`. No re-derivation, no HSL alts, no opinionated additions. Plus a `:root` block aliasing the shadcn token names (`--background`, `--foreground`, `--card`, ...) to the mockup tokens, as the mapping table in `design.md` specifies.
- [ ] Edit `ui/src/globals.css` to `@import "./styles/tokens.css"` *before* the `@tailwind` directives.
- [ ] Rewrite `ui/tailwind.config.ts` to extend `theme.colors`, `theme.fontFamily`, `theme.borderRadius` via `var(--…)` references (no hex values in the config).
- [ ] Create `ui/src/lib/theme.ts` — Zustand store with `theme: "dark" | "light"`, `setTheme(...)`, `toggleTheme()`. `applyTheme(theme)` writes `data-theme` to `document.documentElement` and persists to `localStorage["cerebro-theme"]`. On first load: prefer the stored value; if absent, read `window.matchMedia("(prefers-color-scheme: dark)")`.
- [ ] Export `useTheme()` from the same file as a thin wrapper around the Zustand hook.
- [ ] No hardcoded colors anywhere in `ui/src/**/*.ts(x)`. Comments explain token intent in design terms, never spec / milestone identifiers.
- [ ] `pnpm typecheck`, `pnpm build`, `pnpm test` all green.
- [ ] `npx gitnexus analyze` after commit.

## Task 6b — UI shell components

**Spec:** `.docs/cerebro-open-spec.md` Part III §3, §4.
**Commit:** `feat(ui): app shell — topbar, sidebar, viewheader, theme toggle`

- [ ] `gitnexus_search` for `TopBar`, `Sidebar`, `ViewHeader`, `ThemeToggle`.
- [ ] Create `ui/src/components/layout/TopBar.tsx`, `Sidebar.tsx`, `ViewHeader.tsx` matching the mockup layout, typography, grain, and glow.
- [ ] Create `ui/src/components/brand/BrandMark.tsx` (concentric-rings logo as the mockup defines).
- [ ] Create `ui/src/components/ui/ThemeToggle.tsx` consuming `useTheme()` from task 6a.
- [ ] Update `ui/src/App.tsx` to wire the shell around the routed view region.
- [ ] Side-by-side comparison against `.docs/cerebro-dashboard.html` for the shell shows matching shapes; the theme toggle round-trips dark↔light visibly.
- [ ] `pnpm lint`, `pnpm typecheck`, `pnpm build`, `pnpm test` all green.
- [ ] `npx gitnexus analyze` after commit.

## Task 7 — Overview view wired to the API

**Spec:** `.docs/cerebro-open-spec.md` Part III §6 (state mgmt), Part VI §3 F1.13.
**Commit:** `feat(ui): overview view rendering artifact via tanstack query`

- [ ] `gitnexus_search` for `Overview`, `useArtifact`.
- [ ] Create `ui/src/lib/api/queries.ts` (or extend the existing one) with `useArtifact(id: string)` calling `GET /artifacts/{id}` via the openapi-typed `fetch`. `staleTime: 5 * 60 * 1000` (artifacts are immutable per Part III §6 example).
- [ ] Create `ui/src/views/Overview.tsx`:
  - 4-stat top row: Objective, Trees (= `model.num_iteration`), Features (= `model.feature_schema.names.length`), Headline metric (`—` for M1, subtitle "no samples at extraction time").
  - Training params panel: render every key/value pair from `model.params` with `tnum` class on values.
  - Feature schema panel: index, name, type (`numeric` blue / `categorical` purple based on `categorical_indices`), const column (mono+ / mono- / — based on `monotone_constraints`).
- [ ] Loading state, error state, and 404 state surface the relevant message — never silent.
- [ ] `tests/ui/Overview.test.tsx`: render against a mocked `useArtifact` returning a fixture; assert objective, tree count, params count, feature rows render correctly.
- [ ] `pnpm api:types` regenerates `ui/src/lib/api/schema.d.ts` against the live `/openapi.json`; commit no drift.
- [ ] `npx gitnexus analyze` after commit.

## Task 8 — End-to-end test

**Spec:** `.docs/cerebro-open-spec.md` Part II §9 (testing strategy).
**Commit:** `test(e2e): walking skeleton — train, extract, serve, render`

- [ ] `gitnexus_search` for `e2e`, `walking_skeleton`.
- [ ] Create `tests/e2e/test_walking_skeleton.py`:
  - Train 50-tree binary `LGBMClassifier` on `make_classification(n_samples=500, n_features=24, random_state=42)`.
  - Run `cerebro.cli.main.app` via `CliRunner` (or call the extract function directly) with the trained booster's saved model file and a `tmp_path` output.
  - Read the file back via `storage.files.read_artifact` and assert the schema is satisfied.
  - Spin up a `TestClient(app)` with `CEREBRO_DATA_DIR` pointed at `tmp_path`; `client.get(f"/artifacts/{id}")` returns 200 and the asserted shape (see `design.md` "What the e2e test asserts").
- [ ] (UI side, optional but valuable) — Add a vitest test that renders `Overview` against the e2e fixture JSON loaded statically; the test catches divergence between the Pydantic export and the TS contract.
- [ ] All quality gates green: `ruff`, `ruff format --check`, `mypy`, `lint-imports`, `pytest -n auto`, `pnpm lint`, `pnpm typecheck`, `pnpm build`, `pnpm test`, `python scripts/check_contracts.py`.
- [ ] `npx gitnexus analyze` after commit.
- [ ] `openspec validate m1-walking-skeleton --strict` is clean.
