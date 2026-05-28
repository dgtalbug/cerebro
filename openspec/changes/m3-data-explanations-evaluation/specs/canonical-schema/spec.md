## MODIFIED Requirements

### Requirement: Explanations field type
The `CerebroArtifact.explanations` field SHALL be typed as
`Explanations | None` (defaulting to `None`) in schema v1.1, where
`Explanations` contains `ShapResult`, `DecisionPath` per sample, and
`PartialDependence` profiles. In v1.0.0 the field was typed as `None` only.
v1.0.0 artifacts (where the field is absent or null) SHALL continue to
validate against the v1.1 schema.

#### Scenario: v1.0.0 artifact loads without explanations
- **WHEN** a v1.0.0 artifact JSON with no `explanations` key is loaded by the v1.1 schema
- **THEN** validation passes and `artifact.explanations` is `None`

#### Scenario: v1.1 artifact with ShapResult validates
- **WHEN** a v1.1 artifact JSON contains a valid `explanations` block with `shap_values`
- **THEN** validation passes and `artifact.explanations.shap` is a `ShapResult`

### Requirement: Evaluation field type
The `CerebroArtifact.evaluation` field SHALL be typed as
`BinaryEval | MulticlassEval | RegressionEval | RankingEval | None`
(defaulting to `None`) in schema v1.1. In v1.0.0 the field was `None` only.
v1.0.0 artifacts SHALL continue to validate.

#### Scenario: v1.0.0 artifact loads without evaluation
- **WHEN** a v1.0.0 artifact JSON with no `evaluation` key is loaded by the v1.1 schema
- **THEN** validation passes and `artifact.evaluation` is `None`

#### Scenario: v1.1 artifact with BinaryEval validates
- **WHEN** a v1.1 artifact JSON contains a valid `evaluation` block with `objective: "binary"`
- **THEN** validation passes and `artifact.evaluation` is a `BinaryEval`

## ADDED Requirements

### Requirement: data_profile optional field
The `CerebroArtifact` in schema v1.1 SHALL include an optional `data_profile`
field of type `DataProfile | None` (defaulting to `None`). Artifacts without
this field SHALL remain valid.

#### Scenario: v1.1 artifact with data_profile validates
- **WHEN** a v1.1 artifact JSON contains a valid `data_profile` block
- **THEN** validation passes and `artifact.data_profile` is a `DataProfile`

#### Scenario: v1.0.0 artifact without data_profile validates
- **WHEN** a v1.0.0 artifact JSON has no `data_profile` key
- **THEN** validation passes and `artifact.data_profile` is `None`
