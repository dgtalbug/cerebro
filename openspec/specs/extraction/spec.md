# Extraction

## Purpose

Turn a trained LightGBM artifact into a fully populated, framework-agnostic
`CerebroArtifact`. Extraction is the only LightGBM-aware layer in the system:
it loads the booster, dumps its structure, computes importance and (when
samples are supplied) explanations and evaluation, then hands a validated
canonical artifact to storage. Everything downstream reads that artifact and
never touches the live model.

This is the inbound half of the core value proposition in Part I §1, §4:
"model artifact in → canonical introspection JSON out."

### Source references

Future changes to this capability MUST reconcile against:

- `.docs/cerebro-open-spec.md` Part I §3 (What Gets Extracted), §4 (Architecture
  layer boundary), §5 (Tech Stack rationale for `Booster.dump_model`, `shap`,
  `sklearn`)
- `.docs/cerebro-open-spec.md` Part II §4.1 (`extractors/`), §4.3 (`analyzers/`),
  §5 (Extraction Pipeline), §7 (Exception Hierarchy)
- `.docs/cerebro-open-spec.md` Part VI §3.1 (features F1.01–F1.05, F1.07–F1.10)
  and §3.3 (acceptance criteria)
- `.docs/BACKEND.md` (upstream source of Part II — authoritative when the
  consolidated doc and the source file conflict)

## Requirements

### Requirement: LightGBM-only extraction boundary

The extraction layer SHALL be the only place in the codebase that imports or
depends on LightGBM. All extractors SHALL implement a common `Extractor`
protocol (`can_extract`, `extract`) so that additional frameworks can be added
in later versions without changing consumers.

#### Scenario: A consumption module imports LightGBM

- **WHEN** a module under `analyzers/` (downstream of the canonical boundary),
  `schema/`, `storage/`, `api/`, `agent/`, or the UI imports `lightgbm`
- **THEN** that import is a defect: the canonical artifact, not the live model,
  is the contract between layers (Part I §4 hard rule)

#### Scenario: Selecting an extractor for an artifact path

- **WHEN** `extract` is invoked with a path to a trained model artifact
- **THEN** the registered `Extractor` whose `can_extract(path)` returns true is
  used
- **AND** in v0.1 the only registered implementation is `LGBExtractor`

### Requirement: Extract all five LightGBM variants

The extractor SHALL produce a complete canonical artifact for each supported
LightGBM variant, dispatching by objective: binary classifier, multiclass
classifier, regressor, ranker (`lambdarank`), and multi-output configurations.

#### Scenario: Extracting a binary classifier

- **WHEN** a trained `LGBMClassifier` with a binary objective is extracted
- **THEN** the artifact's `model.objective` is `"binary"` and every tree, node,
  split feature, threshold, decision type, and leaf value is captured

#### Scenario: Extracting a multiclass classifier

- **WHEN** a trained multiclass `LGBMClassifier` is extracted
- **THEN** each per-class tree carries its `class_index`
- **AND** `model.num_class` reflects the number of classes

#### Scenario: Extracting a ranker

- **WHEN** a `lambdarank` model is extracted
- **THEN** `model.objective` is `"lambdarank"` and group/query metadata needed
  for ranking evaluation is preserved

#### Scenario: Validation after extraction

- **WHEN** any of the five variants is extracted
- **THEN** the resulting artifact passes canonical schema validation before it
  is returned or written (see [[canonical-schema]])

### Requirement: Fail loudly on unsupported input

The extractor SHALL raise a typed error rather than return a partial or
silently degraded artifact when it cannot fully extract the input.

#### Scenario: Unsupported objective

- **WHEN** a model with an objective the extractor does not support is loaded
- **THEN** `UnsupportedObjectiveError` is raised with structured context
  (e.g. the offending objective)
- **AND** no partial artifact is written

#### Scenario: Corrupt or unreadable artifact

- **WHEN** the input file cannot be loaded as a LightGBM booster
- **THEN** `CorruptArtifactError` (or `UnsupportedFrameworkError` when the file
  is a different framework) is raised, with the original cause chained via
  `raise ... from`

### Requirement: Single-pass without samples, two-pass with samples

The extraction pipeline SHALL produce structural data, metadata, and built-in
importance (gain, split) without any sample data. When samples are provided it
SHALL additionally compute the sample-dependent sections.

#### Scenario: Extraction without samples

- **WHEN** `extract` is called with no `samples`
- **THEN** the artifact contains `model`, `trees`, and `importance` (gain +
  split) and omits `explanations` and `evaluation`

#### Scenario: Extraction with labeled samples

- **WHEN** `extract` is called with `samples` (and labels)
- **THEN** the artifact additionally includes SHAP values and expected value,
  permutation importance, and the objective-appropriate evaluation section

### Requirement: Importance computation

The extractor SHALL populate built-in `gain` and `split` importance from the
booster with no additional dependencies, and SHALL compute permutation
importance via `sklearn.inspection.permutation_importance` when labeled samples
are available.

#### Scenario: Built-in importance always present

- **WHEN** any artifact is extracted
- **THEN** `importance.gain` and `importance.split` are populated as
  `{feature_name: float}` maps

#### Scenario: Permutation importance requires samples

- **WHEN** no labeled samples are provided
- **THEN** `importance.permutation` is null rather than fabricated

### Requirement: Explanations from extracted structure

When samples are provided, the extractor SHALL compute SHAP values via
`shap.TreeExplainer` on the rehydrated booster, decision-path traces as pure
functions over the canonical tree, and partial-dependence data points.

#### Scenario: SHAP computed against provided samples

- **WHEN** a sample set is supplied
- **THEN** `explanations.shap_values` has shape n_samples × n_features and
  `explanations.samples` records the exact inputs SHAP was computed against

#### Scenario: Decision-path trace operates on canonical tree

- **WHEN** a decision path is traced for a sample
- **THEN** the trace is produced from the canonical `Tree`/`Node` structure,
  not by re-querying the live booster

### Requirement: Objective-aware evaluation

When labeled samples are provided, the extractor SHALL compute evaluation
metrics dispatched by objective family and store them in the matching
evaluation section.

#### Scenario: Classification evaluation

- **WHEN** labeled samples are supplied for a classifier
- **THEN** `evaluation.classification` contains confusion matrix, ROC, and
  precision/recall data

#### Scenario: Regression evaluation

- **WHEN** labeled samples are supplied for a regressor
- **THEN** `evaluation.regression` contains residuals and prediction-interval
  data

#### Scenario: Ranking evaluation

- **WHEN** labeled samples with group metadata are supplied for a ranker
- **THEN** `evaluation.ranking` contains nDCG and MAP data

### Requirement: Optional training-table ingestion and data profile

The extractor SHALL optionally ingest a training table (CSV / Parquet / JSON,
autodetected, loaded via DuckDB) and, when present, emit a `data_profile`
section describing distributions, missingness, correlations, and type
verification. Samples for SHAP/evaluation MAY be drawn from this table.

#### Scenario: Training table provided

- **WHEN** a training table is supplied at extraction time
- **THEN** the artifact includes a `data_profile` section and the table may be
  sampled to compute explanations and evaluation

#### Scenario: No training table provided

- **WHEN** no training table is supplied
- **THEN** the `data_profile` section is omitted and extraction still succeeds

### Requirement: Extractor protocol

The system SHALL define `cerebro.extractors.base.Extractor` as a `typing.Protocol`
exposing `extract(model_path: str | Path) -> CerebroArtifact`. Concrete
extractors SHALL be the only modules permitted to import their underlying
ML framework; every consumer downstream SHALL operate on `CerebroArtifact`
exclusively.

#### Scenario: Protocol contract

- **WHEN** a new framework extractor is added in a later change
- **THEN** it implements `Extractor`'s single method without further
  coordination from `storage`, `api`, `agent`, or any UI module

#### Scenario: Boundary enforcement

- **WHEN** `lint-imports` runs in CI
- **THEN** any module under `cerebro.schema`, `cerebro.storage`,
  `cerebro.api`, or `cerebro.agent` that imports `lightgbm` fails the
  import-linter contract

### Requirement: LightGBM binary extraction

The system SHALL provide `cerebro.extractors.lightgbm.LGBExtractor`, an
`Extractor` implementation that produces a `CerebroArtifact` from a
LightGBM Booster model file when the objective is `binary`. The extractor
SHALL build the artifact from `Booster.dump_model()` and
`Booster.feature_importance(...)`, never from the live model object after
return.

#### Scenario: Extracting a binary model

- **WHEN** `LGBExtractor().extract(<path-to-binary-booster>)` runs
- **THEN** it returns a `CerebroArtifact` with `model.objective == "binary"`,
  a non-empty `trees` list whose length matches the booster's actual
  iteration count, and `importance.gain` keyed by every feature name

#### Scenario: Unsupported objective fails loudly

- **WHEN** the extractor is asked to extract a non-binary booster (e.g. a
  regression model) in v1.0.0
- **THEN** it raises `UnsupportedObjectiveError`, with
  `context = {"objective": <found_value>}`, before any artifact is built

#### Scenario: Corrupt model surfaces as a domain error

- **WHEN** the extractor encounters an unreadable or malformed model file
- **THEN** the underlying `lightgbm`-raised exception is transformed via
  `raise CorruptArtifactError(...) from original`, preserving the cause
  chain and exposing the offending path in `context`
