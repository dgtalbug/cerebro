## ADDED Requirements

### Requirement: Structural diff between two artifacts
The system SHALL compute a per-section structural diff between two canonical artifacts, producing a typed CerebroDiff object with per-section change summaries.

#### Scenario: Importance delta computed
- **WHEN** two artifacts are diffed
- **THEN** the diff includes per-feature gain and split delta (new_value - old_value) for all features present in either artifact

#### Scenario: Feature schema changes detected
- **WHEN** the two artifacts have different feature_schema.names lists
- **THEN** the diff reports added features (in artifact B but not A) and removed features (in A but not B)

#### Scenario: Metric deltas computed when evaluation present
- **WHEN** both artifacts have evaluation sections with the same objective family
- **THEN** the diff reports primary metric delta (e.g., AUC delta for binary, RMSE delta for regression)

#### Scenario: Diff is directional
- **WHEN** artifacts A and B are diffed as `diff(a, b)`
- **THEN** positive deltas mean B is higher than A; negative deltas mean B is lower

### Requirement: CLI diff command
The system SHALL provide a `cerebro diff <artifact-a> <artifact-b>` command that prints a human-readable diff summary and exits 0.

#### Scenario: Human-readable output by default
- **WHEN** `cerebro diff a.cerebro.json b.cerebro.json` is run
- **THEN** a table of changed features, metric deltas, and schema changes is printed to stdout

#### Scenario: JSON output flag
- **WHEN** `cerebro diff a.cerebro.json b.cerebro.json --json` is run
- **THEN** the full CerebroDiff object is emitted as JSON to stdout

### Requirement: Diff view in dashboard
The system SHALL provide a two-pane diff view in the dashboard at `/artifacts/:id/diff/:compareId`.

#### Scenario: Side-by-side importance comparison
- **WHEN** the diff view is loaded with two valid artifact IDs
- **THEN** feature importances for both artifacts are shown side by side with delta indicators (up/down/unchanged)

#### Scenario: Changed features highlighted
- **WHEN** a feature's gain changed by more than 5% relative
- **THEN** it is visually highlighted in the diff view

#### Scenario: Missing section handled
- **WHEN** one artifact lacks an evaluation section and the other has it
- **THEN** the diff view shows "not present in A" for the absent section without erroring
