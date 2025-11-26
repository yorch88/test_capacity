import React, { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

function UsersPage() {
  const [users, setUsers] = useState([]);
  const token = localStorage.getItem("access_token");

  async function loadUsers() {
    try {
      const res = await fetch(`${API_BASE}/auth/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      setUsers(data);
    } catch (err) {
      console.error(err);
    }
  }

  useEffect(() => {
    if (token) {
      loadUsers();
    }
  }, [token]);

  async function activateUser(id) {
    try {
      const res = await fetch(`${API_BASE}/auth/users/${id}/activate`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        console.error("Failed to activate user");
        return;
      }
      loadUsers();
    } catch (err) {
      console.error(err);
    }
  }

  if (!token) {
    return <p className="text-sm text-slate-400">Please log in as admin via API to manage users.</p>;
  }

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 text-sm">
      <h2 className="text-lg font-semibold mb-4">Users</h2>
      {users.length === 0 ? (
        <p className="text-slate-400">No users found.</p>
      ) : (
        <ul className="divide-y divide-slate-800">
          {users.map((u) => (
            <li key={u.id} className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium">{u.username}</p>
                <p className="text-slate-400">{u.email}</p>
                <p className="text-xs text-slate-500">
                  Role: {u.is_admin ? "Admin" : "User"} · Status:{" "}
                  {u.is_active ? "Active" : "Inactive"}
                </p>
              </div>
              {!u.is_active && (
                <button
                  onClick={() => activateUser(u.id)}
                  className="inline-flex items-center justify-center rounded-lg bg-emerald-500 hover:bg-emerald-400 px-3 py-1 text-xs font-medium text-slate-950"
                >
                  Give access
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default UsersPage;