## 1. Schema Extensions (v1.1)

- [ ] 1.1 Create `schemas/v1.1/` folder and copy v1 DDL as base
- [ ] 1.2 Add `src/cerebro/schema/v1/explanations.py` with `ShapResult`, `DecisionPath`, `PDPFeature` Pydantic models
- [ ] 1.3 Add `src/cerebro/schema/v1/evaluation.py` with `BinaryEval`, `MulticlassEval`, `RegressionEval`, `RankingEval` Pydantic models
- [ ] 1.4 Add `src/cerebro/schema/v1/data_profile.py` with `ColumnProfile`, `DataProfile` Pydantic models
- [ ] 1.5 Update `src/cerebro/schema/v1/artifact.py` to use the new union types for `explanations` and `evaluation` fields
- [ ] 1.6 Verify existing v1.0.0 fixture artifacts still validate (run `pytest tests/schema/`)

## 2. Data Ingestion

- [ ] 2.1 Create `src/cerebro/data/__init__.py`
- [ ] 2.2 Implement `src/cerebro/data/loader.py` — `load_table(path)` with DuckDB autodetect for csv/parquet/json; raise `UnsupportedFormatError` for unknown extensions
- [ ] 2.3 Implement `src/cerebro/data/profiler.py` — `profile_table(relation)` returning `DataProfile`; distributions, missingness, Pearson correlations via DuckDB SQL aggregations
- [ ] 2.4 Add `UnsupportedFormatError` to `src/cerebro/exceptions.py`

## 3. Analyzers — Explanations

- [ ] 3.1 Implement `src/cerebro/analyzers/explanations.py` — `compute_shap(booster, samples, labels)` with stratified/uniform background sampling; cap at `SHAP_MAX_EXPLAIN_SAMPLES`; returns `ShapResult`
- [ ] 3.2 Implement `trace_path(tree, sample_values)` pure function returning `DecisionPath`; no LGB import
- [ ] 3.3 Implement `compute_pdp(booster, samples, feature_names, importance, categorical_indices)` returning list of `PDPFeature`; top-N by gain; categorical grid uses distinct values

## 4. Analyzers — Evaluation

- [ ] 4.1 Implement `src/cerebro/analyzers/evaluation.py` — `evaluate(predictions, labels, objective, query_ids)` dispatcher
- [ ] 4.2 Implement `_evaluate_binary(predictions, labels)` → `BinaryEval` with ROC (≥100 thresholds), AUC, 2×2 confusion matrix at 0.5 threshold
- [ ] 4.3 Implement `_evaluate_multiclass(predictions, labels, n_classes)` → `MulticlassEval` with NxN confusion matrix and per-class precision/recall/F1
- [ ] 4.4 Implement `_evaluate_regression(predictions, labels)` → `RegressionEval` with residuals histogram, scatter, 5th–95th interval band
- [ ] 4.5 Implement `_evaluate_ranking(predictions, labels, query_ids)` → `RankingEval` with nDCG@{1,3,5,10}, MAP, per-query nDCG@10 distribution

## 5. Extractor Integration

- [ ] 5.1 Wire `data/loader.py` + `data/profiler.py` into `LGBExtractor.extract` when `--training-table` path is provided; populate `artifact.data_profile`
- [ ] 5.2 Wire `analyzers/explanations.compute_shap` into extractor when `samples` provided; populate `artifact.explanations`
- [ ] 5.3 Wire `analyzers/evaluation.evaluate` into extractor when labeled eval samples provided; populate `artifact.evaluation`
- [ ] 5.4 Add `--training-table` and `--eval-samples` flags to `cerebro extract` CLI command

## 6. API Routes

- [ ] 6.1 Add `GET /artifacts/{id}/explanations` route returning `artifact.explanations` or `{"detail": "explanations not available"}`
- [ ] 6.2 Add `GET /artifacts/{id}/evaluation` route returning `artifact.evaluation` or `{"detail": "evaluation not available"}`
- [ ] 6.3 Add `GET /artifacts/{id}/data-profile` route returning `artifact.data_profile` or `{"detail": "data profile not available"}`
- [ ] 6.4 Register all three routes in `api/app.py`

## 7. UI — Data View

- [ ] 7.1 Add `useDataProfile(id)` hook to `ui/src/lib/api/queries.ts`
- [ ] 7.2 Implement `ui/src/views/Data.tsx` — lazy-loaded; distribution charts, missingness table, correlation heatmap using Reaviz; placeholder when no profile
- [ ] 7.3 Wire Data view into sidebar nav and router

## 8. UI — Explanations View

- [ ] 8.1 Add `useExplanations(id)` hook to `ui/src/lib/api/queries.ts`
- [ ] 8.2 Implement `ui/src/views/Explanations.tsx` — lazy-loaded; sample picker, three-tab inspector (SHAP / Path / Raw), PDP sparklines panel; copper highlight on path features; placeholder when no data
- [ ] 8.3 Wire Explanations view into sidebar nav and router

## 9. UI — Evaluation View

- [ ] 9.1 Add `useEvaluation(id)` hook to `ui/src/lib/api/queries.ts`
- [ ] 9.2 Implement `ui/src/views/evaluation/BinaryPanel.tsx` — lazy-loaded; ROC curve (Reaviz LineChart + reference diagonal), confusion matrix (Reaviz Heatmap)
- [ ] 9.3 Implement `ui/src/views/evaluation/MulticlassPanel.tsx` — lazy-loaded; NxN confusion matrix heatmap, per-class metrics table
- [ ] 9.4 Implement `ui/src/views/evaluation/RegressionPanel.tsx` — lazy-loaded; residuals histogram, predicted-vs-actual scatter with reference diagonal, interval band
- [ ] 9.5 Implement `ui/src/views/evaluation/RankingPanel.tsx` — lazy-loaded; nDCG@k bars (highlight @10), MAP badge, per-query distribution
- [ ] 9.6 Implement `ui/src/views/Evaluation.tsx` — objective-driven shell that lazy-loads the correct panel; placeholder when no evaluation
- [ ] 9.7 Wire Evaluation view into sidebar nav and router

## 10. Tests

- [ ] 10.1 `tests/data/test_loader.py` — CSV, Parquet, JSON (records + columnar), unsupported extension
- [ ] 10.2 `tests/data/test_profiler.py` — distributions, missingness, correlations, empty table
- [ ] 10.3 `tests/analyzers/test_explanations.py` — SHAP for each of the 5 LGB variants; stratified vs uniform background; cap behaviour; `trace_path` correctness; categorical split; PDP shape
- [ ] 10.4 `tests/analyzers/test_evaluation.py` — dispatcher routing for all 4 objectives; metric math (AUC, nDCG); multiclass matrix shape; regression residuals; unknown objective error
- [ ] 10.5 `tests/schema/test_v11.py` — v1.0.0 artifacts validate unchanged; v1.1 artifacts with each new section validate
- [ ] 10.6 `tests/api/test_explanations_routes.py` — present / absent / 404 for all three new endpoints
- [ ] 10.7 Full regression: `pytest tests/` — all M1/M2 tests pass alongside new tests
