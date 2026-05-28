# Evaluation

## Purpose

Compute frozen evaluation metrics for a trained model at extraction time.
Metrics are dispatched by objective type (binary, multiclass, regression,
ranking) and stored in the canonical artifact so the dashboard and AI agent
can render them without a live model. The evaluation module MUST NOT import
LightGBM.

## Requirements

### Requirement: Objective-aware evaluation dispatcher

The system SHALL provide `analyzers/evaluation.py` with an `evaluate` function
that dispatches to the correct panel computation based on the artifact's
objective field. Unsupported objectives SHALL raise `UnsupportedObjectiveError`.
The function SHALL NOT import lightgbm. All metrics SHALL be computed at
extraction time and stored frozen in the artifact.

#### Scenario: Binary objective routes to binary panel

- **WHEN** `evaluate(predictions, labels, objective="binary")` is called
- **THEN** returns a `BinaryEval` with `roc_curve` and `confusion_matrix` populated

#### Scenario: Multiclass routes to multiclass panel

- **WHEN** `evaluate(predictions, labels, objective="multiclass")` is called
- **THEN** returns a `MulticlassEval` with an NxN confusion matrix and per-class metrics

#### Scenario: Regression routes to regression panel

- **WHEN** `evaluate(predictions, labels, objective="regression")` is called
- **THEN** returns a `RegressionEval` with residuals histogram, scatter data, and prediction intervals

#### Scenario: Ranking routes to ranking panel

- **WHEN** `evaluate(predictions, labels, objective="lambdarank", query_ids=q)` is called
- **THEN** returns a `RankingEval` with nDCG@k bars, MAP, and per-query score distribution

#### Scenario: Unsupported objective raises error

- **WHEN** `evaluate(predictions, labels, objective="unknown")` is called
- **THEN** raises `UnsupportedObjectiveError`

### Requirement: Binary evaluation panel

The system SHALL compute ROC curve points and a confusion matrix for binary
models. ROC SHALL be computed at multiple thresholds (minimum 100). The
confusion matrix SHALL use the 0.5 default threshold. AUC SHALL be included.

#### Scenario: ROC curve points

- **WHEN** binary eval runs against a dataset with both positive and negative labels
- **THEN** `BinaryEval.roc_curve` contains at least 100 `(fpr, tpr)` points

#### Scenario: Confusion matrix at 0.5 threshold

- **WHEN** binary eval runs
- **THEN** `BinaryEval.confusion_matrix` is a 2×2 matrix with TP/FP/TN/FN counts

### Requirement: Multiclass evaluation panel

The system SHALL compute an NxN confusion matrix and per-class precision,
recall, and F1 for multiclass models.

#### Scenario: NxN confusion matrix

- **WHEN** multiclass eval runs with N distinct classes
- **THEN** `MulticlassEval.confusion_matrix` has shape N×N

#### Scenario: Per-class metrics

- **WHEN** multiclass eval runs
- **THEN** `MulticlassEval.per_class` contains precision, recall, and F1 for each class index

### Requirement: Regression evaluation panel

The system SHALL compute a residuals histogram, predicted-vs-actual scatter
data, and prediction intervals (5th–95th percentile band) for regression models.

#### Scenario: Residuals histogram

- **WHEN** regression eval runs
- **THEN** `RegressionEval.residuals_histogram` contains bin edges and counts

#### Scenario: Predicted-vs-actual scatter

- **WHEN** regression eval runs
- **THEN** `RegressionEval.scatter` contains `(predicted, actual)` pairs

#### Scenario: Prediction interval band

- **WHEN** regression eval runs
- **THEN** `RegressionEval.interval_band` contains 5th and 95th percentile bounds per prediction

### Requirement: Ranking evaluation panel

The system SHALL compute nDCG@k for k ∈ {1,3,5,10}, MAP, and a per-query
score distribution for ranking models.

#### Scenario: nDCG@k values

- **WHEN** ranking eval runs
- **THEN** `RankingEval.ndcg_at_k` contains values for k in {1, 3, 5, 10}

#### Scenario: MAP computed

- **WHEN** ranking eval runs
- **THEN** `RankingEval.mean_average_precision` is a float between 0 and 1

#### Scenario: Per-query distribution

- **WHEN** ranking eval runs with multiple queries
- **THEN** `RankingEval.per_query_ndcg` contains one nDCG@10 value per query
