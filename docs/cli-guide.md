# Cerebro CLI Guide

The CLI is a thin wrapper over the library. Every command uses the same
code path the API uses, so a green CLI run is a reliable signal of API
correctness too.

Install: `uv sync` installs the `cerebro` entrypoint into the venv.

```
cerebro --help
```

---

## `cerebro extract`

Extract a canonical artifact from a trained LightGBM model file.

```
cerebro extract MODEL --output PATH [options]
```

**Arguments**

| Argument | Required | Description |
|---|---|---|
| `MODEL` | yes | Path to a `.txt` LightGBM model file |
| `--output PATH`, `-o` | yes | Where to write the `.cerebro.json` artifact |

**Options**

| Option | Description |
|---|---|
| `--samples CSV` | Feature samples (CSV) for SHAP and permutation importance |
| `--labels CSV` | Single-column CSV with ground-truth labels aligned to `--samples` |
| `--eval-samples CSV` | Held-out feature samples for evaluation metrics |
| `--eval-labels CSV` | Ground-truth labels aligned to `--eval-samples` |
| `--training-table CSV` | Full training table for data profiling |

`--samples` and `--labels` must be used together.
`--eval-samples` and `--eval-labels` must be used together.

**Examples**

```bash
# Minimal — trees + importance only
cerebro extract loan.txt --output loan.cerebro.json

# With SHAP + evaluation
cerebro extract loan.txt \
  --samples train.csv --labels labels.csv \
  --eval-samples eval.csv --eval-labels eval_labels.csv \
  --output loan.cerebro.json

# With data profile
cerebro extract loan.txt \
  --training-table full_train.csv \
  --output loan.cerebro.json
```

**Exit codes**

| Code | Meaning |
|---|---|
| 0 | Success |
| 2 | `ArtifactNotFoundError` — model file not found |
| 3 | `CorruptArtifactError` — model file unreadable |
| 4 | `UnsupportedObjectiveError` / `UnsupportedFrameworkError` |
| 1 | Any other `CerebroError` |

---

## `cerebro validate`

Load and validate a `.cerebro.json` artifact end-to-end.

```
cerebro validate ARTIFACT
```

Reads the artifact through the same path the API uses. If it validates,
the artifact will be served correctly.

```bash
cerebro validate loan.cerebro.json
# valid: schema=1.0.0 framework=lightgbm objective=binary trees=100 features=12
```

---

## `cerebro index`

Register `.cerebro.json` artifacts in the SQLite registry.

```
cerebro index [--directory DIR] [--rebuild] [--db PATH]
```

**Options**

| Option | Default | Description |
|---|---|---|
| `--directory`, `-d` | `./data/artifacts` | Root directory containing `<model>/<version>/` sub-directories |
| `--rebuild` | false | Drop all tables, reinitialise schema v2, and rescan |
| `--db` | `./data/cerebro.db` | Path to the SQLite registry database |

Expected layout: `<directory>/<model_name>/v<N>/<file>.cerebro.json`.
Files not matching this layout are skipped with a warning.

```bash
# Incremental index
cerebro index

# Full rebuild from scratch
cerebro index --rebuild

# Custom paths
cerebro index --directory /mnt/models --db /mnt/cerebro.db
```

---

## `cerebro serve`

Start the FastAPI server.

```
cerebro serve [--host HOST] [--port PORT]
```

**Options**

| Option | Default | Description |
|---|---|---|
| `--host` | `0.0.0.0` | Bind address |
| `--port` | `8000` | TCP port |

```bash
cerebro serve
# API: http://localhost:8000
# Swagger: http://localhost:8000/docs
```

---

## `cerebro ask`

Ask the AI agent a question about an artifact file.

```
cerebro ask ARTIFACT QUESTION
```

Requires `CEREBRO_LLM_PROVIDER` to be set (see [README](../README.md#ai-agent-configuration)).

**Examples**

```bash
CEREBRO_LLM_PROVIDER=ollama \
cerebro ask loan.cerebro.json "What are the top three features?"

CEREBRO_LLM_PROVIDER=copilot \
GITHUB_TOKEN=ghp_... \
cerebro ask loan.cerebro.json "Does this model show signs of leakage?"
```

**Output**

```
The top three features by gain importance are credit_score (artifact:
importance.gain.credit_score), annual_income (artifact: importance.gain.annual_income),
and loan_amount (artifact: importance.gain.loan_amount).

Citations:
  - importance.gain.credit_score
  - importance.gain.annual_income
  - importance.gain.loan_amount
```
