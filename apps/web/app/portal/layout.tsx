"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

function getClientUser() {
  if (typeof window === "undefined") return null;
  try {
    const u = localStorage.getItem("bpo_client_user");
    return u ? JSON.parse(u) : null;
  } catch { return null; }
}

export default function PortalLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  useEffect(() => {
    const user = getClientUser();
    if (!user) {
      router.replace("/portal/login");
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Portal header */}
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <span className="text-lg font-bold text-slate-800">Client Portal</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-500">
              {getClientUser()?.clientName || "Loading..."}
            </span>
            <button
              onClick={() => {
                localStorage.removeItem("bpo_client_token");
                localStorage.removeItem("bpo_client_user");
                router.replace("/portal/login");
              }}
              className="text-sm text-slate-400 hover:text-red-500 transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>
      {children}
    </div>
  );
}
