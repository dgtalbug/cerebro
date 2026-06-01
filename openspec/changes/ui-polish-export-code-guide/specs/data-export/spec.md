## ADDED Requirements

### Requirement: User can export tabular data as CSV
The system SHALL provide a CSV export action on every view that presents tabular or list data (Artifacts, Evaluation metrics, Feature Importance, Explanations, Data statistics). The export SHALL produce a valid RFC 4180 CSV file containing all visible rows and column headers. The export SHALL be triggered client-side with no API call required.

#### Scenario: Export artifact list as CSV
- **WHEN** user clicks the Export dropdown on the Artifacts view and selects "CSV"
- **THEN** the browser downloads a file named `artifacts.csv` containing one row per artifact with columns: id, name, framework, objective, extracted_at, tags

#### Scenario: Export evaluation metrics as CSV
- **WHEN** user clicks the Export dropdown on the Evaluation view and selects "CSV"
- **THEN** the browser downloads a file named `evaluation-<artifact-id>.csv` containing all displayed metric rows (metric name, value)

#### Scenario: Export feature importance as CSV
- **WHEN** user clicks the Export dropdown on the Importance view and selects "CSV"
- **THEN** the browser downloads a file named `importance-<artifact-id>.csv` containing feature name and importance value columns

#### Scenario: Empty table export
- **WHEN** user triggers CSV export on a view with no rows
- **THEN** the downloaded file contains only the header row and a toast notification informs the user that no data rows were exported

### Requirement: User can export a view panel as PDF
The system SHALL provide a PDF export action on views that present evaluation panels. The PDF SHALL capture the full panel content as a rendered image embedded in an A4 landscape page. The export SHALL be client-side only using DOM capture.

#### Scenario: Export evaluation panel as PDF
- **WHEN** user clicks the Export dropdown on the Evaluation view and selects "PDF"
- **THEN** the browser downloads a file named `evaluation-<artifact-id>.pdf` containing a rendered capture of the metrics panel

#### Scenario: Export loading in progress
- **WHEN** user triggers PDF export and the capture is in progress
- **THEN** the Export button shows a loading spinner and is disabled until the download begins

#### Scenario: Export error
- **WHEN** PDF generation fails (e.g., canvas error)
- **THEN** a toast notification displays "Export failed — try again" and the button returns to its default state

### Requirement: Export menu is accessible and discoverable
The system SHALL present export actions through a dropdown menu anchored to an "Export" button in the view header actions area. The dropdown SHALL list available formats. The button SHALL use the standard icon from the project icon library.

#### Scenario: Export menu renders in view header
- **WHEN** user views any export-enabled view (Artifacts, Evaluation, Importance, Explanations, Data)
- **THEN** an "Export" button with a download icon is visible in the top-right view-actions area

#### Scenario: Keyboard navigation of export menu
- **WHEN** user opens the Export dropdown via keyboard (Enter/Space on focused button)
- **THEN** focus moves into the dropdown and arrow keys navigate between CSV and PDF options
