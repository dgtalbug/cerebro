# Variant Coverage — proposal

> **Spec reference:** Implements `.docs/cerebro-open-spec.md` Part VI §3.2 (M2
> tasks E1.017–E1.027). Schema, extraction, importance, and UI additions are
> constrained by Part I §6, Part II §5, §6, §7, §8, and Part III §3, §4, §5.

## What

Extend the binary-only walking skeleton from M1 to all five LightGBM variants
(multiclass, regression, ranker, multi-output), add permutation importance
and divergence detection, and ship two new dashboard views: Trees and
Importance. The binary variant already works — M2 proves the extractor
pattern generalizes without breaking what M1 shipped.

> train any LGB variant → extract a canonical artifact → serve via the same
> API → render in Overview + two new views (Trees, Importance).

## Why

The product claims to support all five LightGBM variants. M1 proved one works;
M2 proves all five. Permutation importance turns the importance dashboard
panel from a "pretty listing" into a diagnostic tool — the first concrete
signal toward the "make your model better" value proposition. The Trees view
is a differentiator: no other tool renders full tree topology from a frozen
canonical artifact.

The extractor architecture decision — Protocol + per-variant classes — also
validates that the pattern scales. If it works cleanly for LightGBM's five
objectives, it'll work for XGBoost and CatBoost extractors later.

## Scope

**In scope — five LGB variants + importance + two views**

1. Extractors for multiclass, regression, ranker, and multi-output LGB
   boosters (binary is already done).
2. Shared base helpers (`_lightgbm_base.py`) extracted from the M1
   `LGBExtractor` — no copy-paste of node-building, importance, or
   parameter extraction logic.
3. Permutation importance via `sklearn.inspection.permutation_importance`
   — runs only when labeled samples are provided at extraction time.
4. Divergence detection: gain-rank vs permutation-rank disagreement,
   configurable threshold (default 5 ranks).
5. `GET /artifacts/{id}/importance?type=gain|split|permutation` endpoint.
6. Importance view in UI — gain/split/permutation tabs using CSS bars
   (matching the mockup `.fi-` classes), divergence callout panel.
7. Trees view in UI — tree selector dropdown, depth filter, node inspector
   panel. `react-d3-tree` lazy-loaded (only bundled when Trees mounts).
8. Committed example artifacts in `examples/` — one per variant.
9. Snapshot tests for each variant's canonical output.
10. Regression guard: M1 binary variant still passes all existing tests.

**Out of scope (deferred to later changes)**

- SHAP explanations, decision-path tracing, partial dependence (M3).
- Evaluation metrics, confusion matrices, ROC curves (M3).
- Data profile and training-table ingestion (M3).
- Agent view and LLM integration (M4).
- Schema version bump to v1.1 (not needed — M2 additions are optional fields
  with defaults; existing v1.0.0 artifacts validate unchanged).
- XGBoost / CatBoost extractors (M2 / M3).
- Reaviz charting library (the mockup uses CSS bars for importance;
  Reaviz is a later integration if vector SVG charts are needed).
- Tree node "sample coverage" from `dump_model()` (LightGBM doesn't store
  sample counts per node in boosters trained without `--store-data`; the
  node inspector shows available data — split feature, threshold, leaf
  value, gain — but not sample count unless the booster was trained with it).

## How — twelve tasks in dependency order

Backend tasks 1→6 are sequential because each variant depends on the base
helpers and the widened schema. Frontend tasks (8, 9, 10) can be developed
in parallel with backend tasks 3→6 once the API contract is frozen by
task 2 (schema widening) + task 6 (importance endpoint).

| # | Task | Acceptance check |
|---|------|------------------|
| 1 | Shared base helpers — extract M1 `LGBExtractor` private methods into `_lightgbm_base.py`. No functional change; existing 75 tests still green. | `pytest -n auto` is 75/75. `import-linter` still forbids consumption modules from importing `lightgbm`. |
| 2 | Schema widening — `objective` → union of 5 literals, `num_class` → int, `divergence_warnings` optional field on Importance, `rank_metadata` optional on artifact. Schema v1.0.0 still frozen on disk. | Existing binary fixtures validate against widened models. `round_trip` test still passes. JSON-Schema drift gate still green. |
| 3 | LGBBinaryExtractor — clone of M1's `LGBExtractor` but using base helpers. CLI and API wired to the new class. M1 `LGBExtractor` stays for backward compat in tests; deprecated after M2. | `pytest tests/extractors/test_lightgbm_binary.py` passes with the new extractor. CLI `cerebro extract` works. |
| 4 | Multiclass extractor — per-class trees with `class_index`. | 50-tree 3-class classifier → artifact validates, every tree has `class_index` set, `num_class == 3`. |
| 5 | Regression extractor — continuous leaf values, no `num_class` constraint. | 50-tree regressor → artifact validates, `objective == "regression"`, leaf values are continuous. |
| 6 | Ranker extractor — `lambdarank` objective, group metadata in `rank_metadata`. | 30-tree ranker (synthetic queries) → artifact validates, `rank_metadata` has `group_sizes`. |
| 7 | Multi-output extractor — multiple targets, multiple importance vectors. | Multi-output regressor (2 targets) → artifact validates, importance keys differ per output. |
| 8 | `analyzers/importance.py` — permutation computation + divergence logic. | Accept numpy array + booster → return permutation scores + divergence warnings. Unit test on known feature set. |
| 9 | `GET /artifacts/{id}/importance` endpoint. | `TestClient` hits endpoint with `?type=gain`, `?type=split`, `?type=permutation` — each returns 200 with expected shape. Missing type → 422. No permutation data → structured message. |
| 10 | Importance view — gain/split/permutation tabs, CSS bar charts matching mockup, divergence callout. | Renders against mocked API response; tab switching works; divergence panel shows warnings when present. |
| 11 | Trees view — tree selector, depth filter, react-d3-tree (lazy-loaded), node inspector. | Renders against mocked API response with 3-tree fixture; tree selector changes rendered tree; node click shows inspector. |
| 12 | Snapshot tests + example artifacts + regression guard. | Five committed example artifacts; snapshot tests assert binary-equivalent output; M1 binary tests all still green; full gate sweep: ruff, mypy, pytest (all 75 + new), UI lint/typecheck/build/test, contracts. |

## Key decision: schema widening without a new folder

The project constitution says "schema versioning is by folder copy." M2 adds
optional fields with defaults and widens literal types — both are backward-
compatible operations that don't invalidate existing v1.0.0 artifacts. A
binary artifact extracted by M1 still validates against the widened Pydantic
models. The committed JSON Schema in `schemas/v1/cerebro-artifact.schema.json`
gets regenerated (it reflects the widened types), but the *folder* is not
duplicated — `schemas/v1/` remains the single source of truth for artifacts
that carry `schema_version: "1.0.0"`.

If a future change removes a field or changes a non-optional type, that
change creates `schemas/v1.1/` with a folder copy. M2 doesn't do that.

## Objective detection (the variant dispatch seam)

LightGBM's `dump_model()` stores `objective` as `"<name> <args>"`. The first
token is the keyword. M2 replaces `_guard_objective` with
`_resolve_objective`:

```
"binary ..."            → "binary"
"multiclass ..."        → "multiclass"
"regression ..."        → "regression"
"lambdarank ..."        → "lambdarank"
"multi_output ..."      → "multi_output"
```

Unknown keywords still raise `UnsupportedObjectiveError`. The mapping lives
in `_lightgbm_base.py` so all variant extractors share it.

## Divergence threshold — configurable, default 5

`extractor.extract(model_path, samples=samples, labels=labels, divergence_threshold=5)`

Features where `|gain_rank - permutation_rank| > divergence_threshold` are
flagged. The threshold is NOT stored in the artifact — it's an extraction-time
parameter. Re-extraction with a different threshold produces different
warnings. The default of 5 ranks is conservative; users tuning for
sensitivity can lower it, users who only want extreme cases can raise it.

One structured log entry per artifact when divergence IS detected:
```python
log.info("importance.divergence.detected", num_divergent=3, threshold=5)
```

No per-feature log spam.

## Constraints carried forward

- No spec identifiers in code, comments, or logs.
- No bare `except:` / `except Exception:` in library code.
- structlog JSON logging with bound fields.
- `gitnexus_search` before new modules; `npx gitnexus analyze` after commits.
- One Conventional Commit per task; no AI-attribution trailers.
- Extractor Protocol — variants are new classes, not edits to existing.
- Schema v1.0.0 stays frozen on disk; Pydantic models widen compatibly.
- `react-d3-tree` is `React.lazy()` — not in the initial bundle.

## Dependencies

This change depends on M1 (everything on `main`). All 75 backend tests and
18 UI tests must stay green throughout.

This change does NOT depend on:
- Reaviz (we use CSS bars matching the mockup).
- New Python dependencies beyond what's already in `pyproject.toml`
  (sklearn and lightgbm are already dev dependencies from M1).
- Any schema v1.1 folder.
- Any infrastructure changes (Docker, CI, compose).

## Acceptance

- [ ] All five LGB variants extract and pass schema validation.
- [ ] `GET /artifacts/{id}/importance` returns gain, split, and (when
      samples provided) permutation data.
- [ ] Importance view renders gain/split/permutation tabs; divergence
      callout shows warnings when present.
- [ ] Trees view renders tree selector, depth filter, node inspector;
      react-d3-tree loaded on demand.
- [ ] Five example artifacts committed in `examples/`.
- [ ] Snapshot tests pass against committed examples.
- [ ] M1 binary variant: all 75 existing backend tests still green.
- [ ] Full gate sweep: ruff + format, mypy --strict, lint-imports,
      pytest -n auto, pnpm lint/typecheck/build/test, contract checks.
- [ ] `openspec validate m2-variant-coverage --strict` clean.
