## ADDED Requirements

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
