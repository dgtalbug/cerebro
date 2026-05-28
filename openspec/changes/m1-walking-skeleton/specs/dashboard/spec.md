## ADDED Requirements

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

#### Scenario: First load with no stored preference

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
