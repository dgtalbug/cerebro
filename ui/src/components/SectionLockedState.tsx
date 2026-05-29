interface FileHint {
  label: string;
  hint: string;
}

interface Props {
  title: string;
  description: string;
  files: FileHint[];
  onAction: () => void;
  actionLabel: string;
}

export function SectionLockedState({ title, description, files, onAction, actionLabel }: Props) {
  return (
    <div
      style={{
        maxWidth: "560px",
        margin: "32px 0",
        display: "flex",
        flexDirection: "column",
        gap: "20px",
      }}
    >
      <div>
        <div
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "18px",
            marginBottom: "8px",
            color: "var(--text)",
          }}
        >
          {title}
        </div>
        <div
          style={{
            fontSize: "13px",
            color: "var(--text-muted)",
            lineHeight: "1.6",
          }}
        >
          {description}
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "10px",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            color: "var(--text-dim)",
            marginBottom: "2px",
          }}
        >
          Files required
        </div>
        {files.map((f) => (
          <div
            key={f.label}
            style={{
              padding: "10px 14px",
              background: "var(--bg-elev)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              display: "flex",
              flexDirection: "column",
              gap: "4px",
            }}
          >
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "12px",
                fontWeight: 500,
                color: "var(--text)",
              }}
            >
              {f.label}
            </div>
            <div style={{ fontSize: "11px", color: "var(--text-dim)", lineHeight: "1.5" }}>
              {f.hint}
            </div>
          </div>
        ))}
      </div>

      <button
        className="btn primary"
        onClick={onAction}
        style={{ alignSelf: "flex-start" }}
      >
        {actionLabel}
      </button>
    </div>
  );
}
