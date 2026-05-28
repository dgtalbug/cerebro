# Variant Coverage — tasks

> Implementation runs in this order. Each task lands as exactly one
> Conventional Commit. Before creating any new module, run `gitnexus_search`
> for similar names; after each commit lands, run `npx gitnexus analyze`.
> No `Co-Authored-By` trailers anywhere.

## Task 1 — Shared base helpers

**Spec:** `.docs/cerebro-open-spec.md` Part II §5.
**Commit:** `refactor(extractor): extract shared LGB helpers into _lightgbm_base.py`

- [ ] `gitnexus_impact` on `LGBExtractor` — report blast radius before extracting methods.
- [ ] Create `src/cerebro/extractors/_lightgbm_base.py` containing the shared helper functions:
  - `_resolve_objective(dumped: dict) -> str` — replaces `_guard_objective`; returns one of "binary", "multiclass", "regression", "lambdarank", "multi_output".
  - `_load_booster(path: Path) -> Booster`
  - `_build_node(raw: dict, counter: list[int]) -> TreeNode`
  - `_build_feature_schema(dumped, booster) -> FeatureSchema`
  - `_extract_params(booster) -> dict`
  - `_build_importance(booster, names) -> Importance`
  - `_build_source() -> Source`
- [ ] `_resolve_objective` handles all five keyword cases; unknown keywords still raise `UnsupportedObjectiveError`.
- [ ] `LGBExtractor` (M1, in `lightgbm.py`) imports and calls the shared helpers — no logic duplication, no behavior change.
- [ ] `pytest -n auto` is 75/75. `import-linter` contracts still green. `ruff` + `mypy` green.
- [ ] `npx gitnexus analyze` after commit.

## Task 2 — Schema widening

**Spec:** `.docs/cerebro-open-spec.md` Part I §6, Part II §4.2.
**Commit:** `feat(schema): widen objective and num_class; add divergence_warnings and rank_metadata`

- [ ] `gitnexus_impact` on `Model`, `Importance`, `CerebroArtifact` — review callers.
- [ ] Widen `Model.objective` from `Literal["binary"]` to `Literal["binary", "multiclass", "regression", "lambdarank", "multi_output"]`.
- [ ] Widen `Model.num_class` from `Literal[1]` to `int`.
- [ ] Add `divergence_warnings: list[dict[str, str | int | float]] | None = None` to `Importance`.
- [ ] Add `rank_metadata: dict[str, Any] | None = None` to `CerebroArtifact`.
- [ ] Regenerate `schemas/v1/cerebro-artifact.schema.json` via `scripts/export_schema.py`. Run `scripts/check_contracts.py` — drift gate must stay green.
- [ ] Existing round-trip and binary extraction tests still pass (widened schema is backward-compatible).
- [ ] `tests/schema/test_extra_keys_rejected.py` still rejects unknown keys.
- [ ] All gates green: ruff, mypy --strict, pytest -n auto (75/75), contract checks.
- [ ] `npx gitnexus analyze` after commit.

## Task 3 — LGBBinaryExtractor (M2-enabled binary, replaces M1 in CLI/API)

**Spec:** `.docs/cerebro-open-spec.md` Part II §5.
**Commit:** `feat(extractor): LGBBinaryExtractor using shared base helpers`

- [ ] Create `src/cerebro/extractors/lightgbm_binary.py` — `LGBBinaryExtractor` class using `_lightgbm_base` helpers.
- [ ] Identical behavior to M1 `LGBExtractor` — same assertions pass with same fixture.
- [ ] Wire `LGBBinaryExtractor` in `cerebro.extractors.__init__` and the auto-dispatch registry.
- [ ] Wire `cerebro extract` CLI to use auto-detection (`get_extractor()`).
- [ ] M1 `LGBExtractor` stays as-is (backward compat). Tests that import it directly still pass.
- [ ] `tests/extractors/test_lightgbm_binary.py` — duplicate the M1 binary test but use the new extractor; assertion set is identical.
- [ ] All gates green. `import-linter` contracts still hold (extractors-only-imports-lightgbm).
- [ ] `npx gitnexus analyze` after commit.

## Task 4 — Multiclass extractor

**Spec:** `.docs/cerebro-open-spec.md` Part II §5, Part VI §3.2 (E1.017).
**Commit:** `feat(extractor): multiclass LGB extractor with per-class trees`

- [ ] Create `src/cerebro/extractors/lightgbm_multiclass.py` — `LGBMulticlassExtractor`.
- [ ] Multiclass `dump_model()` has `tree_info` grouped per class (e.g. 50 trees × 3 classes = 150 entries). Each tree entry already has a class index embedded in its structure (the class is the leading dimension in LightGBM's tree array for multiclass).
- [ ] `_build_tree` sets `class_index` from the booster's per-tree metadata. For multiclass, `class_index` is the class that tree predicts.
- [ ] `num_class` = number of classes parsed from `objective` args (e.g. `"multiclass num_class:3"` → 3).
- [ ] `tests/extractors/test_multiclass.py`: train 3-class classifier (20 trees, `make_classification(n_classes=3, n_informative=6)`), extract, assert `num_class == 3`, every tree has `class_index`, trees count = 20 × 3 = 60.
- [ ] Register in auto-dispatch.
- [ ] All gates green.
- [ ] `npx gitnexus analyze` after commit.

## Task 5 — Regression extractor

**Spec:** `.docs/cerebro-open-spec.md` Part II §5, Part VI §3.2 (E1.018).
**Commit:** `feat(extractor): regression LGB extractor`

- [ ] Create `src/cerebro/extractors/lightgbm_regression.py` — `LGBRegressionExtractor`.
- [ ] Simpler than binary: `num_class=1`, leaf values are continuous (no sigmoid transform needed), no `class_index`.
- [ ] `tests/extractors/test_regression.py`: train regressor on `make_regression(n_samples=300)`, extract, assert `objective == "regression"`, leaf values are floats, no `class_index` on any tree.
- [ ] Register in auto-dispatch.
- [ ] All gates green.
- [ ] `npx gitnexus analyze` after commit.

## Task 6 — Ranker extractor

**Spec:** `.docs/cerebro-open-spec.md` Part II §5, Part VI §3.2 (E1.019).
**Commit:** `feat(extractor): ranker LGB extractor with group metadata`

- [ ] Create `src/cerebro/extractors/lightgbm_ranker.py` — `LGBRankerExtractor`.
- [ ] Ranker boosters have `objective: "lambdarank"` (or `rank_xendcg`). The dump_model shape is the same as binary/regression — no per-class trees.
- [ ] Preserve group metadata in `rank_metadata`. LightGBM stores `group` in params when trained with `lgb.Dataset(group=...)`. Extract and store the group sizes array in `rank_metadata.group_sizes`.
- [ ] If group metadata is not available (booster saved without training data), `rank_metadata` is still populated with an empty `group_sizes` and a note.
- [ ] `tests/extractors/test_ranker.py`: train small ranker with synthetic query groups (`make_regression` + assign fake group IDs), extract, assert `objective == "lambdarank"`, `rank_metadata` populated.
- [ ] Register in auto-dispatch.
- [ ] All gates green.
- [ ] `npx gitnexus analyze` after commit.

## Task 7 — Multi-output extractor

**Spec:** `.docs/cerebro-open-spec.md` Part II §5, Part VI §3.2 (E1.020).
**Commit:** `feat(extractor): multi-output LGB extractor`

- [ ] Create `src/cerebro/extractors/lightgbm_multi_output.py` — `LGBMultiOutputExtractor`.
- [ ] Multi-output boosters have one tree sequence per output target. `dump_model()["tree_info"]` is a flat list — extractor needs to group by output.
- [ ] `importance.gain` and `importance.split` are aggregated across outputs (sum). Per-output importance breakdown stored in `rank_metadata.multi_output_importance`.
- [ ] `tests/extractors/test_multi_output.py`: train multi-output regressor on `make_regression(n_targets=2)`, extract, assert `objective == "multi_output"`, `rank_metadata.multi_output_importance` has keys for each output.
- [ ] Register in auto-dispatch.
- [ ] All gates green.
- [ ] `npx gitnexus analyze` after commit.

## Task 8 — Permutation importance + divergence detection

**Spec:** `.docs/cerebro-open-spec.md` Part II §5 (permutation), Part VI §3.2 (E1.021, E1.022, E1.024).
**Commit:** `feat(importances): permutation importance and divergence detection`

- [ ] Create `src/cerebro/analyzers/__init__.py` (package init, exports).
- [ ] Create `src/cerebro/analyzers/importance.py`:
  - `compute_permutation_importance(booster, samples, labels, feature_names) -> dict[str, dict[str, float]]`
  - `detect_divergence(gain, permutation, feature_names, threshold=5) -> list[dict]`
- [ ] `compute_permutation_importance` uses `sklearn.inspection.permutation_importance` with appropriate scoring based on booster objective.
- [ ] `detect_divergence` sorts by rank, compares, returns warnings sorted by delta descending.
- [ ] `LGBBinaryExtractor` (and all other extractors) accept optional `samples` + `labels` params. When both provided: call `compute_permutation_importance`, set `importance.permutation`, call `detect_divergence`, set `importance.divergence_warnings`.
- [ ] When only one of `samples`/`labels` is provided: raise `ValueError` with a clear message.
- [ ] `tests/analyzers/test_importance.py`: unit tests for permutation scores (known feature set, known ranks), divergence detection (contrived ranks with known divergence, threshold edge cases).
- [ ] `tests/extractors/test_binary_with_samples.py`: train binary model, extract with samples, assert `permutation` is populated, `divergence_warnings` is populated (may be empty if no divergence, but must be a list).
- [ ] All gates green. New `import-linter` contract: `analyzers/` never imports `extractors/`.
- [ ] `npx gitnexus analyze` after commit.

## Task 9 — Importance sub-resource endpoint

**Spec:** `.docs/cerebro-open-spec.md` Part II §6, Part VI §3.2 (E1.023).
**Commit:** `feat(api): GET /artifacts/{id}/importance endpoint`

- [ ] Create `src/cerebro/api/routes/importance.py`:
  - `GET /artifacts/{artifact_id}/importance?type=gain|split|permutation`
  - `?type` param is required, validated via FastAPI `Query(enum=["gain", "split", "permutation"])`.
  - Returns `ImportanceResponse` Pydantic model matching the contract in `design.md`.
  - When `type=permutation` and `importance.permutation` is None: returns 200 with `features: []` and a `detail` field.
- [ ] `tests/api/test_importance.py`: TestClient hits endpoint for each type. Existing fixture artifact returns gain + split data. Permutation returns the empty/data-missing shape.
- [ ] Wire sub-resource router into `app.py`.
- [ ] Regenerate OpenAPI doc (`scripts/export_openapi.py`). Run contract drift check — must stay green.
- [ ] All gates green: ruff, mypy, pytest (existing 75 + new API tests), lint-imports, contracts.
- [ ] `npx gitnexus analyze` after commit.

## Task 10 — Importance view in UI

**Spec:** `.docs/cerebro-open-spec.md` Part III §5, §6, Part VI §3.2 (E1.023, E1.024).
**Commit:** `feat(ui): importance view with gain/split/permutation tabs`

- [ ] `gitnexus_search` for `Importance`, `ImportanceBarChart`, `DivergenceCallout` — confirm no collisions.
- [ ] Create `ui/src/lib/api/queries.ts` addition: `useImportance(id, type)` calling `GET /artifacts/{id}/importance?type=...`.
- [ ] Create `ui/src/views/Importance.tsx`:
  - ViewHeader: "Feature *importance*", subtitle from mockup.
  - Two panels side by side: "Aggregate importance" (with tabs: gain/split/permutation) and "Gain vs permutation" (divergence).
  - Aggregate panel: sorted bar list using `.fi-` CSS classes (matching mockup).
  - Divergence panel: bar list showing gain-vs-permutation delta, color-coded (green = aligned, red = divergent). Red callout box when warnings present.
  - Permutation tab: calls sub-resource endpoint. Shows "not computed" state when no data.
- [ ] `ui/src/components/importance/DivergenceCallout.tsx` — red-tinted warning panel listing divergent features.
- [ ] Loading, error, and "no permutation data" states each render a distinct UI.
- [ ] `tests/ui/Importance.test.tsx`: mock `useImportance` for each type; assert tab switching, bar rendering, divergence callout appears/disappears with data.
- [ ] Activate "Importance" nav item in Sidebar (remove `disabled` + `pointer-events-none` from M1).
- [ ] `pnpm lint`, `pnpm typecheck`, `pnpm build`, `pnpm test` all green. Backend gates green.
- [ ] `npx gitnexus analyze` after commit.

## Task 11 — Trees view in UI

**Spec:** `.docs/cerebro-open-spec.md` Part III §5, Part VI §3.2 (E1.026).
**Commit:** `feat(ui): trees view with react-d3-tree and node inspector`

- [ ] `gitnexus_search` for `Trees`, `TreeViz`, `NodeInspector` — confirm no collisions.
- [ ] Add `react-d3-tree` to `ui/package.json` dependencies.
- [ ] Create `ui/src/lib/api/queries.ts` addition: `useTrees(id)` uses full-artifact endpoint (trees are already in the cache from Overview).
- [ ] Create `ui/src/components/trees/TreeViz.tsx`:
  - Wraps `React.lazy(() => import("react-d3-tree"))` — renders a loading placeholder until the chunk loads.
  - Transforms canonical `Tree` → `react-d3-tree` data shape (`{name, children, attributes}`).
  - On node click: fires callback to `NodeInspector`.
- [ ] Create `ui/src/components/trees/TreeControls.tsx`:
  - Tree selector dropdown: `<select>` populated from `artifact.trees`.
  - Depth filter: "All (n)", "≤ 3", "≤ 4", "≤ 5" options.
  - Stats bar: "N nodes · M leaves · depth D".
- [ ] Create `ui/src/components/trees/NodeInspector.tsx`:
  - Split node: shows feature name, threshold, decision type, gain (if available from booster params).
  - Leaf node: shows leaf value (raw score), "terminal" badge.
  - NO sample counts (see design.md: "Tree node structure — what dump_model() provides").
- [ ] Create `ui/src/views/Trees.tsx`:
  - ViewHeader: "Tree *topology*", subtitle from mockup.
  - TreeControls + TreeViz + NodeInspector in a split layout.
- [ ] Loading, error, and empty states handled.
- [ ] `tests/ui/Trees.test.tsx`: mock `useArtifact` returning small fixture with 3 trees; assert tree selector renders 3 options, clicking different tree changes the rendered tree, node click populates inspector.
- [ ] Activate "Trees" nav item in Sidebar.
- [ ] `pnpm lint`, `pnpm typecheck`, `pnpm build`, `pnpm test` all green. Backend gates green.
- [ ] `npx gitnexus analyze` after commit.

## Task 12 — Snapshot tests, example artifacts, regression guard

**Spec:** `.docs/cerebro-open-spec.md` Part VI §3.2 (E1.025, E1.027).
**Commit:** `test(snapshots): example artifacts and variant snapshot tests`

- [ ] `gitnexus_search` for `snapshot`, `example_artifact` — confirm no collisions.
- [ ] Create example artifact fixtures in `examples/`:
  - `examples/binary_artifact.cerebro.json` (from existing e2e fixture, regenerated from `LGBBinaryExtractor`).
  - `examples/multiclass_artifact.cerebro.json`
  - `examples/regression_artifact.cerebro.json`
  - `examples/ranker_artifact.cerebro.json`
  - `examples/multi_output_artifact.cerebro.json`
- [ ] Create `tests/extractors/test_snapshots.py`: for each variant, train a model with the same training parameters as the corresponding example, extract, assert the artifact is identical to the committed example (compare Pydantic model dicts — timestamp fields normalized to a fixture value).
- [ ] `tests/extractors/test_m1_regression.py`: assert M1 binary tests (importing `LGBExtractor` directly) still pass.
- [ ] Remove `disabled` from all nav items that are now wired (Importance, Trees).
- [ ] Full gate sweep: `ruff`, `ruff format --check`, `mypy --strict`, `lint-imports`, `pytest -n auto`, `pnpm lint`, `pnpm typecheck`, `pnpm build`, `pnpm test`, contract checks.
- [ ] `npx gitnexus analyze` after commit.
- [ ] `openspec validate m2-variant-coverage --strict` clean.
