## Context

Cerebro UI is a Vite + React 18 + TypeScript + TailwindCSS v3 SPA. The design token system lives in `src/styles/tokens.css` and is already wired to shadcn's CSS variable aliases. `components.json` is configured (style: new-york, CSS vars) but no shadcn primitives have been installed. All icons are inline SVG literals hand-authored per component. There is no export functionality. The dashboard has ~14 views and a growing set of chart and data components built on `reaviz` and `react-d3-tree`.

The team uses the mockup in `docs/cerebro-dashboard.html` as the visual source of truth — token values must not drift from it.

## Goals / Non-Goals

**Goals:**
- Establish `lucide-react` as the canonical icon source and migrate all inline SVGs
- Install a curated set of shadcn/ui primitives that map cleanly onto existing CSS token variables
- Introduce a second accent color token (`--interactive`) for interactive affordances without breaking the amber brand identity
- Provide CSV and PDF export for all tabular/metric views through a single reusable `<ExportMenu>` component
- Ship a `/artifacts/:id/code-guide` view that generates training-reproduction code from existing artifact metadata — no new API surface

**Non-Goals:**
- Full design system overhaul or removing the custom CSS layer in `globals.css`
- Mobile / responsive layout work
- Backend changes or new API endpoints
- Dark/light theme changes beyond the new `--interactive` token
- Authentication, permissions, or role-based UI gating
- Chart library migration (reaviz stays)

## Decisions

### D1 — Icon library: `lucide-react` over Heroicons or Phosphor
Lucide is shadcn's default icon set. The existing hand-coded SVGs already use Lucide's exact stroke conventions (1.5px, round caps). Migration is a near-direct find-and-replace. Heroicons was considered but uses a different naming convention; Phosphor adds bundle weight for no gain.

### D2 — shadcn over Radix primitives directly
shadcn components are pre-styled against our exact CSS variable names (`--background`, `--primary`, etc., which already alias our mockup tokens). Using raw Radix would require writing all the token wiring ourselves. The new-york style variant is closer to the current bespoke aesthetic than the default style.

### D3 — `jsPDF + html2canvas` for PDF, not `@react-pdf/renderer`
`html2canvas` captures the live DOM panel as a canvas and `jsPDF` embeds it as an image — zero new React component tree required, works with any existing panel. `@react-pdf/renderer` would require a parallel React render tree for every exported layout, roughly tripling the work for a v1. The trade-off is pixel-fidelity over layout control; acceptable for a dashboard export use case.

### D4 — `shiki` for Code Guide syntax highlighting
`shiki` is tree-shakeable, produces static HTML with inline styles (no runtime CSS injection), and supports every language Cerebro needs (Python, bash). `prism-react-renderer` was considered but requires a runtime and heavier configuration. `highlight.js` lacks TypeScript types.

### D5 — Code Guide derives content from existing `useArtifact()` data
Artifact metadata already contains: `framework`, `objective`, `params` (hyperparameters), and `features`. A pure-client code generator avoids adding a backend endpoint and keeps the feature shippable without backend coordination. The trade-off is that generated code is template-based, not executable-verified — documented as a known limitation.

### D6 — `--interactive: #7B9FFF` token: dark theme only, not overriding light
The light theme's amber anchor (`#a07338`) works well as the single accent on aged-paper backgrounds. Adding periwinkle to light theme would break the archival aesthetic. The new token is defined only in `:root` / `:root[data-theme="dark"]`.

## Risks / Trade-offs

- **html2canvas fidelity** — CSS custom properties and backdrop-filter may not render perfectly in the canvas capture → Mitigation: test against the three most common panels (Evaluation metrics, Feature Importance, Artifacts list) and document known limitations in the export tooltip.
- **Bundle size** — jspdf (~250KB gz), html2canvas (~140KB gz), shiki (~varies, load per language) add weight → Mitigation: lazy-import all three via `React.lazy` / dynamic `import()` so they are not in the initial bundle.
- **shadcn component drift** — if shadcn upstream changes a component, our copy diverges → Mitigation: pin shadcn CLI version in `package.json` devDeps and document that component updates are manual.
- **Code Guide accuracy** — generated snippets are framework-templated, not tested → Mitigation: prominently label the page "Reference guide — verify before running" and link to official framework docs.

## Migration Plan

1. Install new npm deps (`lucide-react`, `jspdf`, `html2canvas`, `shiki`) and run `shadcn add` for 10 components
2. Add `--interactive` and `--interactive-dim` tokens to `tokens.css`
3. Migrate icons view-by-view (no user-visible behavior change)
4. Adopt shadcn Button/Badge/Tabs/Dialog — gate behind a `?uiV2=1` query flag initially for QA, then remove flag
5. Wire ExportMenu into each view
6. Ship CodeGuide route

Rollback: all changes are frontend-only. Reverting a commit is sufficient; no database or API migration needed.

## Open Questions

- Should the Code Guide page live as a tab within `ModelDetail.tsx` or as a standalone route? (Current proposal: standalone route `/artifacts/:id/code-guide` — easier to deep-link.)
- Should PDF export capture the full scrollable panel or just the visible viewport? (Default: full panel via `html2canvas` `scrollY` option.)
