# UI Fidelity Gap Report — M0–M3

Audit date: 2026-05-29  
HTML source of truth: `.docs/cerebro-dashboard.html`  
React implementation: `ui/src/`  
Scope: Overview, Data, Trees, Importance, Explanations, Evaluation, shell (TopBar, Sidebar, ViewHeader).  
Out of scope (M4): Agent view, Schema/JSON view. Both are present in the HTML but disabled (`disabled` props) in React — correct placeholder state, no gaps to report.

---

## Summary

| Severity | Count |
|----------|-------|
| Blocker  | 1     |
| Major    | 11    |
| Minor    | 6     |
| Cosmetic | 2     |
| **Total** | **20** |

| Category | Count |
|----------|-------|
| token    | 7 (all hardcoded color violations) |
| layout   | 3 |
| spacing  | 1 |
| typography | 1 |
| color    | 2 |
| component | 5 |
| state    | 1 |

### Fix these first (root causes that each close multiple gaps)

1. **Add missing CSS classes to `globals.css`** — closes the blocker and all panel/stat/kv/fi-row structural gaps.
2. **Replace `COPPER`, `MUTED_RED`, `"#1a2a40"` hardcodes** — closes all token category gaps.
3. **Fix tab toggle styles** (Importance + Explanations) — closes two major component gaps.

---

## Gap Table

### G-001 — Missing component CSS classes in `globals.css`

| Field | Value |
|-------|-------|
| Severity | **blocker** |
| Category | component |
| Views | Overview, Importance, Explanations, Evaluation, Data |
| HTML ref | `.docs/cerebro-dashboard.html` lines 412–648 (`.panel`, `.grid-*`, `.stat`, `.kv`, `.fi-*`) |
| React file | `ui/src/globals.css` — entire file (377 lines) |

`globals.css` (377 lines) contains only the shell-layer CSS (app grid, topbar, sidebar, main, view-header). The HTML mockup's `<style>` block also defines all component CSS:
- `.panel`, `.panel-header`, `.panel-title`, `.panel-subtitle`, `.panel-tabs`, `.panel-tab`
- `.grid`, `.grid-2`, `.grid-3`, `.grid-4`
- `.stat`, `.stat-label`, `.stat-value`, `.stat-meta`, `.stat-meta .up/.down`
- `.kv`, `.kv dt`, `.kv dd`
- `.fi-list`, `.fi-row`, `.fi-name`, `.fi-bar-wrap`, `.fi-bar`, `.fi-value`
- `.tree-controls`, `.tree-viz`
- `.shap-row`, `.shap-name`, `.shap-bar-wrap`, `.shap-bar.pos/.neg`, `.shap-val`
- `.sample-tabs`, `.sample-tab`
- `.cm`, `.cm-cell`, `.cm-cell.tp/.tn/.fp/.fn`, `.cm-axis-x/.y`
- `.pdp-grid`, `.pdp-tile`
- Scrollbar overrides (`::-webkit-scrollbar*`)
- Mobile fallback (`@media (max-width: 1024px)`)

None of these are present in `globals.css`. Every React component that uses `className="panel"` etc. renders as an unstyled div.

**Fix:** Port all missing CSS blocks verbatim from the HTML `<style>` block to `globals.css`.

---

### G-002 — `COPPER` hardcoded hex in Explanations, Data, BinaryPanel

| Field | Value |
|-------|-------|
| Severity | **major** |
| Category | token |
| Views | Explanations, Data, Evaluation (binary) |
| HTML ref | N/A (HTML uses `var(--accent)` / `var(--accent-dim)` for path highlighting) |
| React files | `ui/src/views/Explanations.tsx:13`, `ui/src/views/Data.tsx:8`, `ui/src/views/evaluation/BinaryPanel.tsx:6` |

`COPPER = "#b87333"` does not match any token. The equivalent in the token system is `var(--accent)` (dark: `#d4a574`, light: `#a07338`). Decision path feature highlighting in the HTML uses accent-family tokens (`var(--accent-dim)` for borders, `var(--accent)` for text).

**Fix:** Remove the `COPPER` constant in each file and use `"var(--accent)"` inline or `getComputedStyle(document.documentElement).getPropertyValue("--accent")` where a JS string is required (Reaviz `colorScheme`).

---

### G-003 — `MUTED_RED` hardcoded hex for negative SHAP direction

| Field | Value |
|-------|-------|
| Severity | **major** |
| Category | token |
| View | Explanations |
| HTML ref | `.docs/cerebro-dashboard.html` line 961: `.shap-bar.neg { background: var(--blue) }` |
| React file | `ui/src/views/Explanations.tsx:15`, line 64, line 73 |

HTML uses `var(--blue)` for negative SHAP bars and `var(--blue)` for negative value text. React uses `MUTED_RED = "#c0392b"` — wrong color family AND a hardcoded hex.

**Fix:** Replace `MUTED_RED` with `"var(--blue)"`. Update both bar background and value text references.

---

### G-004 — Heatmap colorScheme uses hardcoded `"#1a2a40"`

| Field | Value |
|-------|-------|
| Severity | **major** |
| Category | token |
| Views | Evaluation (binary confusion matrix), Data (correlation matrix) |
| HTML ref | N/A (Reaviz is the locked alternative to SVG, but colors must still use tokens) |
| React files | `ui/src/views/evaluation/BinaryPanel.tsx:73`, `ui/src/views/Data.tsx:102` |

`colorScheme={["#1a2a40", COPPER]}` uses a non-token dark blue as the low-end color. `#1a2a40` is close to `--bg-elev-2` (`#161b27`) but does not match any token.

**Fix:** Create a `useTokenColors()` helper that reads CSS variables from `document.documentElement` and expose the two-stop array as `[cssVar("--bg-elev"), cssVar("--accent")]`. Pass this to Reaviz `colorScheme`. Re-evaluate on theme change via Zustand store subscription.

---

### G-005 — `DivergenceCallout` color uses unnecessary fallback hex

| Field | Value |
|-------|-------|
| Severity | minor |
| Category | token |
| View | Importance |
| HTML ref | `.docs/cerebro-dashboard.html` line 1401 (inline red border callout) |
| React file | `ui/src/components/importance/DivergenceCallout.tsx:19,26` |

`var(--red, #c0392b)` — the fallback hex is unnecessary since `--red` is always defined by `tokens.css`. It also disagrees with the actual token value (`--red: #c95a5a` dark / `--red: #a23030` light).

**Fix:** Remove the fallback: `var(--red)`.

---

### G-006 — Importance tab toggle: wrong style (pill vs segmented control)

| Field | Value |
|-------|-------|
| Severity | **major** |
| Category | component |
| View | Importance |
| HTML ref | `.docs/cerebro-dashboard.html` lines 448–472 (`.panel-tabs`, `.panel-tab`, `.panel-tab.active`) |
| React file | `ui/src/views/Importance.tsx:258–280` |

HTML style — `.panel-tabs` container:
```css
background: var(--bg); border: 1px solid var(--border);
border-radius: var(--radius); padding: 3px; gap: 4px;
```
HTML style — `.panel-tab.active`:
```css
background: var(--bg-elev-2); color: var(--accent); border-radius: 3px;
```

React style — each tab button:
```
border-radius: 100px (pill); active: background var(--accent), color var(--bg)
```

The pill shape with filled accent background is the inverse of the mockup's intent (accent text, elevated-2 background). The container chrome (outer border + padding) is entirely missing.

**Fix:** Replace the tab `<div>` with `className="panel-tabs"` and each button with `className={\`panel-tab \${active ? "active" : ""}\`}`. Remove all inline tab styles once G-001 (CSS classes) is fixed.

---

### G-007 — Explanations sample tabs: wrong style (pill vs underline)

| Field | Value |
|-------|-------|
| Severity | **major** |
| Category | component |
| View | Explanations |
| HTML ref | `.docs/cerebro-dashboard.html` lines 901–922 (`.sample-tabs`, `.sample-tab`, `.sample-tab.active`) |
| React file | `ui/src/views/Explanations.tsx:206–219` |

HTML style — `.sample-tab.active`:
```css
color: var(--accent); border-bottom-color: var(--accent); border-bottom: 1px solid accent;
```
(Underline tab on a bottom-bordered container, `margin-bottom: -1px` to merge into the line below.)

React style — pill buttons with filled background when active. Different shape entirely.

**Fix:** Replace tab markup with `className="sample-tabs"` wrapper and `className={\`sample-tab \${tab === t ? "active" : ""}\`}` buttons. Remove inline styles.

---

### G-008 — SHAP bars: wrong height, wrong negative color, missing centerline

| Field | Value |
|-------|-------|
| Severity | **major** |
| Category | component |
| View | Explanations |
| HTML ref | `.docs/cerebro-dashboard.html` lines 924–970 (`.shap-row`, `.shap-bar-wrap`, `.shap-bar.pos/.neg`) |
| React file | `ui/src/views/Explanations.tsx:66–77` |

Differences vs HTML:

| Property | HTML | React |
|----------|------|-------|
| Bar height | `6px` | `4px` |
| Negative bar color | `var(--blue)` | `MUTED_RED = "#c0392b"` |
| Centerline | `::before` pseudo on wrap (1px `var(--border-strong)` vertical) | absent |
| Bidirectional layout | `.pos { margin-left: 50% }` / `.neg { margin-right: 50%; margin-left: auto }` | `float: left/right` |
| Bar track background | No explicit track (transparent) | `var(--bg-elev)` |

**Fix:** Use `className="shap-bar-wrap"` and `className={\`shap-bar \${pos ? "pos" : "neg"}\`}` once G-001 CSS is in place. Remove inline height/color/float styles.

---

### G-009 — Importance bar: wrong height, missing gradient and glow

| Field | Value |
|-------|-------|
| Severity | **major** |
| Category | component |
| View | Importance |
| HTML ref | `.docs/cerebro-dashboard.html` lines 544–600 (`.fi-bar-wrap`, `.fi-bar`, `.fi-bar::after`) |
| React file | `ui/src/views/Importance.tsx:30–45` (FeatureBar inner bar div) |

| Property | HTML | React |
|----------|------|-------|
| Bar height | `8px` | `4px` |
| Bar gradient | `linear-gradient(90deg, var(--accent-dim), var(--accent))` | solid `var(--accent)` |
| Bar track border | `1px solid var(--border)` | none |
| Bar glow tip | `::after` — 1px `var(--accent-bright)`, `box-shadow 0 0 6px var(--accent)` | none |
| Name column width | `140px` fixed | `1fr` (flexible) |
| Value column width | `60px` | `120px` |

Also: the overall `.fi-row` is `grid-template-columns: 140px 1fr 60px` but React FeatureBar uses `1fr 120px` with the bar embedded inside the left column — structurally different.

**Fix:** Use `className="fi-list"` on the container and `className="fi-row"` on each row with `className="fi-name"`, `className="fi-bar-wrap"` > `className="fi-bar"`, `className="fi-value"` once G-001 CSS is in place. Remove FeatureBar inline styles.

---

### G-010 — TreeControls: box style replaced with border-bottom divider

| Field | Value |
|-------|-------|
| Severity | **major** |
| Category | layout |
| View | Trees |
| HTML ref | `.docs/cerebro-dashboard.html` lines 602–636 (`.tree-controls`) |
| React file | `ui/src/components/trees/TreeControls.tsx:35–45` |

HTML `.tree-controls`:
```css
background: var(--bg-elev-2); border: 1px solid var(--border);
border-radius: var(--radius); padding: 12px; flex-wrap: wrap;
```

React inline style:
```
borderBottom: "1px solid var(--border)"; padding: "10px 0 14px"; no background; no outer border
```

The visual treatment is completely different — a contained box vs a plain horizontal rule.

Also missing: the "Highlight" `<select>` (third dropdown in HTML). React has Tree and Depth only.

**Fix:** Use `className="tree-controls"` once G-001 CSS is in place. Add the Highlight selector (Leaf value / Sample count / Gain).

---

### G-011 — Evaluation confusion matrix: Reaviz Heatmap vs per-cell color coding

| Field | Value |
|-------|-------|
| Severity | **major** |
| Category | component |
| View | Evaluation |
| HTML ref | `.docs/cerebro-dashboard.html` lines 649–703 (`.cm`, `.cm-cell.tp/.tn/.fp/.fn`) |
| React file | `ui/src/views/evaluation/BinaryPanel.tsx:63–75` |

HTML uses a hand-rolled `<div class="cm">` grid with per-cell semantic classes:
- `.cm-cell.tp` → `rgba(127,176,105, 0.22)` background, `rgba(127,176,105, 0.4)` border (green)
- `.cm-cell.tn` → lighter green
- `.cm-cell.fp` → `rgba(201,90,90, 0.10)` background (light red)
- `.cm-cell.fn` → slightly darker red

React uses a `Heatmap` with a continuous gradient `["#1a2a40", COPPER]`, losing the semantic TP/TN/FP/FN color distinction entirely.

**Fix:** Replace the Reaviz `Heatmap` with the `.cm` CSS grid + `.cm-cell.tp/.tn/.fp/.fn` class pattern from the HTML. Once G-001 CSS is in place, the colors come from the CSS class definitions verbatim.

---

### G-012 — Evaluation view missing objective tab bar

| Field | Value |
|-------|-------|
| Severity | **major** |
| Category | layout |
| View | Evaluation |
| HTML ref | `.docs/cerebro-dashboard.html` lines 1579–1589 (objective tabs switcher) |
| React file | `ui/src/views/Evaluation.tsx:61–100` |

The HTML mockup shows an objective switcher tab bar at the top of the Evaluation view ("binary / multiclass / regression / ranking") that lets users see all four panel layouts regardless of the artifact's objective. React renders only the panel matching `data.objective` — no switcher tab.

This is partially intentional (artifact-driven, no mock data), but the switcher is part of the visual design and its chrome (the `.panel-tabs` container + objective label + "artifact objective: binary" hint) should be rendered even when only one panel is active.

**Fix:** Render the objective switcher in read-only mode — tabs present but the inactive ones are `disabled` / `opacity-40`. Show "artifact objective: `{evalData.objective}`" hint.

---

### G-013 — TopBar missing model context badges

| Field | Value |
|-------|-------|
| Severity | **major** |
| Category | component |
| View | Shell (TopBar) |
| HTML ref | `.docs/cerebro-dashboard.html` lines 1049–1059 (framework badge, "artifact valid" badge, schema version badge) |
| React file | `ui/src/components/layout/TopBar.tsx:14–17` |

HTML model-bar contains three badges after the model name/hash:
1. `.badge.framework` — accent-colored with `badge-dot` in accent color, shows "lightgbm 4.1.0"
2. `.badge` — green `badge-dot`, "artifact valid"
3. `.badge` — "schema v1.0.0"

React model-bar shows only `—` for both model name and hash, no badges.

**Fix:** Pass artifact data to TopBar through shared context (Zustand store or React context). Render the three badges when artifact is loaded. The framework badge color difference is intentional: use `className="badge framework"` for the framework badge.

---

### G-014 — Explanations SHAP header: missing prediction column

| Field | Value |
|-------|-------|
| Severity | **major** |
| Category | component |
| View | Explanations |
| HTML ref | `.docs/cerebro-dashboard.html` lines 1432–1446 |
| React file | `ui/src/views/Explanations.tsx:49–58` |

HTML shows a three-column equation: `expected_value  +  SHAP sum  =  prediction`. The prediction value (`expectedValue + shapSum`) is shown in `var(--green)`.

React shows only two columns: `expected_value  +  SHAP sum`. The `=` operator and prediction column are missing.

**Fix:** Add the third column to `ShapBreakdown`. Prediction = `(expectedValue + shapSum).toFixed(3)`, color `var(--green)`.

---

### G-015 — Importance/Explanations panels use `var(--radius)` instead of `var(--radius-lg)`

| Field | Value |
|-------|-------|
| Severity | minor |
| Category | spacing |
| Views | Importance, Explanations, Evaluation |
| HTML ref | `.docs/cerebro-dashboard.html` line 422: `.panel { border-radius: var(--radius-lg) }` |
| React files | `ui/src/views/Importance.tsx:246`, `ui/src/views/Trees.tsx:136` |

Several inline-styled panel wrappers use `borderRadius: "var(--radius)"` (4px) instead of `var(--radius-lg)` (8px). Once G-001 CSS is in place, using `className="panel"` will fix this automatically.

**Fix:** Covered by G-001. Verify after CSS classes land.

---

### G-016 — Sidebar footer always shows `—`

| Field | Value |
|-------|-------|
| Severity | minor |
| Category | state |
| View | Shell (Sidebar) |
| HTML ref | `.docs/cerebro-dashboard.html` lines 1117–1121 |
| React file | `ui/src/components/layout/Sidebar.tsx:149–153` |

HTML shows extracted timestamp, size, and extractor version. React always shows `—` because Sidebar has no access to artifact data.

**Fix:** Expose artifact metadata in the global store. Populate in Sidebar using a `useArtifactMeta()` selector that returns `null` when no artifact is loaded (show `—` gracefully when absent).

---

### G-017 — Panel title typography mismatch

| Field | Value |
|-------|-------|
| Severity | minor |
| Category | typography |
| View | Overview, Importance, Explanations, Evaluation |
| HTML ref | `.docs/cerebro-dashboard.html` lines 433–438: `.panel-title { font-family: var(--font-display); font-size: 20px; font-weight: 400 }` |
| React files | `ui/src/views/Importance.tsx:257`, `ui/src/views/Trees.tsx:141` |

Some inline `<h3>` panel titles use `fontSize: "13px"` and `fontWeight: 600` (e.g. Importance). The mockup panel title is Instrument Serif at 20px / weight 400. Covered by G-001 once `className="panel-title"` is used consistently.

**Fix:** Covered by G-001. Switch from inline styles to `className="panel-title"`.

---

### G-018 — Explanations loading/error states use undefined CSS classes

| Field | Value |
|-------|-------|
| Severity | minor |
| Category | component |
| View | Explanations, Evaluation |
| HTML ref | N/A (no loading state in mockup) |
| React files | `ui/src/views/Explanations.tsx:157–158`, `ui/src/views/Evaluation.tsx:65–66` |

`.view-loading` and `.view-error` are used as class names but are not defined anywhere in `globals.css` or the HTML mockup.

**Fix:** Replace with Tailwind utility classes or define them in `globals.css`. Suggested:
```css
.view-loading, .view-error {
  padding: 32px 40px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-muted);
}
.view-error { color: var(--red); }
```

---

### G-019 — Data view: no HTML reference section (M3 addition)

| Field | Value |
|-------|-------|
| Severity | cosmetic |
| Category | layout |
| View | Data |
| HTML ref | None — Data view was added in M3 after the mockup was locked |
| React file | `ui/src/views/Data.tsx` |

The Data view has no section in `cerebro-dashboard.html`. Its layout (full-width panels stacked vertically: Missingness table → Column distributions grid → Correlation heatmap) is reasonable and spec-conformant. The only actionable issues are the hardcoded color violations covered by G-002 and G-004.

No structural changes required. Both hardcoded color gaps are covered by G-002/G-004.

---

### G-020 — Sidebar nav order: Data item added between Importance and Explanations

| Field | Value |
|-------|-------|
| Severity | cosmetic |
| Category | layout |
| View | Shell (Sidebar) |
| HTML ref | `.docs/cerebro-dashboard.html` lines 1076–1115 (no Data item) |
| React file | `ui/src/components/layout/Sidebar.tsx:43–55` |

The HTML mockup has no Data nav item. React adds it between Importance and Explanations as an M3 feature. Since Data is in-scope per the spec, the placement is acceptable. No fix required — note this as a deliberate M3 extension with no mockup counterpart.

---

## Proposed Change Set

### CS-1: Port missing CSS classes to `globals.css` (closes G-001, G-015, G-006 partially, G-007 partially, G-008 partially, G-009 partially, G-010 partially, G-017)

Append to `ui/src/globals.css` after the existing `.view-actions` block:

```css
/* ===== CARDS / PANELS ===== */
.grid { display: grid; gap: 16px; }
.grid-2 { grid-template-columns: repeat(2, 1fr); }
.grid-3 { grid-template-columns: repeat(3, 1fr); }
.grid-4 { grid-template-columns: repeat(4, 1fr); }

.panel {
  background: var(--bg-elev);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px;
  position: relative;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.panel-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 400;
  letter-spacing: -0.01em;
}

.panel-subtitle {
  font-family: var(--font-mono);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-dim);
}

.panel-tabs {
  display: flex;
  gap: 4px;
  padding: 3px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.panel-tab {
  padding: 4px 10px;
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  border-radius: 3px;
  cursor: pointer;
  background: transparent;
  border: none;
  transition: all 0.12s;
}

.panel-tab.active {
  background: var(--bg-elev-2);
  color: var(--accent);
}

/* ===== STAT TILES ===== */
.stat {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 18px 20px;
  background: var(--bg-elev);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  position: relative;
  overflow: hidden;
}

.stat-label {
  font-family: var(--font-mono);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-dim);
}

.stat-value {
  font-family: var(--font-display);
  font-size: 38px;
  font-weight: 400;
  line-height: 1;
  letter-spacing: -0.01em;
  color: var(--text);
}

.stat-value em {
  font-style: italic;
  color: var(--accent);
  margin-right: 4px;
}

.stat-meta {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

.stat-meta .up { color: var(--green); }
.stat-meta .down { color: var(--red); }

/* ===== KEY-VALUE LISTS ===== */
.kv {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 10px 24px;
  font-size: 13px;
}

.kv dt {
  font-family: var(--font-mono);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-dim);
  align-self: center;
}

.kv dd {
  font-family: var(--font-mono);
  color: var(--text);
  font-size: 12px;
}

.kv dd .accent { color: var(--accent); }

/* ===== FEATURE IMPORTANCE BARS ===== */
.fi-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.fi-row {
  display: grid;
  grid-template-columns: 140px 1fr 60px;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
}

.fi-name {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fi-bar-wrap {
  height: 8px;
  background: var(--bg);
  border-radius: 2px;
  overflow: hidden;
  position: relative;
  border: 1px solid var(--border);
}

.fi-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--accent-dim), var(--accent));
  border-radius: 2px;
  position: relative;
}

.fi-bar::after {
  content: '';
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 1px;
  background: var(--accent-bright);
  box-shadow: 0 0 6px var(--accent);
}

.fi-value {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  text-align: right;
}

/* ===== TREE VISUALIZATION ===== */
.tree-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--bg-elev-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  flex-wrap: wrap;
}

.tree-controls label {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.tree-controls select, .tree-controls input {
  background: var(--bg);
  border: 1px solid var(--border-strong);
  color: var(--text);
  font-family: var(--font-mono);
  font-size: 12px;
  padding: 4px 8px;
  border-radius: var(--radius);
  outline: none;
}

.tree-controls select:focus, .tree-controls input:focus {
  border-color: var(--accent-dim);
}

.tree-viz {
  background:
    radial-gradient(circle at 50% 0%, rgba(212, 165, 116, 0.04), transparent 70%),
    var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  min-height: 440px;
  overflow: auto;
}

/* ===== CONFUSION MATRIX ===== */
.cm {
  display: grid;
  grid-template-columns: auto repeat(2, 1fr);
  grid-template-rows: auto repeat(2, 1fr);
  gap: 4px;
  max-width: 360px;
  margin: 0 auto;
}

.cm-axis-x, .cm-axis-y {
  font-family: var(--font-mono);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-dim);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
}

.cm-axis-y { writing-mode: vertical-rl; transform: rotate(180deg); }

.cm-cell {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius);
  font-family: var(--font-mono);
  position: relative;
  border: 1px solid var(--border);
}

.cm-cell .cm-num {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 400;
  color: var(--text);
  letter-spacing: -0.02em;
}

.cm-cell .cm-pct {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-dim);
  margin-top: 2px;
}

.cm-cell.tp { background: rgba(127,176,105,0.22); border-color: rgba(127,176,105,0.4); }
.cm-cell.tn { background: rgba(127,176,105,0.12); border-color: rgba(127,176,105,0.3); }
.cm-cell.fp { background: rgba(201,90,90,0.10);   border-color: rgba(201,90,90,0.25); }
.cm-cell.fn { background: rgba(201,90,90,0.15);   border-color: rgba(201,90,90,0.3); }

/* ===== PARTIAL DEPENDENCE GRID ===== */
.pdp-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.pdp-tile {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px;
}

.pdp-tile h4 {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
  margin-bottom: 6px;
}

/* ===== SAMPLE INSPECTOR TABS ===== */
.sample-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.sample-tab {
  padding: 8px 14px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  border: none;
  background: transparent;
  cursor: pointer;
  border-bottom: 1px solid transparent;
  margin-bottom: -1px;
}

.sample-tab.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

/* ===== SHAP BARS ===== */
.shap-row {
  display: grid;
  grid-template-columns: 140px 1fr 80px;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
  border-bottom: 1px solid var(--border);
}

.shap-row:last-child { border-bottom: none; }

.shap-name { font-family: var(--font-mono); font-size: 12px; color: var(--text); }

.shap-bar-wrap {
  position: relative;
  height: 6px;
  background: var(--bg);
  border-radius: 2px;
  display: flex;
}

.shap-bar-wrap::before {
  content: '';
  position: absolute;
  left: 50%;
  top: -2px;
  bottom: -2px;
  width: 1px;
  background: var(--border-strong);
}

.shap-bar {
  height: 100%;
  border-radius: 2px;
}

.shap-bar.pos { background: var(--accent); margin-left: 50%; }
.shap-bar.neg { background: var(--blue); margin-right: 50%; margin-left: auto; }

.shap-val {
  font-family: var(--font-mono);
  font-size: 11px;
  text-align: right;
}

.shap-val.pos { color: var(--accent); }
.shap-val.neg { color: var(--blue); }

/* ===== LOADING / ERROR STATES ===== */
.view-loading, .view-error {
  padding: 32px 40px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-muted);
}

.view-error { color: var(--red); }

/* ===== SCROLLBARS ===== */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-dim); }

/* ===== MOBILE FALLBACK ===== */
@media (max-width: 1024px) {
  .app::after {
    content: 'Cerebro dashboard is desktop-first. Open on a wider screen.';
    position: fixed;
    inset: 0;
    background: var(--bg);
    color: var(--text-muted);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px;
    font-family: var(--font-display);
    font-size: 24px;
    text-align: center;
    z-index: 100;
  }
}
```

### CS-2: Fix hardcoded color constants (closes G-002, G-003, G-004, G-005)

**`ui/src/views/Explanations.tsx`** — remove `COPPER` and `MUTED_RED`:
```diff
-const COPPER = "#b87333";
-const ACCENT = "var(--accent)";
-const MUTED_RED = "#c0392b";
+const ACCENT = "var(--accent)";
+const BLUE = "var(--blue)";
```
Then replace `COPPER` with `ACCENT` and `MUTED_RED` with `BLUE` throughout the file.

**`ui/src/views/Data.tsx`** — remove `COPPER`:
```diff
-const COPPER = "#b87333";
```
Replace with `var(--accent)` inline where needed.

**`ui/src/views/evaluation/BinaryPanel.tsx`** — remove `COPPER`:
```diff
-const COPPER = "#b87333";
```
For `colorScheme`, use a `useTokenColors()` helper (see below).

**`ui/src/components/importance/DivergenceCallout.tsx`** — remove fallback:
```diff
-border: "1px solid var(--red, #c0392b)",
+border: "1px solid var(--red)",
```
```diff
-color: "var(--red, #c0392b)",
+color: "var(--red)",
```

**`ui/src/lib/tokenColors.ts`** — new helper for Reaviz colorScheme:
```ts
export function useTokenColors(): { low: string; high: string } {
  const { theme } = useTheme.getState();
  // Re-run when theme changes
  const root = document.documentElement;
  const low = getComputedStyle(root).getPropertyValue("--bg-elev").trim();
  const high = getComputedStyle(root).getPropertyValue("--accent").trim();
  return { low, high };
}
```
Then in BinaryPanel and Data: `colorScheme={[colors.low, colors.high]}`.

### CS-3: Switch Importance tabs to `.panel-tabs` pattern (closes G-006)

**`ui/src/views/Importance.tsx`** — replace the tab toggle div:
```diff
-<div style={{ display: "flex", gap: "4px" }}>
+<div className="panel-tabs">
   {TABS.map((tab) => (
     <button
       key={tab.key}
       data-testid={`tab-${tab.key}`}
       onClick={() => setActiveTab(tab.key)}
-      style={{ padding: "3px 10px", ... border-radius: "100px" ... }}
+      className={`panel-tab${activeTab === tab.key ? " active" : ""}`}
     >
       {tab.label}
     </button>
   ))}
 </div>
```

### CS-4: Switch Explanations tabs to `.sample-tabs` pattern (closes G-007)

**`ui/src/views/Explanations.tsx`** — replace the tab buttons wrapper:
```diff
-<div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
+<div className="sample-tabs">
   {(["shap", "path", "raw"] as SampleTab[]).map(t => (
     <button
       key={t}
       onClick={() => setTab(t)}
-      style={{ padding: "4px 12px", borderRadius: "4px", border: "1px solid var(--border)",
-               background: tab === t ? "var(--accent)" : "transparent", ... }}
+      className={`sample-tab${tab === t ? " active" : ""}`}
     >
       {t === "shap" ? "SHAP breakdown" : t === "path" ? "Decision path" : "Raw features"}
     </button>
   ))}
 </div>
```

### CS-5: Fix SHAP bars to use CSS classes (closes G-008)

**`ui/src/views/Explanations.tsx`** — replace `ShapBreakdown` row markup:
```diff
-<div key={name} style={{ display: "grid", gridTemplateColumns: "140px 1fr 64px", ... }}>
-  <div style={{ fontSize: "12px", fontWeight: inPath ? 700 : 400, color: inPath ? COPPER : "var(--text)", ... }}>
+<div key={name} className="shap-row">
+  <span className="shap-name" style={{ color: inPath ? "var(--accent)" : undefined }}>
     {inPath && <span style={{ marginRight: "4px" }}>◆</span>}{name}
-  </div>
-  <div style={{ height: "4px", background: "var(--bg-elev)", ... }}>
-    <div style={{ width: `${pct}%`, height: "100%", background: barColor, float: ... }} />
-  </div>
-  <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: ..., textAlign: "right" }}>
+  </span>
+  <div className="shap-bar-wrap">
+    <div className={`shap-bar ${value >= 0 ? "pos" : "neg"}`} style={{ width: `${pct}%` }} />
+  </div>
+  <span className={`shap-val ${value >= 0 ? "pos" : "neg"} tnum`}>
     {value >= 0 ? "+" : ""}{value.toFixed(3)}
-  </div>
+  </span>
 </div>
```

### CS-6: Fix Importance bars to use `.fi-row` pattern (closes G-009)

**`ui/src/views/Importance.tsx`** — replace `FeatureBar`:
```tsx
function FeatureBar({ name, value, max }: { name: string; value: number; max: number }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="fi-row">
      <span className="fi-name">{name}</span>
      <div className="fi-bar-wrap">
        <div className="fi-bar" style={{ width: `${pct}%` }} />
      </div>
      <span className="fi-value tnum">{value.toLocaleString(undefined, { maximumFractionDigits: 1 })}</span>
    </div>
  );
}
```

### CS-7: Fix TreeControls to use `.tree-controls` CSS class (closes G-010)

**`ui/src/components/trees/TreeControls.tsx`** — replace outer div:
```diff
-<div style={{ display: "flex", alignItems: "center", gap: "16px", padding: "10px 0 14px", borderBottom: "1px solid var(--border)", marginBottom: "16px", flexWrap: "wrap" }}>
+<div className="tree-controls">
```
Remove the inline `border-bottom` / `padding` style object entirely. Add the "Highlight" select (third control):
```tsx
<div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
  <label>Highlight</label>
  <select value="leaf" onChange={() => {}}>
    <option value="leaf">Leaf value</option>
    <option value="samples">Sample count</option>
    <option value="gain">Gain</option>
  </select>
</div>
```

### CS-8: Fix BinaryPanel confusion matrix (closes G-011)

**`ui/src/views/evaluation/BinaryPanel.tsx`** — replace `Heatmap` with `.cm` grid:
```tsx
function ConfusionMatrix({ ev }: { ev: BinaryEval }) {
  const total = ev.confusion_matrix.reduce((s, c) => s + c.count, 0);
  const cells: Record<string, { count: number; pct: string; cls: string }> = {};
  for (const c of ev.confusion_matrix) {
    const key = `${c.actual}-${c.predicted}`;
    const isPositive = c.actual === 1;
    const isMatch = c.actual === c.predicted;
    const cls = isMatch && isPositive ? "tp" : isMatch ? "tn" : isPositive ? "fn" : "fp";
    cells[key] = { count: c.count, pct: ((c.count / total) * 100).toFixed(1) + "%", cls };
  }
  const get = (a: number, p: number) => cells[`${a}-${p}`] ?? { count: 0, pct: "0.0%", cls: "tn" };
  return (
    <div className="cm">
      <div /><div className="cm-axis-x">pred: 0</div><div className="cm-axis-x">pred: 1</div>
      <div className="cm-axis-y">actual: 0</div>
      <div className={`cm-cell ${get(0,0).cls}`}><span className="cm-num tnum">{get(0,0).count}</span><span className="cm-pct">{get(0,0).pct}</span></div>
      <div className={`cm-cell ${get(0,1).cls}`}><span className="cm-num tnum">{get(0,1).count}</span><span className="cm-pct">{get(0,1).pct}</span></div>
      <div className="cm-axis-y">actual: 1</div>
      <div className={`cm-cell ${get(1,0).cls}`}><span className="cm-num tnum">{get(1,0).count}</span><span className="cm-pct">{get(1,0).pct}</span></div>
      <div className={`cm-cell ${get(1,1).cls}`}><span className="cm-num tnum">{get(1,1).count}</span><span className="cm-pct">{get(1,1).pct}</span></div>
    </div>
  );
}
```

### CS-9: Add prediction column to SHAP header (closes G-014)

**`ui/src/views/Explanations.tsx`** — `ShapBreakdown` header div:
```diff
+<div>
+  <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-dim)" }}>prediction</div>
+  <div style={{ fontFamily: "var(--font-display)", fontSize: "24px", color: "var(--green)" }} className="tnum">{(expectedValue + shapSum >= 0 ? "+" : "") + (expectedValue + shapSum).toFixed(3)}</div>
+</div>
 ...header flex row
```
Add `=` operator column between SHAP sum and prediction.

---

## Verification Checklist

After all changes land, verify each view in both dark and light themes.

### Shell

- [ ] Dark: body background `#0a0d14`, grain overlay visible
- [ ] Light: body background `#f4efe2`, grain visible at lower opacity
- [ ] TopBar: brand mark + "cer*e*bro" in display font visible
- [ ] TopBar: model name, hash, framework badge, "artifact valid" badge, schema badge all present when artifact loaded
- [ ] TopBar: theme toggle flips theme and icon switches moon↔sun
- [ ] TopBar: theme persists on reload
- [ ] Sidebar: active nav item shows accent left indicator (2px)
- [ ] Sidebar: hover state on nav items works in both themes
- [ ] Sidebar: footer shows extracted timestamp, size, extractor version when artifact loaded
- [ ] Sidebar: Data nav item between Importance and Explanations
- [ ] Mobile (<1024px): fallback overlay appears

### Overview

- [ ] 4 stat tiles render in a row with card chrome (bg-elev, border, radius-lg)
- [ ] Stat values use display font at 38px
- [ ] Objective tile shows italic accent text
- [ ] Training parameters panel: display font title, kv grid with mono dt/dd
- [ ] Feature schema panel: 4-column grid (idx, name, type, const)
- [ ] Categorical features colored purple, numeric colored blue
- [ ] Monotone features show accent-colored "mono+" / "mono-"

### Trees

- [ ] TreeControls renders as a contained box (bg-elev-2, border, radius) not just a divider
- [ ] Three selects present: Tree, Depth, Highlight
- [ ] Node inspector panel appears on right (bg-elev, border, radius)
- [ ] react-d3-tree renders in the tree-viz area
- [ ] Tree selector updates the visualization
- [ ] Node click populates inspector

### Importance

- [ ] Left panel: "Aggregate importance" in display font 20px
- [ ] Tab toggle is a segmented control (outer border container, active tab = accent text on bg-elev-2, no pill shape)
- [ ] Feature bars: 8px height, gradient accent-dim→accent, 1px border on track, glow tip
- [ ] Name column is 140px fixed-width, value column is 60px
- [ ] Right panel: "Gain vs permutation" with feature/gain-rank/perm-rank/delta table
- [ ] DivergenceCallout uses `var(--red)` (no hardcoded hex fallback)

### Explanations

- [ ] Sample tabs are underline style (not pills) — active tab has accent underline
- [ ] SHAP header shows 3-column equation: expected value + SHAP sum = prediction (green)
- [ ] SHAP bars: 6px height, centerline rule, positive = accent, negative = blue
- [ ] Decision path features highlighted in `var(--accent)` (not hardcoded copper)
- [ ] Partial dependence grid shows 3-column layout

### Evaluation

- [ ] Objective indicator visible with "artifact objective: binary" hint
- [ ] Binary: stat tiles render with card chrome
- [ ] Binary: confusion matrix uses green/red per-cell color coding (TP=green, TN=light green, FP=light red, FN=red)
- [ ] Binary: ROC curve renders (Reaviz line chart acceptable)
- [ ] Both themes: metric values readable, chart colors update with token cascade

### Data

- [ ] Missingness table: highlight color for >10% is `var(--accent)` not copper hex
- [ ] Heatmap colorScheme uses computed token values, updates on theme toggle
- [ ] Placeholder state renders correctly when no data_profile present

### Both themes across all views

- [ ] No hardcoded hex colors visible in DevTools Styles panel (outside tokens.css)
- [ ] All `.panel` containers have `border-radius: 8px` (var(--radius-lg))
- [ ] All nav, badge, and button colors update correctly on theme toggle
- [ ] Scrollbars render with `var(--border-strong)` thumb in both themes
