import { Outlet } from "react-router-dom";
import { TopBar } from "./TopBar";
import { Sidebar } from "./Sidebar";

export function AppShell() {
  return (
    <div className="app">
      <TopBar />
      <Sidebar />
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
