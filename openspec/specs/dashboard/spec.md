# Dashboard

## Purpose

A single-page React application that lets a user explore any compliant
`CerebroArtifact` visually. It is a pure consumer: it talks only to the REST API
and reads the canonical artifact — it never loads a model and never imports
LightGBM. It renders the views defined in the locked design mockup, ships light
and dark themes from day one, and keeps navigable state in the URL so every view
is deep-linkable.

### Source references

Future changes to this capability MUST reconcile against:

- `.docs/cerebro-open-spec.md` Part III (Frontend Architecture, all sections)
- `.docs/cerebro-open-spec.md` Part VI §3.1 (features F1.13–F1.22) and §3.3
  (acceptance: all views render, both themes production-ready)
- `.docs/FRONTEND.md` (authoritative source for Part III)
- `.docs/cerebro-dashboard.html` (Appendix A — the locked visual mockup and
  design tokens)
- API contract: [[distribution]] and Part II §6 / live `/openapi.json`

## Requirements

### Requirement: Core artifact views

The dashboard SHALL render the seven core views against any compliant artifact:
Overview, Trees, Importance, Explanations, Evaluation, Agent, and Schema/JSON.

#### Scenario: Rendering against a committed example artifact

- **WHEN** the dashboard loads an example artifact for any supported variant
- **THEN** each of the seven views renders without error, showing data drawn
  from that artifact

#### Scenario: Overview surfaces top-line model facts

- **WHEN** the Overview view is shown
- **THEN** it displays objective, tree count, feature count, top-line metrics,
  training params, and the feature schema

#### Scenario: Trees view renders interactive topology

- **WHEN** the Trees view is shown
- **THEN** it renders tree topology via react-d3-tree with a tree selector,
  depth filter, and highlight modes, loading one tree at a time

### Requirement: Conditional Data view

The dashboard SHALL render a Data view (distributions, missingness profile,
correlation matrix, type verification) only when the artifact contains a
`data_profile` section.

#### Scenario: Training table was provided

- **WHEN** the artifact includes a `data_profile`
- **THEN** the Data view is available and renders the profile charts

#### Scenario: No data profile present

- **WHEN** the artifact has no `data_profile`
- **THEN** the Data view is hidden or disabled rather than rendering empty
  charts

### Requirement: Objective-aware evaluation panels

The Evaluation view SHALL dispatch on the artifact's objective and render the
matching panel: binary, multiclass, regression, or ranking.

#### Scenario: Binary classifier evaluation

- **WHEN** the artifact objective is binary
- **THEN** the Evaluation view shows ROC and confusion-matrix panels

#### Scenario: Regression evaluation

- **WHEN** the artifact objective is regression
- **THEN** the Evaluation view shows residuals histogram, predicted-vs-actual
  scatter, and prediction intervals

### Requirement: API-only data access through hooks

No view component SHALL call `fetch` directly. All server interaction SHALL go
through TanStack Query hooks, and the dashboard SHALL never access a model
directly — only the canonical artifact via the REST API.

#### Scenario: A view needs artifact data

- **WHEN** a view renders and needs data
- **THEN** it obtains it through a query hook (e.g. `useArtifact`, `useTree`),
  keeping loading/error/refetch behavior consistent and views testable with
  mocked hooks

### Requirement: Theme system

The dashboard SHALL ship both light and dark themes, detect the system
preference on first load, persist the user's choice to localStorage, and theme
all charts through the same tokens with no hardcoded colors.

#### Scenario: First load with no stored preference

- **WHEN** a user opens the dashboard for the first time
- **THEN** the theme follows `prefers-color-scheme`

#### Scenario: Toggling and revisiting

- **WHEN** a user toggles the theme and later returns
- **THEN** the chosen theme is restored from localStorage, and charts re-render
  in the active theme's tokens

### Requirement: Deep-linkable URL state

The dashboard SHALL keep navigable concepts — selected artifact, tree, and
sample, and the active view — in the URL, not in React-only state, so every
view is deep-linkable.

#### Scenario: Sharing a link to a specific tree

- **WHEN** a user copies the URL while viewing
  `/artifacts/:id/trees/:treeIndex`
- **THEN** opening that URL elsewhere restores the same artifact, view, and
  selected tree

### Requirement: Performance via pagination and lazy loading

The dashboard SHALL avoid loading all trees at once, code-split views, and
lazy-load heavy chart libraries.

#### Scenario: Browsing a model with many trees

- **WHEN** the Trees view is opened for a model with many trees
- **THEN** tree summaries are fetched paginated and a full tree is fetched only
  when selected, rather than requesting every tree up front
