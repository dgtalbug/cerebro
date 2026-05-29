# Design Token Diff — HTML mockup vs React implementation

Source of truth: `.docs/cerebro-dashboard.html` `:root` and `[data-theme="light"]` blocks.
Implementation: `ui/src/styles/tokens.css`.

---

## Dark Theme (`:root` / `:root[data-theme="dark"]`)

HTML defines 27 core tokens. `tokens.css` carries all 27 plus shadcn aliases.

| Token | HTML value | `tokens.css` value | Match |
|-------|-----------|-------------------|-------|
| `--bg` | `#0a0d14` | `#0a0d14` | ✓ |
| `--bg-elev` | `#11151f` | `#11151f` | ✓ |
| `--bg-elev-2` | `#161b27` | `#161b27` | ✓ |
| `--bg-hover` | `#1a2030` | `#1a2030` | ✓ |
| `--border` | `#1f2632` | `#1f2632` | ✓ |
| `--border-strong` | `#2a3242` | `#2a3242` | ✓ |
| `--text` | `#e8e6df` | `#e8e6df` | ✓ |
| `--text-muted` | `#8b92a8` | `#8b92a8` | ✓ |
| `--text-dim` | `#5a6275` | `#5a6275` | ✓ |
| `--accent` | `#d4a574` | `#d4a574` | ✓ |
| `--accent-bright` | `#e8be8a` | `#e8be8a` | ✓ |
| `--accent-dim` | `#8a6d4f` | `#8a6d4f` | ✓ |
| `--accent-glow` | `rgba(212,165,116,0.15)` | `rgba(212,165,116,0.15)` | ✓ |
| `--blue` | `#6b8dde` | `#6b8dde` | ✓ |
| `--green` | `#7fb069` | `#7fb069` | ✓ |
| `--red` | `#c95a5a` | `#c95a5a` | ✓ |
| `--amber` | `#d4a574` | `#d4a574` | ✓ |
| `--purple` | `#9b87c4` | `#9b87c4` | ✓ |
| `--font-display` | `'Instrument Serif', 'Times New Roman', serif` | `"Instrument Serif", "Times New Roman", serif` | ✓ |
| `--font-body` | `'Geist', system-ui, sans-serif` | `"Geist", system-ui, sans-serif` | ✓ |
| `--font-mono` | `'JetBrains Mono', 'SF Mono', monospace` | `"JetBrains Mono", "SF Mono", monospace` | ✓ |
| `--radius` | `4px` | `4px` | ✓ |
| `--radius-lg` | `8px` | `8px` | ✓ |
| `--grain-opacity` | `0.4` | `0.4` | ✓ |
| `--grain-blend` | `overlay` | `overlay` | ✓ |
| `--glow-1` | `rgba(212,165,116,0.15)` | `rgba(212,165,116,0.15)` | ✓ |
| `--glow-2` | `rgba(107,141,222,0.06)` | `rgba(107,141,222,0.06)` | ✓ |

**Result: 27 / 27 tokens match. Zero mismatches.**

`tokens.css` additionally defines shadcn aliases in the same block. Those are additive and correct — they reference mockup tokens by `var(--x)` so both themes pick them up automatically through cascade.

---

## Light Theme (`:root[data-theme="light"]`)

HTML defines 22 override tokens (typography and radii inherit from `:root`).

| Token | HTML value | `tokens.css` value | Match |
|-------|-----------|-------------------|-------|
| `--bg` | `#f4efe2` | `#f4efe2` | ✓ |
| `--bg-elev` | `#fbf7eb` | `#fbf7eb` | ✓ |
| `--bg-elev-2` | `#ede6d1` | `#ede6d1` | ✓ |
| `--bg-hover` | `#e4dbc1` | `#e4dbc1` | ✓ |
| `--border` | `#d8cdaf` | `#d8cdaf` | ✓ |
| `--border-strong` | `#b8aa86` | `#b8aa86` | ✓ |
| `--text` | `#1f1d18` | `#1f1d18` | ✓ |
| `--text-muted` | `#5c574a` | `#5c574a` | ✓ |
| `--text-dim` | `#8a8270` | `#8a8270` | ✓ |
| `--accent` | `#a07338` | `#a07338` | ✓ |
| `--accent-bright` | `#b8884a` | `#b8884a` | ✓ |
| `--accent-dim` | `#c9b78f` | `#c9b78f` | ✓ |
| `--accent-glow` | `rgba(160,115,56,0.10)` | `rgba(160,115,56,0.1)` | ✓ ¹ |
| `--blue` | `#3d5d9b` | `#3d5d9b` | ✓ |
| `--green` | `#4a7a3d` | `#4a7a3d` | ✓ |
| `--red` | `#a23030` | `#a23030` | ✓ |
| `--amber` | `#a07338` | `#a07338` | ✓ |
| `--purple` | `#6e5896` | `#6e5896` | ✓ |
| `--grain-opacity` | `0.25` | `0.25` | ✓ |
| `--grain-blend` | `multiply` | `multiply` | ✓ |
| `--glow-1` | `rgba(160,115,56,0.08)` | `rgba(160,115,56,0.08)` | ✓ |
| `--glow-2` | `rgba(61,93,155,0.04)` | `rgba(61,93,155,0.04)` | ✓ |

¹ Trailing zero difference (`0.10` vs `0.1`) is semantically identical.

**Result: 22 / 22 tokens match. Zero mismatches.**

---

## Hardcoded colors in component files (token violations)

These are NOT token-layer mismatches (the tokens themselves are correct), but they are violations of the "no hardcoded colors" constraint. They are root causes of several major view-level gaps.

| Location | Hardcoded value | Should be | Severity |
|----------|----------------|-----------|----------|
| `ui/src/views/Explanations.tsx:13` | `const COPPER = "#b87333"` | `var(--accent)` | major |
| `ui/src/views/Explanations.tsx:15` | `const MUTED_RED = "#c0392b"` | `var(--red)` | major |
| `ui/src/views/Data.tsx:8` | `const COPPER = "#b87333"` | `var(--accent)` | major |
| `ui/src/views/evaluation/BinaryPanel.tsx:6` | `const COPPER = "#b87333"` | `var(--accent)` | major |
| `ui/src/views/evaluation/BinaryPanel.tsx:73` | `colorScheme={["#1a2a40", COPPER]}` | token-derived values | major |
| `ui/src/views/Data.tsx:102` | `colorScheme={["#1a2a40", COPPER]}` | token-derived values | major |
| `ui/src/components/importance/DivergenceCallout.tsx:19` | `var(--red, #c0392b)` fallback | `var(--red)` (no fallback) | minor |

**Root cause note on `"#1a2a40"`:** This value is close to `--bg-elev-2` (`#161b27`) but is not a token. The Reaviz Heatmap and BarChart colorSchemes should use `[getComputedStyle(document.documentElement).getPropertyValue("--bg-elev"), getComputedStyle(…).getPropertyValue("--accent")]` or a theme-aware helper, since Reaviz accepts JS strings not CSS variables.

---

## Conclusion

The token layer is **perfect** — zero CSS variable mismatches between the HTML and `tokens.css`. All fidelity drift is caused by:
1. Missing CSS class definitions in `globals.css` (see gap report)
2. Hardcoded hex/rgb values in component files that bypass the token system
