import { Navigate, Route, Routes, useParams } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { Agent } from "./views/Agent";
import { Ingest } from "./views/Ingest";
import { ModelDetail } from "./views/ModelDetail";
import { Overview } from "./views/Overview";
import { Importance } from "./views/Importance";
import { Trees } from "./views/Trees";
import { Data } from "./views/Data";
import { Explanations } from "./views/Explanations";
import { Evaluation } from "./views/Evaluation";
import { Registry } from "./views/Registry";
import { useModelVersions } from "./lib/api/queries";

function VersionRedirect() {
  const { id, version } = useParams<{ id: string; version: string }>();
  const { data: versions } = useModelVersions(id ?? "");
  const v = versions?.find((ver) => String(ver.version) === version);
  if (!v) {
    return (
      <div className="flex items-center justify-center h-full text-text-muted font-mono text-sm">
        Version not found
      </div>
    );
  }
  return <Navigate to={`/artifacts/${v.artifact_id}/overview`} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Registry />} />
        <Route path="/ingest" element={<Ingest />} />
        <Route path="/models/:id" element={<ModelDetail />} />
        <Route path="/models/:id/versions/:version" element={<VersionRedirect />} />
        <Route path="/artifacts/:id/overview" element={<Overview />} />
        <Route path="/artifacts/:id/importance" element={<Importance />} />
        <Route path="/artifacts/:id/trees" element={<Trees />} />
        <Route path="/artifacts/:id/data" element={<Data />} />
        <Route path="/artifacts/:id/explanations" element={<Explanations />} />
        <Route path="/artifacts/:id/evaluation" element={<Evaluation />} />
        <Route path="/artifacts/:id/agent" element={<Agent />} />
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
