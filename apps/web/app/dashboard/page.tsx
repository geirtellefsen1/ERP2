"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

interface Stats {
  total_clients: number;
  active_clients: number;
  pending_tasks: number;
  overdue_invoices: number;
}

interface Client {
  id: number;
  name: string;
  country: string;
  industry: string;
  is_active: boolean;
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

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [recentClients, setRecentClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const clients: Client[] = await apiGet("/api/v1/clients");
        setRecentClients(clients.slice(0, 5));
        setStats({
          total_clients: clients.length,
          active_clients: clients.filter((c) => c.is_active).length,
          pending_tasks: 0,
          overdue_invoices: 0,
        });
      } catch {
        // API not available or not authenticated
        setStats({ total_clients: 0, active_clients: 0, pending_tasks: 0, overdue_invoices: 0 });
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const statCards = [
    { label: "Total Clients", value: stats?.total_clients ?? "—", emoji: "🏢" },
    { label: "Active Clients", value: stats?.active_clients ?? "—", emoji: "✅" },
    { label: "Pending Tasks", value: stats?.pending_tasks ?? "—", emoji: "⏳" },
    { label: "Overdue Invoices", value: stats?.overdue_invoices ?? "—", emoji: "⚠️" },
  ];

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Agency Dashboard</h1>
        <p className="text-slate-500 mt-1">Welcome back — here's what's happening today.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((card) => (
          <div key={card.label} className="bg-white rounded-xl p-5 shadow-sm border border-slate-100">
            <div className="text-3xl mb-2">{card.emoji}</div>
            <div className="text-2xl font-bold text-slate-900">
              {loading ? "…" : card.value}
            </div>
            <div className="text-sm text-slate-500">{card.label}</div>
          </div>
        ))}
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <Link
          href="/dashboard/clients"
          className="bg-blue-50 border border-blue-100 rounded-xl p-5 hover:bg-blue-100 transition-colors"
        >
          <div className="text-xl mb-1">🏢</div>
          <div className="font-semibold text-blue-900">Manage Clients</div>
          <div className="text-sm text-blue-600">View, add and edit client companies</div>
        </Link>
        <Link
          href="/dashboard/tasks"
          className="bg-green-50 border border-green-100 rounded-xl p-5 hover:bg-green-100 transition-colors"
        >
          <div className="text-xl mb-1">✅</div>
          <div className="font-semibold text-green-900">Task Queue</div>
          <div className="text-sm text-green-600">Manage SLA tasks and assignments</div>
        </Link>
        <Link
          href="/dashboard/reports"
          className="bg-purple-50 border border-purple-100 rounded-xl p-5 hover:bg-purple-100 transition-colors"
        >
          <div className="text-xl mb-1">📊</div>
          <div className="font-semibold text-purple-900">Reports</div>
          <div className="text-sm text-purple-600">P&L, Cashflow, Compliance</div>
        </Link>
      </div>

      {/* Recent clients */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h2 className="font-semibold text-slate-900">Recent Clients</h2>
          <Link href="/dashboard/clients" className="text-sm text-blue-600 hover:text-blue-700">
            View all →
          </Link>
        </div>
        {loading ? (
          <div className="p-6 text-slate-400 text-center">Loading...</div>
        ) : recentClients.length === 0 ? (
          <div className="p-6 text-slate-400 text-center">
            No clients yet.{" "}
            <Link href="/dashboard/clients" className="text-blue-600">
              Add your first client
            </Link>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-slate-50">
              <tr>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Name</th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Country</th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Industry</th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {recentClients.map((client) => (
                <tr key={client.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 font-medium text-slate-900">{client.name}</td>
                  <td className="px-6 py-4 text-slate-600">{client.country}</td>
                  <td className="px-6 py-4 text-slate-600">{client.industry || "—"}</td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        client.is_active
                          ? "bg-green-100 text-green-700"
                          : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {client.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
