## Why

Cerebro's dashboard has a functional but unpolished UI: icons are hand-coded inline SVGs, no shadcn primitives are actually installed despite being configured, there is no way to export any data or metrics, and users have no in-app guidance on how to reproduce an artifact through training. These gaps make the dashboard feel incomplete and create friction for ML practitioners who need to share results or understand provenance.

## What Changes

- Replace all inline SVG literals across views and layout components with `lucide-react` icons (consistent stroke, tree-shakeable, zero maintenance)
- Install and adopt 10 shadcn/ui primitives: `button`, `badge`, `table`, `tabs`, `dialog`, `tooltip`, `dropdown-menu`, `separator`, `skeleton`, `sonner`
- Add `--interactive: #7B9FFF` design token (periwinkle blue) for CTA buttons and focus rings alongside the existing amber identity
- Polish stat tiles, ArtifactCard hover states, nav active indicators, and loading skeletons
- Add CSV export (zero-dep utility) and PDF export (`jsPDF` + `html2canvas`) to Artifacts, Evaluation, Importance, Explanations, and Data views via a shared `<ExportMenu>` dropdown
- Add a new **Code Guide** page per artifact (`/artifacts/:id/code-guide`) that auto-generates a 6-step training walkthrough from stored artifact metadata — no new backend API required

## Capabilities

### New Capabilities

- `data-export`: Ability to download table/metric data as CSV or PDF from any view that presents tabular data. Covers ExportMenu component, csv utility, pdf utility.
- `code-guide`: Per-artifact page showing step-by-step training code derived from artifact metadata (framework, hyperparams, features, objective). Includes syntax highlighting and copy-to-clipboard per block.

### Modified Capabilities

- `dashboard`: UI component system upgrades — lucide icons, shadcn primitives, new `--interactive` token, and visual polish across all views.

## Impact

- **New dependencies (frontend)**: `lucide-react`, `jspdf`, `html2canvas`, `shiki`
- **New shadcn components** (no version bump to shadcn itself): button, badge, table, tabs, dialog, tooltip, dropdown-menu, separator, skeleton, sonner
- **Files added**: `src/lib/export/csv.ts`, `src/lib/export/pdf.ts`, `src/components/ui/ExportMenu.tsx`, `src/views/CodeGuide.tsx`
- **Files modified**: `src/styles/tokens.css` (+2 tokens), `src/globals.css` (minor btn/badge refactor), all view `.tsx` files (icon swap + export mount), `src/App.tsx` (new route)
- **No backend changes** — Code Guide derives all content from existing `useArtifact()` data
- **No breaking API changes**
