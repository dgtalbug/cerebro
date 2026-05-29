import { useNavigate } from "react-router-dom";
import { SectionChips } from "../components/data/SectionChips";
import { useModels, type ModelSummary } from "../lib/api/queries";

function SkeletonCard() {
  return (
    <div
      style={{
        background: "var(--bg-elev)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)",
        padding: "20px",
        display: "flex",
        flexDirection: "column",
        gap: "12px",
      }}
    >
      {[80, 50, 100].map((w) => (
        <div
          key={w}
          style={{
            height: "12px",
            width: `${w}%`,
            background: "var(--bg-elev-2)",
            borderRadius: "var(--radius)",
            animation: "pulse 1.4s ease-in-out infinite",
          }}
        />
      ))}
    </div>
  );
}

function ModelCard({ model, onClick }: { model: ModelSummary; onClick: () => void }) {
  const date = model.latest_version_date.slice(0, 10);

  return (
    <button
      onClick={onClick}
      style={{
        background: "var(--bg-elev)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)",
        padding: "20px",
        cursor: "pointer",
        textAlign: "left",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        gap: "12px",
        transition: "border-color 0.15s, background 0.15s",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = "var(--border-strong)";
        (e.currentTarget as HTMLElement).style.background = "var(--bg-hover)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = "var(--border)";
        (e.currentTarget as HTMLElement).style.background = "var(--bg-elev)";
      }}
    >
      {/* Name + version */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "8px" }}>
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "13px",
            fontWeight: 600,
            color: "var(--text)",
            wordBreak: "break-all",
          }}
        >
          {model.name}
        </div>
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "10px",
            color: "var(--text-dim)",
            whiteSpace: "nowrap",
            flexShrink: 0,
          }}
        >
          v{model.latest_version} · {date}
        </div>
      </div>

      {/* Badges */}
      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "10px",
            padding: "2px 7px",
            borderRadius: "var(--radius)",
            background: "rgba(107,141,222,0.12)",
            color: "var(--blue)",
            border: "1px solid rgba(107,141,222,0.2)",
          }}
        >
          {model.framework}
        </span>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "10px",
            padding: "2px 7px",
            borderRadius: "var(--radius)",
            background: "rgba(212,165,116,0.1)",
            color: "var(--accent)",
            border: "1px solid var(--accent-dim)",
          }}
        >
          {model.objective}
        </span>
      </div>

      {/* Section chips */}
      <SectionChips status={model.section_status} size="xs" />
    </button>
  );
}

function EmptyState() {
  const navigate = useNavigate();
  return (
    <div
      style={{
        gridColumn: "1 / -1",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "16px",
        padding: "64px 32px",
        color: "var(--text-muted)",
      }}
    >
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" opacity={0.4}>
        <rect x="2" y="3" width="20" height="14" rx="2" />
        <path d="M8 21h8M12 17v4" />
      </svg>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: "13px", textAlign: "center" }}>
        No models yet
      </div>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-dim)", textAlign: "center", maxWidth: "280px" }}>
        Upload a LightGBM model to create your first entry in the registry.
      </div>
      <button
        className="btn primary"
        onClick={() => navigate("/ingest")}
        style={{ gap: "8px" }}
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
        </svg>
        Load first model
      </button>
    </div>
  );
}

export function Registry() {
  const navigate = useNavigate();
  const { data: models, isLoading, isError } = useModels();

  return (
    <section className="view" style={{ maxWidth: "none" }}>
      <div className="view-header">
        <div>
          <h1 className="view-title">Model <em>Registry</em></h1>
          <p className="view-subtitle">All registered models — click a card to view version history and artifact details.</p>
        </div>
        <button
          className="btn primary"
          onClick={() => navigate("/ingest")}
          style={{ gap: "8px", flexShrink: 0 }}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Load model
        </button>
      </div>

      {isError && (
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--red)", padding: "16px 0" }}>
          Failed to load models.
        </div>
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: "16px",
        }}
      >
        {isLoading
          ? Array.from({ length: 6 }, (_, i) => <SkeletonCard key={i} />)
          : models?.length === 0
          ? <EmptyState />
          : models?.map((m) => (
              <ModelCard
                key={m.id}
                model={m}
                onClick={() => navigate(`/models/${m.id}`)}
              />
            ))}
      </div>

      <style>{`@keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:0.4 } }`}</style>
    </section>
  );
}
