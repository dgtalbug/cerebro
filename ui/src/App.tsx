import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { Overview } from "./views/Overview";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/artifacts/placeholder/overview" replace />} />
        <Route path="/artifacts/:id/overview" element={<Overview />} />
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
