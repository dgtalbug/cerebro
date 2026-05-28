## ADDED Requirements

### Requirement: DuckDB-backed table loading
The system SHALL provide a `data/loader.py` module that loads tabular data
from CSV, Parquet, or JSON files using DuckDB. The loader SHALL auto-detect
the file format by extension. The loader SHALL NOT import pandas. The loader
SHALL operate in read-only mode; it MUST NOT modify the source file.

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

### Requirement: Statistical profiling
The system SHALL provide a `data/profiler.py` module that computes a
`DataProfile` from a loaded table. The profiler SHALL compute for each column:
per-column value distributions (counts and bin edges for numeric; top-K
categories for categoricals), missingness rate, and inferred dtype. The
profiler SHALL compute a Pearson correlation matrix over numeric columns.
The profiler SHALL run entirely as DuckDB SQL aggregations.

#### Scenario: Profile numeric column distributions
- **WHEN** `profile_table(relation)` is called on a table with numeric columns
- **THEN** the returned `DataProfile` contains histogram bin edges and counts for each numeric column

#### Scenario: Profile categorical column top-K
- **WHEN** `profile_table(relation)` is called on a table with string columns
- **THEN** the returned `DataProfile` contains the top-10 value counts for each string column

#### Scenario: Missingness rate
- **WHEN** a column contains NULL values
- **THEN** `DataProfile.columns[col].missingness` equals `null_count / total_rows`

#### Scenario: Pearson correlation matrix
- **WHEN** the table has at least two numeric columns
- **THEN** `DataProfile.correlations` contains pairwise Pearson coefficients

#### Scenario: Empty table
- **WHEN** `profile_table(relation)` is called on a table with zero rows
- **THEN** the function returns a `DataProfile` with empty distributions and zero missingness

### Requirement: Optional data_profile in artifact schema
The artifact schema SHALL include an optional `data_profile` field in v1.1.
Artifacts without `data_profile` (all v1.0.0 artifacts) SHALL continue to
validate without modification. The `data_profile` field SHALL use the
`DataProfile` Pydantic model defined in `schemas/v1.1/`.

#### Scenario: v1.0.0 artifact validates without data_profile
- **WHEN** a v1.0.0 artifact JSON (no `data_profile` key) is loaded
- **THEN** validation passes and `artifact.data_profile` is `None`

#### Scenario: v1.1 artifact with data_profile validates
- **WHEN** a v1.1 artifact JSON with a valid `data_profile` section is loaded
- **THEN** validation passes and `artifact.data_profile` is a `DataProfile` instance
