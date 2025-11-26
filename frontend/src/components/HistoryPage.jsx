import React, { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

function HistoryPage() {
  const [records, setRecords] = useState([]);
  const [families, setFamilies] = useState([]);
  const [filters, setFilters] = useState({
    sku: "",
    family_id: "",
  });
  const [loading, setLoading] = useState(false);

  const token = localStorage.getItem("access_token");

  async function loadFamilies() {
    try {
      const res = await fetch(`${API_BASE}/families`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      setFamilies(data);
    } catch (err) {
      console.error(err);
    }
  }

  async function loadHistory() {
    if (!token) return;
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.sku) params.append("sku", filters.sku);
      if (filters.family_id) params.append("family_id", filters.family_id);

      const res = await fetch(`${API_BASE}/analytics?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        console.error("Failed to load history");
        setLoading(false);
        return;
      }
      const data = await res.json();
      setRecords(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      loadFamilies();
      loadHistory();
    }
  }, [token]);

  function handleChange(e) {
    const { name, value } = e.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    loadHistory();
  }

  if (!token) {
    return <p className="text-sm text-slate-400">Please log in to view history.</p>;
  }

  return (
    <div className="space-y-4">
      <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 text-sm">
        <h2 className="text-lg font-semibold mb-3">History filters</h2>
        <form onSubmit={handleSubmit} className="flex flex-wrap gap-3 items-end">
          <div className="flex flex-col">
            <label className="mb-1">SKU</label>
            <input
              name="sku"
              value={filters.sku}
              onChange={handleChange}
              placeholder="e.g. ABC-123"
              className="rounded-lg bg-slate-900 border border-slate-700 px-3 py-2"
            />
          </div>
          <div className="flex flex-col">
            <label className="mb-1">Family</label>
            <select
              name="family_id"
              value={filters.family_id}
              onChange={handleChange}
              className="rounded-lg bg-slate-900 border border-slate-700 px-3 py-2"
            >
              <option value="">All families</option>
              {families.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name}
                </option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            className="inline-flex items-center justify-center rounded-lg bg-emerald-500 hover:bg-emerald-400 px-4 py-2 text-sm font-medium text-slate-950"
          >
            {loading ? "Loading..." : "Apply filters"}
          </button>
        </form>
      </section>

      <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 text-sm overflow-auto">
        <h2 className="text-lg font-semibold mb-3">History</h2>
        {records.length === 0 ? (
          <p className="text-slate-400">No records found.</p>
        ) : (
          <table className="min-w-full text-xs border-collapse">
            <thead className="bg-slate-950">
              <tr>
                <th className="px-3 py-2 border-b border-slate-800 text-left">Created at</th>
                <th className="px-3 py-2 border-b border-slate-800 text-left">Family</th>
                <th className="px-3 py-2 border-b border-slate-800 text-left">SKU</th>
                <th className="px-3 py-2 border-b border-slate-800 text-right">Qty</th>
                <th className="px-3 py-2 border-b border-slate-800 text-right">Slots</th>
                <th className="px-3 py-2 border-b border-slate-800 text-right">Manpower</th>
                <th className="px-3 py-2 border-b border-slate-800 text-right">Units/tech/day</th>
                <th className="px-3 py-2 border-b border-slate-800 text-left">Release datetime</th>
                <th className="px-3 py-2 border-b border-slate-800 text-left">First unit datetime</th>
                <th className="px-3 py-2 border-b border-slate-800 text-right">CT (min)</th>
                <th className="px-3 py-2 border-b border-slate-800 text-left">Bottleneck</th>
                <th className="px-3 py-2 border-b border-slate-800 text-left">Created by</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r) => (
                <tr key={r.id} className="odd:bg-slate-900 even:bg-slate-950/40">
                  <td className="px-3 py-2 border-b border-slate-800">
                    {new Date(r.created_at).toLocaleString()}
                  </td>
                  <td className="px-3 py-2 border-b border-slate-800">
                    {r.family_name || r.family_id}
                  </td>
                  <td className="px-3 py-2 border-b border-slate-800">{r.sku || "-"}</td>
                  <td className="px-3 py-2 border-b border-slate-800 text-right">{r.quantity}</td>
                  <td className="px-3 py-2 border-b border-slate-800 text-right">{r.capacity_slots}</td>
                  <td className="px-3 py-2 border-b border-slate-800 text-right">{r.manpower_qty}</td>
                  <td className="px-3 py-2 border-b border-slate-800 text-right">
                    {r.units_per_manpower_per_day}
                  </td>
                  <td className="px-3 py-2 border-b border-slate-800">
                    {new Date(r.fecha_release).toLocaleString()}
                  </td>
                  <td className="px-3 py-2 border-b border-slate-800">
                    {new Date(r.first_unit_datetime).toLocaleString()}
                  </td>
                  <td className="px-3 py-2 border-b border-slate-800 text-right">
                    {r.input_cycle_time_minutes.toFixed(2)}
                  </td>
                  <td className="px-3 py-2 border-b border-slate-800">
                    {r.bottleneck_type}
                  </td>
                  <td className="px-3 py-2 border-b border-slate-800">
                    {r.created_by_email || r.created_by_user_id}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

export default HistoryPage;
