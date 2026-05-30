## Context

MVP 1 produced a fully working canonical artifact pipeline: LightGBM extraction → schema v1.0.0 → seven-view dashboard → AI agent. The schema is frozen. The import-linter boundary (no consumption module imports LightGBM) is enforced in CI. Feature importance, SHAP, and evaluation all land in the artifact; the agent reasons over it.

MVP 2 adds a diagnostics layer on top of the existing canonical artifact — no reprocessing of the model required — and extends the extractor side to cover XGBoost. The canonical schema gains an additive v1.1.0 with a `feature_diagnostics` section. Existing consumers and artifacts remain untouched.

Current constraints:
- `from __future__ import annotations` is used project-wide; lazy imports for heavy optional deps are already established (see `_lightgbm_base.py` pattern).
- Import-linter enforces that analyzers never import the extractor layer.
- CI runs `uv sync --frozen` without ML deps; any new extractor must follow the lazy-import pattern.
- Schema versioning is folder-copy, never edit-in-place (`schema/v1/`, `schema/v1_1/`).

## Goals / Non-Goals

**Goals:**
- Redundancy, leakage, interaction-strength, and unused-feature diagnostics computable from the canonical artifact alone (no raw model required after extraction)
- Schema v1.1.0 is strictly additive; v1.0.0 artifacts round-trip without modification
- XGBoost extractor covers binary, multiclass, regression — same canonical schema as LightGBM
- `cerebro diff` CLI produces structured per-section deltas between two artifacts
- UI surfaces diagnostics in Importance view and exposes diff in a two-pane view
- Agent can answer "how do I improve this model" using the new `feature_diagnostics` section

**Non-Goals:**
- Automated feature engineering or training (that is MVP 3)
- CatBoost, sklearn, or any other framework beyond XGBoost
- Cross-artifact aggregation queries (DuckDB upgrade is deferred per spec §IV.7)
- Streaming or incremental diagnostics

## Decisions

### D1: Diagnostics computed from canonical artifact, not from the live model

**Decision:** `analyzers/feature_diagnostics.py` takes a `CerebroArtifact` and returns a `FeatureDiagnostics` object. It never touches the booster.

**Why:** Preserves the core invariant — consumption layers never import the ML framework. Diagnostics from the canonical artifact are reproducible and versionable. The required inputs (trees, importance.gain, importance.split, data_profile) are all already in the artifact.

**Alternative considered:** Compute interaction strength from the live booster via SHAP interaction values. Rejected — requires the booster at consumption time, breaks the boundary, and is significantly more expensive.

### D2: Schema v1.1.0 as a folder copy with null default

**Decision:** `schema/v1_1/` copies v1.0.0 and adds `feature_diagnostics: FeatureDiagnostics | None = None` to `CerebroArtifact`. Reading a v1.0.0 artifact under the v1.1.0 schema succeeds with `feature_diagnostics=None`.

**Why:** The spec mandates folder-copy versioning. A null default means no migration is needed — existing artifacts simply have no diagnostics until re-extracted or enriched via the new `/diagnostics` endpoint.

**Alternative considered:** In-place addition to v1.0.0. Rejected — spec explicitly forbids editing v1.0.0 in place.

### D3: XGBoost extractor follows the same lazy-import pattern as LightGBM

**Decision:** `extractors/_xgboost_base.py` uses `TYPE_CHECKING` guard + `_require_xgboost()` function. CI does not install XGBoost; tests requiring XGBoost are marked with `pytest.mark.skipif(xgboost not installed)`.

**Why:** CI's `uv sync --frozen` omits ML deps. The LightGBM lazy-import pattern is already established and passes CI; XGBoost must follow the same contract.

**Alternative considered:** Separate `xgboost` test job with `uv sync --extra ml`. Rejected — adds CI complexity; the lazy-import pattern is simpler and already proven.

### D4: Diff algorithm operates on canonical artifact sections, not raw JSON

**Decision:** `analyzers/diff.py` computes per-section structural diffs: importance delta (feature-by-feature gain/split change), feature schema changes (added/removed features), evaluation metric deltas. Output is a `CerebroDiff` Pydantic model — not a raw JSON patch.

**Why:** Raw JSON diff (e.g., `jsondiff`) would expose internal array indices and be unreadable. A typed section-by-section diff is meaningful, citeable by the agent, and renderable directly in the UI.

**Alternative considered:** `jsondiff` or `deepdiff`. Rejected — produces unstructured output that requires a second pass to be useful.

### D5: Tags stored in `registry.tags` table, already in the DDL

**Decision:** The `tags` table is already in `schemas/registry/v1/init.sql`. MVP 2 activates the CRUD surface: `POST /artifacts/{id}/tags`, `DELETE /artifacts/{id}/tags/{tag}`, `GET /artifacts?tag=<tag>`.

**Why:** No schema migration required. The DDL already exists; only the storage layer and routes need implementation.

### D6: Interaction strength heuristic: co-occurrence count normalized by individual split frequencies

**Decision:** Walk every tree path from root to leaf. For each ordered pair `(feature_a, feature_b)` co-occurring in a path, increment `co_count[a][b]`. Normalize by `sqrt(split_count[a] * split_count[b])` to produce a symmetric interaction score in `[0, 1]`.

**Why:** Exact SHAP interaction values require the booster at runtime. The co-occurrence heuristic is computable from the canonical trees, correlates well with SHAP interactions for tree models, and is O(D × T) where D is tree depth and T is tree count — fast.

**Alternative considered:** SHAP interaction values via `shap.TreeExplainer(booster).shap_interaction_values(X)`. Rejected — requires the live booster and a sample dataset, neither of which is available in the consumption layer.

## Risks / Trade-offs

- **Interaction heuristic accuracy**: Co-occurrence ≠ SHAP interaction. For highly correlated features, the heuristic over-counts. → Mitigation: document the approximation clearly in UI tooltips and agent context. Provide the SHAP-based alternative as a future upgrade path.

- **v1.1.0 schema adoption**: Consumers pinned to v1.0.0 may not display diagnostics silently. → Mitigation: the v1.0.0 schema validator will pass on artifacts with unknown keys by default (Pydantic `model_config = ConfigDict(extra='ignore')`); no runtime error.

- **XGBoost booster format changes**: XGBoost's internal JSON format has changed across major versions (1.x → 2.x). → Mitigation: pin `xgboost>=2.0` in `[ml]` optional deps; document minimum version in BACKEND.md.

- **Diff view rendering performance**: Two large artifacts compared client-side may be slow for 1000-tree models. → Mitigation: diff is computed server-side and returned as a typed `CerebroDiff` object; the UI only renders the delta, not the full artifact pair.

## Migration Plan

1. Schema v1.1.0 ships alongside v1.0.0 (no removal). API continues serving v1.0.0 artifacts unchanged.
2. New `/artifacts/{id}/diagnostics` endpoint runs the diagnostics analyzer on demand and optionally persists the result back to the artifact file (flag: `?persist=true`).
3. `cerebro index --rebuild` re-registers existing artifacts; `feature_diagnostics` will be null until diagnostics are run.
4. No database migration required — `tags` table already exists in the DDL.

## Open Questions

- **`feature_diagnostics` invalidation**: If `data_profile` is added to an artifact that previously had none, should diagnostics recompute automatically? — Spec §VI.6 defers this decision to before E2.01. Proposed answer: no auto-recompute; diagnostics are on-demand. A stale-diagnostics warning can be surfaced in the UI if `artifact.feature_diagnostics.computed_at < artifact.data_profile.updated_at`.
- **Leakage threshold**: What gain-vs-permutation divergence ratio triggers a leakage flag? Needs a calibration pass on the example artifacts. Default proposal: flag if `gain_rank - permutation_rank > N/4` for a feature ranked in the top half by gain.
- **XGBoost ranker support**: XGBoost supports learning-to-rank objectives. Include in MVP 2 or defer? — Proposal: defer; cover binary/multiclass/regression first, add ranker in a follow-on.
