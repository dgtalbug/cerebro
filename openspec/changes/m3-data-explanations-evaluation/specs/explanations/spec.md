## ADDED Requirements

### Requirement: SHAP computation at extraction time
The system SHALL provide `analyzers/explanations.py` with a `compute_shap`
function that wraps `shap.TreeExplainer`. The function SHALL accept a booster
object, a sample matrix, and optional labels for background stratification.
The function SHALL NOT import lightgbm at module level. The computed SHAP
values SHALL be stored in the artifact as a `ShapResult`; no live model is
needed at view time. The background dataset size SHALL be capped at
`SHAP_BACKGROUND_SAMPLES` (named constant). When labels are provided the
background SHALL be stratified by target quintile; otherwise uniform random.

#### Scenario: SHAP with binary booster and labels
- **WHEN** `compute_shap(booster, samples, labels=labels)` is called
- **THEN** returns a `ShapResult` with `shap_values` of shape `(n_samples, n_features)` and non-null `expected_value`

#### Scenario: SHAP background stratified
- **WHEN** labels are provided
- **THEN** the background dataset contains samples from each target quintile proportionally

#### Scenario: SHAP capped at max samples
- **WHEN** the sample matrix has more rows than `SHAP_MAX_EXPLAIN_SAMPLES`
- **THEN** a random subset of `SHAP_MAX_EXPLAIN_SAMPLES` rows is used and a warning is logged

#### Scenario: SHAP without labels uses uniform background
- **WHEN** no labels are provided
- **THEN** the background dataset is a uniform random sample of `SHAP_BACKGROUND_SAMPLES` rows

### Requirement: Decision path tracing
The system SHALL provide a `trace_path` pure function in `analyzers/explanations.py`
that traces a single sample's path through a canonical `Tree` to a leaf. The
function SHALL NOT import lightgbm. The function SHALL return a `DecisionPath`
listing each split node visited (feature index, threshold, decision direction)
and the leaf value. The function SHALL be deterministic and side-effect free.

#### Scenario: Binary split path
- **WHEN** `trace_path(tree, sample_values)` is called
- **THEN** returns a `DecisionPath` whose `nodes` list ends at a leaf node

#### Scenario: Categorical split path
- **WHEN** a tree node uses `decision_type == "=="` for a categorical feature
- **THEN** the tracer evaluates membership correctly and follows the correct branch

#### Scenario: Sample values length mismatch
- **WHEN** `sample_values` length differs from the number of features in the tree
- **THEN** raises `ValueError` with a clear message

### Requirement: Partial dependence computation
The system SHALL provide a `compute_pdp` function in `analyzers/explanations.py`
that computes partial dependence profiles for the top-N features by gain
importance. The function SHALL precompute a grid of `PDP_GRID_POINTS` values
per feature. For categorical features the grid SHALL use the known category
values. The returned data SHALL be in `{feature, grid, values}` shape suitable
for Reaviz `Sparkline`.

#### Scenario: PDP over numeric features
- **WHEN** `compute_pdp(booster, samples, feature_names, importance, categorical_indices)` is called
- **THEN** returns a list of `PDPFeature` objects each with `grid` and `values` of length `PDP_GRID_POINTS`

#### Scenario: PDP over categorical features
- **WHEN** a top-N feature has a categorical index
- **THEN** the PDP grid contains the distinct category values, not a numeric linspace

#### Scenario: Top-N capped correctly
- **WHEN** the model has fewer features than `PDP_TOP_N_FEATURES`
- **THEN** all features are profiled without error
