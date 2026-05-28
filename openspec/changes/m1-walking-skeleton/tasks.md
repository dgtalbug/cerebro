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

- [ ] `gitnexus_search` for `Extractor`, `LGBExtractor`, `lightgbm` — confirm no extractors exist yet.
- [ ] Create `src/cerebro/extractors/__init__.py`.
- [ ] Create `src/cerebro/extractors/base.py` defining `Extractor` as a `Protocol` with `extract(model_path: str | Path) -> CerebroArtifact`.
- [ ] Create `src/cerebro/extractors/lightgbm.py` with `LGBExtractor` implementing that protocol — accepts a model file path, loads via `lightgbm.Booster(model_file=...)`, calls `booster.dump_model()`, builds a `CerebroArtifact`.
- [ ] Binary-only guard: if `objective` isn't `binary`, raise `UnsupportedObjectiveError` with `context = {"objective": <found>}`.
- [ ] Map `dump_model()` fields to canonical schema: `tree_info` → `trees[]` (with `class_index=None`), `feature_names` → `model.feature_schema.names`, importance via `booster.feature_importance(importance_type="gain"/"split")`.
- [ ] Set `permutation = None`, `explanations = None`, `evaluation = None`.
- [ ] No bare excepts; any `lightgbm` exception transforms via `raise CorruptArtifactError(...) from original` with structured context.
- [ ] `tests/extractors/test_lightgbm_binary.py`: train a 20-tree `LGBMClassifier` on `make_classification(n=200, n_features=8)`, extract, assert `model.objective == "binary"`, `len(trees) == 20`, `importance.gain` keyed by all feature names.
- [ ] `tests/extractors/test_unsupported_objective.py`: a regression model raises `UnsupportedObjectiveError`.
- [ ] `uv run lint-imports` still green (extractors-only-imports-lightgbm contract holds).
- [ ] `npx gitnexus analyze` after commit.

## Task 3 — Filesystem read/write with gzip and validate-on-read

**Spec:** `.docs/cerebro-open-spec.md` Part I §8 (fail fast at boundaries), Part VI §3 F1.12 (gzip-on-disk).
**Commit:** `feat(storage): gzipped .cerebro.json read/write with validate-on-read`

- [ ] `gitnexus_search` for `read_artifact`, `write_artifact`, `cerebro.storage`.
- [ ] Create `src/cerebro/storage/__init__.py`.
- [ ] Create `src/cerebro/storage/files.py` exposing `write_artifact(artifact: CerebroArtifact, path: Path) -> None` and `read_artifact(path: Path) -> CerebroArtifact`.
- [ ] Write path: serialize via `artifact.model_dump_json(indent=None)`, gzip-encode, write atomically (write to `path.with_suffix(path.suffix + ".tmp")`, then rename).
- [ ] Read path: open with `gzip.open(...)`, parse via `CerebroArtifact.model_validate_json(...)`. Catch `gzip.BadGzipFile`, `pydantic.ValidationError`, raise `CorruptArtifactError(...) from original` with `context = {"artifact_path": str(path)}`.
- [ ] Missing path raises `ArtifactNotFoundError`.
- [ ] `tests/storage/test_round_trip.py`: write then read produces an equal model.
- [ ] `tests/storage/test_corrupt_input.py`: a file with junk bytes raises `CorruptArtifactError`.
- [ ] `tests/storage/test_missing_path.py`: missing file raises `ArtifactNotFoundError`.
- [ ] `npx gitnexus analyze` after commit.

## Task 4 — CLI: `cerebro extract` and `cerebro validate`

**Spec:** `.docs/cerebro-open-spec.md` Part II §6 (Distribution: CLI), Part VI §3 F1.25.
**Commit:** `feat(cli): cerebro extract and cerebro validate commands (binary)`

- [ ] `gitnexus_search` for `cli`, `typer`, `extract_command`, `validate_command`.
- [ ] Create `src/cerebro/cli/__init__.py` and `src/cerebro/cli/main.py` exposing `app = typer.Typer()`.
- [ ] `extract`: `cerebro extract <model> --output <file>`. Loads model via `LGBExtractor`, writes via `storage.files.write_artifact`. Exit code 0 on success, non-zero on `CerebroError`.
- [ ] `validate`: `cerebro validate <file>`. Reads via `storage.files.read_artifact`. Exit code 0 if validation passes, non-zero with structured stderr otherwise.
- [ ] Process-boundary exception handler: catch `CerebroError`, log via structlog at `error`, print a one-line summary to stderr, exit with the right code. Never bare-`except`.
- [ ] Wire `cerebro` console-script entry in `pyproject.toml` under `[project.scripts]` (the script that M0 deferred because the CLI module didn't exist yet).
- [ ] `tests/cli/test_extract_validate.py`: invoke via `typer.testing.CliRunner`, train → extract → validate → exit code 0.
- [ ] `tests/cli/test_validate_corrupt.py`: validate against a known-corrupt fixture → exit code != 0, stderr contains the error class name.
- [ ] `npx gitnexus analyze` after commit.

## Task 5 — FastAPI bootstrap: `/health`, `/artifacts/{id}`, middleware, exception handler

**Spec:** `.docs/cerebro-open-spec.md` Part II §6, §7, §8.
**Commit:** `feat(api): fastapi bootstrap with /health and /artifacts/{id}`

- [ ] `gitnexus_search` for `FastAPI`, `app`, `correlation_id`, `exception_handler`.
- [ ] Create `src/cerebro/api/__init__.py`, `src/cerebro/api/app.py`, `src/cerebro/api/deps.py`.
- [ ] `app.py`: `app = FastAPI(title="Cerebro", openapi_url="/openapi.json")` with Swagger at `/docs` and ReDoc at `/redoc`.
- [ ] `GET /health` returns `{"status": "ok", "version": <pkg_version>, "schema_version": "1.0.0"}`.
- [ ] `GET /artifacts/{id}` resolves the path via `deps.get_artifact_loader()` (M1: filesystem-backed, takes `CEREBRO_DATA_DIR/artifacts/{id}.cerebro.json`), returns the validated artifact.
- [ ] Correlation-ID middleware: read `X-Request-ID` header (or generate a UUID4), bind via `structlog.contextvars.bind_contextvars`, echo in the response header.
- [ ] Single `@app.exception_handler(CerebroError)` mapping the taxonomy to status codes per the table in `design.md`; body is the RFC 7807 shape; correlation ID echoed in the body.
- [ ] `tests/api/test_health.py`: `GET /health` returns the expected shape.
- [ ] `tests/api/test_artifacts.py`: a known fixture path is round-tripped; missing id → 404; corrupt artifact → 422; both error bodies carry a `correlation_id`.
- [ ] `tests/api/test_correlation_id.py`: a request with `X-Request-ID: foo` echoes `foo` in the response header and the logs.
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
