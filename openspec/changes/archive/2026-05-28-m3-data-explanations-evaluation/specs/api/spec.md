## ADDED Requirements

### Requirement: Explanations endpoint
The API SHALL expose `GET /artifacts/{id}/explanations` returning the
artifact's `explanations` section as JSON. The endpoint SHALL return HTTP 404
when the artifact does not exist. The endpoint SHALL return HTTP 200 with a
`detail` message when the artifact exists but has no explanations.

#### Scenario: Artifact with explanations
- **WHEN** `GET /artifacts/{id}/explanations` is called for an artifact with SHAP data
- **THEN** returns HTTP 200 with the `ShapResult`, decision paths, and PDP profiles

#### Scenario: Artifact without explanations
- **WHEN** `GET /artifacts/{id}/explanations` is called for an artifact with `explanations: null`
- **THEN** returns HTTP 200 with `{"detail": "explanations not available", "shap": null}`

#### Scenario: Unknown artifact
- **WHEN** `GET /artifacts/{id}/explanations` is called with an unknown ID
- **THEN** returns HTTP 404

### Requirement: Evaluation endpoint
The API SHALL expose `GET /artifacts/{id}/evaluation` returning the artifact's
`evaluation` section as JSON. Absent evaluation returns HTTP 200 with a detail
message. Unknown artifact returns HTTP 404.

#### Scenario: Artifact with evaluation
- **WHEN** `GET /artifacts/{id}/evaluation` is called for an artifact with evaluation data
- **THEN** returns HTTP 200 with the typed evaluation payload

#### Scenario: Artifact without evaluation
- **WHEN** `GET /artifacts/{id}/evaluation` is called and evaluation is null
- **THEN** returns HTTP 200 with `{"detail": "evaluation not available"}`

### Requirement: Data profile endpoint
The API SHALL expose `GET /artifacts/{id}/data-profile` returning the
artifact's `data_profile` section as JSON. Absent profile returns HTTP 200
with a detail message. Unknown artifact returns HTTP 404.

#### Scenario: Artifact with data profile
- **WHEN** `GET /artifacts/{id}/data-profile` is called for an artifact with a profile
- **THEN** returns HTTP 200 with the `DataProfile` payload

#### Scenario: Artifact without data profile
- **WHEN** `GET /artifacts/{id}/data-profile` is called and profile is null
- **THEN** returns HTTP 200 with `{"detail": "data profile not available"}`
