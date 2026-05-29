import { useParams } from "react-router-dom";
import { BrandMark } from "../brand/BrandMark";
import { ThemeToggle } from "../ui/ThemeToggle";
import { useArtifact } from "../../lib/api/queries";

export function TopBar() {
  const { id } = useParams<{ id?: string }>();
  const { data } = useArtifact(id ?? "");
  const artifact = id ? data?.data : undefined;

  const frameworkLabel = artifact
    ? `${artifact.source.framework} ${artifact.source.framework_version}`
    : null;
  const schemaLabel = artifact ? `schema ${artifact.schema_version}` : null;
  const modelLabel = artifact
    ? `${artifact.source.framework}-${artifact.model.objective}`
    : "—";
  const hashLabel = artifact
    ? `@ ${artifact.source.extracted_at.slice(0, 10)}`
    : "—";

  return (
    <header className="topbar">
      <div className="brand">
        <BrandMark className="w-[26px] h-[26px] text-accent" />
        <div className="brand-name">
          cer<em>e</em>bro
        </div>
      </div>

      <div className="model-bar">
        <span className="model-name">{modelLabel}</span>
        <span className="model-hash">{hashLabel}</span>
        {frameworkLabel && (
          <span className="badge framework">
            <span className="badge-dot" style={{ background: "var(--accent)", boxShadow: "0 0 6px var(--accent)" }} />
            {frameworkLabel}
          </span>
        )}
        {artifact && (
          <>
            <span className="badge">
              <span className="badge-dot" />
              artifact valid
            </span>
            <span className="badge">{schemaLabel}</span>
          </>
        )}
      </div>

      <div className="topbar-actions">
        <button className="icon-btn" title="Search" aria-label="Search">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="7" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </button>
        <ThemeToggle />
        <button className="btn" disabled>Export</button>
        <button className="btn primary" disabled>Re-extract</button>
      </div>
    </header>
  );
}
