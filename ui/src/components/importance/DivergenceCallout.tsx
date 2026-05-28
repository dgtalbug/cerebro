import type { DivergenceWarning } from "../../lib/api/queries";

interface Props {
  warnings: DivergenceWarning[];
}

export function DivergenceCallout({ warnings }: Props) {
  if (warnings.length === 0) return null;

  const names = warnings.map((w) => w.feature).join(", ");

  return (
    <div
      data-testid="divergence-callout"
      style={{
        marginTop: "16px",
        padding: "12px 14px",
        borderRadius: "var(--radius)",
        border: "1px solid var(--red, #c0392b)",
        background: "rgba(192, 57, 43, 0.08)",
        fontFamily: "var(--font-mono)",
        fontSize: "12px",
        color: "var(--text)",
      }}
    >
      <div style={{ fontWeight: 600, color: "var(--red, #c0392b)", marginBottom: "4px" }}>
        Heads up.
      </div>
      <div>
        {names}{" "}
        {warnings.length === 1 ? "has" : "have"} high gain importance but low permutation
        importance — {warnings.length === 1 ? "it" : "they"} may benefit from regularisation
        or feature review.
      </div>
    </div>
  );
}
