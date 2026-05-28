import { useParams } from "react-router-dom";
import { ViewHeader } from "../components/layout/ViewHeader";
import { useArtifact } from "../lib/api/queries";

function StatTile({
  label,
  value,
  meta,
  emphasis = false,
}: {
  label: string;
  value: string;
  meta: string;
  emphasis?: boolean;
}) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-value">
        {emphasis ? <em>{value}</em> : value}
      </div>
      <div className="stat-meta">{meta}</div>
    </div>
  );
}

function monoTonicityLabel(n: number): string {
  if (n === 1) return "mono+";
  if (n === -1) return "mono-";
  return "—";
}

export function Overview() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading, isError, error } = useArtifact(id ?? "placeholder");

  if (isLoading) {
    return (
      <section className="view">
        <ViewHeader
          title="Model"
          titleEmphasis="overview"
          subtitle="Loading artifact…"
        />
        <div className="text-text-muted font-mono text-sm p-8 text-center">
          Fetching canonical artifact from API…
        </div>
      </section>
    );
  }

  if (isError || !data?.data) {
    const status = error?.message?.includes?.("404") ? 404 : undefined;
    return (
      <section className="view">
        <ViewHeader
          title="Model"
          titleEmphasis="overview"
          subtitle={status === 404 ? "Artifact not found." : "Failed to load artifact."}
        />
        <div className="p-8 rounded-lg border border-red bg-bg-elev text-text-muted font-mono text-sm">
          {status === 404
            ? "The requested artifact could not be found. Check the artifact ID and try again."
            : `An error occurred while loading the artifact. ${error?.message ?? ""}`}
        </div>
      </section>
    );
  }

  const artifact = data.data;
  const { model } = artifact;
  const feat = model.feature_schema;
  const params = model.params as Record<string, number | string | boolean | null>;

  return (
    <section className="view">
      <ViewHeader
        title="Model"
        titleEmphasis="overview"
        subtitle="Everything Cerebro pulled from the artifact at extraction time. Source of truth for every panel that follows — no live model required."
      >
        <button className="btn" disabled>Copy artifact path</button>
        <button className="btn" disabled>Diff vs previous</button>
      </ViewHeader>

      {/* Stat tiles */}
      <div className="grid grid-4 mb-4">
        <StatTile
          label="Objective"
          value={model.objective}
          meta={`classification · ${typeof params?.metric === "string" ? params.metric : "log_loss"}`}
          emphasis
        />
        <StatTile
          label="Trees"
          value={String(model.num_iteration)}
          meta="avg depth — · max —"
        />
        <StatTile
          label="Features"
          value={String(feat.names.length)}
          meta="— categorical · — numeric"
        />
        <StatTile
          label="Test AUC"
          value="—"
          meta="no samples at extraction time"
        />
      </div>

      <div className="grid grid-2">
        {/* Training params */}
        <div className="panel">
          <div className="panel-header">
            <h3 className="panel-title">Training parameters</h3>
            <span className="panel-subtitle">params</span>
          </div>
          <dl className="kv">
            {Object.entries(params).map(([key, value]) => (
              <div key={key} style={{ display: "contents" }}>
                <dt>{key}</dt>
                <dd className="tnum">
                  <span className="accent">{String(value)}</span>
                </dd>
              </div>
            ))}
          </dl>
        </div>

        {/* Feature schema */}
        <div className="panel">
          <div className="panel-header">
            <h3 className="panel-title">Feature schema</h3>
            <span className="panel-subtitle">{feat.names.length} features</span>
          </div>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "6px",
              maxHeight: "360px",
              overflowY: "auto",
            }}
          >
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "28px 1fr 80px 70px",
                gap: "10px",
                fontFamily: "var(--font-mono)",
                fontSize: "11px",
                color: "var(--text-dim)",
                paddingBottom: "6px",
                borderBottom: "1px solid var(--border)",
                marginBottom: "4px",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
              }}
            >
              <span>idx</span>
              <span>name</span>
              <span>type</span>
              <span>const</span>
            </div>

            {feat.names.map((name, i) => {
              const isCategorical = feat.categorical_indices.includes(i);
              const mono = feat.monotone_constraints[i] ?? 0;
              return (
                <div
                  key={i}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "28px 1fr 80px 70px",
                    gap: "10px",
                    fontFamily: "var(--font-mono)",
                    fontSize: "12px",
                    color: "var(--text)",
                    padding: "3px 0",
                  }}
                >
                  <span style={{ color: "var(--text-dim)" }}>
                    {String(i).padStart(2, "0")}
                  </span>
                  <span>{name}</span>
                  <span
                    style={{
                      color: isCategorical ? "var(--purple)" : "var(--blue)",
                    }}
                  >
                    {isCategorical ? "categorical" : "numeric"}
                  </span>
                  <span
                    style={{
                      color: mono !== 0 ? "var(--accent)" : "var(--text-dim)",
                    }}
                  >
                    {monoTonicityLabel(mono)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
