import { useState } from "react";
import { useParams } from "react-router-dom";
import { ViewHeader } from "../components/layout/ViewHeader";
import { DivergenceCallout } from "../components/importance/DivergenceCallout";
import { useImportance, useDiagnostics, type ImportanceType } from "../lib/api/queries";

const TABS: { key: ImportanceType; label: string }[] = [
  { key: "gain", label: "gain" },
  { key: "split", label: "split" },
  { key: "permutation", label: "permutation" },
];

function FeatureBar({ name, value, max }: { name: string; value: number; max: number }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="fi-row">
      <span className="fi-name">{name}</span>
      <div className="fi-bar-wrap">
        <div className="fi-bar" style={{ width: `${pct}%` }} />
      </div>
      <span className="fi-value tnum">
        {value.toFixed(2)}
      </span>
    </div>
  );
}

function DivergenceBar({
  name,
  gainRank,
  permRank,
}: {
  name: string;
  gainRank: number;
  permRank: number;
}) {
  const delta = gainRank - permRank;
  const isDivergent = Math.abs(delta) > 5;
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 60px 60px 50px",
        gap: "8px",
        alignItems: "center",
        padding: "5px 0",
        borderBottom: "1px solid var(--border)",
        fontSize: "12px",
        fontFamily: "var(--font-mono)",
      }}
    >
      <span style={{ fontFamily: "var(--font-body)", fontSize: "13px" }}>{name}</span>
      <span style={{ color: "var(--text-muted)" }}>#{gainRank}</span>
      <span style={{ color: "var(--text-muted)" }}>#{permRank}</span>
      <span
        style={{
          color: isDivergent ? "var(--red)" : "var(--green)",
          fontWeight: isDivergent ? 600 : 400,
        }}
      >
        {delta > 0 ? "+" : ""}{delta}
      </span>
    </div>
  );
}

function UnnamedFeaturesNotice() {
  return (
    <div
      style={{
        padding: "8px 12px",
        marginBottom: "12px",
        borderRadius: "6px",
        background: "var(--bg-elev-2)",
        border: "1px solid var(--border)",
        fontSize: "11px",
        fontFamily: "var(--font-mono)",
        color: "var(--text-dim)",
      }}
    >
      Feature names were not set at training time — showing auto-generated column IDs.
      Pass a named DataFrame or set <code>feature_name=</code> in LightGBM to fix this.
    </div>
  );
}

function ImportancePanel({ id, type }: { id: string; type: ImportanceType }) {
  const { data, isLoading, isError } = useImportance(id, type);

  if (isLoading) {
    return (
      <div
        style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)", fontSize: "12px" }}
      >
        Loading…
      </div>
    );
  }
  if (isError || !data) {
    return (
      <div style={{ color: "var(--red)", fontSize: "12px" }}>
        Failed to load importance data.
      </div>
    );
  }
  if (data.detail) {
    return (
      <div
        style={{
          color: "var(--text-dim)",
          fontFamily: "var(--font-mono)",
          fontSize: "12px",
          padding: "24px 0",
        }}
      >
        {data.detail}
      </div>
    );
  }

  const isUnnamed = data.features.length > 0 && data.features.every((f) => /^Column_\d+$/.test(f.name));
  const max = Math.max(...data.features.map((f) => f.value), 0);
  return (
    <div>
      {isUnnamed && <UnnamedFeaturesNotice />}
      {data.features.map((f) => (
        <FeatureBar key={f.name} name={f.name} value={f.value} max={max} />
      ))}
      {data.divergence_warnings && data.divergence_warnings.length > 0 && (
        <DivergenceCallout warnings={data.divergence_warnings} />
      )}
    </div>
  );
}

function GainVsPermPanel({ id }: { id: string }) {
  const gain = useImportance(id, "gain");
  const perm = useImportance(id, "permutation");

  if (gain.isLoading || perm.isLoading) {
    return (
      <div style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)", fontSize: "12px" }}>
        Loading…
      </div>
    );
  }

  const gainFeatures = gain.data?.features ?? [];
  const permFeatures = perm.data?.features ?? [];

  if (permFeatures.length === 0 || perm.data?.detail) {
    return (
      <div
        style={{
          color: "var(--text-dim)",
          fontFamily: "var(--font-mono)",
          fontSize: "12px",
          padding: "16px 0",
        }}
      >
        Permutation importance not computed — provide evaluation samples at extraction time to
        enable rank comparison.
      </div>
    );
  }

  const gainRankMap = Object.fromEntries(gainFeatures.map((f, i) => [f.name, i + 1]));
  const permRankMap = Object.fromEntries(permFeatures.map((f, i) => [f.name, i + 1]));
  const names = gainFeatures.map((f) => f.name);

  const warnings = perm.data?.divergence_warnings ?? [];

  return (
    <div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 60px 60px 50px",
          gap: "8px",
          padding: "4px 0 8px",
          borderBottom: "1px solid var(--border)",
          fontSize: "10px",
          fontFamily: "var(--font-mono)",
          color: "var(--text-dim)",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
        }}
      >
        <span>feature</span>
        <span>gain</span>
        <span>perm</span>
        <span>Δ rank</span>
      </div>
      {names.map((name) => (
        <DivergenceBar
          key={name}
          name={name}
          gainRank={gainRankMap[name] ?? 0}
          permRank={permRankMap[name] ?? 0}
        />
      ))}
      {warnings.length > 0 && <DivergenceCallout warnings={warnings} />}
    </div>
  );
}

export function Importance() {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState<ImportanceType>("gain");
  const artifactId = id ?? "placeholder";

  return (
    <section className="view">
      <ViewHeader
        title="Feature"
        titleEmphasis="importance"
        subtitle="Built-in LightGBM importance plus permutation importance computed on the held-out evaluation set."
      />

      <div className="grid grid-2" style={{ alignItems: "start" }}>
        {/* Left panel — aggregate importance */}
        <div className="panel">
          <div className="panel-header">
            <h3 className="panel-title">Aggregate importance</h3>
            <div className="panel-tabs">
              {TABS.map((tab) => (
                <button
                  key={tab.key}
                  data-testid={`tab-${tab.key}`}
                  onClick={() => setActiveTab(tab.key)}
                  className={`panel-tab${activeTab === tab.key ? " active" : ""}`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
          <div className="fi-list">
            <ImportancePanel id={artifactId} type={activeTab} />
          </div>
        </div>

        {/* Right panel — gain vs permutation */}
        <div className="panel">
          <div className="panel-header">
            <h3 className="panel-title">Gain vs permutation</h3>
            <span className="panel-subtitle">divergence</span>
          </div>
          <GainVsPermPanel id={artifactId} />
        </div>
      </div>

      {/* Interaction heatmap */}
      <InteractionHeatmap id={artifactId} />

      {/* Recommendations panel */}
      <RecommendationsPanel id={artifactId} />
    </section>
  );
}

function RecommendationsPanel({ id }: { id: string }) {
  const { data, isLoading } = useDiagnostics(id);

  if (isLoading) return null;

  if (!data) {
    return (
      <div className="panel" style={{ marginTop: "16px" }}>
        <div className="panel-header">
          <h3 className="panel-title">Recommendations</h3>
        </div>
        <p style={{ fontSize: "13px", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
          No diagnostics available. Run{" "}
          <code style={{ color: "var(--accent)" }}>cerebro diagnostics --persist</code>{" "}
          to compute feature recommendations.
        </p>
      </div>
    );
  }

  const { recommendations, notes } = data;

  return (
    <div className="panel" style={{ marginTop: "16px" }}>
      <div className="panel-header">
        <h3 className="panel-title">Recommendations</h3>
        <span className="panel-subtitle">{recommendations.length} suggestions</span>
      </div>
      {notes.length > 0 && (
        <div style={{ marginBottom: "12px" }}>
          {notes.map((n, i) => (
            <p key={i} style={{ fontSize: "11px", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
              note: {n}
            </p>
          ))}
        </div>
      )}
      {recommendations.length === 0 ? (
        <p style={{ fontSize: "13px", color: "var(--text-dim)" }}>No recommendations.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          {recommendations.map((r, i) => (
            <div
              key={i}
              style={{
                display: "grid",
                gridTemplateColumns: "80px 160px 1fr 80px",
                gap: "12px",
                alignItems: "start",
                padding: "8px 0",
                borderBottom: "1px solid var(--border)",
                fontSize: "12px",
                fontFamily: "var(--font-mono)",
              }}
            >
              <span
                style={{
                  color: r.impact_estimate === "high" ? "var(--red)"
                    : r.impact_estimate === "medium" ? "var(--amber)"
                    : "var(--text-dim)",
                  fontWeight: 600,
                  textTransform: "uppercase",
                  fontSize: "10px",
                  letterSpacing: "0.08em",
                }}
              >
                {r.kind.replace(/_/g, " ")}
              </span>
              <span style={{ color: "var(--accent)" }}>{r.feature}</span>
              <span style={{ color: "var(--text-muted)", fontFamily: "var(--font-body)" }}>{r.reason}</span>
              <span style={{ color: "var(--text-dim)", fontSize: "10px" }}>{r.impact_estimate}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function InteractionHeatmap({ id }: { id: string }) {
  const { data } = useDiagnostics(id);
  if (!data || data.interactions.length === 0) return null;

  const TOP = 12;
  const top = data.interactions.slice(0, TOP);
  const features = Array.from(
    new Set(top.flatMap((s) => [s.feature_a, s.feature_b]))
  ).slice(0, TOP);
  const n = features.length;

  const scoreMap = new Map<string, number>();
  for (const s of top) {
    scoreMap.set(`${s.feature_a}:${s.feature_b}`, s.score);
    scoreMap.set(`${s.feature_b}:${s.feature_a}`, s.score);
  }

  return (
    <div className="panel" style={{ marginTop: "16px" }}>
      <div className="panel-header">
        <h3 className="panel-title">Interaction strength</h3>
        <span className="panel-subtitle">co-occurrence in tree paths</span>
      </div>
      <div style={{ overflowX: "auto" }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: `80px repeat(${n}, 28px)`,
            gap: "2px",
            fontSize: "10px",
            fontFamily: "var(--font-mono)",
          }}
        >
          <div />
          {features.map((f) => (
            <div
              key={f}
              title={f}
              style={{
                writingMode: "vertical-rl",
                transform: "rotate(180deg)",
                color: "var(--text-dim)",
                fontSize: "9px",
                overflow: "hidden",
                textOverflow: "ellipsis",
                maxHeight: "64px",
              }}
            >
              {f}
            </div>
          ))}
          {features.map((fa) => (
            <>
              <div
                key={`row-${fa}`}
                style={{
                  color: "var(--text-dim)",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                  alignSelf: "center",
                }}
                title={fa}
              >
                {fa}
              </div>
              {features.map((fb) => {
                const score = fa === fb ? 1 : (scoreMap.get(`${fa}:${fb}`) ?? 0);
                const alpha = fa === fb ? 0.15 : score * 0.8;
                return (
                  <div
                    key={`${fa}:${fb}`}
                    title={`${fa} × ${fb}: ${score.toFixed(3)}`}
                    style={{
                      width: "28px",
                      height: "28px",
                      background: `rgba(212, 165, 116, ${alpha})`,
                      borderRadius: "2px",
                      border: "1px solid var(--border)",
                    }}
                  />
                );
              })}
            </>
          ))}
        </div>
      </div>
    </div>
  );
}
