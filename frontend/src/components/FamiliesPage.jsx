import React, { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

function FamiliesPage() {
  const [families, setFamilies] = useState([]);
  const [name, setName] = useState("");
  const [ctHours, setCtHours] = useState("10");

  const token = localStorage.getItem("access_token");

  async function loadFamilies() {
    try {
      const res = await fetch(`${API_BASE}/families`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) return;
      const data = await res.json();
      setFamilies(data);
    } catch (err) {
      console.error(err);
    }
  }

  useEffect(() => {
    if (token) {
      loadFamilies();
    }
  }, [token]);

  async function handleCreate(e) {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/families`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name,
          test_cycle_time_hours: parseFloat(ctHours),
        }),
      });
      if (!res.ok) {
        console.error("Failed to create family");
        return;
      }
      setName("");
      setCtHours("10");
      loadFamilies();
    } catch (err) {
      console.error(err);
    }
  }

  if (!token) {
    return <p className="text-sm text-slate-400">Please log in using the API first to manage families.</p>;
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[2fr,3fr]">
      <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4">
        <h2 className="text-lg font-semibold mb-4">Create Family</h2>
        <form onSubmit={handleCreate} className="space-y-3 text-sm">
          <div>
            <label className="block mb-1">Name</label>
            <input
              className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Juniper A3"
              required
            />
          </div>
          <div>
            <label className="block mb-1">Test cycle time (hours)</label>
            <input
              type="number"
              min="0"
              step="0.1"
              className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2"
              value={ctHours}
              onChange={(e) => setCtHours(e.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            className="mt-2 inline-flex items-center justify-center rounded-lg bg-emerald-500 hover:bg-emerald-400 px-4 py-2 text-sm font-medium text-slate-950"
          >
            Save family
          </button>
        </form>
      </section>
      <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4">
        <h2 className="text-lg font-semibold mb-4">Existing families</h2>
        {families.length === 0 ? (
          <p className="text-sm text-slate-400">No families yet.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {families.map((f) => (
              <li
                key={f.id}
                className="flex items-center justify-between rounded-lg border border-slate-800 px-3 py-2 bg-slate-950/40"
              >
                <div>
                  <p className="text-slate-400">
                    Family: {f.name}, CT: {f.test_cycle_time_hours} h · Created by:{" "}
                    {f.created_by_email || f.created_by_user_id}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

export default FamiliesPage;