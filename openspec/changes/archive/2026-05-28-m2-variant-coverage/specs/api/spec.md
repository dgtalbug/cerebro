## ADDED Requirements

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
