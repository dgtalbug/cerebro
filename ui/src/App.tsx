import { Overview } from "./views/Overview";

// Layout shell placeholder. The TopBar/Sidebar/ViewHeader shell and the seven
// views are added as the dashboard is built.
export default function App() {
  return (
    <main className="min-h-screen p-8 font-mono">
      <h1 className="text-2xl">Cerebro</h1>
      <p className="text-foreground/70">Model introspection.</p>
      <Overview />
    </main>
  );
}
