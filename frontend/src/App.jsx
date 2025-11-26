// frontend/src/App.jsx
import React, { useState } from "react";
import FamiliesPage from "./components/FamiliesPage.jsx";
import AnalyticsPage from "./components/AnalyticsPage.jsx";
import UsersPage from "./components/UsersPage.jsx";
import LoginPanel from "./components/LoginPanel.jsx";

function App() {
  const [page, setPage] = useState("analytics");

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-800 px-6 py-4 flex items-center justify-between bg-slate-950/80 backdrop-blur">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-semibold">Test Capacity Analytics</h1>
          <nav className="flex gap-4 text-sm">
            <button
              className={page === "analytics" ? "font-semibold underline" : ""}
              onClick={() => setPage("analytics")}
            >
              Analytics
            </button>
            <button
              className={page === "families" ? "font-semibold underline" : ""}
              onClick={() => setPage("families")}
            >
              Families
            </button>
            <button
              className={page === "users" ? "font-semibold underline" : ""}
              onClick={() => setPage("users")}
            >
              Users
            </button>
          </nav>
        </div>
        <LoginPanel />
      </header>
      <main className="flex-1 p-6">
        {page === "analytics" && <AnalyticsPage />}
        {page === "families" && <FamiliesPage />}
        {page === "users" && <UsersPage />}
      </main>
    </div>
  );
}

export default App;
