## 1. Schema v1.1.0

- [x] 1.1 Create `src/cerebro/schema/v1_1/` as a folder copy of `schema/v1/`
- [x] 1.2 Add `FeatureDiagnostics` Pydantic model to `schema/v1_1/` (redundancy warnings, leakage warnings, interactions, unused_features, recommendations)
- [x] 1.3 Add `feature_diagnostics: FeatureDiagnostics | None = None` to `CerebroArtifact` in `schema/v1_1/artifact.py`
- [x] 1.4 Update `schema/__init__.py` to export `CURRENT_SCHEMA = v1_1`
- [x] 1.5 Unit-test that a v1.0.0 artifact JSON round-trips cleanly under v1.1.0 schema with `feature_diagnostics=None`
- [x] 1.6 Export updated OpenAPI schema; run `pnpm api:types` in `ui/` and commit regenerated `schema.d.ts`

## 2. Feature diagnostics analyzer

- [x] 2.1 Create `src/cerebro/analyzers/feature_diagnostics.py` with `compute_diagnostics(artifact: CerebroArtifact) -> FeatureDiagnostics`
- [x] 2.2 Implement redundancy detection (Pearson correlation from data_profile + gain overlap; skip when data_profile absent)
- [x] 2.3 Implement leakage detection (gain rank vs. permutation rank divergence; skip when permutation absent)
- [x] 2.4 Implement interaction strength (co-occurrence walk over trees, normalize by `sqrt(split_a * split_b)`)
- [x] 2.5 Implement unused feature detection (features in feature_schema.names absent from all tree splits)
- [x] 2.6 Implement recommendation ranker producing drop + engineering suggestions sorted by impact
- [x] 2.7 Unit-test all six functions against a fixture artifact (binary classifier with data_profile and permutation importance)
- [x] 2.8 Unit-test graceful skip paths (no data_profile, no permutation importance)

## 3. Artifact diff analyzer

- [x] 3.1 Create `src/cerebro/analyzers/diff.py` with `diff_artifacts(a: CerebroArtifact, b: CerebroArtifact) -> CerebroDiff`
- [x] 3.2 Add `CerebroDiff` Pydantic model to `schema/v1_1/` with per-section delta fields
- [x] 3.3 Implement importance delta (per-feature gain and split change)
- [x] 3.4 Implement feature schema diff (added/removed features)
- [x] 3.5 Implement evaluation metric delta (objective-aware; skip when either artifact lacks evaluation)
- [x] 3.6 Unit-test diff with two fixture artifacts (one with a feature added, one with metric improvement)

## 4. CLI extensions

- [x] 4.1 Add `cerebro diff <artifact-a> <artifact-b> [--json]` command to `src/cerebro/cli/main.py`
- [x] 4.2 Add `cerebro diagnostics <artifact> [--persist]` command that runs `compute_diagnostics` and prints/persists the result
- [x] 4.3 Test `cerebro diff` outputs human-readable table and `--json` emits valid JSON
- [x] 4.4 Test `cerebro diagnostics` populates and persists `feature_diagnostics` correctly

## 5. API extensions

- [x] 5.1 Add `GET /artifacts/{id}/diagnostics?persist=false` route to `api/routes/`
- [x] 5.2 Add `POST /artifacts/{id}/tags` and `DELETE /artifacts/{id}/tags/{tag}` routes
- [x] 5.3 Add `tag` query parameter to `GET /artifacts` list endpoint
- [x] 5.4 Add `GET /artifacts/{id}/diff/{compare_id}` route returning `CerebroDiff`
- [x] 5.5 Add tags CRUD to `storage/registry.py` (insert, delete, filter-by-tag)
- [x] 5.6 API tests for all new routes (happy path + error cases)

## 6. XGBoost extractor

- [ ] 6.1 Create `src/cerebro/extractors/_xgboost_base.py` with lazy `_require_xgboost()` import (mirrors `_lightgbm_base.py` pattern)
- [ ] 6.2 Implement `_load_booster(path)` for XGBoost JSON and pickle formats
- [ ] 6.3 Implement tree topology extraction from XGBoost's `get_dump(dump_format='json')` output
- [ ] 6.4 Implement importance extraction (`booster.get_score(importance_type='gain')` and `'split'`)
- [ ] 6.5 Create `src/cerebro/extractors/xgboost.py` extractor for binary, multiclass, and regression objectives
- [ ] 6.6 Register XGBoost extractor in extractor registry / auto-detection logic
- [ ] 6.7 Add `xgboost>=2.0` to `[project.optional-dependencies].ml` and to dev dependency group
- [ ] 6.8 Add import-linter exceptions if needed (mirror LightGBM lazy-import exceptions)
- [ ] 6.9 Integration tests: train tiny XGBoost models (binary, multiclass, regression) in fixtures; verify canonical artifact round-trip
- [ ] 6.10 Test that importing `cerebro.extractors.xgboost` succeeds in environments without xgboost installed

## 7. Agent extensions

- [ ] 7.1 Extend `agent/context.py` to include `feature_diagnostics` summary block (top-3 drops, top-3 engineering, flagged leakage/redundancy) when present
- [ ] 7.2 Add system-prompt guidance in `agent/prompts.py` for improvement-oriented questions citing `feature_diagnostics.*` paths
- [ ] 7.3 Update agent-context provenance note to cover XGBoost artifacts (framework-agnostic reasoning over canonical schema)
- [ ] 7.4 Unit-test that context shaper includes diagnostics block when present and omits it gracefully when absent
- [ ] 7.5 Unit-test agent improvement answer contains ≥3 recommendations citing `feature_diagnostics.*` paths

## 8. Dashboard — diagnostics and diff UI

- [ ] 8.1 Add Recommendations panel to `ui/src/views/Importance.tsx` (visible when `feature_diagnostics` present; notice otherwise)
- [ ] 8.2 Add interaction strength heatmap to Importance view (Reaviz `Heatmap`, top-20 features, hover tooltips)
- [ ] 8.3 Create `ui/src/views/Diff.tsx` — two-pane diff view with importance delta, feature schema changes, metric deltas
- [ ] 8.4 Add `/artifacts/:id/diff/:compareId` route to React Router
- [ ] 8.5 Add TanStack Query hook `useDiff(artifactId, compareId)` to `lib/api/queries.ts`
- [ ] 8.6 Add tags display (pills) to artifact cards in list view; click-to-filter updates URL query param
- [ ] 8.7 Implement filterable artifact list view (`ui/src/views/Artifacts.tsx`): framework/objective/date/tag filters via URL state
- [ ] 8.8 Add TanStack Query hooks `useTags`, `useAddTag`, `useRemoveTag` to `lib/api/queries.ts`

## 9. Docs and spec sync

- [ ] 9.1 Update `docs/cerebro-open-spec.md` Part VI §2 Current Status to reflect MVP 2 shipped
- [ ] 9.2 Document XGBoost extractor usage in BACKEND.md adapter pattern section
- [ ] 9.3 Run `ruff check`, `mypy --strict`, `pytest`; ensure green
- [ ] 9.4 Run `npx gitnexus analyze` to refresh the knowledge graph
- [ ] 9.5 One Conventional Commit per task group (no AI attribution)
