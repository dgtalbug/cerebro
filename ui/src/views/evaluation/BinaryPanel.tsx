import { useMemo } from "react";
import { LineChart, LineSeries, LinearXAxis, LinearYAxis, LinearXAxisTickSeries, LinearYAxisTickSeries } from "reaviz";
import type { ChartShallowDataShape } from "reaviz";
import type { BinaryEval } from "../../lib/api/queries";
import { useAccentColor } from "../../lib/tokenColors";

function MetricBadge({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ textAlign: "center", padding: "12px 16px", background: "var(--bg-elev)", borderRadius: "var(--radius)" }}>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-muted)", marginBottom: "4px" }}>{label}</div>
      <div style={{ fontFamily: "var(--font-display)", fontSize: "22px" }}>{value}</div>
    </div>
  );
}

function ConfusionMatrix({ ev }: { ev: BinaryEval }) {
  const total = ev.confusion_matrix.reduce((s, c) => s + c.count, 0);
  const get = (actual: number, predicted: number) => {
    const cell = ev.confusion_matrix.find(c => c.actual === actual && c.predicted === predicted);
    const count = cell?.count ?? 0;
    const pct = total > 0 ? ((count / total) * 100).toFixed(1) + "%" : "0.0%";
    const isMatch = actual === predicted;
    const isPositive = actual === 1;
    const cls = isMatch && isPositive ? "tp" : isMatch ? "tn" : isPositive ? "fn" : "fp";
    return { count, pct, cls };
  };
  const [tn, fp] = [get(0, 0), get(0, 1)];
  const [fn, tp] = [get(1, 0), get(1, 1)];
  return (
    <div className="cm">
      <div />
      <div className="cm-axis-x">pred: 0</div>
      <div className="cm-axis-x">pred: 1</div>
      <div className="cm-axis-y">actual: 0</div>
      <div className={`cm-cell ${tn.cls}`}><span className="cm-num tnum">{tn.count}</span><span className="cm-pct">{tn.pct}</span></div>
      <div className={`cm-cell ${fp.cls}`}><span className="cm-num tnum">{fp.count}</span><span className="cm-pct">{fp.pct}</span></div>
      <div className="cm-axis-y">actual: 1</div>
      <div className={`cm-cell ${fn.cls}`}><span className="cm-num tnum">{fn.count}</span><span className="cm-pct">{fn.pct}</span></div>
      <div className={`cm-cell ${tp.cls}`}><span className="cm-num tnum">{tp.count}</span><span className="cm-pct">{tp.pct}</span></div>
    </div>
  );
}

export default function BinaryPanel({ eval: ev }: { eval: BinaryEval }) {
  const accentColor = useAccentColor();
  const rocData = useMemo<ChartShallowDataShape[]>(() =>
    ev.roc_curve.map(p => ({ key: p.fpr, data: p.tpr })),
    [ev.roc_curve]
  );

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
      <div className="panel">
        <div className="panel-header">
          <h3 className="panel-title">ROC curve</h3>
          <span className="panel-subtitle">AUC = {ev.auc.toFixed(3)}</span>
        </div>
        <div style={{ marginBottom: "16px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "8px", marginBottom: "16px" }}>
            <MetricBadge label="Precision" value={ev.precision.toFixed(3)} />
            <MetricBadge label="Recall" value={ev.recall.toFixed(3)} />
            <MetricBadge label="F1" value={ev.f1.toFixed(3)} />
          </div>
          {rocData.length > 1 && (
            <LineChart
              height={200}
              width={280}
              data={rocData}
              series={<LineSeries colorScheme={[accentColor]} interpolation="linear" />}
              xAxis={<LinearXAxis type="value" tickSeries={<LinearXAxisTickSeries label={null} />} />}
              yAxis={<LinearYAxis type="value" tickSeries={<LinearYAxisTickSeries label={null} />} />}
            />
          )}
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">
          <h3 className="panel-title">Confusion matrix</h3>
          <span className="panel-subtitle">threshold = {ev.threshold.toFixed(2)}</span>
        </div>
        <ConfusionMatrix ev={ev} />
      </div>
    </div>
  );
}
