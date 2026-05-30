# Distribution Specification (Delta)

## ADDED Requirements

### Requirement: `cerebro doctor` CLI Command
The CLI SHALL provide a `doctor` command that reports dashboard readiness for a
model file without writing any artifact.

#### Scenario: Doctor invoked on a model
- **WHEN** `cerebro doctor <model>` is run
- **THEN** a per-tab readiness report and the model's feature contract are
  printed
- **AND** no artifact file is written

#### Scenario: Doctor with JSON flag
- **WHEN** `cerebro doctor <model> --json` is run
- **THEN** a machine-readable readiness object is written to stdout

### Requirement: `extract --synthetic` Flag
The CLI `extract` command SHALL accept a `--synthetic` flag that fills
data-dependent explanation sections from model-only synthetic inputs when real
data is not supplied.

#### Scenario: Extract with synthetic and no data
- **WHEN** `cerebro extract <model> -o <out> --synthetic` is run with no data
  options
- **THEN** the artifact includes approximate SHAP, PDP, and a feature-range
  pseudo-profile marked as synthetic provenance
- **AND** permutation importance and evaluation metrics remain empty

#### Scenario: Extract with synthetic and real samples
- **WHEN** `--synthetic` is combined with `--samples`/`--labels`
- **THEN** the real data is used for explanations
- **AND** synthetic generation is skipped for sections the real data populates
