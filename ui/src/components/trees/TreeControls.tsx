interface CanonicalTree {
  index: number;
  class_index: number | null;
  num_leaves: number;
  root: object;
}

interface Props {
  trees: CanonicalTree[];
  selectedIndex: number;
  depth: number | null;
  nodeCount: number;
  leafCount: number;
  onTreeChange: (index: number) => void;
  onDepthChange: (depth: number | null) => void;
}

const DEPTH_OPTIONS: { label: string; value: number | null }[] = [
  { label: "All", value: null },
  { label: "≤ 3", value: 3 },
  { label: "≤ 4", value: 4 },
  { label: "≤ 5", value: 5 },
];

export function TreeControls({
  trees,
  selectedIndex,
  depth,
  nodeCount,
  leafCount,
  onTreeChange,
  onDepthChange,
}: Props) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "16px",
        padding: "10px 0 14px",
        borderBottom: "1px solid var(--border)",
        marginBottom: "16px",
        flexWrap: "wrap",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <label
          style={{ fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.08em" }}
        >
          Tree
        </label>
        <select
          data-testid="tree-selector"
          value={selectedIndex}
          onChange={(e) => onTreeChange(Number(e.target.value))}
          style={{
            background: "var(--bg-elev)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            color: "var(--text)",
            fontSize: "12px",
            fontFamily: "var(--font-mono)",
            padding: "4px 8px",
            cursor: "pointer",
          }}
        >
          {trees.map((t) => (
            <option key={t.index} value={t.index}>
              #{t.index}
              {t.class_index !== null ? ` · class ${t.class_index}` : ""}
            </option>
          ))}
        </select>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <label
          style={{ fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.08em" }}
        >
          Depth
        </label>
        <div style={{ display: "flex", gap: "4px" }}>
          {DEPTH_OPTIONS.map((opt) => (
            <button
              key={String(opt.value)}
              data-testid={`depth-${opt.value ?? "all"}`}
              onClick={() => onDepthChange(opt.value)}
              style={{
                padding: "3px 8px",
                fontSize: "11px",
                fontFamily: "var(--font-mono)",
                border: "1px solid var(--border)",
                borderRadius: "100px",
                cursor: "pointer",
                background: depth === opt.value ? "var(--accent)" : "var(--bg-elev-2)",
                color: depth === opt.value ? "var(--bg)" : "var(--text-muted)",
                transition: "all 0.12s",
              }}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div
        style={{
          marginLeft: "auto",
          fontSize: "11px",
          fontFamily: "var(--font-mono)",
          color: "var(--text-dim)",
        }}
      >
        {nodeCount} nodes · {leafCount} leaves
      </div>
    </div>
  );
}
