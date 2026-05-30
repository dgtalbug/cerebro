## Why

MVP 1 shows users what's inside their model — MVP 2 closes the loop by telling them what to fix. Without diagnostics, users can see importance and SHAP values but have no systematic way to identify leakage, redundancy, or interaction opportunities. The feature_diagnostics layer, model diff tooling, and XGBoost extractor are the next logical step once the canonical schema is stable.

## What Changes

- **New**: `analyzers/feature_diagnostics.py` — redundancy, leakage, interaction strength, unused feature detection
- **New**: Schema `v1.1.0` in `schema/v1_1/` — additive `feature_diagnostics` section; all v1.0.0 artifacts remain valid
- **New**: `/artifacts/{id}/diagnostics` API endpoint
- **New**: Recommendations panel in Importance view (UI)
- **New**: Interaction strength heatmap (UI)
- **New**: Artifact list view with framework/objective/date/tag filters (UI)
- **New**: Tags CRUD — `registry.tags` table activated; tag endpoints + UI
- **New**: `cerebro diff a.cerebro.json b.cerebro.json` CLI + diff view UI
- **New**: XGBoost extractor (`extractors/xgboost.py`) — binary, multiclass, regression using same canonical schema
- **New**: Agent diagnostics context shaping; answers "how do I improve this" questions
- **Modified**: `agent/context.py` extended to include `feature_diagnostics` section when present
- **Modified**: `agent/prompts.py` extended with diagnostics-aware guidance
- **Modified**: Artifact list view replaces placeholder with filterable/searchable UI (F2.11)

## Capabilities

### New Capabilities

- `feature-diagnostics`: Analyze a canonical artifact for redundant features, leakage signals, interaction strengths, and unused features; produce ranked recommendations
- `artifact-diff`: Structural diff between two canonical artifacts — importance deltas, feature schema changes, metric deltas; `cerebro diff` CLI + two-pane diff view
- `artifact-tags`: Tag artifacts with user-defined labels; filter by tag in list view; tags persisted in `registry.tags`
- `xgboost-extractor`: Extract canonical artifacts from XGBoost binary classifiers, multiclass classifiers, and regressors using the same schema as the LightGBM extractor

### Modified Capabilities

- `importance`: Gains a Recommendations panel and interaction heatmap powered by `feature_diagnostics`
- `ai-agent`: Extended context shaping to include `feature_diagnostics` when present; new system-prompt guidance for improvement-oriented questions

## Impact

- **Backend**: New `analyzers/feature_diagnostics.py`; new `extractors/xgboost.py`; new `schema/v1_1/`; new API endpoints `/diagnostics`, `/diff`, `/tags`; `storage/registry.py` activates tags table
- **Frontend**: Recommendations panel in Importance view; interaction heatmap; artifact list view becomes filterable; diff view (new route `/artifacts/:id/diff/:compareId`); tags UI
- **Dependencies**: XGBoost extractor adds `xgboost` to `[project.optional-dependencies].ml`; `scipy` may be needed for interaction normalization
- **Schema**: v1.1.0 is strictly additive — no breaking changes; consumers pinned to v1.0.0 are unaffected
- **CI**: XGBoost integration tests require the `xgboost` package in the dev dependency group
