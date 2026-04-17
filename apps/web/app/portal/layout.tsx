"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { ToastProvider } from "@/components/ui/toast"

function getUser() {
  if (typeof window === "undefined") return null
  try {
    const clientUser = localStorage.getItem("bpo_client_user")
    if (clientUser) return JSON.parse(clientUser)
    const bpoUser = localStorage.getItem("bpo_user")
    if (bpoUser) return JSON.parse(bpoUser)
    return null
  } catch {
    return null
  }
}

function hasToken(): boolean {
  if (typeof window === "undefined") return false
  return !!(
    localStorage.getItem("bpo_client_token") ||
    localStorage.getItem("bpo_token")
  )
}

export default function PortalLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    if (!hasToken()) {
      router.replace("/portal/login")
      return
    }
    setUser(getUser())
  }, [router])

  return (
    <ToastProvider>
      <div className="min-h-screen bg-slate-50">
        <header className="bg-white border-b border-slate-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div>
              <span className="text-lg font-bold text-slate-800">
                ClaudERP Portal
              </span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-slate-500">
                {user?.clientName || user?.email || "Loading..."}
              </span>
              <button
                onClick={() => {
                  localStorage.removeItem("bpo_client_token")
                  localStorage.removeItem("bpo_client_user")
                  router.replace("/portal/login")
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
    </ToastProvider>
  )
}
