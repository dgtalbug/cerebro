import { useMemo } from "react";
import { BarChart, BarSeries, LinearXAxis, LinearYAxis } from "reaviz";
import type { ChartShallowDataShape } from "reaviz";
import type { RegressionEval } from "../../lib/api/queries";

const COPPER = "#b87333";

function MetricBadge({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ textAlign: "center", padding: "10px 14px", background: "var(--bg-elev)", borderRadius: "6px" }}>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-muted)", marginBottom: "4px" }}>{label}</div>
      <div style={{ fontFamily: "var(--font-display)", fontSize: "20px" }}>{value}</div>
    </div>
  );
}

export default function RegressionPanel({ eval: ev }: { eval: RegressionEval }) {
  const histData = useMemo<ChartShallowDataShape[]>(() =>
    ev.residuals_histogram.map(bin => ({
      key: bin.lower.toFixed(2),
      data: bin.count,
    })),
    [ev.residuals_histogram]
  );

  const scatterData = useMemo<ChartShallowDataShape[]>(() =>
    ev.scatter.map(p => ({ key: p.predicted, data: p.actual })),
    [ev.scatter]
  );

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "8px", marginBottom: "24px" }}>
        <MetricBadge label="RMSE" value={ev.rmse.toFixed(4)} />
        <MetricBadge label="MAE" value={ev.mae.toFixed(4)} />
        <MetricBadge label="R²" value={ev.r2.toFixed(4)} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
        <div className="panel">
          <div className="panel-header">
            <h3 className="panel-title">Residuals histogram</h3>
            <span className="panel-subtitle">actual − predicted</span>
          </div>
          {histData.length > 0 && (
            <BarChart
              height={200}
              width={280}
              data={histData}
              series={<BarSeries colorScheme={[COPPER]} />}
              xAxis={<LinearXAxis type="category" />}
              yAxis={<LinearYAxis />}
            />
          )}
        </div>

        <div className="panel">
          <div className="panel-header">
            <h3 className="panel-title">Predicted vs actual</h3>
            <span className="panel-subtitle">5th–95th interval band</span>
          </div>
          {scatterData.length > 0 && (
            <BarChart
              height={200}
              width={280}
              data={scatterData}
              series={<BarSeries colorScheme={[COPPER]} />}
              xAxis={<LinearXAxis type="value" />}
              yAxis={<LinearYAxis />}
            />
          )}
        </div>
      </div>
    </div>
  );
}
