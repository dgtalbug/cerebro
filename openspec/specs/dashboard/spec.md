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

### Requirement: Design tokens lifted verbatim from the mockup

The dashboard SHALL declare every color, typography, radius, and atmosphere
value as a CSS custom property under `:root[data-theme="dark"]` and
`:root[data-theme="light"]` in `ui/src/styles/tokens.css`. The values SHALL
be lifted byte-for-byte from `.docs/cerebro-dashboard.html` with no
re-derivation, no rounding, no opinion-driven adjustments. No UI component
file SHALL contain a hardcoded hex, rgb, hsl, or named color.

#### Scenario: Token completeness

- **WHEN** the dark theme is active
- **THEN** the document defines exactly the 28 tokens enumerated in the
  mockup's default `:root` block; the light theme overrides the 23 tokens
  enumerated in the mockup's `[data-theme="light"]` block; typography and
  radii are inherited from the default `:root` and not redefined under the
  light theme

#### Scenario: No hardcoded colors elsewhere

- **WHEN** the UI build runs
- **THEN** an ESLint rule (or equivalent lint pass) reports zero hardcoded
  colors outside `tokens.css`

### Requirement: Theme switching is persistent and respects system preference

The system SHALL expose a single `useTheme()` hook backed by a Zustand
store and a free `applyTheme(theme)` helper that writes the
`data-theme` attribute on `document.documentElement` and persists the
chosen theme in `localStorage["cerebro-theme"]`. On first load, the
selected theme SHALL be taken from `localStorage` if present, else from
`window.matchMedia("(prefers-color-scheme: dark)")`, falling back to
dark only if both signals are absent.

#### Scenario: First load with OS dark preference and no stored key

- **WHEN** the dashboard loads with no `localStorage["cerebro-theme"]` key
  and the OS reports a dark color scheme
- **THEN** `document.documentElement` is rendered with `data-theme="dark"`

#### Scenario: Toggle round-trips

- **WHEN** the user clicks the theme toggle
- **THEN** the document's `data-theme` flips, `localStorage["cerebro-theme"]`
  records the new value, and a subsequent reload restores the same value

### Requirement: shadcn token aliasing

The system SHALL alias the shadcn token namespace (`--background`,
`--foreground`, `--card`, `--popover`, `--primary`, `--primary-foreground`,
`--secondary`, `--muted`, `--muted-foreground`, `--accent`,
`--accent-foreground`, `--destructive`, `--border`, `--input`, `--ring`,
`--radius`) to the mockup token namespace within `tokens.css`. shadcn/ui
primitives copied into the project SHALL theme correctly from the mockup
tokens without further per-component patching.

#### Scenario: shadcn primitive renders with mockup colors

- **WHEN** a shadcn `Button` primitive is rendered with `variant="default"`
- **THEN** its background reads from `var(--accent)` and its text from
  `var(--bg)` via the shadcn `--primary` / `--primary-foreground` aliases

### Requirement: UI shell layout

The dashboard SHALL render a persistent shell containing `TopBar`,
`Sidebar`, and `ViewHeader` components in a layout that matches
`.docs/cerebro-dashboard.html`. Background atmosphere (radial glows and
SVG noise grain) SHALL render from the same `--glow-1`, `--glow-2`,
`--grain-opacity`, and `--grain-blend` tokens the mockup uses.

#### Scenario: Visual parity with the mockup

- **WHEN** the dashboard is loaded in both themes
- **THEN** the shell layout (column proportions, spacing, typography,
  grain, glow) is visually indistinguishable from the mockup at the same
  viewport size

### Requirement: Overview view consumes the artifact endpoint

The Overview view SHALL fetch the canonical artifact via a TanStack Query
hook (`useArtifact(id)`) calling `GET /artifacts/{id}`. The view SHALL
render:

- the objective stat tile
- the trees count stat tile (= `model.num_iteration`)
- the features count stat tile (= `model.feature_schema.names.length`)
- the headline-metric stat tile — for v1.0.0 this renders `—` with subtitle
  *"no samples at extraction time"*
- the training parameters panel — every key in `model.params` as a `<dl>`
  row with tabular numerals
- the feature schema panel — index, name, type (numeric / categorical
  driven by `categorical_indices`), and const column
  (mono+ / mono- / —) driven by `monotone_constraints`

#### Scenario: Rendering against the fixture artifact

- **WHEN** the route resolves with a valid artifact id
- **THEN** the four stat tiles render with the artifact-derived values, the
  training parameters panel lists every key in `model.params`, and the
  feature schema panel lists every entry in `feature_schema.names` with the
  correct type and const annotation

#### Scenario: Loading and error states

- **WHEN** the underlying query is pending or fails
- **THEN** a non-silent loading or error state renders; the UI never
  pretends to have data it does not have

### Requirement: API ↔ UI type contract

The system SHALL regenerate `ui/src/lib/api/schema.d.ts` via
`openapi-typescript` from the running API's `/openapi.json`. CI SHALL fail
if the regenerated file differs from what is committed, so a backend
schema drift cannot reach the dashboard silently.

#### Scenario: Drift fails CI

- **WHEN** the backend's OpenAPI document changes shape and the committed
  `schema.d.ts` is not updated in the same PR
- **THEN** the CI step running `pnpm api:types` followed by
  `git diff --exit-code -- src/lib/api/schema.d.ts` fails the build

### Requirement: Importance view with three-way tab toggle

The dashboard SHALL provide an Importance view at `/artifacts/:id/importance`
that renders feature importance as CSS bar charts (no charting library) with a
three-way tab toggle for gain, split, and permutation types. When divergence
warnings are present, a `DivergenceCallout` component SHALL appear identifying
the flagged features. When permutation importance was not computed, a "not
computed" state message SHALL be shown instead of an empty chart.

#### Scenario: Tab switching loads correct data type

- **WHEN** the user clicks the "split" tab
- **THEN** the component calls `useImportance(id, "split")` and re-renders
  the bar chart with split importance values

#### Scenario: Divergence callout appears with warnings

- **WHEN** the permutation response contains non-empty `divergence_warnings`
- **THEN** the `DivergenceCallout` component is rendered, naming the flagged
  features

#### Scenario: Not-computed state shown for missing permutation

- **WHEN** the permutation response returns `detail` (no evaluation samples)
- **THEN** a message containing "not computed" is rendered instead of bars

### Requirement: Trees view with lazy-loaded react-d3-tree

The dashboard SHALL provide a Trees view at `/artifacts/:id/trees` that
renders the selected tree's topology using `react-d3-tree`, imported via
`React.lazy()` so it is never included in the initial bundle. The view SHALL
include a tree selector dropdown, a depth filter, and a node inspector panel
that populates on node click.

#### Scenario: react-d3-tree not in initial bundle

- **WHEN** the app loads on a route other than `/trees`
- **THEN** the react-d3-tree chunk is not included in the initial JavaScript
  payload (verified by build output showing a separate chunk)

#### Scenario: Tree selector changes rendered tree

- **WHEN** the user selects a different tree from the dropdown
- **THEN** the tree visualisation updates to show the newly selected tree
  and the node inspector is cleared

#### Scenario: Node click populates inspector

- **WHEN** the user clicks a node in the tree visualisation
- **THEN** the node inspector panel shows the node's split feature,
  threshold, and decision type (for split nodes) or leaf value (for leaves)
