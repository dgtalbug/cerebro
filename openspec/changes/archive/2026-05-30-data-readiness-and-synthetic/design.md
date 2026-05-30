# Design — data-readiness-and-synthetic

## Context

`cerebro extract` already accepts `--samples/--labels/--eval-*/--training-table`
and routes them to `analyzers/explanations.py` (`compute_explanations`),
`analyzers/importance.py` (permutation), `analyzers/evaluation.py`, and
`data/profiler.py`. The model file alone yields Overview, Trees, and gain/split
importance. The gap is purely *inputs*: when an engineer has only a model file,
the data-dependent tabs are blank with no diagnosis.

Two independent capabilities close that gap and share one foundation — the
split-threshold data already present in `schema/v1/tree.py` (`SplitNode` carries
`feature_index` + `threshold`). `doctor` reports against it; `--synthetic`
samples from it.

## Goals

- `cerebro doctor <model> [--artifact <art>]` prints per-tab readiness, the
  missing input for each unsatisfied tab, and the exact ordered feature contract.
- `cerebro extract --synthetic` produces approximate SHAP, PDP, and a
  feature-range pseudo-profile with no data supplied.
- Every synthetic-derived section is provenance-tagged so UI/agent never present
  it as ground truth.

## Non-Goals

- No synthesis of labels, permutation importance, or evaluation metrics — these
  require ground truth and stay honestly empty/blocked.
- No repo scanning / auto-discovery (that is L3, a separate future change).
- No export-script scaffolding (L2, separate future change).
- No change to the existing data-supplied paths' numerical behavior.

## Decisions

### D1 — `doctor` is read-only and reuses the extractor's introspection
`doctor` loads the model via `get_extractor(model)` and inspects the booster's
feature names directly (the same source `extract` uses). If `--artifact` is
passed, it reads the `.cerebro.json` and checks which sections are already
populated. Output is a per-tab table plus the ordered feature contract. It never
writes files. **Rationale:** keeps it a safe, scriptable diagnostic; one source
of truth for "what the model expects."

Exit codes (stable, for CI): `0` = all tabs the model *can* satisfy are
satisfiable from the model alone; `1` = data-dependent tabs unmet. A
`--json` flag emits machine-readable readiness for the UI to consume later.

### D2 — Synthetic samples come from per-feature split-threshold ranges
Walk every `SplitNode`, group thresholds by `feature_index`. For each feature
derive `[min_threshold, max_threshold]`; sample uniformly (with small padding
beyond the extremes so leaf regions on the tails are exercised). Features that
never appear in any split get a constant (their single observed threshold, or 0)
and are reported as unconstrained. Produces an `(n_rows, n_features)` matrix in
the model's exact feature order. **Rationale:** thresholds are the only
data-distribution signal the model contains; uniform-within-range is naive but
sufficient to drive path-dependent TreeSHAP and PDP.

### D3 — Synthetic path reuses existing analyzers unchanged
The generated matrix is passed straight into the existing
`compute_explanations(booster, samples, feature_names, ...)`. Path-dependent
TreeSHAP (LightGBM `pred_contrib`) needs no real background set, so SHAP and PDP
work as-is. The feature-range pseudo-profile is a new, small producer that emits
a `DataProfile`-shaped section from the threshold ranges (range, split count per
feature) rather than real column statistics. **Rationale:** zero duplication of
the SHAP/PDP logic; the only genuinely new code is matrix generation + the
pseudo-profile producer.

### D4 — Provenance marker on the schema, not a parallel section
Add an optional `provenance: "measured" | "synthetic"` (default `"measured"`)
field to the affected schema sections (explanations, the data profile, and any
synthetic importance). UI badges and the agent context shaper branch on it.
**Rationale:** a single typed field is simpler and less error-prone than
duplicate "approximate_*" sections, and it is backward compatible (defaulted).

### D5 — `--synthetic` is mutually informed by, not exclusive with, real data
If real `--samples` are supplied, `--synthetic` is ignored for explanations
(real data wins) and a warning is logged. `--synthetic` only fills sections that
would otherwise be empty. **Rationale:** least-surprise; never silently degrade
a real result to an approximate one.

## Risks / Trade-offs

- **Misleading approximations.** Uniform-in-range samples can produce SHAP/PDP
  that misrepresent real behavior on skewed features. Mitigation: D4 provenance
  tag + explicit "approximate" badge; docs state the synthetic distribution
  assumption; eval/permutation never synthesized so no correctness metric is
  ever faked.
- **Features absent from all splits.** No range signal. Mitigation: hold
  constant, mark unconstrained, surface in `doctor` output.
- **Schema field addition.** Downstream readers must tolerate the new
  `provenance` field. Mitigation: optional with a `"measured"` default; bump is
  additive, no version break.

## Open Questions

- Padding fraction beyond min/max thresholds — fixed default (e.g. 5%) or
  configurable flag? (Leaning fixed default for v1.)
- Number of synthetic rows — fixed (e.g. 500) or scaled to feature count?
