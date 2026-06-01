## 1. Dependencies & Tooling

- [x] 1.1 Add `lucide-react` to `ui/package.json` dependencies and run `pnpm install`
- [x] 1.2 Install shadcn components: `pnpm dlx shadcn@latest add button badge table tabs dialog tooltip dropdown-menu separator skeleton sonner`
- [x] 1.3 Add `jspdf` and `html2canvas` to `ui/package.json` dependencies and run `pnpm install`
- [x] 1.4 Add `shiki` to `ui/package.json` dependencies and run `pnpm install`

## 2. Design Tokens

- [x] 2.1 Add `--interactive: #7B9FFF` and `--interactive-dim: rgba(123, 159, 255, 0.15)` to the dark theme block in `ui/src/styles/tokens.css`
- [x] 2.2 Update `.btn.primary` in `globals.css` to use `var(--interactive)` instead of `var(--accent)` for background and border
- [x] 2.3 Add a global `focus-visible` outline rule in `globals.css` using `var(--interactive)` for keyboard focus rings

## 3. Icon Migration

- [x] 3.1 Audit all inline SVG literals across `src/views/` and `src/components/` — list every icon name and usage location
- [x] 3.2 Replace inline SVGs in layout components (`src/components/layout/`, topbar, sidebar nav items) with lucide-react equivalents
- [x] 3.3 Replace inline SVGs in `Ingest.tsx` (upload icon, check icon)
- [x] 3.4 Replace inline SVGs in `Artifacts.tsx` (delete icon, tag icon, navigate icon)
- [x] 3.5 Replace inline SVGs in all remaining view files (`Data.tsx`, `Evaluation.tsx`, `Importance.tsx`, `Explanations.tsx`, `Registry.tsx`, `Readiness.tsx`)
- [x] 3.6 Remove any remaining `<svg>` literals used as icons (non-data-visualization) from the codebase

## 4. shadcn Component Adoption

- [x] 4.1 Refactor `ArtifactCard` delete confirmation from inline conditional rendering to shadcn `Dialog`
- [x] 4.2 Replace raw `.btn` / `.icon-btn` HTML button elements in `Artifacts.tsx` and `Ingest.tsx` with shadcn `Button`
- [x] 4.3 Replace `.badge` spans in `Overview.tsx` and `ModelDetail.tsx` with shadcn `Badge`
- [x] 4.4 Replace `.panel-tabs` and `.sample-tab` patterns with shadcn `Tabs` in `Evaluation.tsx` and `Explanations.tsx`
- [x] 4.5 Add loading skeleton states to `Overview.tsx`, `Evaluation.tsx`, `Importance.tsx` using shadcn `Skeleton` (replace plain text loading states)
- [x] 4.6 Mount `<Toaster>` (sonner) in `App.tsx` root and fire toast on: ingest success, ingest error, artifact delete success, artifact delete error

## 5. Data Export — CSV

- [x] 5.1 Create `src/lib/export/csv.ts` — pure utility `exportCsv(rows, filename)` with no external dependencies
- [x] 5.2 Create `src/components/ui/ExportMenu.tsx` — shadcn `DropdownMenu`-based component accepting `onCsv` and `onPdf` callbacks; shows loading state during async exports
- [x] 5.3 Wire `ExportMenu` into `Artifacts.tsx` — CSV exports artifact list rows
- [x] 5.4 Wire `ExportMenu` into `Importance.tsx` — CSV exports feature name + importance value rows
- [x] 5.5 Wire `ExportMenu` into `Explanations.tsx` — CSV exports SHAP feature + value rows
- [x] 5.6 Wire `ExportMenu` into `Data.tsx` — CSV exports dataset statistics rows
- [x] 5.7 Wire `ExportMenu` into `Evaluation.tsx` — CSV exports displayed metric name + value rows

## 6. Data Export — PDF

- [x] 6.1 Create `src/lib/export/pdf.ts` — lazy-imports `jspdf` and `html2canvas`, exposes `exportPanelPdf(elementRef, filename)` utility
- [x] 6.2 Wire PDF export in `ExportMenu` for `Evaluation.tsx` panels — captures the evaluation metrics panel element
- [x] 6.3 Wire PDF export in `ExportMenu` for `Importance.tsx` — captures the feature importance panel
- [x] 6.4 Fire error toast via sonner if PDF capture throws

## 7. Code Guide Page

- [x] 7.1 Create `src/lib/codegen/templates.ts` — framework-keyed template functions that accept artifact metadata and return an array of `{ step, title, language, code }` objects for XGBoost, LightGBM, sklearn, and a generic fallback
- [x] 7.2 Create `src/views/CodeGuide.tsx` — page component that reads `:id` param, calls `useArtifact()`, maps metadata through `templates.ts`, and renders a numbered step list
- [x] 7.3 Integrate `shiki` (lazy-imported) for syntax highlighting in `CodeGuide.tsx` — highlight Python and bash blocks
- [x] 7.4 Add copy-to-clipboard button (lucide `Copy` → `Check` for 1.5s) to each code block in `CodeGuide.tsx`
- [x] 7.5 Add route `/artifacts/:id/code-guide` in `App.tsx` (or wherever routes are defined)
- [x] 7.6 Add "Code Guide" nav link to the artifact sub-navigation (alongside Overview, Evaluation, Importance, etc.)
- [x] 7.7 Inject artifact `params` hyperparameter values into the "Define model params" template code block
- [x] 7.8 Inject artifact `features` list into the "Load & prepare data" template code block
- [x] 7.9 Handle loading and error states in `CodeGuide.tsx` (skeleton + error message)

## 8. Verification

- [x] 8.1 Run `pnpm run typecheck` — zero type errors
- [x] 8.2 Run `pnpm run lint` — zero lint errors
- [x] 8.3 Run `pnpm run test` — all existing tests pass
- [ ] 8.4 Manual smoke test: CSV export downloads valid file from Artifacts view
- [ ] 8.5 Manual smoke test: PDF export downloads file from Evaluation view
- [ ] 8.6 Manual smoke test: Code Guide renders correct XGBoost template with artifact params injected
- [ ] 8.7 Manual smoke test: Copy button on Code Guide copies text and shows checkmark
- [ ] 8.8 Manual smoke test: Delete confirm Dialog opens and closes correctly in ArtifactCard
