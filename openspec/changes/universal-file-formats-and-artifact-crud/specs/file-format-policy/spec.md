## ADDED Requirements

### Requirement: Universal tabular format acceptance for all data upload fields

The system SHALL accept CSV (`.csv`), Parquet (`.parquet`), and JSON (`.json`)
for every tabular data upload field: `samples`, `labels`, `eval_samples`,
`eval_labels`, and `training_table`. No upload field MAY restrict tabular inputs
to CSV only. Model files are exempt — they have framework-specific formats.

#### Scenario: Upload labels as Parquet

- **WHEN** a user uploads a `.parquet` file to the labels field
- **THEN** the file is accepted and parsed correctly by the backend

#### Scenario: Upload eval_labels as JSON

- **WHEN** a user uploads a `.json` file to the eval_labels field
- **THEN** the file is accepted and parsed correctly by the backend

#### Scenario: UI accept attribute matches accepted formats

- **WHEN** a user opens the file picker for any tabular data field
- **THEN** the browser filter shows `.csv`, `.parquet`, and `.json`

### Requirement: Client-side file size limit on upload fields

Every data upload field (excluding model files) SHALL enforce a configurable
maximum file size. The default limit is 500 MB. Files exceeding the limit SHALL
be rejected immediately in the browser with an inline error message. The size
limit SHALL be displayed as a tag/badge on or near the dropzone so users know
the constraint before selecting a file.

#### Scenario: File under limit accepted

- **WHEN** a user selects a file smaller than the configured limit
- **THEN** the file is accepted and shown in the dropzone

#### Scenario: File over limit rejected

- **WHEN** a user selects or drops a file larger than the configured limit
- **THEN** the file is rejected without uploading
- **AND** an inline error message states the file size and the limit

#### Scenario: Size limit badge displayed

- **WHEN** a dropzone is rendered with a max file size configured
- **THEN** a badge or tag showing the limit (e.g., "max 500 MB") is visible on the dropzone

#### Scenario: Model file field has no size cap

- **WHEN** the model file field is rendered
- **THEN** no size-limit badge is shown and no client-side size check is applied
