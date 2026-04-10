"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/dashboard/clients", label: "Clients", icon: "🏢" },
  { href: "/dashboard/tasks", label: "Tasks", icon: "✅" },
  { href: "/dashboard/reports", label: "Reports", icon: "📋" },
  { href: "/dashboard/billing", label: "Billing", icon: "💳" },
  { href: "/dashboard/settings", label: "Settings", icon: "⚙️" },
];

function getUser() {
  if (typeof window === "undefined") return null;
  try {
    const u = localStorage.getItem("bpo_user");
    return u ? JSON.parse(u) : null;
  } catch {
    return null;
  }
}

export default function Sidebar() {
  const pathname = usePathname();
  const user = getUser();

  return (
    <aside className="w-64 bg-slate-900 text-white flex flex-col min-h-screen">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-slate-700">
        <div className="text-xl font-bold tracking-tight">BPO Nexus</div>
        <div className="text-xs text-slate-400 mt-0.5">
          {user ? `${user.agency_id}` : "Loading..."}
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                active
                  ? "bg-blue-600 text-white"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              }`}
            >
              <span>{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* User */}
      <div className="px-4 py-4 border-t border-slate-700">
        <div className="text-sm text-slate-300">{user?.email || "Unknown"}</div>
        <div className="text-xs text-slate-500 capitalize">{user?.role || "agent"}</div>
        <button
          onClick={() => {
            localStorage.removeItem("bpo_token");
            localStorage.removeItem("bpo_user");
            window.location.href = "/login";
          }}
          className="mt-2 text-xs text-slate-500 hover:text-red-400 transition-colors"
        >
          Sign Out
        </button>
      </div>
    </aside>
  );
}
