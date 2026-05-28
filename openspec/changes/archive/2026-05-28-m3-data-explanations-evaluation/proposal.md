## Why

M1 and M2 gave us a frozen canonical artifact with tree topology and feature
importance. The artifact is structurally complete but analytically opaque:
there is no way to understand *why* a prediction was made (explanations), how
well the model generalises (evaluation), or what the training data looks like
(data profile). These three capabilities are the minimal bar for Cerebro to be
useful as a model introspection tool rather than a tree serialiser.

## What Changes

- `src/cerebro/data/loader.py` — new DuckDB-backed reader; autodetects
  CSV / Parquet / JSON; read-only; no pandas dependency.
- `src/cerebro/data/profiler.py` — new profiler: per-column distributions,
  missingness rates, Pearson correlations, dtype inference.
- `schemas/v1.1/` — additive schema folder with optional `data_profile` and
  updated `explanations` / `evaluation` union types. v1.0.0 artifacts continue
  to validate unchanged.
- `src/cerebro/schema/v1/explanations.py` — new Pydantic models: `ShapResult`,
  `DecisionPath`, `PartialDependence`.
- `src/cerebro/schema/v1/evaluation.py` — new Pydantic models: `BinaryEval`,
  `MulticlassEval`, `RegressionEval`, `RankingEval`.
- `src/cerebro/analyzers/explanations.py` — SHAP TreeExplainer wrapper with
  stratified background sampling; decision-path tracer (pure, no LGB import);
  partial dependence computation over top-N features.
- `src/cerebro/analyzers/evaluation.py` — objective dispatcher routing to the
  correct eval panel computation.
- `src/cerebro/api/routes/` — new routes: `/explanations`, `/evaluation`,
  `/data-profile`.
- `ui/src/views/Data.tsx` — Data view: distributions, missingness, correlation
  matrix, type table; only renders when data_profile present.
- `ui/src/views/Explanations.tsx` — Explanations view: SHAP breakdown,
  decision path trace, partial dependence sparklines; copper highlight on
  path features.
- `ui/src/views/Evaluation.tsx` — Evaluation view: lazy-loads the correct
  panel set (binary / multiclass / regression / ranking) based on objective.
- Tests for all new modules plus full M1/M2 regression guard.

**Decisions made:**
- **Training table JSON shape**: records-oriented by default; columnar
  autodetected via shape heuristic.
- **SHAP background sampling**: stratified by target when labels are present,
  uniform otherwise.
- **Multi-class explanation rendering**: per-class breakdown with an aggregated
  summary toggle.

## Capabilities

### New Capabilities

- `data-ingestion`: DuckDB-backed table loading and statistical profiling;
  optional `data_profile` section in the artifact schema (v1.1 additive only).
- `explanations`: SHAP TreeExplainer wrapper, decision-path tracer (pure over
  canonical tree topology), partial dependence computation.
- `evaluation`: Objective-aware evaluation dispatcher; binary, multiclass,
  regression, and ranking panels with frozen metrics stored in the artifact.

### Modified Capabilities

- `canonical-schema`: `explanations` and `evaluation` fields promoted from
  `None`-typed stubs to proper union types; v1.0.0 artifacts still valid.
- `dashboard`: Data, Explanations, and Evaluation views added; Explanations
  and Evaluation panels are lazy-loaded components.
- `api`: Three new endpoints — `/artifacts/{id}/explanations`,
  `/artifacts/{id}/evaluation`, `/artifacts/{id}/data-profile`.

## Impact

- **Backend deps added**: `duckdb`, `shap` (already transitive via sklearn),
  `scikit-learn` already present.
- **Frontend deps**: no new packages; uses existing Reaviz, Zustand, TanStack
  Query.
- **No breaking changes**: all new schema fields are optional; existing v1.0.0
  artifacts validate without modification.
- **Extractor touched**: `LGBExtractor.extract` gains optional `samples`,
  `labels` parameters already in protocol; wiring them to the new analyzers.
- **API surface expanded**: three new read-only GET endpoints; no existing
  routes modified.
- Spec reference: `.docs/cerebro-open-spec.md` Part II §4.3 (analyzers),
  Part II §4.2 (schema), Part III §4–6 (component architecture), Part VI §3.2
  (M3 tasks).
