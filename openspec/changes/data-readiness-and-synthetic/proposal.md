## Why

The richest dashboard tabs (Explanations, Evaluation, Importance/permutation,
Data Profile) only populate when the engineer hand-supplies `--samples`,
`--labels`, `--eval-*`, and `--training-table`. Today the only help is a manual
playbook (`docs/dashboard-readiness.md`): grep your repo, hand-write an export
script. Many engineers receive only a model file — their data was left behind —
so those tabs stay silently blank with no explanation of why or what to do.

This change gives those engineers two things: a command that tells them exactly
what is missing and the precise feature contract the model expects (**L1**), and
a model-only path that synthesizes approximate SHAP / PDP and a feature-range
pseudo-profile from the trees themselves (**L4**) so the artifact is non-empty
even with zero data.

## What Changes

- Add a `cerebro doctor <model>` CLI command that inspects a model file (and an
  optional already-extracted artifact) and prints, per dashboard tab: whether it
  is satisfiable, what input is missing, and the exact ordered feature-name
  contract the model expects. Exit code reflects readiness for scripting.
- Add a `--synthetic` flag to `cerebro extract` that, with no data supplied,
  synthesizes a feature matrix by sampling within each feature's observed split
  thresholds, then computes **approximate** path-dependent SHAP, PDP, and a
  feature-range pseudo-profile.
- Synthetic-derived sections are explicitly flagged as approximate in the
  artifact so the UI and agent never present them as ground truth.
- Honest boundaries: permutation importance and evaluation metrics require
  labels and are **never** synthesized — `doctor` reports them as label-blocked
  and `--synthetic` leaves them empty.

## Capabilities

### New Capabilities
- `data-readiness`: A model-introspection report (`cerebro doctor`) that maps a
  model file to per-tab readiness, lists missing inputs, and emits the exact
  feature-name contract required to supply data.
- `synthetic-inputs`: Model-only synthesis of an approximate feature matrix from
  split-threshold ranges, used to produce approximate SHAP, PDP, and a
  feature-range pseudo-profile, with provenance marking each section approximate.

### Modified Capabilities
- `distribution`: Adds the `doctor` subcommand and the `extract --synthetic`
  flag to the CLI surface.

## Impact

- New CLI commands/flags in `src/cerebro/cli/main.py`.
- New modules under `src/cerebro/` for readiness reporting and synthetic input
  generation (consuming existing `schema/v1/tree.py` split data and the
  `analyzers/explanations.py` / `analyzers/importance.py` machinery).
- Canonical schema gains a provenance/approximate marker on affected sections
  (`schema/v1/explanations.py`, importance, data profile).
- Dashboard (UI) must render an "approximate" badge for synthetic sections; the
  agent context shaper must disclose approximate provenance. Both are downstream
  consumers flagged here; their detailed work is scoped in tasks.
- No breaking changes — all additions are opt-in; existing extract behavior is
  unchanged when no new flags are used.
