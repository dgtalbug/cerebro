## MODIFIED Requirements

### Requirement: Dashboard uses a canonical icon library
The dashboard SHALL use `lucide-react` as the exclusive source for all UI icons. Inline SVG literals in component files SHALL NOT be used for icons. All icons SHALL use a consistent stroke width of 1.5 and inherit color from their parent element via `currentColor`.

#### Scenario: Nav icons render from lucide-react
- **WHEN** user views the sidebar navigation
- **THEN** all navigation item icons are rendered via lucide-react components (not inline SVG strings)

#### Scenario: Icon color inherits from parent
- **WHEN** a nav item is active
- **THEN** the nav icon color changes to `var(--accent)` through CSS inheritance without per-icon color props

### Requirement: Interactive affordances use the --interactive design token
The dashboard SHALL define a `--interactive: #7B9FFF` token in the dark theme block of `tokens.css`. Primary CTA buttons and keyboard focus rings SHALL use this token to distinguish interactive elements from the brand amber accent.

#### Scenario: Primary button uses --interactive token
- **WHEN** user views any view with a primary CTA button (e.g., Ingest submit)
- **THEN** the button background uses `var(--interactive)` not `var(--accent)`

#### Scenario: Focus ring uses --interactive token
- **WHEN** user navigates any focusable element via keyboard
- **THEN** the focus ring outline uses `var(--interactive)` color

### Requirement: Shared shadcn/ui primitives are used for common UI patterns
The dashboard SHALL use shadcn/ui `Button`, `Badge`, `Dialog`, `Skeleton`, and `Tabs` components for their respective UI patterns instead of custom HTML elements with manual class names. Existing CSS custom property tokens SHALL remain the source of styling — Tailwind hardcoded color classes SHALL NOT replace them.

#### Scenario: ArtifactCard delete confirm uses Dialog
- **WHEN** user clicks the delete button on an artifact card
- **THEN** a shadcn Dialog component opens to confirm the action (not inline conditional rendering)

#### Scenario: Loading states use Skeleton
- **WHEN** a view is fetching data from the API
- **THEN** shadcn Skeleton components render as placeholder shapes matching the expected content layout

#### Scenario: Toast notifications use Sonner
- **WHEN** an ingest, delete, or export action completes or fails
- **THEN** a shadcn Sonner toast notification appears at the bottom-right of the screen with the action result
