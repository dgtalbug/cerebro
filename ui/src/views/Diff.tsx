import { useParams } from "react-router-dom";
import { ViewHeader } from "../components/layout/ViewHeader";
import { useDiff } from "../lib/api/queries";

export function Diff() {
  const { id: artifactId = "", compareId = "" } = useParams<{ id: string; compareId: string }>();

  const { data, isLoading, isError } = useDiff(artifactId, compareId);

  return (
    <section className="view">
      <ViewHeader
        title="Artifact"
        titleEmphasis="diff"
        subtitle={`Comparing ${artifactId} → ${compareId}`}
      />

      {isLoading && (
        <p style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)", fontSize: "12px" }}>
          Computing diff…
        </p>
      )}
      {isError && (
        <p style={{ color: "var(--red)", fontSize: "12px" }}>Failed to load diff.</p>
      )}
      {data && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Summary row */}
          <div className="grid grid-4">
            <StatTile label="Objective A" value={data.objective_a} />
            <StatTile label="Objective B" value={data.objective_b} />
            <StatTile label="Framework A" value={data.framework_a} />
            <StatTile label="Tree Δ" value={data.tree_count_delta >= 0 ? `+${data.tree_count_delta}` : String(data.tree_count_delta)} />
          </div>

          {/* Feature schema diff */}
          {(data.feature_schema_diff.added.length > 0 || data.feature_schema_diff.removed.length > 0) && (
            <div className="panel">
              <div className="panel-header">
                <h3 className="panel-title">Feature schema changes</h3>
              </div>
              {data.feature_schema_diff.added.length > 0 && (
                <div style={{ marginBottom: "8px" }}>
                  <span style={{ color: "var(--green)", fontSize: "11px", fontFamily: "var(--font-mono)" }}>
                    + Added: {data.feature_schema_diff.added.join(", ")}
                  </span>
                </div>
              )}
              {data.feature_schema_diff.removed.length > 0 && (
                <div>
                  <span style={{ color: "var(--red)", fontSize: "11px", fontFamily: "var(--font-mono)" }}>
                    − Removed: {data.feature_schema_diff.removed.join(", ")}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Importance deltas */}
          <div className="panel">
            <div className="panel-header">
              <h3 className="panel-title">Importance deltas</h3>
              <span className="panel-subtitle">gain Δ (top 20)</span>
            </div>
            <ImportanceDeltaTable deltas={data.importance_deltas.slice(0, 20)} />
          </div>

          {/* Metric deltas */}
          {data.metric_deltas.length > 0 && (
            <div className="panel">
              <div className="panel-header">
                <h3 className="panel-title">Metric deltas</h3>
              </div>
              <MetricDeltaTable deltas={data.metric_deltas} />
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat">
      <span className="stat-label">{label}</span>
      <span style={{ fontFamily: "var(--font-mono)", fontSize: "14px", color: "var(--text)" }}>{value}</span>
    </div>
  );
}

function ImportanceDeltaTable({ deltas }: { deltas: import("../lib/api/queries").ImportanceDelta[] }) {
  const maxAbs = Math.max(...deltas.map((d) => Math.abs(d.gain_delta)), 0.001);
  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 100px 80px", gap: "8px", padding: "4px 0 8px", borderBottom: "1px solid var(--border)", fontSize: "10px", fontFamily: "var(--font-mono)", color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
        <span>feature</span><span>gain Δ bar</span><span>Δ value</span>
      </div>
      {deltas.map((d) => {
        const pct = (Math.abs(d.gain_delta) / maxAbs) * 100;
        const isPos = d.gain_delta >= 0;
        return (
          <div key={d.feature} style={{ display: "grid", gridTemplateColumns: "1fr 100px 80px", gap: "8px", alignItems: "center", padding: "5px 0", borderBottom: "1px solid var(--border)", fontSize: "12px", fontFamily: "var(--font-mono)" }}>
            <span style={{ color: "var(--text)" }}>{d.feature}</span>
            <div style={{ height: "6px", background: "var(--bg)", borderRadius: "2px", overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${pct}%`, background: isPos ? "var(--green)" : "var(--red)", borderRadius: "2px" }} />
            </div>
            <span style={{ color: isPos ? "var(--green)" : "var(--red)", textAlign: "right" }}>
              {isPos ? "+" : ""}{d.gain_delta.toFixed(4)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function MetricDeltaTable({ deltas }: { deltas: import("../lib/api/queries").MetricDelta[] }) {
  return (
    <div>
      {deltas.map((m) => {
        const isPos = m.delta >= 0;
        return (
          <div key={m.metric} style={{ display: "grid", gridTemplateColumns: "120px 80px 80px 80px", gap: "12px", alignItems: "center", padding: "6px 0", borderBottom: "1px solid var(--border)", fontSize: "12px", fontFamily: "var(--font-mono)" }}>
            <span style={{ color: "var(--text-dim)", textTransform: "uppercase", fontSize: "10px", letterSpacing: "0.08em" }}>{m.metric}</span>
            <span style={{ color: "var(--text-muted)" }}>{m.value_a.toFixed(4)}</span>
            <span style={{ color: "var(--text)" }}>{m.value_b.toFixed(4)}</span>
            <span style={{ color: isPos ? "var(--green)" : "var(--red)", fontWeight: 600 }}>
              {isPos ? "+" : ""}{m.delta.toFixed(4)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
