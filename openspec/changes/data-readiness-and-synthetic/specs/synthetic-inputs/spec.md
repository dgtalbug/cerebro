# Synthetic Inputs Specification

## Purpose

Produce a model-only approximation of the data-dependent explanation artifacts
when no real data is available, by synthesizing a feature matrix from the tree
split thresholds. Implements the L4 step of the readiness ladder (see
`docs/cerebro-open-spec.md` explanations/importance sections).

## ADDED Requirements

### Requirement: Threshold-Derived Feature Matrix
The system SHALL synthesize a feature matrix in the model's exact feature order
by sampling each feature within the range of thresholds at which it is split.

#### Scenario: Feature appearing in splits
- **WHEN** a feature appears as a split feature in one or more trees
- **THEN** synthetic values for it are sampled within its observed
  threshold range (with bounded padding beyond the extremes)

#### Scenario: Feature absent from all splits
- **WHEN** a feature never appears as a split feature
- **THEN** it is held at a constant value
- **AND** it is reported as unconstrained

### Requirement: Approximate SHAP and PDP From Synthetic Data
The system SHALL compute SHAP values and partial-dependence curves from the
synthetic matrix using the existing explanation machinery.

#### Scenario: Synthetic explanations produced
- **WHEN** extraction runs in synthetic mode with no real samples
- **THEN** SHAP values and PDP curves are produced from the synthetic matrix

### Requirement: Feature-Range Pseudo-Profile
The system SHALL produce a feature-range pseudo-profile from split thresholds in
place of a real data profile when no training table is supplied.

#### Scenario: Pseudo-profile produced
- **WHEN** extraction runs in synthetic mode with no training table
- **THEN** a profile reporting per-feature threshold range and split count is
  produced

### Requirement: Approximate Provenance Marking
The system SHALL mark every synthetic-derived section with provenance indicating
it is approximate, so consumers do not present it as measured ground truth.

#### Scenario: Synthetic sections tagged
- **WHEN** a section is produced from synthetic data
- **THEN** its provenance is recorded as synthetic
- **WHEN** a section is produced from real supplied data
- **THEN** its provenance is recorded as measured

### Requirement: No Synthesis of Label-Dependent Artifacts
The system SHALL NOT synthesize labels, permutation importance, or evaluation
metrics, since these require ground truth.

#### Scenario: Label-dependent sections stay empty
- **WHEN** extraction runs in synthetic mode
- **THEN** permutation importance and evaluation metrics are left empty

### Requirement: Real Data Takes Precedence
The system SHALL prefer real supplied data over synthetic data for any section
that real data can populate.

#### Scenario: Real samples supplied alongside synthetic flag
- **WHEN** real samples are supplied and synthetic mode is also requested
- **THEN** explanations are computed from the real samples
- **AND** the synthetic generation is skipped for that section with a warning
