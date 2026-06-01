## ADDED Requirements

### Requirement: Delete artifact by ID

The system SHALL expose `DELETE /artifacts/{artifact_id}` to permanently remove
a registered artifact. The endpoint MUST delete the `.cerebro.json` file from
disk, the `artifacts` row, the corresponding `model_versions` row, and all
associated `tags` rows. If the deleted artifact was the model's only remaining
version, the `models` row MUST also be deleted in the same transaction. The
operation SHALL be logged with `artifact_id`, `model_id`, and `freed_bytes`.

#### Scenario: Delete existing artifact

- **WHEN** `DELETE /artifacts/{artifact_id}` is called with a valid ID
- **THEN** the response is 204 No Content
- **AND** the `.cerebro.json` file no longer exists on disk
- **AND** `GET /artifacts/{artifact_id}` subsequently returns 404
- **AND** the model version is no longer listed under the model

#### Scenario: Delete last version cascades to model

- **WHEN** `DELETE /artifacts/{artifact_id}` is called and no other versions exist for the model
- **THEN** the model entry is also removed from the registry
- **AND** `GET /models` no longer lists that model

#### Scenario: Delete non-existent artifact

- **WHEN** `DELETE /artifacts/{artifact_id}` is called with an unknown ID
- **THEN** the response is 404 Not Found with a JSON detail message

#### Scenario: Registry cleanup on disk deletion failure

- **WHEN** the `.cerebro.json` file cannot be deleted (permissions, missing)
- **THEN** the endpoint returns 500 Internal Server Error
- **AND** the registry rows are NOT deleted (abort on disk failure)

### Requirement: Registry delete_artifact method

The `Registry` class SHALL provide a `delete_artifact(artifact_id: str) -> dict`
method that performs the deletion in a single SQLite transaction. It MUST return
a dict containing `model_id`, `artifact_path`, and `freed_bytes` so the caller
can delete the file and emit a structured log entry. If the artifact ID does not
exist, it MUST raise `ArtifactNotFoundError`.

#### Scenario: Successful registry deletion

- **WHEN** `registry.delete_artifact(artifact_id)` is called with a valid ID
- **THEN** the method returns a dict with `model_id`, `artifact_path`, `freed_bytes`
- **AND** the artifact, version, and tag rows are removed from the database

#### Scenario: Artifact not found in registry

- **WHEN** `registry.delete_artifact(artifact_id)` is called with an unknown ID
- **THEN** `ArtifactNotFoundError` is raised

### Requirement: Frontend delete action on artifact list

The artifact list view SHALL display a delete button for each artifact version.
Activating the delete MUST show a confirmation prompt. If the artifact is the
only version of its model, the confirmation MUST warn the user that the model
entry will also be removed. On confirmation, the client calls
`DELETE /artifacts/{artifact_id}` and refreshes the artifact list.

#### Scenario: User deletes a non-last version

- **WHEN** the user clicks delete on an artifact that has sibling versions
- **THEN** a confirmation dialog appears without a cascade warning
- **AND** on confirm, the artifact row disappears from the list

#### Scenario: User deletes the last version

- **WHEN** the user clicks delete on the sole version of a model
- **THEN** the confirmation dialog includes text indicating the model entry will also be removed
- **AND** on confirm, the model no longer appears in the artifact list

#### Scenario: Delete cancellation

- **WHEN** the user clicks delete but then cancels the confirmation
- **THEN** no API call is made and the artifact remains in the list
