"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import Sidebar from "@/components/Sidebar"
import TopBar from "@/components/TopBar"
import { ToastProvider } from "@/components/ui/toast"
import { ClientProvider } from "@/lib/client-context"
import { I18nProvider } from "@/i18n/provider"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()

  useEffect(() => {
    const token = localStorage.getItem("bpo_token")
    if (!token) {
      router.replace("/login")
    }
  }, [router])

  return (
    <I18nProvider>
      <ToastProvider>
        <ClientProvider>
          <div className="flex h-screen overflow-hidden">
            <Sidebar />
            <main className="flex-1 overflow-y-auto bg-background">
              <TopBar />
              <div className="mx-auto max-w-6xl px-6 py-6">{children}</div>
            </main>
          </div>
        </ClientProvider>
      </ToastProvider>
    </I18nProvider>
  )
}
