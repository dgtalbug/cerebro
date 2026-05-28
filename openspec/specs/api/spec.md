# API

## Purpose

Expose canonical artifacts and their computed data through a FastAPI REST
service. The API is a pure consumption layer — it reads stored artifacts and
serves their data; it never imports LightGBM or triggers extraction. Every
route maps to a resource in the canonical artifact shape, and every response
cites its schema version.

### Source references

Future changes to this capability MUST reconcile against:

- `.docs/cerebro-open-spec.md` Part II §6 (API layer)
- `.docs/cerebro-open-spec.md` Part VI §3.2 (E1.023)
- `contracts/openapi/openapi.json` — the committed OpenAPI contract

## Requirements

### Requirement: Canonical artifact endpoint

The system SHALL expose `GET /artifacts/{id}` returning the full
`CerebroArtifact` payload for the requested identifier.

#### Scenario: Existing artifact returns 200

- **WHEN** `GET /artifacts/{id}` is called for an artifact that exists in
  storage
- **THEN** HTTP 200 is returned with the full canonical artifact serialised
  as JSON

#### Scenario: Missing artifact returns 404

- **WHEN** `GET /artifacts/{id}` is called for an identifier that does not
  exist
- **THEN** HTTP 404 is returned with an RFC-7807 problem body

### Requirement: Importance sub-resource endpoint

The system SHALL expose `GET /artifacts/{id}/importance?type=gain|split|permutation`
as a sub-resource endpoint that returns typed importance data from a stored
artifact. The `type` query parameter SHALL be required and validated; invalid
values SHALL return HTTP 422. When permutation importance was not computed at
extraction time, `?type=permutation` SHALL return HTTP 200 with an empty
`features` list and a `detail` message — not HTTP 404.

#### Scenario: Gain and split always available

- **WHEN** `GET /artifacts/{id}/importance?type=gain` is called for an
  existing artifact
- **THEN** HTTP 200 is returned with a features list sorted by value
  descending, each feature having `name`, `value`, and `rank_gain` fields

#### Scenario: Permutation absent returns 200 empty

- **WHEN** `GET /artifacts/{id}/importance?type=permutation` is called and
  no permutation data was computed
- **THEN** HTTP 200 is returned with `features: []` and a `detail` string
  explaining that no evaluation samples were provided at extraction time

#### Scenario: Invalid type returns 422

- **WHEN** `GET /artifacts/{id}/importance?type=gini` is called
- **THEN** HTTP 422 is returned with a body indicating the valid type values

#### Scenario: Missing artifact returns 404

- **WHEN** `GET /artifacts/nonexistent/importance?type=gain` is called
- **THEN** HTTP 404 is returned with an RFC-7807 problem body

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
