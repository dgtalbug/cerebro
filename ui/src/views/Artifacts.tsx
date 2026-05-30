import { useNavigate, useSearchParams } from "react-router-dom";
import { ViewHeader } from "../components/layout/ViewHeader";
import { useArtifactList, type ArtifactRow } from "../lib/api/queries";

function TagPill({
  tag,
  onClick,
  active,
}: {
  tag: string;
  onClick: (tag: string) => void;
  active: boolean;
}) {
  return (
    <button
      onClick={() => onClick(tag)}
      style={{
        padding: "2px 8px",
        borderRadius: "100px",
        border: `1px solid ${active ? "var(--accent)" : "var(--border-strong)"}`,
        background: active ? "var(--accent-glow)" : "var(--bg-elev)",
        color: active ? "var(--accent)" : "var(--text-muted)",
        fontFamily: "var(--font-mono)",
        fontSize: "10px",
        cursor: "pointer",
        letterSpacing: "0.04em",
      }}
    >
      {tag}
    </button>
  );
}

function ArtifactCard({
  artifact,
  onNavigate,
}: {
  artifact: ArtifactRow;
  onNavigate: (id: string) => void;
}) {
  const date = artifact.extracted_at.slice(0, 10);
  // Tags are stored separately; we parse any tags from the artifact's name or use a stub
  return (
    <div
      style={{
        background: "var(--bg-elev)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)",
        padding: "16px 20px",
        cursor: "pointer",
        transition: "border-color 0.15s",
      }}
      onClick={() => onNavigate(artifact.id)}
      onKeyDown={(e) => e.key === "Enter" && onNavigate(artifact.id)}
      role="button"
      tabIndex={0}
    >
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "12px" }}>
        <div>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "13px", fontWeight: 500, color: "var(--text)", marginBottom: "4px" }}>
            {artifact.name || artifact.id}
          </p>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)" }}>
            {artifact.id}
          </p>
        </div>
        <span
          className="badge framework"
          style={{ flexShrink: 0 }}
        >
          {artifact.framework}
        </span>
      </div>
      <div style={{ display: "flex", gap: "16px", marginTop: "12px", fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
        <span>obj: {artifact.objective}</span>
        <span>{artifact.num_trees} trees</span>
        <span>{artifact.num_features} features</span>
        <span style={{ marginLeft: "auto", color: "var(--text-dim)" }}>{date}</span>
      </div>
    </div>
  );
}

export function Artifacts() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const activeTag = searchParams.get("tag") ?? "";

  const { data, isLoading, isError } = useArtifactList(activeTag || undefined);

  function handleTagClick(tag: string) {
    if (tag === activeTag) {
      setSearchParams({});
    } else {
      setSearchParams({ tag });
    }
  }

  return (
    <section className="view">
      <ViewHeader
        title="Artifact"
        titleEmphasis="list"
        subtitle="All registered artifacts. Filter by tag or framework."
      />

      {activeTag && (
        <div style={{ marginBottom: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "11px", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
            Filtering by tag:
          </span>
          <TagPill tag={activeTag} onClick={handleTagClick} active />
          <button
            onClick={() => setSearchParams({})}
            style={{ fontSize: "11px", color: "var(--text-dim)", background: "none", border: "none", cursor: "pointer", fontFamily: "var(--font-mono)" }}
          >
            ✕ clear
          </button>
        </div>
      )}

      {isLoading && (
        <p style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)", fontSize: "12px" }}>Loading…</p>
      )}
      {isError && (
        <p style={{ color: "var(--red)", fontSize: "12px" }}>Failed to load artifacts.</p>
      )}
      {data && data.items.length === 0 && (
        <p style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)", fontSize: "12px" }}>
          {activeTag ? `No artifacts tagged "${activeTag}".` : "No artifacts registered."}
        </p>
      )}
      {data && data.items.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {data.items.map((artifact) => (
            <ArtifactCard
              key={artifact.id}
              artifact={artifact}
              onNavigate={(id) => navigate(`/artifacts/${id}/overview`)}
            />
          ))}
        </div>
      )}
    </section>
  );
}
