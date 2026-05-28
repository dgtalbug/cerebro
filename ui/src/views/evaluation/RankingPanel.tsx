import { useMemo } from "react";
import { BarChart, BarSeries, LinearXAxis, LinearYAxis } from "reaviz";
import type { ChartShallowDataShape } from "reaviz";
import type { RankingEval } from "../../lib/api/queries";

const COPPER = "#b87333";
const ACCENT_COLOR = "var(--accent)";
const HIGHLIGHT_K = 10;

export default function RankingPanel({ eval: ev }: { eval: RankingEval }) {
  const ndcgData = useMemo<ChartShallowDataShape[]>(() =>
    ev.ndcg_at_k.map(n => ({ key: `@${n.k}`, data: n.value })),
    [ev.ndcg_at_k]
  );

  const perQueryData = useMemo<ChartShallowDataShape[]>(() =>
    ev.per_query_ndcg.map((v, i) => ({ key: String(i + 1), data: v })),
    [ev.per_query_ndcg]
  );

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
      <div className="panel">
        <div className="panel-header">
          <h3 className="panel-title">nDCG@k</h3>
          <span className="panel-subtitle">MAP = {ev.mean_average_precision.toFixed(4)}</span>
        </div>
        {ndcgData.length > 0 && (
          <BarChart
            height={180}
            width={240}
            data={ndcgData}
            series={
              <BarSeries
                colorScheme={ndcgData.map(d =>
                  d.key === `@${HIGHLIGHT_K}` ? COPPER : ACCENT_COLOR
                )}
              />
            }
            xAxis={<LinearXAxis type="category" />}
            yAxis={<LinearYAxis domain={[0, 1]} />}
          />
        )}
      </div>

      <div className="panel">
        <div className="panel-header">
          <h3 className="panel-title">Per-query nDCG@10</h3>
          <span className="panel-subtitle">{ev.per_query_ndcg.length} queries</span>
        </div>
        {perQueryData.length > 0 && (
          <BarChart
            height={180}
            width={240}
            data={perQueryData}
            series={<BarSeries colorScheme={[COPPER]} />}
            xAxis={<LinearXAxis type="category" />}
            yAxis={<LinearYAxis domain={[0, 1]} />}
          />
        )}
      </div>
    </div>
  );
}
