"use client";
import { useEffect, useState } from "react";

interface Client {
  id: number;
  name: string;
  country: string;
  industry: string;
  registration_number: string | null;
  is_active: boolean;
  created_at: string;
}

function getToken() {
  return typeof window !== "undefined" ? localStorage.getItem("bpo_token") : null;
}

async function apiGet(path: string) {
  const token = getToken();
  const res = await fetch(`http://localhost:8000${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 401) {
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  return res.json();
}

async function apiPost(path: string, body: object) {
  const token = getToken();
  const res = await fetch(`http://localhost:8000${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const d = await res.json();
    throw new Error(d.detail || "Request failed");
  }
  return res.json();
}

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ name: "", country: "ZA", industry: "", registration_number: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    try {
      const data: Client[] = await apiGet("/api/v1/clients");
      setClients(data);
    } catch {
      setError("Failed to load clients");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await apiPost("/api/v1/clients", form);
      setShowModal(false);
      setForm({ name: "", country: "ZA", industry: "", registration_number: "" });
      load();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Clients</h1>
          <p className="text-slate-500">{clients.length} client{clients.length !== 1 ? "s" : ""} total</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="bg-blue-600 text-white font-semibold px-5 py-2.5 rounded-lg hover:bg-blue-700 transition-colors"
        >
          + Add Client
        </button>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 text-red-700 rounded-lg px-4 py-2 text-sm">{error}</div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading...</div>
        ) : clients.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            No clients yet. Add your first client to get started.
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-slate-50">
              <tr>
                {["Name", "Country", "Industry", "Reg. Number", "Status", "Created"].map((h) => (
                  <th key={h} className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {clients.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 font-medium text-slate-900">{c.name}</td>
                  <td className="px-6 py-4 text-slate-600">{c.country}</td>
                  <td className="px-6 py-4 text-slate-600">{c.industry || "—"}</td>
                  <td className="px-6 py-4 text-slate-600 font-mono text-sm">{c.registration_number || "—"}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      c.is_active ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-600"
                    }`}>
                      {c.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-500 text-sm">
                    {c.created_at ? new Date(c.created_at).toLocaleDateString() : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Add Client Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
            <h2 className="text-lg font-bold text-slate-900 mb-4">Add New Client</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Company Name *</label>
                <input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full border border-slate-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Country *</label>
                <select
                  value={form.country}
                  onChange={(e) => setForm({ ...form, country: e.target.value })}
                  className="w-full border border-slate-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                >
                  <option value="ZA">South Africa 🇿🇦</option>
                  <option value="NO">Norway 🇳🇴</option>
                  <option value="UK">United Kingdom 🇬🇧</option>
                  <option value="EU">European Union 🇪🇺</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Industry</label>
                <input
                  value={form.industry}
                  onChange={(e) => setForm({ ...form, industry: e.target.value })}
                  className="w-full border border-slate-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  placeholder="e.g. Hospitality, Retail, Construction"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Registration Number</label>
                <input
                  value={form.registration_number}
                  onChange={(e) => setForm({ ...form, registration_number: e.target.value })}
                  className="w-full border border-slate-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  placeholder="CIPC / Brønnøysund / Companies House"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 bg-blue-600 text-white font-semibold py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? "Saving..." : "Add Client"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
