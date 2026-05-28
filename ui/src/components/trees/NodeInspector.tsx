interface SelectedNode {
  id: number;
  split_feature: number | null;
  threshold: number | null;
  decision_type: string | null;
  leaf_value: number | null;
}

interface Props {
  node: SelectedNode | null;
  featureNames: string[];
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "contents" }}>
      <dt style={{ color: "var(--text-dim)", fontSize: "11px", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
        {label}
      </dt>
      <dd style={{ fontSize: "12px", fontFamily: "var(--font-mono)", color: "var(--text)" }}>
        {value}
      </dd>
    </div>
  );
}

export function NodeInspector({ node, featureNames }: Props) {
  if (node === null) {
    return (
      <div
        data-testid="node-inspector-empty"
        style={{
          color: "var(--text-dim)",
          fontSize: "12px",
          fontFamily: "var(--font-mono)",
          padding: "16px 0",
        }}
      >
        Click any node to inspect.
      </div>
    );
  }

  const isLeaf = node.leaf_value !== null && node.split_feature === null;

  return (
    <div data-testid="node-inspector">
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          marginBottom: "12px",
        }}
      >
        <span style={{ fontSize: "12px", fontWeight: 600 }}>Node #{node.id}</span>
        {isLeaf && (
          <span
            style={{
              fontSize: "10px",
              fontFamily: "var(--font-mono)",
              background: "var(--bg-elev-2)",
              border: "1px solid var(--border)",
              borderRadius: "100px",
              padding: "1px 8px",
              color: "var(--text-dim)",
            }}
          >
            terminal
          </span>
        )}
      </div>

      <dl style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "8px 16px" }}>
        {isLeaf ? (
          <Row label="leaf value" value={node.leaf_value!.toFixed(6)} />
        ) : (
          <>
            <Row
              label="feature"
              value={
                node.split_feature !== null
                  ? (featureNames[node.split_feature] ?? `feature_${node.split_feature}`)
                  : "—"
              }
            />
            <Row label="threshold" value={node.threshold?.toFixed(4) ?? "—"} />
            <Row label="decision" value={node.decision_type ?? "—"} />
          </>
        )}
      </dl>
    </div>
  );
}
