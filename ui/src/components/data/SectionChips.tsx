import type { SectionStatus } from "../../lib/api/queries";

const SECTIONS: { key: keyof SectionStatus; label: string }[] = [
  { key: "trees", label: "trees" },
  { key: "importance", label: "importance" },
  { key: "shap", label: "shap" },
  { key: "evaluation", label: "eval" },
  { key: "data_profile", label: "data" },
];

interface Props {
  status: SectionStatus;
  size?: "sm" | "xs";
}

export function SectionChips({ status, size = "sm" }: Props) {
  const fontSize = size === "xs" ? "9px" : "10px";
  const padding = size === "xs" ? "2px 5px" : "3px 7px";

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
      {SECTIONS.map(({ key, label }) => {
        const present = status[key];
        return (
          <span
            key={key}
            style={{
              fontFamily: "var(--font-mono)",
              fontSize,
              padding,
              borderRadius: "var(--radius)",
              border: `1px solid ${present ? "var(--green)" : "var(--border-strong)"}`,
              color: present ? "var(--green)" : "var(--text-dim)",
              background: present ? "rgba(127,176,105,0.08)" : "transparent",
              letterSpacing: "0.03em",
            }}
          >
            {label}
          </span>
        );
      })}
    </div>
  );
}
