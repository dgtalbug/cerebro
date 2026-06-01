## MODIFIED Requirements

### Requirement: DuckDB-backed table loading

The system SHALL provide a `data/loader.py` module that loads tabular data
from CSV, Parquet, or JSON files using DuckDB. The loader SHALL auto-detect
the file format by extension. The loader SHALL NOT import pandas. The loader
SHALL operate in read-only mode; it MUST NOT modify the source file.

The `labels` and `eval_labels` upload fields SHALL accept CSV, Parquet, and JSON
in addition to CSV, identical to `samples`, `eval_samples`, and `training_table`.
The API endpoints `POST /artifacts/ingest` and `PATCH /artifacts/{id}/enrich`
MUST parse labels files using the same DuckDB-based `_to_ndarray` path
regardless of extension.

#### Scenario: Load CSV file

- **WHEN** `load_table(path)` is called with a `.csv` file path
- **THEN** the function returns a DuckDB relation representing the table rows

#### Scenario: Load Parquet file

- **WHEN** `load_table(path)` is called with a `.parquet` file path
- **THEN** the function returns a DuckDB relation without error

#### Scenario: Load JSON file records-oriented

- **WHEN** `load_table(path)` is called with a `.json` file in records format
- **THEN** the function returns a DuckDB relation with one row per JSON object

#### Scenario: Load JSON file columnar

- **WHEN** `load_table(path)` is called with a `.json` file in columnar format
- **THEN** the loader auto-detects the columnar shape and returns a relation equivalent to the records form

#### Scenario: Unsupported extension

- **WHEN** `load_table(path)` is called with an unsupported extension
- **THEN** the function raises `UnsupportedFormatError` with the extension in the message

#### Scenario: Labels supplied as Parquet via ingest endpoint

- **WHEN** `POST /artifacts/ingest` receives a `.parquet` labels file
- **THEN** the file is parsed by `_to_ndarray` and produces a 1-D numpy array of label values

#### Scenario: Eval labels supplied as JSON via enrich endpoint

- **WHEN** `PATCH /artifacts/{id}/enrich` receives a `.json` eval_labels file
- **THEN** the file is parsed by `_to_ndarray` and produces a 1-D numpy array of label values
