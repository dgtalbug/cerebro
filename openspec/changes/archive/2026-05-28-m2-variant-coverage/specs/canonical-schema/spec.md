## MODIFIED Requirements

### Requirement: Canonical artifact schema v1.0.0

The schema SHALL support all five LightGBM objectives and two new optional
fields (`divergence_warnings` on `Importance`, `rank_metadata` on
`CerebroArtifact`). All changes MUST be backward-compatible: existing binary
artifacts SHALL validate unchanged against the updated Pydantic models.

#### Scenario: All five objectives validate

- **WHEN** a canonical artifact with `model.objective` set to any of
  `"binary"`, `"multiclass"`, `"regression"`, `"lambdarank"`,
  or `"multi_output"` is validated
- **THEN** `CerebroArtifact.model_validate` succeeds without error

#### Scenario: Widened num_class accepts integers above 1

- **WHEN** a multiclass artifact carries `model.num_class = 3`
- **THEN** validation succeeds; the previous `Literal[1]` constraint is
  replaced by `int`

#### Scenario: Optional divergence_warnings field

- **WHEN** an artifact's `importance` section omits `divergence_warnings`
  or sets it to null
- **THEN** validation succeeds; existing binary artifacts without the field
  are backward-compatible

#### Scenario: Optional rank_metadata field

- **WHEN** a non-ranker artifact omits `rank_metadata` or sets it to null
- **THEN** validation succeeds; the field defaults to null and does not
  break existing artifacts
