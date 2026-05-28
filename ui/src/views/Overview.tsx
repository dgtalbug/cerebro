import { API_URL } from "../lib/api/queries";

// Placeholder view. This fetches via a query hook (never `fetch` directly —
// the eslint boundaries rule enforces that in src/views/**).
export function Overview() {
  return (
    <section className="mt-6 rounded border border-border p-4">
      <h2 className="text-lg">Overview</h2>
      <p className="text-foreground/60">API target: {API_URL}</p>
    </section>
  );
}
