import React, { useEffect, useState } from "react";
import DateTimePicker from "./DateTimePicker.jsx";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

function AnalyticsPage() {
  const [families, setFamilies] = useState([]);
  const [form, setForm] = useState({
  family_id: "",
  sku: "",
  quantity: 300,
  capacity_slots: 10,
  manpower_qty: 8,
  units_per_manpower_per_day: 8,
  });

  const [fechaRelease, setFechaRelease] = useState(null);
  const [result, setResult] = useState(null);

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

  useEffect(() => {
    if (token) {
      loadFamilies();
    }
  }, [token]);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!token) return;
    if (!fechaRelease) {
      console.error("Release datetime is required");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/analytics`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        
        body: JSON.stringify({
        ...form,
        quantity: Number(form.quantity),
        capacity_slots: Number(form.capacity_slots),
        manpower_qty: Number(form.manpower_qty),
        units_per_manpower_per_day: Number(form.units_per_manpower_per_day),
        fecha_release: fechaRelease.toISOString(),
      }),
      });
      if (!res.ok) {
        console.error("Failed to compute analytics");
        return;
      }
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
    }
  }

  if (!token) {
    return (
      <div className="max-w-xl text-sm space-y-2">
        <p className="text-slate-200 font-medium">How to use the API</p>
        <ol className="list-decimal list-inside text-slate-400 space-y-1">
          <li>Call <code>/api/auth/register-initial-admin</code> via Postman or curl to create the first admin.</li>
          <li>Call <code>/api/auth/login</code> and save the returned access token in <code>localStorage.access_token</code>.</li>
          <li>Reload this page.</li>
        </ol>
      </div>
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[2fr,3fr]">
      <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 text-sm">
        <h2 className="text-lg font-semibold mb-4">Compute test capacity</h2>
        <form className="space-y-3" onSubmit={handleSubmit}>
          <div>
            <label className="block mb-1">Family</label>
            <select
              name="family_id"
              className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2"
              value={form.family_id}
              onChange={handleChange}
              required
            >
              <option value="">Select a family</option>
              {families.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name} (CT {f.test_cycle_time_hours} h)
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block mb-1">SKU (optional)</label>
            <input
              name="sku"
              value={form.sku}
              onChange={handleChange}
              className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2"
              placeholder="SKU-123"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block mb-1">Quantity</label>
              <input
                type="number"
                name="quantity"
                min="1"
                value={form.quantity}
                onChange={handleChange}
                className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2"
                required
              />
            </div>
            <div>
              <label className="block mb-1">Capacity slots</label>
              <input
                type="number"
                name="capacity_slots"
                min="1"
                value={form.capacity_slots}
                onChange={handleChange}
                className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2"
                required
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block mb-1">Manpower qty</label>
              <input
                type="number"
                name="manpower_qty"
                min="1"
                value={form.manpower_qty}
                onChange={handleChange}
                className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2"
                required
              />
            </div>
            <div>
              <label className="block mb-1">Units per manpower per day</label>
              <input
                type="number"
                name="units_per_manpower_per_day"
                min="1"
                value={form.units_per_manpower_per_day}
                onChange={handleChange}
                className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2"
                required
              />
            </div>
          </div>
          <div>
            <label className="block mb-1">Target release - Commit Date</label>
            <DateTimePicker
              value={fechaRelease}
              onChange={(date) => setFechaRelease(date)}
            />
          </div>
          <button
            type="submit"
            className="mt-2 inline-flex items-center justify-center rounded-lg bg-emerald-500 hover:bg-emerald-400 px-4 py-2 text-sm font-medium text-slate-950"
          >
            Calculate
          </button>
        </form>
      </section>
      <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 text-sm">
        <h2 className="text-lg font-semibold mb-4">Result</h2>
        {!result ? (
          <p className="text-slate-400">Fill the form and calculate to see the result.</p>
        ) : (
          <div className="space-y-2">
            <p>
              <span className="font-semibold">Bottleneck:</span> {result.bottleneck_type}
            </p>
            <p>
              <span className="font-semibold">Input cycle time:</span>{" "}
              {result.input_cycle_time_minutes.toFixed(2)} minutes per unit
            </p>
            <p>
              <span className="font-semibold">First unit must arrive at:</span>{" "}
              {new Date(result.first_unit_datetime).toLocaleString()}
            </p>
            <p>
              <span className="font-semibold">Total duration:</span>{" "}
              {result.total_duration_hours.toFixed(2)} hours
            </p>
            <p className="text-slate-400 mt-3">
              Equipment capacity: {result.equipment_capacity_units_per_day.toFixed(2)} units/day · Manpower capacity:{" "}
              {result.manpower_capacity_units_per_day.toFixed(2)} units/day
            </p>
          </div>
        )}
      </section>
    </div>
  );
}

export default AnalyticsPage;