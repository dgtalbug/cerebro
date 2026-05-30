# Cerebro Dashboard — Data & Config Readiness Checklist

Use this to audit your codebase and data pipeline. For each tab, check what
exists, what needs generating, and what needs wiring.

---

## Tab 1 — Overview

**Always available from the model file alone. No action needed.**

Displays: objective, tree count, feature count, model params (learning rate,
num_leaves, etc.), framework version, extraction timestamp.

**You have this if:** you have a `.lgb`, `.txt`, or `.pkl` LightGBM model file.

---

## Tab 2 — Trees

**Always available from the model file alone. No action needed.**

Displays: full decision tree topology — every split node, threshold, feature,
leaf value.

**You have this if:** you have a model file.

---

## Tab 3 — Importance

**Gain + split: always available. Permutation importance: needs samples + labels.**

| Section | Requires | Search for |
|---|---|---|
| Gain importance | model file | nothing |
| Split importance | model file | nothing |
| Permutation importance | `--samples` (feature matrix CSV) + `--labels` (target CSV) | see Explanations below |

Permutation importance shows how much accuracy drops when each feature is
shuffled — more reliable than gain for detecting redundant features.

---

## Tab 4 — Explanations

**Needs: feature matrix (samples) + optionally labels**

Displays: SHAP values per sample, mean |SHAP| ranking, decision path traces,
partial dependence plots (PDP) for top features.

### Required file: `samples.csv`

- One row per sample, one column per feature
- Column names must match the model's feature names **exactly**
- Must be post-feature-engineering, post-encoding (same feature space the model
  was trained on)
- Recommended: 200–1000 rows (SHAP is computed per-row; more = slower)

### Search your repo for

```
fit_transform(    X_train     y_train    features_df
.transform(X)    build_feature_matrix    get_features
encode(df)       X.to_csv    X.to_parquet
```

### If not found

Write a script that:

1. Loads raw training data
2. Runs the full feature engineering pipeline (same pipeline used at train time)
3. Applies any fitted encoders (OrdinalEncoder, LabelEncoder, etc.)
4. Writes the feature matrix as a flat CSV — no nested or struct columns

### Optional: `labels.csv`

- Single column, same row count as `samples.csv`
- Enables SHAP stratified background sampling (better quality) and permutation
  importance
- Search for: `y_train`, `target_col`, `label_col`, the target column name in
  your training code

---

## Tab 5 — Evaluation

**Needs: eval feature matrix + eval labels (held-out set)**

Displays based on objective:

| Objective | Metrics shown |
|---|---|
| `binary`, `cross_entropy` | AUC, ROC curve, confusion matrix, precision / recall / F1 |
| `multiclass` | Per-class metrics, macro F1, accuracy, NxN confusion matrix |
| `regression`, `quantile`, `mape`, `huber`, `poisson`, `tweedie` | RMSE, MAE, R², residuals histogram, predicted-vs-actual scatter |
| `lambdarank` | nDCG@k, MAP, per-query nDCG distribution |

### Required files: `eval_samples.csv` + `eval_labels.csv`

- Same format as `samples.csv` / `labels.csv` above
- Must be a held-out set **not** used during training (val / test split)
- Recommended: at least 500 rows for stable metrics

### Search your repo for

```
X_val    X_test    eval_set    validation_data
test_size=    train_test_split    stratified_split
holdout    cv_split    val_df
```

### If not found

Split your feature matrix:

```python
from sklearn.model_selection import train_test_split
X_train, X_eval, y_train, y_eval = train_test_split(X, y, test_size=0.2, random_state=42)
X_eval.to_csv("eval_samples.csv", index=False)
y_eval.to_frame("label").to_csv("eval_labels.csv", index=False)
```

> **Note for multiclass:** labels must be integer class indices (0, 1, 2…),
> not string labels. If you have a `LabelEncoder`, apply it to `y` before
> exporting.

---

## Tab 6 — Data Profile

**Needs: training table (raw or lightly processed training dataset)**

Displays: per-column statistics (min, max, mean, std, missingness, histogram
for numeric columns, top categories for categoricals), pairwise Pearson
correlations between numeric columns.

### Required file: any flat tabular file — CSV, Parquet, or JSON

- Should represent the full training distribution (not just a small sample)
- Can be raw / pre-encoding — this tab does **not** pass data through the model
- **Exclude nested / struct columns** (arrays of objects, JSON blobs) — they
  will cause a parse error
- Column names do not need to match model features — this is a statistical
  profile of the data, independent of the model

### Search your repo for

```
training_data.parquet    train.csv    features.parquet
training_df    df_train    raw_data    feature_store
```

### If not found

Export your training dataframe before feature engineering:

```python
# Select flat columns only — drop any list / struct / nested columns
flat_cols = [c for c in df.columns if not df[c].apply(lambda x: isinstance(x, (list, dict))).any()]
df[flat_cols].to_parquet("training_table.parquet", index=False)
```

---

## Tab 7 — Agent

**Needs: LLM provider configuration. No training data required.**

Displays: chat interface that reasons over the artifact — answers questions
about feature importance, decision logic, model weaknesses, and behavior
patterns.

### Required: one of the following environment variables

| Provider | Variables to set |
|---|---|
| **Ollama (local)** | `CEREBRO_LLM_PROVIDER=ollama` + optionally `OLLAMA_BASE_URL` (default: `http://localhost:11434/v1`) + `OLLAMA_MODEL` (default: `llama3.2`) |
| **GitHub Copilot Models API** | `CEREBRO_LLM_PROVIDER=copilot` + `GITHUB_TOKEN=<your PAT>` + optionally `GITHUB_COPILOT_MODEL` (default: `gpt-4o-mini`) |

### Search your repo for

```
OLLAMA    ollama    GITHUB_TOKEN    GITHUB_COPILOT
LLM_PROVIDER    .env    docker-compose
```

### If not found

**Ollama:** install from [ollama.com](https://ollama.com), run
`ollama pull llama3.2`, then add to `.env`:

```
CEREBRO_LLM_PROVIDER=ollama
```

**GitHub Copilot:** create a GitHub PAT with Copilot access, then add to
`.env`:

```
CEREBRO_LLM_PROVIDER=copilot
GITHUB_TOKEN=ghp_...
```

No data prep needed — the agent reads the already-extracted artifact.

---

## Quick status matrix

| Tab | Model file | samples.csv | labels.csv | eval_samples.csv | eval_labels.csv | training_table | LLM config |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Overview | ✅ | | | | | | |
| Trees | ✅ | | | | | | |
| Importance (gain / split) | ✅ | | | | | | |
| Importance (permutation) | ✅ | ✅ | ✅ | | | | |
| Explanations | ✅ | ✅ | optional | | | | |
| Evaluation | ✅ | | | ✅ | ✅ | | |
| Data Profile | | | | | | ✅ | |
| Agent | ✅ | | | | | | ✅ |

---

## Common pitfalls

```python
# Columns that will break ingest if present in your CSV / Parquet:
#   - List / array columns
#   - Struct / nested object columns
#   - Columns with all-null values

# Verify your feature matrix matches the model:
booster.feature_name()     # exact column names the model expects
len(booster.feature_name()) == len(df.columns)  # must be True

# Verify label format matches the objective:
# binary / cross_entropy  → 0 or 1 integers
# multiclass              → 0, 1, 2 … N-1 integers  (not strings)
# regression / quantile   → continuous floats
# lambdarank              → integer relevance grades (0–4)
```
