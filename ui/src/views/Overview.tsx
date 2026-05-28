import { ViewHeader } from "../components/layout/ViewHeader";

export function Overview() {
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

      <div className="text-text-muted font-mono text-sm p-8 rounded-lg border border-border bg-bg-elev">
        Overview data renders here (Task 7).
      </div>
    </section>
  );
}
