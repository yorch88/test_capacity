import React, { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

function HistoryPage() {
    const [pagination, setPagination] = useState({
  page: 1,
  page_size: 20,
  total_pages: 1,
  total: 0,
});
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

 async function loadHistory(page = 1) {
  if (!token) return;
  setLoading(true);
  try {
    const params = new URLSearchParams();
    if (filters.sku) params.append("sku", filters.sku);
    if (filters.family_id) params.append("family_id", filters.family_id);
    params.append("page", String(page));
    params.append("page_size", String(pagination.page_size));

    const res = await fetch(`${API_BASE}/analytics?${params.toString()}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      console.error("Failed to load history");
      setLoading(false);
      return;
    }
    const data = await res.json();
    setRecords(data.items);
    setPagination({
      page: data.page,
      page_size: data.page_size,
      total_pages: data.total_pages,
      total: data.total,
    });
  } catch (err) {
    console.error(err);
  } finally {
    setLoading(false);
  }
}

  useEffect(() => {
    if (token) {
      loadFamilies();
      loadHistory(1);
    }
  }, [token]);

  function handleChange(e) {
    const { name, value } = e.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    loadHistory(1);
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
                <th className="px-3 py-2 border-b border-slate-800 text-right">Prod input CT (min)</th>
                <th className="px-3 py-2 border-b border-slate-800 text-right">Input capacity (u/d)</th>
                <th className="px-3 py-2 border-b border-slate-800 text-left">Est. first unit</th>
                <th className="px-3 py-2 border-b border-slate-800 text-left">Commit Date on risk?</th>
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
                  <td className="px-3 py-2 border-b border-slate-800 text-right">
                    {r.input_cycle_time_minutes_input
                      ? r.input_cycle_time_minutes_input.toFixed(2)
                      : "-"}
                  </td>
                  <td className="px-3 py-2 border-b border-slate-800 text-right">
                    {r.input_capacity_units_per_day
                      ? r.input_capacity_units_per_day.toFixed(2)
                      : "-"}
                  </td>
                  <td className="px-3 py-2 border-b border-slate-800">
                  {r.estimated_first_unit_datetime
                    ? new Date(r.estimated_first_unit_datetime).toLocaleString()
                    : "-"}
                </td>
                <td className="px-3 py-2 border-b border-slate-800">
                  <span
                    className={`px-2 py-1 rounded text-white ${
                      r.commit_on_risk ? "bg-red-600" : "bg-green-600"
                    }`}
                  >
                    {r.commit_on_risk ? "Yes" : "No"}
                  </span>
                </td>
                </tr>
              ))}
            </tbody>
          </table>
          
        )}

{records.length > 0 && (
  <div className="mt-3 flex items-center justify-between text-xs text-slate-300">
    <div>
      Page {pagination.page} of {pagination.total_pages} ·{" "}
      {pagination.total} records
    </div>
    <div className="flex gap-2">
      <button
        type="button"
        disabled={pagination.page <= 1 || loading}
        onClick={() => loadHistory(pagination.page - 1)}
        className="px-3 py-1 rounded-md border border-slate-700 disabled:opacity-40"
      >
        Prev
      </button>
      <button
        type="button"
        disabled={
          pagination.page >= pagination.total_pages || loading
        }
        onClick={() => loadHistory(pagination.page + 1)}
        className="px-3 py-1 rounded-md border border-slate-700 disabled:opacity-40"
      >
        Next
      </button>
    </div>
  </div>
)}

      </section>
    </div>
  );
}

export default HistoryPage;
