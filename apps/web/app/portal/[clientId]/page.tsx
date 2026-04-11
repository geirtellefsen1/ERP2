"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface PortalStats {
  pending_invoices: number;
  overdue_invoices: number;
  recent_documents: number;
  next_due_date: string | null;
}

function getClientToken() {
  return typeof window !== "undefined" ? localStorage.getItem("bpo_client_token") : null;
}

export default function PortalClientPage() {
  const params = useParams();
  const clientId = params.clientId as string;
  const [stats, setStats] = useState<PortalStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // In production: fetch real data
    // For now: show placeholder data
    setStats({
      pending_invoices: 0,
      overdue_invoices: 0,
      recent_documents: 0,
      next_due_date: null,
    });
    setLoading(false);
  }, [clientId]);

  const cards = [
    {
      label: "Documents",
      value: stats?.recent_documents ?? "—",
      desc: "Upload & manage documents",
      href: `/portal/${clientId}/documents`,
      color: "blue",
    },
    {
      label: "Invoices",
      value: stats?.pending_invoices ?? "—",
      desc: `${stats?.overdue_invoices ?? 0} overdue`,
      href: `/portal/${clientId}/invoices`,
      color: "amber",
    },
    {
      label: "Reports",
      value: "→",
      desc: "View financial reports",
      href: `/portal/${clientId}/reports`,
      color: "purple",
    },
    {
      label: "Settings",
      value: "→",
      desc: "Account & preferences",
      href: `/portal/${clientId}/settings`,
      color: "slate",
    },
  ];

  const colorMap: Record<string, string> = {
    blue: "bg-blue-50 border-blue-100 text-blue-700 hover:bg-blue-100",
    amber: "bg-amber-50 border-amber-100 text-amber-700 hover:bg-amber-100",
    purple: "bg-purple-50 border-purple-100 text-purple-700 hover:bg-purple-100",
    slate: "bg-slate-50 border-slate-100 text-slate-700 hover:bg-slate-100",
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Welcome to Your Portal</h1>
        <p className="text-slate-500 mt-1">Your BPO services dashboard</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className={`block p-5 rounded-xl border transition-colors ${colorMap[card.color]}`}
          >
            <div className="text-2xl font-bold mb-1">{card.value}</div>
            <div className="font-semibold text-sm">{card.label}</div>
            <div className="text-xs opacity-70 mt-1">{card.desc}</div>
          </Link>
        ))}
      </div>

      {/* Quick actions */}
      <div className="mt-8 bg-white rounded-xl border border-slate-100 shadow-sm p-6">
        <h2 className="font-semibold text-slate-900 mb-4">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <Link
            href={`/portal/${clientId}/documents`}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            + Upload Document
          </Link>
          <Link
            href={`/portal/${clientId}/invoices`}
            className="px-4 py-2 border border-slate-300 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-50 transition-colors"
          >
            View Invoices
          </Link>
          <Link
            href={`/portal/${clientId}/reports`}
            className="px-4 py-2 border border-slate-300 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-50 transition-colors"
          >
            Financial Reports
          </Link>
        </div>
      </div>
    </div>
  );
}
