import { Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { Home } from "./views/Home";
import { Overview } from "./views/Overview";
import { Importance } from "./views/Importance";
import { Trees } from "./views/Trees";
import { Data } from "./views/Data";
import { Explanations } from "./views/Explanations";
import { Evaluation } from "./views/Evaluation";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Home />} />
        <Route path="/artifacts/:id/overview" element={<Overview />} />
        <Route path="/artifacts/:id/importance" element={<Importance />} />
        <Route path="/artifacts/:id/trees" element={<Trees />} />
        <Route path="/artifacts/:id/data" element={<Data />} />
        <Route path="/artifacts/:id/explanations" element={<Explanations />} />
        <Route path="/artifacts/:id/evaluation" element={<Evaluation />} />
        <Route
          path="*"
          element={
            <div className="flex items-center justify-center h-full text-text-muted font-mono text-sm">
              404 — page not found
            </div>
          }
        />
      </Route>
    </Routes>
  );
}
