# Cerebro Artifact Schema — v1.0.0

The canonical artifact is a gzip-compressed JSON file (`.cerebro.json`).
Every downstream consumer — the dashboard, the agent, CLI tools — reads
this file; none of them import LightGBM.

## Top-level structure

```json
{
  "schema_version": "1.0.0",
  "source": { ... },
  "model": { ... },
  "trees": [ ... ],
  "importance": { ... },
  "explanations": null,
  "evaluation": null,
  "data_profile": null
}
```

`explanations`, `evaluation`, and `data_profile` are optional — they are
`null` when the corresponding data was not provided at extraction time.

---

## `source`

Extraction provenance.

```json
{
  "framework": "lightgbm",
  "framework_version": "4.6.0",
  "extractor_version": "0.1.0",
  "extracted_at": "2026-05-29T10:00:00Z"
}
```

---

## `model`

Model metadata extracted from the booster.

```json
{
  "objective": "binary",
  "num_class": 1,
  "num_iteration": 100,
  "params": {
    "learning_rate": 0.1,
    "num_leaves": 31,
    "max_depth": -1
  },
  "feature_schema": {
    "names": ["age", "income", "credit_score"],
    "categorical_indices": [],
    "monotone_constraints": []
  }
}
```

`objective` is one of `"binary"`, `"multiclass"`, `"regression"`,
`"lambdarank"`, `"cross_entropy"`, `"mape"`, or `"huber"`.

---

## `trees`

Array of decision trees in the ensemble. Each tree:

```json
{
  "index": 0,
  "class_index": null,
  "num_leaves": 31,
  "root": {
    "id": 0,
    "split_feature": 2,
    "threshold": 650.5,
    "decision_type": "<=",
    "left": { ... },
    "right": { ... },
    "leaf_value": null,
    "internal_value": 0.0,
    "internal_count": 1000
  }
}
```

For multiclass models `class_index` identifies which class the tree belongs to.
Leaf nodes have `leaf_value` set and `left`/`right` as `null`.

---

## `importance`

Built-in LightGBM feature importance scores.

```json
{
  "gain": { "credit_score": 847.2, "age": 312.5 },
  "split": { "credit_score": 142, "age": 98 },
  "permutation": null
}
```

`permutation` is populated only when eval samples are provided.

---

## `explanations`

SHAP values computed for a sample set.

```json
{
  "expected_value": -1.23,
  "shap_values": [[0.12, -0.34, 0.56], ...],
  "feature_names": ["age", "income", "credit_score"],
  "sample_count": 100,
  "background_sample_count": 100,
  "decision_paths": [ ... ],
  "partial_dependence": [ ... ]
}
```

`decision_paths` is a list of lists — one inner list per sample, each
containing one `DecisionPath` per tree.

`partial_dependence` contains one entry per top feature (up to 10):

```json
{
  "feature": "credit_score",
  "feature_index": 2,
  "grid": [500.0, 550.0, ...],
  "values": [0.1, 0.2, ...],
  "is_categorical": false
}
```

---

## `evaluation`

Objective-specific metrics. The `objective` field discriminates the variant.

### Binary

```json
{
  "objective": "binary",
  "auc": 0.87,
  "threshold": 0.5,
  "precision": 0.82,
  "recall": 0.79,
  "f1": 0.80,
  "roc_curve": [{"fpr": 0.0, "tpr": 0.0, "threshold": 1.0}, ...],
  "confusion_matrix": [{"predicted": 0, "actual": 0, "count": 45}, ...]
}
```

### Multiclass

```json
{
  "objective": "multiclass",
  "macro_f1": 0.76,
  "accuracy": 0.78,
  "confusion_matrix": [...],
  "per_class": [{"class_index": 0, "precision": 0.8, "recall": 0.7, "f1": 0.75, "support": 50}, ...]
}
```

### Regression

```json
{
  "objective": "regression",
  "rmse": 12.3,
  "mae": 8.1,
  "r2": 0.91,
  "residuals_histogram": [...],
  "scatter": [...],
  "interval_band": [...]
}
```

### Ranking (lambdarank)

```json
{
  "objective": "lambdarank",
  "mean_average_precision": 0.73,
  "ndcg_at_k": [{"k": 1, "value": 0.85}, {"k": 5, "value": 0.78}],
  "per_query_ndcg": [0.9, 0.7, ...]
}
```

---

## `data_profile`

Statistical profile of the training table.

```json
{
  "row_count": 10000,
  "column_count": 15,
  "columns": [
    {
      "name": "credit_score",
      "dtype": "DOUBLE",
      "is_numeric": true,
      "is_categorical": false,
      "total_rows": 10000,
      "null_count": 12,
      "missingness": 0.0012,
      "min": 300.0,
      "max": 850.0,
      "mean": 680.4,
      "std": 87.2,
      "histogram": [{"lower": 300.0, "upper": 327.5, "count": 42}, ...]
    }
  ],
  "correlations": [
    {"feature_a": "age", "feature_b": "income", "pearson": 0.34}
  ]
}
```

---

## Versioning policy

Schema version is a three-part semver string in `schema_version`.

- **Patch** (1.0.x): bug fixes to existing field types, no structural change.
- **Minor** (1.x.0): additive optional fields; v1.0.0 artifacts remain valid.
- **Major** (x.0.0): breaking change to existing required fields; requires a migration.

The committed JSON Schema contract lives at `schemas/v1/cerebro-artifact.schema.json`.
CI fails if it drifts from the Pydantic models.
