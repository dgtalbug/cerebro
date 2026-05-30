# Data Readiness Specification

## Purpose

Diagnose, from a model file alone, which dashboard tabs are satisfiable and what
inputs are missing, and surface the exact feature contract the model expects so
an engineer can supply data correctly. Implements the L1 step of the readiness
ladder (see `docs/cerebro-open-spec.md` distribution/extraction sections).

## ADDED Requirements

### Requirement: Per-Tab Readiness Report
The system SHALL produce, from a model file, a report stating for each dashboard
tab whether it is satisfiable and, when not, the specific input that is missing.

#### Scenario: Model file with no data
- **WHEN** `doctor` is run against a model file with no artifact and no data
- **THEN** Overview, Trees, and gain/split Importance are reported satisfiable
- **AND** Explanations is reported as needing a feature-sample matrix
- **AND** Evaluation is reported as needing eval samples and eval labels
- **AND** Data Profile is reported as needing a training table

#### Scenario: Existing artifact inspected
- **WHEN** `doctor` is run with `--artifact <path>` against an extracted artifact
- **THEN** tabs whose sections are already populated are reported as satisfied
- **AND** only the still-empty tabs are reported as missing their inputs

### Requirement: Feature Contract Disclosure
The system SHALL emit the exact ordered list of feature names the model expects,
so supplied sample/eval matrices can be aligned to it.

#### Scenario: Feature contract printed
- **WHEN** `doctor` runs against any supported model
- **THEN** it prints the feature names in the model's native order
- **AND** the count of features is reported

### Requirement: Label-Blocked Tabs Marked Honestly
The system SHALL distinguish tabs that require ground-truth labels (permutation
importance, evaluation) from tabs that need only feature values, and never
report label-blocked tabs as satisfiable without labels.

#### Scenario: Permutation and evaluation flagged as label-dependent
- **WHEN** `doctor` reports readiness
- **THEN** permutation importance and evaluation are flagged as requiring labels
- **AND** they are not reported as satisfiable from the model file alone

### Requirement: Scriptable Output and Exit Codes
The system SHALL provide machine-readable output and stable exit codes so the
report can be consumed by CI and the dashboard.

#### Scenario: JSON output
- **WHEN** `doctor` is run with `--json`
- **THEN** a machine-readable readiness object is written to stdout

#### Scenario: Exit code reflects readiness
- **WHEN** all tabs satisfiable from the model alone are satisfiable
- **THEN** the process exits with code 0
- **WHEN** data-dependent tabs are unmet
- **THEN** the process exits with a non-zero code
