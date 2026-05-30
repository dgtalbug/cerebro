## ADDED Requirements

### Requirement: Tag an artifact
The system SHALL allow users to add one or more string tags to a registered artifact via `POST /artifacts/{id}/tags`.

#### Scenario: Tag added successfully
- **WHEN** a POST request is made to `/artifacts/{id}/tags` with body `{"tag": "production"}`
- **THEN** the tag is persisted in the registry.tags table and the response returns 201

#### Scenario: Duplicate tag is idempotent
- **WHEN** the same tag is posted to the same artifact twice
- **THEN** the second request returns 200 (not 409) and the tag exists exactly once

### Requirement: Remove a tag
The system SHALL allow users to remove a tag from an artifact via `DELETE /artifacts/{id}/tags/{tag}`.

#### Scenario: Tag removed successfully
- **WHEN** a DELETE request is made to `/artifacts/{id}/tags/production`
- **THEN** the tag is removed from the registry and the response returns 204

#### Scenario: Removing absent tag returns 404
- **WHEN** DELETE is called for a tag that does not exist on the artifact
- **THEN** the response is 404 with a structured error body

### Requirement: Filter artifact list by tag
The system SHALL allow filtering the artifact list by tag via `GET /artifacts?tag=<tag>`.

#### Scenario: Tag filter returns matching artifacts
- **WHEN** `GET /artifacts?tag=production` is called
- **THEN** only artifacts with the "production" tag are returned

#### Scenario: Unknown tag returns empty list
- **WHEN** `GET /artifacts?tag=nonexistent` is called
- **THEN** the response is 200 with an empty `items` array

### Requirement: Tags displayed in artifact list UI
The system SHALL display tags as pills on each artifact card in the filterable artifact list view.

#### Scenario: Tags visible on artifact card
- **WHEN** the artifact list view renders an artifact that has tags
- **THEN** each tag is shown as a pill/badge on the artifact card

#### Scenario: Click-to-filter on tag pill
- **WHEN** a user clicks a tag pill in the list view
- **THEN** the list is filtered to show only artifacts with that tag, updating the URL query param
