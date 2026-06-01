import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "../components/ui/dialog";
import { ExportMenu } from "../components/ui/ExportMenu";
import { ViewHeader } from "../components/layout/ViewHeader";
import { exportCsv } from "../lib/export/csv";
import { useArtifactList, useDeleteArtifact, type ArtifactRow } from "../lib/api/queries";

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
  const { mutate: deleteArtifact, isPending } = useDeleteArtifact();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  function handleDeleteClick(e: React.MouseEvent) {
    e.stopPropagation();
    setDeleteError(null);
    setDialogOpen(true);
  }

  function handleConfirm() {
    deleteArtifact(artifact.id, {
      onSuccess: () => {
        setDialogOpen(false);
        toast.success("Artifact deleted");
      },
      onError: (err) => {
        setDeleteError(err.message);
        toast.error("Delete failed", { description: err.message });
      },
    });
  }

  function handleCancel() {
    setDialogOpen(false);
    setDeleteError(null);
  }

  return (
    <div
      style={{
        background: "var(--bg-elev)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)",
        padding: "16px 20px",
        transition: "border-color 0.15s",
      }}
    >
      <div
        style={{ cursor: "pointer" }}
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
          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexShrink: 0 }}>
            <span className="badge framework">{artifact.framework}</span>
            <button
              onClick={handleDeleteClick}
              title="Delete artifact"
              style={{
                background: "none", border: "none", borderRadius: "var(--radius)",
                color: "var(--text-dim)", cursor: "pointer", padding: "4px",
                display: "flex", alignItems: "center", lineHeight: 1,
              }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = "var(--red)"; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = "var(--text-dim)"; }}
            >
              <Trash2 size={14} strokeWidth={1.5} />
            </button>
          </div>
        </div>
        <div style={{ display: "flex", gap: "16px", marginTop: "12px", fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
          <span>obj: {artifact.objective}</span>
          <span>{artifact.num_trees} trees</span>
          <span>{artifact.num_features} features</span>
          <span style={{ marginLeft: "auto", color: "var(--text-dim)" }}>{date}</span>
        </div>
      </div>

      <Dialog open={dialogOpen} onOpenChange={(open) => { if (!isPending) { setDialogOpen(open); if (!open) setDeleteError(null); } }}>
        <DialogContent style={{ background: "var(--bg-elev-2)", border: "1px solid var(--red)", borderRadius: "var(--radius-lg)", maxWidth: "420px" }}>
          <DialogHeader>
            <DialogTitle style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: "var(--text)", fontWeight: 600 }}>
              Delete artifact
            </DialogTitle>
            <DialogDescription style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)", marginTop: "6px" }}>
              Permanently delete <strong style={{ color: "var(--text)" }}>{artifact.name || artifact.id}</strong>?
              If this is the only version, the model entry will also be removed.
            </DialogDescription>
          </DialogHeader>
          {deleteError && (
            <p style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--red)", margin: 0 }}>
              {deleteError}
            </p>
          )}
          <DialogFooter style={{ gap: "8px", justifyContent: "flex-end" }}>
            <button
              onClick={handleCancel}
              disabled={isPending}
              style={{
                background: "none", border: "1px solid var(--border)", borderRadius: "var(--radius)",
                color: "var(--text-muted)", cursor: "pointer",
                fontFamily: "var(--font-mono)", fontSize: "11px", padding: "4px 12px",
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={isPending}
              style={{
                background: "var(--red)", border: "none", borderRadius: "var(--radius)",
                color: "#fff", cursor: isPending ? "not-allowed" : "pointer",
                fontFamily: "var(--font-mono)", fontSize: "11px", padding: "4px 12px",
              }}
            >
              {isPending ? "Deleting…" : "Confirm delete"}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
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
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "16px", marginBottom: "24px" }}>
        <ViewHeader
          title="Artifact"
          titleEmphasis="list"
          subtitle="All registered artifacts. Filter by tag or framework."
        />
        {data && data.items.length > 0 && (
          <ExportMenu
            onCsv={() => exportCsv(
              data.items.map((a) => ({ id: a.id, name: a.name ?? "", framework: a.framework, objective: a.objective, num_trees: a.num_trees, num_features: a.num_features, extracted_at: a.extracted_at })),
              "artifacts"
            )}
          />
        )}
      </div>

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
