import { useState } from "react";
import type { PageId } from "./constants/riskColors";
import AlertPanel from "./components/AlertPanel";
import NavBar from "./components/NavBar";
import DashboardPage from "./pages/DashboardPage";
import IncidentsPage from "./pages/IncidentsPage";
import SafetyMapPage from "./pages/SafetyMapPage";

export default function App() {
  const [page, setPage] = useState<PageId>("dashboard");

  return (
    <main className="app">
      <header className="app-header">
        <div>
          <h1>PRISM</h1>
          <p>Predictive Risk &amp; Incident Safety Management System</p>
        </div>
        <NavBar current={page} onNavigate={setPage} />
      </header>

      <AlertPanel compact />

      {page === "dashboard" && <DashboardPage />}
      {page === "map" && <SafetyMapPage />}
      {page === "incidents" && <IncidentsPage />}
    </main>
  );
}
