## ADDED Requirements

### Requirement: Shared LightGBM extraction helpers

The system SHALL consolidate all LightGBM booster parsing logic into a
module-level pure-function library at `cerebro.extractors._lightgbm_base`.
This module SHALL be the single source of truth for objective resolution,
booster loading, node building, feature schema construction, parameter
extraction, importance computation, and source metadata — shared by all
per-variant extractors with no duplication.

#### Scenario: Objective resolved from dump

- **WHEN** a LightGBM booster's `dump_model()` returns an objective string
  such as `"binary sigmoid:1"` or `"multiclass num_class:3"`
- **THEN** `_resolve_objective` returns the canonical keyword (`"binary"`,
  `"multiclass"`, etc.) by splitting on whitespace and taking the first token

#### Scenario: Unknown objective raises

- **WHEN** `_resolve_objective` receives a keyword not in the five supported
  values
- **THEN** it raises `UnsupportedObjectiveError` immediately, before any
  partial artifact is constructed

### Requirement: Per-variant LightGBM extractors

The system SHALL provide five extractor classes — `LGBBinaryExtractor`,
`LGBMulticlassExtractor`, `LGBRegressionExtractor`, `LGBRankerExtractor`,
`LGBMultiOutputExtractor` — each implementing the `Extractor` Protocol and
delegating to the shared base helpers for all common logic.

#### Scenario: Multiclass trees carry class_index

- **WHEN** a multiclass booster with N iterations and K classes is extracted
- **THEN** the artifact contains N × K trees, each with `class_index` set to
  its class (0 to K−1) in round-robin order, and `model.num_class` equals K

#### Scenario: Regression uses continuous leaf values

- **WHEN** a regression booster is extracted
- **THEN** `model.objective` is `"regression"`, `model.num_class` is 1,
  no tree carries a `class_index`, and leaf values are unbounded floats

#### Scenario: Ranker preserves group metadata

- **WHEN** a lambdarank booster is extracted
- **THEN** `model.objective` is `"lambdarank"` and `rank_metadata.group_sizes`
  is populated from booster params when available; when unavailable it is an
  empty list with a `source` field set to `"unavailable"`

#### Scenario: Multi-output stores per-output importance

- **WHEN** a multi-output booster is extracted
- **THEN** `rank_metadata.multi_output_importance` contains per-output
  importance vectors keyed by output index, and the canonical
  `importance.gain` / `importance.split` fields hold aggregated (sum) scores

### Requirement: Objective-aware auto-dispatch

The system SHALL provide a `get_extractor(model_path)` function that loads
the booster, resolves the objective keyword, and returns the matching
extractor instance — without the caller selecting a variant explicitly.

#### Scenario: CLI uses auto-dispatch

- **WHEN** `cerebro extract <model_path>` is invoked
- **THEN** the correct variant extractor is selected automatically based on
  the booster's objective, and the resulting artifact reflects the correct
  variant shape

### Requirement: Permutation importance at extraction time

The system SHALL support optional permutation importance computation during
extraction. When `samples` and `labels` are both provided to an extractor's
`extract()` method, the system SHALL compute permutation importance via
`sklearn.inspection.permutation_importance` and populate
`importance.permutation`. When only one is provided, the system SHALL raise
`ValueError`.

#### Scenario: Permutation scores populated with samples

- **WHEN** `extract(model_path, samples=X, labels=y)` is called
- **THEN** `importance.permutation` is a dict keyed by feature name with
  `{"mean": float, "std": float}` values

#### Scenario: Partial samples raises

- **WHEN** only `samples` or only `labels` is provided (not both)
- **THEN** `ValueError` is raised with a message indicating both are required
