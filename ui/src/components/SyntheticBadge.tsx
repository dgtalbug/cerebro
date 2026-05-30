export function SyntheticBadge() {
  return (
    <div style={{
      display: "inline-flex",
      alignItems: "center",
      gap: "6px",
      padding: "4px 10px",
      background: "var(--bg-elev)",
      border: "1px solid var(--border)",
      borderRadius: "4px",
      fontSize: "11px",
      fontWeight: 500,
      color: "var(--text-muted)",
      fontFamily: "var(--font-mono)",
      textTransform: "uppercase",
      letterSpacing: "0.05em",
    }}>
      <span>◇</span>
      <span>Approximate (synthetic)</span>
    </div>
  );
}
